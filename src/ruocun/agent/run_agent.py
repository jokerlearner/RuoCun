"""Synchronous child Session and tool execution from the reference runAgent.ts (MIT)."""
from __future__ import annotations

import asyncio
import copy
import os
import threading
import uuid
from collections.abc import Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager, nullcontext
from contextvars import ContextVar
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any, Literal, cast

from ..client.resilient import ResilientContext, ResilientResult, streamChatResilient
from ..client.types import ChatMessage, ImageData, StreamChatOptions
from ..config.compat import reasoning_effort, resolve_env
from ..config.model_selection import getAgentModel
from ..hooks.hooks import HookRuntime
from ..hooks.journal import HookOutcomeUnknown
from ..obs.backend import observationScope, spanScope
from ..obs.wrap import wrapRequest
from ..permissions.runtime import PermissionRuntime
from ..permissions.settings import PermissionMode
from ..session.contract import (
    ArchiveImport,
    ArchiveRewrite,
    RunRecord,
    RunRef,
    ToolRef,
    ToolResult,
    task_inbox_messages,
)
from ..session.conversation import Conversation
from ..session.session import Session
from ..tools.agent import AgentFailure, AgentRequest
from ..tools.registry import ToolRegistry, ToolSnapshot
from ..tools.tool_batch import UnknownToolOutcome
from ..tools.tools_for_mode import apiToolsForMode
from ..tools.types import ToolContext
from .agent_defs import AgentDefinition
from .agent_handoff import Handoff
from .agent_hooks import startAgentHooks, stopAgentHooks
from .agent_mcp import AgentMcpRuntime
from .agent_memory import agentMemoryPrompt
from .background_types import ExecutionStatus
from .bundled_agents import bundledAgentDefinitions
from .context_runtime import ContextJournal, ContextManager
from .fork_agent import FORK_AGENT, forkRequestMessages
from .loop import Journal, Request, TurnResult, run_turn
from .resume_agent import (
    agentCheckpointSnapshot,
    agentOutputMessages,
    agentOutputOffset,
    agentRecoveryMaterial,
    prepareAgentArchive,
)
from .worktree import GitBoundaryError, Worktree, finishAgentWorktree, openAgentWorktree

if TYPE_CHECKING:
    from .tasks import BgTask, ForegroundAgent

_DISALLOWED = frozenset({"Agent", "AskUserQuestion", "TaskStop", "TaskWait", "EnterWorktree", "ExitWorktree"})
_BACKGROUND_TOOLS = frozenset({
    "Read", "ListDir", "Grep", "Glob", "Bash", "BashOutput", "KillShell", "Write", "Edit", "NotebookEdit",
    "WebSearch", "WebFetch", "TodoWrite", "Skill", "MemoryWrite", "MemoryRead", "ArchiveRead", "NotifyUser", "MessageParent",
})
_MEMORY_TOOLS = frozenset({"Read", "Write", "Edit"})
agentApprovalSignal: ContextVar[threading.Event | None] = ContextVar("agentApprovalSignal", default=None)


def buildAgentRegistry(
    registry: ToolRegistry, definition: AgentDefinition, *, plan: bool = False, is_async: bool = False,
) -> ToolRegistry:
    denied = _DISALLOWED | ({"EnterPlanMode", "ExitPlanMode"} if plan else set())
    allowed = definition.tools
    memory_tools = _MEMORY_TOOLS if definition.memory else frozenset()
    return registry.filtered(lambda tool: tool.name not in denied
                             and (not is_async or tool.name in _BACKGROUND_TOOLS)
                             and (tool.name in memory_tools or (tool.name not in definition.disallowed_tools
                                  and (allowed is None or allowed == ("*",) or tool.name in allowed)))
                             and (not plan or (tool.capability not in {"write", "exec"}
                                              and not tool.name.startswith("mcp__"))))


