"""Frozen reference tools/execute.ts (MIT), adapted to the foreground tool journal."""

from __future__ import annotations

import asyncio
import copy
import threading
import time
from collections.abc import Awaitable, Callable, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, replace
from typing import Any, Protocol

from ..client.types import ChatMessage, ImageData
from ..hooks.hooks import HookDecision, HookOutcome, HookRuntime, HookSpec, RunCtx
from ..hooks.journal import HookOutcomeUnknown, hookJSON, runJournaledHooks
from ..obs.backend import getObsMeta, getObsSession, observationScope
from ..obs.wrap import wrapToolHandler
from ..session.contract import ToolResult
from .execute import Approval, Registry, looksFailed, permitted
from .types import Tool, ToolContext, ToolRejected

_MAX_CONCURRENCY = 8
_EFFECTS = {"write", "exec"}
_CANCELLED = "Error: 本轮已取消，工具未执行。"
_PLAN_DENIED = "Error: 当前为只读规划模式，工具未执行。"
_APPROVAL_INCOMPLETE = "Error: 权限确认未完成，此调用未执行。"
_BARRIER_SKIPPED = "已跳过:本批前一个命令失败，为避免连锁错误未执行。请先处理上一个错误再重试。"


@dataclass(frozen=True)
class BatchCall:
    call_id: str
    tool: Tool
    raw_args: str
    hook_decision: HookDecision | None = None


BatchAuthorize = Callable[[Sequence[BatchCall]], Awaitable[dict[str, bool]]]
CallScope = Callable[[], AbstractContextManager[None]]
Authorize = Callable[[Tool, str], Awaitable[bool]]


class ToolJournal(Protocol):
    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> ToolResult | None: ...
    async def result(self, call_id: str, text: str, image_data: ImageData | None = None) -> None: ...


class UnknownToolOutcome(RuntimeError):
    """A write or exec handler began and its result could not be confirmed."""


class _ApprovalIncomplete(RuntimeError):
    pass


@dataclass
class BatchOutcome:
    messages: list[ChatMessage]
    approval_incomplete: bool


def _message(call_id: str, text: str, image: ImageData | None = None) -> ChatMessage:
    message: ChatMessage = {"role": "tool", "tool_call_id": call_id, "content": text}
    if image is not None:
        message["imageData"] = copy.deepcopy(image)
    return message


def _has_persistent_effect(tool: Tool) -> bool:
    return tool.persistentEffect or tool.capability in _EFFECTS


async def _invoke_tool_hook(
    hooks: HookRuntime, event: str, call_id: str, context: RunCtx, signal: threading.Event,
    selected: Sequence[HookSpec], journal: ToolJournal | None,
) -> HookOutcome:
    if journal is None:
        raise ToolRejected("Hook 缺少工具执行日志，命令未启动。")
    try:
        return await runJournaledHooks(hooks, event, call_id, context, signal, journal, selected=selected)
    except HookOutcomeUnknown as error:
        raise UnknownToolOutcome(str(error)) from error


