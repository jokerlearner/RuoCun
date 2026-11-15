"""定义工具、执行上下文和派发接口。工具通过上下文使用当前回合绑定的目录、权限、取消状态和服务。"""

from __future__ import annotations

import threading
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypedDict

from ..client.types import ImageData
from ..skills.types import Skill

if TYPE_CHECKING:
    from ..agent.agent_defs import AgentDefinition
    from ..agent.agent_mcp import AgentMcpRuntime
    from ..agent.background_types import WaitRequest
    from ..agent.tasks import TaskManager
    from ..agent.worktree import ActiveWorktree, Worktree
    from ..hooks.hooks import HookRuntime
    from ..lsp.manager import LspManager
    from ..memory.memory_audit import MemoryAuditSink
    from ..platform.sandbox_policy import SandboxPolicy
    from ..platform.shell_plan import ShellExecutionPlan
    from ..session.cache_audit import CacheAuditSink
    from .agent import AgentRequest
    from .managed_shell import ManagedShellManager
    from .registry import ToolRegistry, ToolSnapshot
    from .tool_audit import ToolAuditSink
    from .web_network import FetchImpl


class ReadMeta(TypedDict):
    mtime: float
    size: int


class ToolRejected(ValueError):
    """工具在产生副作用前明确拒绝了调用，模型可按原因修正再试。"""


class ChoicePrompt(Protocol):
    async def __call__(self, question: str, options: list[str], multi: bool = False) -> str: ...


@dataclass
class ToolContext:
    workspaceRoot: str
    cwd: str | None = None
    createWorktree: Callable[[str], Worktree | None] | None = None
    activeWorktree: ActiveWorktree | None = None
    signal: threading.Event = field(default_factory=threading.Event)
    readFiles: set[str] = field(default_factory=set)
    readMeta: dict[str, ReadMeta] = field(default_factory=dict)
    pendingUnverifiedWrites: set[str] = field(default_factory=set)
    todoWriteRequired: dict[str, bool] | None = None
    approveExternalRead: Callable[[str], Awaitable[bool]] | None = None
    approveExternalWrite: Callable[[str], Awaitable[bool]] | None = None
    sessionModel: str | None = None
    currentImageData: ImageData | None = None
    headless: bool = False
    lang: str = "zh"
    todos: list[dict[str, str]] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)
    recordSkillUse: Callable[[str], None] | None = None
    adaptSkill: Callable[[str], Awaitable[str]] | None = None
    setMode: Callable[[Literal["normal", "plan"]], None] | None = None
    askChoice: ChoicePrompt | None = None
    ask: Callable[[str], Awaitable[str]] | None = None
    notifyUser: Callable[[str], None] | None = None
    notificationEnv: Mapping[str, str] | None = None
    managedShell: ManagedShellManager | None = None
    subagentDepth: int = 0
    forkToolSnapshot: ToolSnapshot | None = None
    runAgent: Callable[[AgentRequest], Awaitable[str]] | None = None
    launchAgent: Callable[[AgentRequest], Awaitable[str]] | None = None
    agentRunsInBackground: Callable[[str], bool] | None = None
    taskManager: TaskManager | None = None
    toolHooks: HookRuntime | None = None
    toolAudit: ToolAuditSink | None = None
    cacheAudit: CacheAuditSink | None = None
    memoryAudit: MemoryAuditSink | None = None
    auditRedact: Callable[[str], str] | None = None
    mcpConfigDigest: str | None = None
    agentHookRuntime: Callable[[AgentDefinition], HookRuntime | None] | None = None
    agentMcpRuntime: Callable[[AgentDefinition, ToolRegistry, ToolContext], AgentMcpRuntime | None] | None = None
    sendToTask: Callable[[str, str], Awaitable[bool]] | None = None
    resumeAgent: Callable[[str, str], Awaitable[None]] | None = None
    messageParent: Callable[[str, Literal["progress", "attention"]], Awaitable[bool]] | None = None
    maxParallelAgents: int = 10
    requestTaskWait: Callable[[WaitRequest], str] | None = None
    rollbackTaskWait: Callable[[], None] | None = None
    onShellOutput: Callable[[Literal["stdout", "stderr"], str], None] | None = None
    getShellPlan: Callable[[str, str], ShellExecutionPlan] | None = None
    sandboxPolicy: SandboxPolicy | None = None
    authorizeSandboxShell: Callable[[ShellExecutionPlan, list[str]], Awaitable[ShellExecutionPlan]] | None = None
    approveSandboxWrite: Callable[[str], Awaitable[bool]] | None = None
    searchTools: Callable[[str], str] | None = None
    onFileAccessed: Callable[[str], None] | None = None
    onSkillsInstalled: Callable[[Literal["user", "project"]], None] | None = None
    fetchImpl: FetchImpl | None = None
    extractFromPage: Callable[[str, str], Awaitable[str]] | None = None
    lsp: LspManager | None = None
    archiveRead: Callable[[str, int, int], Awaitable[dict[str, Any]]] | None = None


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    schema: dict[str, Any]
    capability: Literal["read", "write", "exec", "plan", "network"]
    approval: Literal["auto", "suggest", "required"]
    handler: Callable[[dict[str, Any], ToolContext], Awaitable[str]]
    descriptionEn: str | None = None
    apiParameters: dict[str, Any] | None = None
    checkPermissions: Callable[[str], Literal["deny", "ask"] | None] | None = None
    shouldDefer: bool = False
    persistentEffect: bool = False  # 需要独占执行并持久记录意图，原有能力标签仍用于权限判断。


class ToolDispatcher(Protocol):
    async def dispatch(self, name: str, rawArgs: str, ctx: ToolContext) -> str: ...