def _positive_integer(value: str | None, default: int) -> int:
    try:
        candidate = float(value or "0")
    except ValueError:
        return default
    return int(candidate) if candidate.is_integer() and 0 < candidate <= 2**53 - 1 else default


class _LinkedSignal(threading.Event):
    def __init__(self, parent: threading.Event) -> None:
        super().__init__()
        self._parent = parent

    def is_set(self) -> bool:
        return super().is_set() or self._parent.is_set()


class _AgentJournal:
    def __init__(
        self, conversation: Conversation, record: RunRecord, parent: ToolRef, prepared: PreparedAgentRun,
    ) -> None:
        self.conversation, self.record, self.parent = conversation, record, parent
        self.prepared = prepared
        self.recoverable = record.kind == "agent" and prepared.definition.agent_type not in {"explore", "plan"}
        self.foreground: ForegroundAgent | None = None

    async def save(self, session: Session) -> None:
        await self._save_messages(session.messages, usage=dict(session.usage))

    def redact(self, text: str) -> str:
        return self.conversation.redact(text)

    async def archive_read(self, identity: str, offset: int, limit: int) -> dict[str, Any]:
        return await self.conversation.worker.archive_read(identity, self.record.run_ref.run_id,
                                                            offset=offset, limit=limit)

    async def model_boundary(self) -> None:
        if self.recoverable or self.foreground is not None:
            session = self.prepared.session
            await self._save_messages(session.messages, decrement=True, deliver_inbox=True, usage=dict(session.usage))

    async def handoff_boundary(self) -> None:
        if self.foreground is not None and self.foreground.record.snapshot.get("task_inbox"):
            await self._save_messages(self.prepared.session.messages, deliver_inbox=True)

    async def _save_messages(
        self, messages: list[dict[str, Any]], *, status: str | None = None, decrement: bool = False,
        deliver_inbox: bool = False, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None, **metadata: Any,
    ) -> None:
        async with self.foreground.checkpoint_lock if self.foreground is not None else nullcontext():
            await self._commit_messages(messages, status=status, decrement=decrement, deliver_inbox=deliver_inbox,
                                        archive_rewrite=archive_rewrite, archive_import=archive_import, **metadata)

    async def _commit_messages(
        self, messages: list[dict[str, Any]], *, status: str | None, decrement: bool, deliver_inbox: bool,
        archive_rewrite: ArchiveRewrite | None, archive_import: ArchiveImport | None, **metadata: Any,
    ) -> None:
        current = self.foreground.record if self.foreground is not None else self.record
        data = {**current.snapshot, **metadata}
        data["archive_scope"] = current.run_ref.run_id
        pending = task_inbox_messages(data.get("task_inbox", [])) if deliver_inbox else []
        candidate_messages = [*messages, *pending] if pending else messages
        try:
            if archive_rewrite is not None and list(archive_rewrite.expected_messages) != self.prepared.session.messages:
                raise RuntimeError("子代理压缩期间上下文已变化，保留原检查点。")
            remaining = current.snapshot.get("turnsRemaining", self.prepared.max_turns)
            if decrement and remaining <= 0:
                raise RuntimeError("同步代理剩余轮次已耗尽。")
            data.update(turnsRemaining=remaining - int(decrement), permissionMode=self.prepared.permission.getMode())
            if self.foreground is not None:
                data["description"] = self.foreground.task.description
            if self.recoverable:
                material = agentRecoveryMaterial(self.prepared, candidate_messages)
                previous = current.snapshot.get("recovery_material", material)
                identity = ("worktree", "worktreeIdentity", "workspaceRoot", "workspaceIdentity")
                if any(material[key] != previous[key] for key in identity):
                    raise RuntimeError("同步代理工作区身份已变化，停止执行并保留原检查点。")
                data = agentCheckpointSnapshot(data, material["messages"], material, remaining - int(decrement), pending)
            else:
                data["messages"] = copy.deepcopy(candidate_messages)
                if pending:
                    data["task_inbox"] = []
            operation_id = "agent-save-" + uuid.uuid4().hex
            data["archive_operation_id"] = operation_id
            if "recovery_material" in data:
                data["recovery_material"]["archive_operation_id"] = operation_id
            candidate = replace(current, status=status or current.status, snapshot=data)
            handle = self.conversation.stage_background(candidate, None, operation_id=operation_id,
                archive_rewrite=archive_rewrite, archive_import=archive_import)
            await handle.wait()
        except BaseException:
            self.conversation.blocked = True
            raise
        self.record = candidate
        messages.extend(pending)
        if self.foreground is not None:
            self.foreground.record = candidate
            self.foreground.task.messages[:] = await agentOutputMessages(self.conversation, candidate)

    async def finish(self, session: Session, status: str, result: str | None = None) -> None:
        await self._save_messages(session.messages, status=status, usage=dict(session.usage),
                                  endedAt=time_ns() // 1_000_000, result=result)

    async def replace_context(self, session: Session, messages: list[dict[str, Any]], *, reset_prompt: bool = True) -> None:
        await self._save_messages(messages)
        session.messages = messages
        if reset_prompt:
            session.lastPromptTokens = None
            session.lastSentLength = 0

    async def compact_context(self, session: Session, messages: list[dict[str, Any]], *, rewrite: ArchiveRewrite) -> None:
        await self._save_messages(messages, archive_rewrite=rewrite)
        session.messages = messages
        session.lastPromptTokens = None
        session.lastSentLength = 0

    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> ToolResult | None:
        return await self.conversation.scoped_intent(ToolRef(self.record.run_ref.run_id, call_id), name, args, effect,
                                                     agent_run=self.record.run_ref, parent_tool_ref=self.parent)

    async def result(self, call_id: str, text: str, image_data: ImageData | None = None) -> None:
        await self.conversation.scoped_result(ToolRef(self.record.run_ref.run_id, call_id), text, image_data)


def _child_permission(parent_mode: PermissionMode, requested: str | None, definition: AgentDefinition) -> PermissionMode:
    selected = requested if requested is not None else definition.permission_mode
    if selected not in {None, "normal", "plan", "auto", "default", "bypassPermissions"}:
        raise AgentFailure(f"代理权限模式无效: {selected}。")
    if parent_mode == "plan" or selected == "plan":
        return "plan"
    if parent_mode == "bypassPermissions" or selected in {None, "normal"}:
        return parent_mode
    if selected == "bypassPermissions":
        return "bypassPermissions"
    return "auto" if selected == "auto" else "default"


def _system_prompt(
    definition: AgentDefinition, project: str, cwd: Path, available: list[str], *,
    memory_root: Path, user_root: Path,
) -> str:
    prompt = definition.system_prompt
    if project and not definition.omit_project_instructions:
        prompt = f"{project}\n\n# 你的专用角色({definition.agent_type})\n{prompt}"
    prompt += (f"\n\n## 当前环境\n- 工作目录: {cwd}\n- 平台: {os.name}\n"
               f"- 可用工具: {', '.join(available)}\n- 结果引用使用绝对路径，不复述整块文件。")
    if definition.critical_system_reminder:
        prompt += "\n\n" + definition.critical_system_reminder
    if definition.memory:
        prompt += "\n\n" + agentMemoryPrompt(definition.agent_type, definition.memory, memory_root, user_root)
    return prompt


@dataclass(frozen=True)
class PreparedAgentRun:
    session: Session
    ctx: ToolContext
    permission: PermissionRuntime
    registry: ToolRegistry
    options: StreamChatOptions
    max_turns: int
    definition: AgentDefinition
    parent_mode: PermissionMode
    env: Mapping[str, str]
    reasoning_effort: str
    requested_mode: Literal["normal", "plan"] | None
    parent_permissions: PermissionRuntime
    exact_tools: ToolSnapshot | None = None
    is_async: bool = False
    lifecycle_hooks: HookRuntime | None = None
    mcp_runtime: AgentMcpRuntime | None = None
    archive_source_scope: str | None = None
    archive_source_indices: tuple[int, ...] | None = None


def prepareAgentRun(
    parent: Session, parent_ctx: ToolContext, registry: ToolRegistry, permissions: PermissionRuntime,
    options: StreamChatOptions, task: AgentRequest, definition: AgentDefinition, *, env: Mapping[str, str],
    project_instructions: str = "", signal: threading.Event | None = None,
    initial_messages: list[ChatMessage] | None = None, is_async: bool = False,
    cwd: Path | None = None, user_root: Path | None = None, exact_tools: ToolSnapshot | None = None,
) -> PreparedAgentRun:
    """Prepare one isolated child, with an independent signal for a background owner."""
    if exact_tools is not None and (initial_messages is None or task.model is not None or task.mode is not None):
        raise AgentFailure("Fork 需要父请求的上下文、模型和权限模式，不能指定覆盖。")
    if definition.hooks and parent_ctx.agentHookRuntime is None:
        raise AgentFailure("代理定义声明了尚未装配的Hook，未派发。")
    lifecycle_hooks = parent_ctx.agentHookRuntime(definition) if parent_ctx.agentHookRuntime is not None else None
    child_signal = signal if signal is not None else _LinkedSignal(parent_ctx.signal)
    if child_signal.is_set():
        raise AgentFailure("子代理已中断。")
    try:
        model = getAgentModel(definition.model, parent.model, task.model)
        parent_mode = permissions.getMode()
        mode = _child_permission(parent_mode, task.mode, definition)
        child_registry = (exact_tools.copy_registry() if exact_tools is not None else
                          buildAgentRegistry(registry, definition, plan=mode == "plan", is_async=is_async))
        project_root = Path(parent_ctx.workspaceRoot).resolve()
        workspace = project_root if cwd is None else cwd.resolve()
        working = Path(cwd or parent_ctx.cwd or workspace).resolve()
        if initial_messages is None:
            initial_tools = apiToolsForMode(child_registry, "plan" if mode == "plan" else "normal", parent_ctx.lang)
            prompt = _system_prompt(definition, project_instructions, working,
                                    [tool["function"]["name"] for tool in initial_tools], memory_root=project_root,
                                    user_root=user_root if user_root is not None else Path.home() / ".ruocun")
    except ValueError as error:
        raise AgentFailure(str(error)) from error
    if initial_messages is not None:
        if not initial_messages or initial_messages[0].get("role") != "system" or not isinstance(initial_messages[0].get("content"), str):
            raise AgentFailure("代理转录缺少原系统提示，拒绝继续。")
        prompt = initial_messages[0]["content"]
    child = Session(prompt, model, env=env)
    child.mode = "plan" if mode == "plan" else "normal"
    if initial_messages is None:
        child.messages.append({"role": "user", "content": task.task})
        if definition.initial_prompt:
            child.messages.append({"role": "user", "content": definition.initial_prompt})
        for skill_name in definition.skills:
            skill = next((skill for skill in parent_ctx.skills
                          if skill_name in (skill.get("name"), skill.get("slug"))), None)
            if skill is not None and "body" in skill:
                child.messages.append({"role": "system", "content": f"[预加载技能: {skill.get('name', skill_name)}]\n{skill['body']}"})
    else:
        child.messages = copy.deepcopy(initial_messages)
    permit = permissions.forAgent(working, child, mode)
    child_ctx = replace(parent_ctx,
                        workspaceRoot=str(workspace), cwd=str(working), signal=child_signal,
                        createWorktree=None, activeWorktree=None,
                        readFiles=set(), readMeta={}, pendingUnverifiedWrites=set(), todoWriteRequired=None,
                        currentImageData=None, todos=[], skills=copy.deepcopy(parent_ctx.skills),
                        adaptSkill=None, onFileAccessed=None, onSkillsInstalled=None, notifyUser=None,
                        toolHooks=None, agentHookRuntime=None, agentMcpRuntime=None,
                        subagentDepth=parent_ctx.subagentDepth + 1, runAgent=None, forkToolSnapshot=None,
                        launchAgent=None, agentRunsInBackground=None, taskManager=None,
                        sendToTask=None, resumeAgent=None, messageParent=None,
                        archiveRead=None,
                        setMode=None if mode == "plan" else permit.setMode, askChoice=None,
                        requestTaskWait=None, rollbackTaskWait=None, onShellOutput=None,
                        getShellPlan=permit.getShellPlan,
                        searchTools=lambda query: child_registry.searchAndActivateDeferred(query, parent_ctx.lang)
                        + "\n" + child_registry.searchAndActivateMcp(query))
    child_options: StreamChatOptions = {**options, "model": model, "background": True}
    child_options.pop("onUsage", None)
    child_options.pop("onFinishReason", None)
    configured_limit = _positive_integer(resolve_env("SUBAGENT_MAX_TURNS", env), 500)
    turn_limit = _positive_integer(str(definition.max_turns), configured_limit) if definition.max_turns is not None else configured_limit
    return PreparedAgentRun(child, child_ctx, permit, child_registry, child_options, turn_limit, definition,
                            parent_mode, dict(env), definition.effort or reasoning_effort(env), task.mode, permissions,
                            exact_tools, is_async, lifecycle_hooks,
                            parent_ctx.agentMcpRuntime(definition, child_registry, child_ctx)
                            if exact_tools is None and parent_ctx.agentMcpRuntime is not None else None)


async def openPreparedAgentMcp(prepared: PreparedAgentRun) -> None:
    if prepared.mcp_runtime is not None:
        await prepared.mcp_runtime.open()


async def closePreparedAgentMcp(prepared: PreparedAgentRun) -> None:
    if prepared.mcp_runtime is not None:
        await prepared.mcp_runtime.close()


async def runPreparedAgent(
    prepared: PreparedAgentRun, *, journal: Journal, request: Request | None = None,
    tool_batch_scope: AbstractAsyncContextManager[None] | None = None,
    on_boundary: Callable[[], Awaitable[None]] | None = None,
    on_assistant_saved: Callable[[dict[str, Any]], None] | None = None,
    on_tool_message: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
) -> TurnResult:
    """Drive the same child turn engine for synchronous and managed background owners."""
    def request_model(opts: StreamChatOptions, context: ResilientContext) -> ResilientResult:
        return wrapRequest(streamChatResilient)(opts, env=dict(prepared.env), context=context)

    async def deny_unbound(_name: str, _args: dict[str, Any]) -> bool:
        return False

    def api_tools() -> list[dict[str, Any]]:
        if prepared.exact_tools is not None:
            return copy.deepcopy(list(prepared.exact_tools.api_tools))
        mode: Literal["plan", "normal"] = "plan" if prepared.permission.getMode() == "plan" else "normal"
        return apiToolsForMode(prepared.registry, mode, prepared.ctx.lang)

    permit = prepared.permission
    prepared.ctx.archiveRead = getattr(journal, "archive_read", None)
    context = ContextManager(prepared.session, cast(ContextJournal, journal), prepared.ctx,
                             prepared.options, dict(prepared.env), lambda _message: None,
                             request=request or request_model, permission_mode=permit.getMode)
    owner = agentApprovalSignal.set(prepared.ctx.signal)
    record = getattr(journal, "record", None)
    ref = record.run_ref if record is not None else None
    try:
        with observationScope(identity="sub", depth=prepared.ctx.subagentDepth,
                              taskId=ref.task_id if ref else None, runId=ref.run_id if ref else None), spanScope("turn"):
            return await run_turn(
                prepared.session, prepared.options, prepared.registry, prepared.ctx, approve=deny_unbound,
                request=request or request_model, journal=journal, authorize_batch=permit.authorizeBatch,
                call_scope=prepared.parent_permissions.callScope, permission_mode=permit.getMode, tool_batch_scope=tool_batch_scope,
                api_tools=api_tools, max_turns=prepared.max_turns, reasoning_effort=prepared.reasoning_effort,
                on_boundary=on_boundary, on_assistant_saved=on_assistant_saved, on_tool_message=on_tool_message,
                self_challenge=True, compact=context.recover_overflow, request_preflight=context.before_request,
            )
    finally:
        agentApprovalSignal.reset(owner)


async def prepareAgentDispatch(
    parent: Session, parent_ctx: ToolContext, registry: ToolRegistry, permissions: PermissionRuntime,
    options: StreamChatOptions, task: AgentRequest, *, definitions: Mapping[str, AgentDefinition],
    env: Mapping[str, str], project_instructions: str, user_root: Path | None, is_async: bool = False,
) -> tuple[PreparedAgentRun, Worktree | None]:
    definition = definitions.get(task.agent_type)
    if definition is None:
        raise AgentFailure(f"未知子代理类型「{task.agent_type}」。可用：{', '.join(definitions)}。")
    if parent_ctx.signal.is_set():
        raise AgentFailure("父会话已取消，未派发子代理。")
    exact_tools = None
    messages = None
    if task.fork:
        exact_tools = parent_ctx.forkToolSnapshot
        if exact_tools is None or task.isolation is not None or task.model is not None or task.mode is not None:
            raise AgentFailure("缺少父请求的精确工具现场，或 fork 参数冲突，未派发。")
        definition = FORK_AGENT
        messages = forkRequestMessages(parent.messages, task.task)
    if definition.background and not is_async:
        raise AgentFailure("当前环境不支持后台子代理。")
    isolation = task.isolation or definition.isolation
    tree = None
    if isolation is not None:
        try:
            tree = await openAgentWorktree(parent_ctx, isolation)
        except GitBoundaryError as error:
            raise AgentFailure(f"隔离工作树未创建，子代理未派发。{error}") from error
    try:
        if parent_ctx.signal.is_set():
            raise AgentFailure("父会话已取消，未派发子代理。")
        prepared = prepareAgentRun(
            parent, parent_ctx, registry, permissions, options, task, definition, env=env,
            project_instructions=project_instructions, user_root=user_root, is_async=is_async,
            signal=threading.Event() if is_async else None, cwd=Path(tree.root) if tree is not None else None,
            initial_messages=messages, exact_tools=exact_tools,
        )
        if task.fork:
            paired = {item.get("tool_call_id") for item in parent.messages if item.get("role") == "tool"}
            indices = tuple(index for index, item in enumerate(parent.messages)
                            if item.get("role") != "assistant"
                            or all(call.get("id") in paired for call in item.get("tool_calls") or ()))
            if [parent.messages[index] for index in indices] != prepared.session.messages[:-1]:
                raise AgentFailure("Fork可见前缀与父请求来源不一致，未派发。")
            prepared = replace(prepared, archive_source_scope="main", archive_source_indices=indices)
        await openPreparedAgentMcp(prepared)
        if parent_ctx.signal.is_set():
            await closePreparedAgentMcp(prepared)
            raise AgentFailure("父会话已取消，未派发子代理。")
    except AgentFailure as error:
        if tree is not None:
            raise AgentFailure(await finishAgentWorktree(tree, str(error))) from error
        raise
    return prepared, tree


def _background_prepared(prepared: PreparedAgentRun) -> PreparedAgentRun:
    mode: Literal["normal", "plan"] = "plan" if prepared.permission.getMode() == "plan" else "normal"
    if prepared.exact_tools is not None:
        registry = prepared.exact_tools.copy_registry()
    else:
        registry = buildAgentRegistry(prepared.registry, prepared.definition, plan=mode == "plan", is_async=True)
        visible = apiToolsForMode(prepared.registry, mode, prepared.ctx.lang)
        registry.restoreDeferredVisibility([entry["function"]["name"] for entry in visible])
    context = replace(prepared.ctx, signal=threading.Event(),
                      searchTools=lambda query: registry.searchAndActivateDeferred(query, prepared.ctx.lang)
                      + "\n" + registry.searchAndActivateMcp(query))
    # Old owner has stopped at a paired boundary. Keep the same session ledger and permissions.
    return replace(prepared, ctx=context, registry=registry, is_async=True,
                   mcp_runtime=prepared.mcp_runtime.rebind(registry, context) if prepared.mcp_runtime else None)


def createAgentRunner(
    parent: Session, parent_ctx: ToolContext, registry: ToolRegistry, permissions: PermissionRuntime,
    conversation: Conversation, options: StreamChatOptions, *, env: Mapping[str, str],
    project_instructions: str = "", request: Request | None = None, handoff: Handoff | None = None,
    definitions: Mapping[str, AgentDefinition] | None = None, user_root: Path | None = None,
) -> Callable[[AgentRequest], Awaitable[str]]:
    """Bind Agent to the actual parent options and a separately journaled child turn."""
    parent_ctx.maxParallelAgents = _positive_integer(resolve_env("MAX_PARALLEL_AGENTS", env), 10)
    available = definitions if definitions is not None else bundledAgentDefinitions(env)

    async def run(task: AgentRequest) -> str:
        parent_signal = parent_ctx.signal
        prepared, tree = await prepareAgentDispatch(
            parent, parent_ctx, registry, permissions, options, task, definitions=available, env=env,
            project_instructions=project_instructions, user_root=user_root,
        )
        try:
            return await run_owned(task, parent_signal, prepared, tree)
        finally:
            await closePreparedAgentMcp(prepared)

    async def run_owned(task: AgentRequest, parent_signal: threading.Event,
                        prepared: PreparedAgentRun, tree: Worktree | None) -> str:
        definition = prepared.definition
        child, child_ctx = prepared.session, prepared.ctx
        parent_ref = conversation.current_agent_parent()
        run_ref = RunRef(f"agent-{uuid.uuid4().hex}", str(uuid.uuid4()))
        inherited = await prepareAgentArchive(conversation, prepared)
        manager = parent_ctx.taskManager
        isolation = task.isolation or definition.isolation
        eligible = manager is not None and ((isolation is None and tree is None) or (isolation == "remote" and tree is not None))
        record = RunRecord(run_ref, "fork" if task.fork else "agent", "running", False, {
            "parent_tool_ref": asdict(parent_ref), "foreground": True, "model": child.model,
            "agentType": definition.agent_type, "description": conversation.redact(task.task[:50]), "cwd": child_ctx.cwd,
            "workspaceRoot": child_ctx.workspaceRoot, "startedAt": time_ns() // 1_000_000,
            "output_start": len(child.messages), "output_raw_offset": agentOutputOffset(child.messages, inherited),
            "handoff_allowed": eligible,
            "isolation": isolation, "isolation_tree": {"root": tree.root, "branch": tree.branch} if tree is not None else None,
            "definitionVersion": definition.version, "permissionMode": prepared.permission.getMode(),
            "turnLimit": prepared.max_turns,
        })
        if prepared.exact_tools is not None:
            record.snapshot["forkToolDigest"] = agentRecoveryMaterial(prepared)["toolRosterDigest"]
        journal = _AgentJournal(conversation, record, parent_ref, prepared)
        await journal._save_messages(child.messages, archive_import=inherited, usage=dict(child.usage))
        foreground = manager.track_foreground(journal.record, child_ctx.signal, eligible=eligible) if manager is not None else None
        journal.foreground = foreground
        transferred: BgTask | None = None

        async def boundary() -> None:
            if foreground is not None and not conversation.blocked and foreground.handoff_requested():
                if tree is not None:
                    try:
                        await asyncio.to_thread(tree.verify)
                    except GitBoundaryError as error:
                        conversation.blocked = True
                        raise UnknownToolOutcome("原 remote 隔离工作树身份无法核实，已停止并保留现场。") from error
                await journal.handoff_boundary()
                if foreground.claim_handoff():
                    return
            await journal.model_boundary()

        hooks = prepared.lifecycle_hooks
        try:
            try:
                if hooks is not None:
                    async with conversation.agent_tool_batches:
                        await startAgentHooks(hooks, child, run_ref, definition.agent_type, child_ctx.workspaceRoot,
                                              child_ctx.signal, journal)
                outcome = await runPreparedAgent(prepared, journal=journal, request=request,
                                                 tool_batch_scope=conversation.agent_tool_batches, on_boundary=boundary)
            except HookOutcomeUnknown as error:
                outcome = TurnResult("outcome_unknown", str(error))
            if outcome.status == "cancelled" and foreground is not None and foreground.claimed and manager is not None:
                transferred = await manager.launch_handoff(foreground, journal.record, _background_prepared(prepared),
                                                            parent_ref, parent_signal, request, worktree=tree)
                if transferred is not None:
                    return (f"已转后台({transferred.id});完成后会自动通知你结果。"
                            "先做其他独立工作,无独立工作时单独调用 TaskWait 等待此 id。")
            if hooks is not None and outcome.status != "outcome_unknown" and not conversation.blocked:
                try:
                    async with conversation.agent_tool_batches:
                        await stopAgentHooks(hooks, run_ref, definition.agent_type, child_ctx.workspaceRoot, journal)
                except HookOutcomeUnknown as error:
                    outcome = TurnResult("outcome_unknown", str(error))
            if outcome.status == "outcome_unknown":
                conversation.blocked = True
                try:
                    await journal.finish(child, "unknown", outcome.error)
                except Exception as error:
                    # A writer with an unconfirmed COMMIT rejects further writes.
                    # The exact scoped intent is retained for recovery to classify.
                    raise UnknownToolOutcome(outcome.error) from error
                raise UnknownToolOutcome(outcome.error)
            if outcome.status != "complete":
                status = "canceled" if outcome.status == "cancelled" else "failed"
                await journal.finish(child, status, outcome.error)
                location = f"\n[隔离目录保留：{tree.root}。]" if tree is not None else ""
                raise AgentFailure((outcome.error or "子代理未完成。") + location)
            activity = await agentOutputMessages(conversation, journal.record)
            final_text = next((message["content"] for message in reversed(activity)
                               if message.get("role") == "assistant" and isinstance(message.get("content"), str)
                               and message["content"]), "(子代理无最终输出)")
            await journal.finish(child, "completed", final_text)
            # Persist the live roster first, then release server cwd handles before Git cleanup.
            await closePreparedAgentMcp(prepared)
            if handoff is not None and prepared.parent_mode == "auto" and not child_ctx.signal.is_set():
                warning = await handoff(conversation.redacted_messages(child.messages), definition.agent_type)
                if warning:
                    final_text = warning + "\n\n" + final_text
            if tree is None:
                return final_text
            if (task.isolation or definition.isolation) == "remote":
                final_text += "\n[remote 在同机 Git 工作树执行。]"
            return await finishAgentWorktree(tree, final_text)
        finally:
            if manager is not None and foreground is not None:
                status = "completed" if transferred is not None else journal.record.status
                result = journal.record.snapshot.get("result")
                manager.finish_foreground(foreground, cast(ExecutionStatus, "unknown" if status == "running" else status),
                    result=conversation.redact(result) if isinstance(result, str) else None,
                    ended_at=transferred.startedAt if transferred is not None else journal.record.snapshot.get("endedAt"),
                    transferred=transferred is not None)

    return run