async def executeToolBatch(
    calls: list[tuple[str, str, str]], registry: Registry, ctx: ToolContext, *,
    approve: Approval, journal: ToolJournal | None,
    authorize: Authorize | None, authorize_batch: BatchAuthorize | None,
    call_scope: CallScope | None, permission_mode: Callable[[], str] | None,
) -> BatchOutcome:
    if ctx.subagentDepth == 0 and len(calls) > 1 and any(name == "TaskWait" for _, name, _ in calls):
        from ..agent.background_runtime import currentWaitControl
        control = currentWaitControl()
        if control is not None:
            control.rollback()
        if ctx.rollbackTaskWait is not None:
            ctx.rollbackTaskWait()
        others = [call for call in calls if call[1] != "TaskWait"]
        completed = await executeToolBatch(others, registry, ctx, approve=approve, journal=journal,
                                           authorize=authorize, authorize_batch=authorize_batch,
                                           call_scope=call_scope, permission_mode=permission_mode) if others else BatchOutcome([], False)
        by_id = {message["tool_call_id"]: message for message in completed.messages}
        return BatchOutcome([by_id.get(call_id, _message(call_id, "Error: TaskWait 必须单独调用,本批未登记等待。"))
                             for call_id, _, _ in calls], completed.approval_incomplete)
    ctx.currentImageData = None
    todo_missing = False
    if ctx.headless and ctx.todoWriteRequired and not ctx.todoWriteRequired.get("done"):
        if any(name == "TodoWrite" for _, name, _ in calls):
            ctx.todoWriteRequired["done"] = True
        else:
            todo_missing = True

    def stop_reason(tool: Tool) -> str | None:
        if ctx.signal.is_set():
            return _CANCELLED
        if (permission_mode is not None and permission_mode() == "plan"
                and (tool.capability in _EFFECTS or tool.name.startswith("mcp__"))):
            return _PLAN_DENIED
        return None

    results: dict[str, ChatMessage] = {}
    ready: dict[str, BatchCall] = {}
    arguments: dict[str, dict[str, Any]] = {}
    invalid_exec: set[str] = set()
    failed_exec: set[str] = set()
    hooks = ctx.toolHooks
    pre_hooks: dict[str, HookOutcome] = {}
    post_hooks: dict[str, tuple[HookSpec, ...]] = {}
    hook_cwd = ctx.workspaceRoot

    def hook_denied(call: BatchCall) -> str:
        if call.hook_decision != "deny":
            return "Error: 权限拒绝此操作，工具未执行。"
        assert hooks is not None
        reason = hooks.redacted(pre_hooks[call.call_id].reason) or "权限被 hook 拒绝(deny)。"
        return f"[被 hook 阻止] {reason}"

    async def audit(call: BatchCall, status: str) -> None:
        if hooks is not None and (call.call_id in pre_hooks or call.call_id in post_hooks):
            await hooks.audit("ToolUse", call.tool.name, call.raw_args, status)
    for call_id, name, raw in calls:
        if ctx.signal.is_set():
            results[call_id] = _message(call_id, _CANCELLED)
            continue
        if todo_missing:
            results[call_id] = _message(
                call_id, "[操作被拒绝] 无人值守会话需要先用 TodoWrite 记录计划。"
                "当前操作尚未执行，请列出具体步骤后再继续。",
            )
            continue
        tool = registry.get(name)
        if tool is not None and (reason := stop_reason(tool)):
            results[call_id] = _message(call_id, reason)
            continue
        decision: HookDecision | None = None
        try:
            if tool is not None and hooks is not None:
                hook_ctx = RunCtx(hook_cwd, tool_name=name, args_json=raw, payload={"tool": name, "args": raw})
                selected = hooks.matching("PreToolUse", hook_ctx)
                if selected:
                    outcome = await _invoke_tool_hook(hooks, "PreToolUse", call_id, hook_ctx, ctx.signal, selected, journal)
                    pre_hooks[call_id] = outcome
                    decision = "deny" if outcome.block else outcome.permission_decision
                    if outcome.updated_input is not None:
                        raw = hookJSON(outcome.updated_input)
                if ctx.signal.is_set():
                    results[call_id] = _message(call_id, _CANCELLED)
                    continue
            args = registry.validate(name, raw)
            if tool is not None and hooks is not None:
                post = hooks.matching("PostToolUse", RunCtx(hook_cwd, tool_name=name, args_json=raw))
                if post:
                    if journal is None:
                        raise ToolRejected("Hook 缺少工具执行日志，命令和工具均未启动。")
                    post_hooks[call_id] = post
        except (ValueError, TypeError, KeyError) as exc:
            if tool is not None and decision == "deny":
                denied_call = BatchCall(call_id, tool, raw, decision)
                results[call_id] = _message(call_id, hook_denied(denied_call))
                await audit(denied_call, "hook-deny")
                continue
            results[call_id] = _message(call_id, f"Error: 工具参数无效：{exc}")
            if tool is not None:
                await audit(BatchCall(call_id, tool, raw, decision), "invalid")
                if tool.capability == "exec":
                    invalid_exec.add(call_id)
            continue
        if tool is None:
            results[call_id] = _message(call_id, "Error: 未注册的工具。")
        else:
            ready[call_id] = BatchCall(call_id, tool, raw, decision)
            arguments[call_id] = args

    async def dispatch(call: BatchCall) -> ChatMessage:
        call_id, tool, raw = call.call_id, call.tool, call.raw_args
        with call_scope() if call_scope is not None else nullcontext():
            if reason := stop_reason(tool):
                return _message(call_id, reason)
            if call.hook_decision == "deny":
                await audit(call, "hook-deny")
                return _message(call_id, hook_denied(call))
            if authorize_batch is None:
                try:
                    allowed = await (authorize(tool, raw) if authorize is not None
                                     else permitted(tool, arguments[call_id], approve))
                    if allowed and call.hook_decision == "ask":
                        allowed = await approve(tool.name, arguments[call_id])
                except Exception as exc:
                    raise _ApprovalIncomplete from exc
                if reason := stop_reason(tool):
                    return _message(call_id, reason)
                if not allowed:
                    kind = "权限" if authorize is not None else "用户"
                    await audit(call, "denied")
                    return _message(call_id, f"Error: {kind}拒绝此操作，工具未执行。")

            effect = _has_persistent_effect(tool)
            if journal is not None:
                cached = await journal.intent(call_id, tool.name, raw, effect)
                if cached is not None:
                    message = copy.deepcopy(cached) if isinstance(cached, dict) else _message(call_id, cached)
                    if tool.capability == "exec" and looksFailed(message["content"]):
                        failed_exec.add(call_id)
                    return message
            image = None
            finished_handler = False
            if reason := stop_reason(tool):
                # Intent committed, handler not yet entered.
                result = reason
            else:
                # Only Read owns an image slot. Baselines, signal, skill
                # access callback and other shared state stay on the business loop.
                call_ctx = replace(ctx, currentImageData=None) if tool.name == "Read" else ctx
                started_at, trace_ok = time.monotonic(), False
                try:
                    with observationScope(toolCallId=call_id):
                        result = await wrapToolHandler(registry.dispatch, tool.name, raw)(tool.name, raw, call_ctx)
                    finished_handler = True
                    if hooks is not None and (pre := pre_hooks.get(call_id)) is not None and pre.additional_context:
                        result += "\n[hook 提示] " + hooks.redacted(pre.additional_context)
                    if tool.name == "Read":
                        image = call_ctx.currentImageData
                    trace_ok = not looksFailed(result) and "被 hook 阻止" not in result
                except ToolRejected as exc:
                    result = f"Error: {exc}"
                except Exception as exc:
                    if effect:
                        if isinstance(exc, UnknownToolOutcome):
                            raise
                        raise UnknownToolOutcome(
                            f"工具执行结果未确认（{type(exc).__name__}），已停止；请检查工作目录。"
                        ) from exc
                    result = f"Error: 工具读取失败（{type(exc).__name__}）。"
                finally:
                    if ctx.toolAudit is not None:
                        try:
                            ctx.toolAudit.call(tool.name, tool.capability, trace_ok,
                                (time.monotonic() - started_at) * 1000, raw,
                                metadata={**getObsMeta(), "sessionId": getObsSession() or "", "toolCallId": call_id})
                        except Exception:
                            pass  # Audit failure cannot replay or change the tool outcome.
                if tool.capability == "exec" and looksFailed(result):
                    failed_exec.add(call_id)
            if journal is not None:
                try:
                    if image is None:
                        await journal.result(call_id, result)
                    else:
                        await journal.result(call_id, result, image)
                except Exception as exc:
                    if not effect:
                        raise
                    raise UnknownToolOutcome(
                        f"工具结果保存未确认（{type(exc).__name__}），已停止；请核实原操作。"
                    ) from exc
            if finished_handler and hooks is not None and call_id in post_hooks and not ctx.signal.is_set():
                post_ctx = RunCtx(hook_cwd, tool_name=tool.name, args_json=raw,
                                  payload={"tool": tool.name, "args": raw, "result": result})
                await _invoke_tool_hook(hooks, "PostToolUse", call_id, post_ctx, ctx.signal, post_hooks[call_id], journal)
            await audit(call, "failed" if looksFailed(result) else "completed")
            return _message(call_id, result, image)

    async def settle(group: list[BatchCall]) -> None:
        failed = False
        pending = iter(group)

        async def worker() -> None:
            nonlocal failed
            while not failed:
                call = next(pending, None)
                if call is None:
                    return
                try:
                    results[call.call_id] = await dispatch(call)
                except BaseException:
                    failed = True
                    raise

        if not group:
            return
        tasks = asyncio.gather(*(worker() for _ in range(min(_MAX_CONCURRENCY, len(group)))),
                               return_exceptions=True)
        try:
            settled = await asyncio.shield(tasks)
        except asyncio.CancelledError:
            ctx.signal.set()
            # A cancelled owner still owns started tools and storage receipts.
            while not tasks.done():
                try:
                    await asyncio.shield(tasks)
                except asyncio.CancelledError:
                    pass
            raise
        errors = [outcome for outcome in settled if isinstance(outcome, BaseException)]
        # An approval failure only proves its own call did not start.
        for error in errors:
            if not isinstance(error, _ApprovalIncomplete):
                raise error
        if errors:
            raise errors[0]

    incomplete = False
    try:
        if authorize_batch is not None and ready:
            try:
                approved = await authorize_batch(tuple(ready.values()))
            except Exception as exc:
                raise _ApprovalIncomplete from exc
            for call_id in ready:
                if ctx.signal.is_set():
                    results[call_id] = _message(call_id, _CANCELLED)
                elif not approved.get(call_id, False) or ready[call_id].hook_decision == "deny":
                    call = ready[call_id]
                    results[call_id] = _message(call_id, hook_denied(call))
                    await audit(call, "hook-deny" if call.hook_decision == "deny" else "denied")

        barrier_aborted = False
        group: list[BatchCall] = []
        for call_id, _, _ in calls:
            if call_id in invalid_exec:
                barrier_aborted = True
            if call_id not in ready or call_id in results:
                continue
            call = ready[call_id]
            if not _has_persistent_effect(call.tool) and call_id not in post_hooks:
                group.append(call)
                continue
            await settle(group)
            group.clear()
            if reason := stop_reason(call.tool):
                results[call_id] = _message(call_id, reason)
            elif barrier_aborted and call.tool.capability in _EFFECTS:
                results[call_id] = _message(call_id, _BARRIER_SKIPPED)
            else:
                await settle([call])
                barrier_aborted = barrier_aborted or call_id in failed_exec
        await settle(group)
    except _ApprovalIncomplete:
        incomplete = True
        for call_id, _, _ in calls:
            results.setdefault(call_id, _message(call_id, _APPROVAL_INCOMPLETE))

    return BatchOutcome([results[call_id] for call_id, _, _ in calls], incomplete)
