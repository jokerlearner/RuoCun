"""组织后台代理的运行、停止、等待和结果交付，复用持久运行记录与事件流。恢复阶段先绑定已有记录，再由正常调度决定后续动作。"""

from __future__ import annotations

import asyncio
import copy
import threading
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass, field, replace
from time import time_ns
from typing import TYPE_CHECKING, Any, Literal, cast

from ..hooks.journal import HookOutcomeUnknown, hookIntentId
from ..session.contract import (
    ArchiveImport,
    ArchiveRewrite,
    RunRecord,
    RunRef,
    StoreError,
    ToolRef,
    ToolResult,
    task_inbox_messages,
)
from ..session.recovery import AgentContinuation, repairToolPairs
from ..session.sqlite_port import CommitUnconfirmedError, RollbackError
from ..tools.agent import AgentFailure
from ..tools.types import ToolRejected
from .agent_hooks import startAgentHooks, stopAgentHooks
from .agent_lifecycle import settleAgentTurn
from .background_types import (
    EventType,
    ExecutionEvent,
    ExecutionSnapshot,
    ExecutionStatus,
    isTerminal,
)
from .monitor import runMonitor
from .resume_agent import (
    agentCheckpointSnapshot,
    agentOutputMessages,
    agentOutputOffset,
    agentRecoveryMaterial,
    prepareAgentArchive,
    validatePreparedContinuation,
)
from .worktree import GitMutationUnknown, Worktree, finishAgentWorktree

if TYPE_CHECKING:
    from threading import Event

    from ..client.types import ImageData
    from ..platform.shell_plan import ShellExecutionPlan
    from ..session.conversation import Conversation
    from ..session.session import Session
    from .background_runtime import BackgroundRuntime
    from .loop import Request
    from .run_agent import PreparedAgentRun


@dataclass(eq=False)
class BgTask:
    id: str
    runId: str
    kind: Literal["agent", "fork", "manual", "monitor"]
    description: str
    status: ExecutionStatus
    result: str | None = None
    error: str | None = None
    summary: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    agentType: str | None = None
    startedAt: int | None = None
    endedAt: int | None = None


@dataclass
class ForegroundAgent:
    task: BgTask
    signal: Event
    eligible: bool
    checkpoint_lock: asyncio.Lock
    record: RunRecord
    requested: asyncio.Future[bool] | None = None
    claimed: bool = False

    def handoff_requested(self) -> bool:
        return self.eligible and self.requested is not None and not self.requested.done() and not self.signal.is_set()

    def claim_handoff(self) -> bool:
        if not self.handoff_requested():
            return False
        self.claimed = True
        self.signal.set()
        return True


@dataclass
class _Execution:
    task: BgTask
    record: RunRecord
    prepared: PreparedAgentRun
    parent: ToolRef
    request: Request | None
    material: dict[str, Any]
    output_start: int
    executor: asyncio.Task[None] | None = None
    worktree: Worktree | None = None
    task_send: ToolRef | None = None
    archive_import: ArchiveImport | None = None


@dataclass
class _MonitorExecution:
    task: BgTask
    record: RunRecord
    plan: ShellExecutionPlan
    signal: Event
    executor: asyncio.Task[None] | None = None


class _AgentStopped(RuntimeError):
    """已准入的任务在派发下一次工具调用前到达取消边界。"""


class _StartHookNotAdmitted(_AgentStopped):
    """启动钩子的意图尚未记录时，已经观察到取消。"""


class _Journal:
    def __init__(self, owner: TaskManager, execution: _Execution) -> None:
        self.owner, self.execution = owner, execution

    async def save(self, session: Session) -> None:
        await self.owner._save(self.execution, session.messages)

    def redact(self, text: str) -> str:
        return self.owner.conversation.redact(text)

    @property
    def record(self) -> RunRecord:
        return self.execution.record

    async def archive_read(self, identity: str, offset: int, limit: int) -> dict[str, Any]:
        return await self.owner.conversation.worker.archive_read(identity, self.record.run_ref.run_id,
                                                                  offset=offset, limit=limit)

    async def replace_context(self, session: Session, messages: list[dict[str, Any]], *, reset_prompt: bool = True) -> None:
        await self.owner._save(self.execution, messages)
        session.messages = messages
        if reset_prompt:
            session.lastPromptTokens = None
            session.lastSentLength = 0

    async def compact_context(self, session: Session, messages: list[dict[str, Any]], *, rewrite: ArchiveRewrite) -> None:
        await self.owner._save(self.execution, messages, archive_rewrite=rewrite)
        session.messages = messages
        session.lastPromptTokens = None
        session.lastSentLength = 0

    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> ToolResult | None:
        async with self.owner._lock:
            run = self.execution.record.run_ref
            stopping = name == "SubagentStop" and effect and call_id == hookIntentId(name, run.run_id)
            if not stopping and (self.execution.task.status != "running" or self.execution.prepared.ctx.signal.is_set()):
                if name == "SubagentStart" and effect and call_id == hookIntentId(name, run.run_id):
                    raise _StartHookNotAdmitted()
                raise _AgentStopped()
            return await self.owner.conversation.scoped_intent(ToolRef(run.run_id, call_id), name, args, effect,
                                                              agent_run=run, parent_tool_ref=self.execution.parent)

    async def result(self, call_id: str, text: str, image_data: ImageData | None = None) -> None:
        run = self.execution.record.run_ref
        await self.owner.conversation.scoped_result(ToolRef(run.run_id, call_id), text, image_data)


class TaskManager:
    def __init__(self, conversation: Conversation, background: BackgroundRuntime, *,
                 handoff: Callable[[list[dict[str, Any]], str], Awaitable[str | None]] | None = None) -> None:
        if background.store is not conversation or background.sessionId != conversation.session_id:
            raise ValueError("任务管理器需绑定同一会话的持久后台事件流。")
        self.conversation, self.background, self.handoff = conversation, background, handoff
        self._lock = asyncio.Lock()
        self._runs: dict[str, _Execution] = {}
        self._monitors: dict[str, _MonitorExecution] = {}
        self._foreground: dict[str, ForegroundAgent] = {}
        self._tasks: dict[str, BgTask] = {}
        self._manual_counter = 0
        self._closed = False

    @staticmethod
    def _snapshot(task: BgTask, status: ExecutionStatus, *, result: str | None = None,
                  summary: str | None = None) -> ExecutionSnapshot:
        kind: Literal["agent", "fork"] = "fork" if task.kind == "fork" else "agent"
        return ExecutionSnapshot(task.id, task.runId, kind, True, task.description, status, result=result,
                                 progress=task.summary if summary is None else summary)

    async def bind(self) -> None:
        """绑定恢复出来的记录。执行仍由后续调度决定。"""
        async with self._lock:
            view = await self.conversation.background_view()
            latest: dict[str, RunRecord] = {}
            for record in view.runs:
                if record.kind not in {"agent", "fork", "manual", "monitor"}:
                    continue
                if (record.kind != "manual" and record.snapshot.get("foreground") is not True
                        and not isinstance(record.snapshot.get("background_execution"), dict)):
                    continue
                latest[record.run_ref.task_id] = record
                suffix = record.run_ref.task_id.removeprefix("task-")
                if record.kind == "manual" and record.run_ref.task_id.startswith("task-") and suffix.isascii() and suffix.isdecimal():
                    self._manual_counter = max(self._manual_counter, int(suffix))
            for record in latest.values():
                task_id, run_id = record.run_ref.task_id, record.run_ref.run_id
                if run_id in self._runs or run_id in self._foreground or run_id in self._monitors:
                    continue
                old = self._tasks.get(task_id)
                if old is not None and old.runId == run_id and old.status == record.status:
                    continue
                raw = record.snapshot.get("background_execution") or {}
                messages = record.snapshot.get("messages", [])
                start = record.snapshot.get("output_start", 0)
                if record.kind in {"agent", "fork"}:
                    visible = await agentOutputMessages(self.conversation, record)
                else:
                    visible = messages[start:] if isinstance(messages, list) and isinstance(start, int) and 0 <= start <= len(messages) else []
                result = raw.get("result", record.snapshot.get("result"))
                kind = cast(Literal["agent", "fork", "manual", "monitor"], record.kind)
                self._tasks[task_id] = BgTask(task_id, run_id, kind,
                    str(raw.get("description", record.snapshot.get("description", task_id))),
                    cast(ExecutionStatus, record.status), result if record.status == "completed" else None,
                    result if record.status != "completed" else None, raw.get("progress"),
                    visible if record.kind != "manual" else [], record.snapshot.get("agentType"),
                    record.snapshot.get("startedAt"), record.snapshot.get("endedAt"))
            self._gc()

    async def _publish_monitor(self, execution: _MonitorExecution, status: ExecutionStatus, *, text: str | None = None) -> None:
        task, record = execution.task, execution.record
        seq = record.snapshot.get("monitor_output_seq", 0) + int(text is not None)
        terminal = status in {"completed", "canceled", "failed", "unknown"}
        snapshot = ExecutionSnapshot(task.id, task.runId, "monitor", True, task.description, status,
                                     result=text if terminal else None)
        data = {**record.snapshot, "monitor_output_seq": seq}
        if terminal:
            data["endedAt"] = time_ns() // 1_000_000
        updated = replace(record, status=status, cancel_requested=record.cancel_requested or status == "canceling", snapshot=data)
        event: EventType = cast(EventType, status) if terminal else "message" if text is not None else "started" if task.id not in self._tasks else "progress"
        event_id = f"{task.runId}:monitor-output:{seq}" if text is not None and not terminal else None
        safe = self.conversation.redact(text) if text is not None else None
        snapshot = replace(snapshot, result=safe if terminal else None)
        await self.background.publish(ExecutionEvent(event, snapshot, safe if not terminal else None,
                                                     text is not None and not terminal, event_id), updated, require_commit=True)
        execution.record = updated
        task.status = status
        if terminal:
            task.endedAt = data["endedAt"]
            if status == "completed":
                task.result = safe
            else:
                task.error = safe

    async def launch_monitor(self, plan: ShellExecutionPlan, description: str, *, timeout_ms: int | None,
                             parent: ToolRef, parent_signal: Event) -> BgTask:
        async with self._lock:
            if self._closed or self.conversation.blocked or parent_signal.is_set():
                raise ToolRejected("当前会话不能启动监控，命令未执行。")
            started = time_ns() // 1_000_000
            ref = RunRef(f"monitor-{uuid.uuid4().hex}", str(uuid.uuid4()))
            safe = self.conversation.redact(description)
            task = BgTask(ref.task_id, ref.run_id, "monitor", safe, "running", startedAt=started)
            record = RunRecord(ref, "monitor", "running", False, {
                "monitor_epoch": self.conversation.owner_epoch, "parent_tool_ref": asdict(parent), "description": safe,
                "command": plan.command, "cwd": plan.cwd, "timeout_ms": timeout_ms, "persistent": timeout_ms is None,
                "startedAt": started,
            })
            execution = _MonitorExecution(task, record, plan, threading.Event())
            await self._publish_monitor(execution, "running")
            self._monitors[ref.run_id] = execution
            self._tasks[task.id] = task
            execution.executor = asyncio.create_task(self._execute_monitor(execution), name="ruocun-monitor-" + ref.run_id)
            return task

    async def _execute_monitor(self, execution: _MonitorExecution) -> None:
        task = execution.task

        async def emit(text: str) -> None:
            async with self._lock:
                if self._monitors.get(task.runId) is execution:
                    await self._publish_monitor(execution, task.status, text=text)

        try:
            async with asyncio.timeout(5):
                while True:
                    view = await self.conversation.background_view()
                    parent = execution.record.snapshot["parent_tool_ref"]
                    tool = next((tool for tool in view.tool_records if asdict(tool.tool_ref) == parent), None)
                    if execution.signal.is_set():
                        break
                    if self.conversation.blocked or tool is None or tool.state == "outcome_unknown":
                        raise RuntimeError("监控启动结果未确认，保留现场。")
                    if tool.state == "result_committed":
                        break
                    await asyncio.sleep(.05)
            result = await runMonitor(execution.plan, task.description, execution.signal,
                                      timeout_ms=execution.record.snapshot["timeout_ms"], emit=emit)
            status: ExecutionStatus = "canceled" if task.status == "canceling" else "completed"
        except BaseException as error:
            status, result = "unknown", f"监控停止或输出结果未确认（{type(error).__name__}），保留现场。"
        try:
            async with self._lock:
                await self._publish_monitor(execution, status, text=result)
        except BaseException as error:
            self.conversation.blocked = True
            self.background.fail(error)
        finally:
            self._monitors.pop(task.runId, None)
            self._gc()

    def get(self, task_id: str) -> BgTask | None:
        return self._tasks.get(task_id)

    def all(self) -> list[BgTask]:
        return list(self._tasks.values())

    def running(self) -> list[BgTask]:
        return [task for task in self.all() if task.status in {"running", "canceling"}]

    def _gc(self) -> None:
        finished = sorted((task for task in self._tasks.values() if isTerminal(task.status)), key=lambda task: task.endedAt or 0)
        for task in finished[:-200]:
            self._tasks.pop(task.id, None)

    def track_foreground(self, record: RunRecord, signal: Event, *, eligible: bool) -> ForegroundAgent:
        if record.kind not in {"agent", "fork"} or self._closed:
            raise AgentFailure("当前任务管理器不能登记前台子代理。")
        task = BgTask(record.run_ref.task_id, record.run_ref.run_id, record.kind, record.snapshot["description"], "running",
                      agentType=record.snapshot["agentType"], startedAt=record.snapshot["startedAt"])
        entry = ForegroundAgent(task, signal, eligible, self._lock, record)
        self._foreground[task.runId] = entry
        self._tasks[task.id] = task
        return entry

    def finish_foreground(self, entry: ForegroundAgent, status: ExecutionStatus, *, result: str | None = None,
                          ended_at: int | None = None, transferred: bool = False) -> None:
        self._foreground.pop(entry.task.runId, None)
        entry.task.status, entry.task.endedAt = status, ended_at
        if status == "completed":
            entry.task.result = result
        else:
            entry.task.error = result
        if entry.requested is not None and not entry.requested.done():
            entry.requested.set_result(transferred)
        self._gc()

    async def convert_foreground(self) -> int:
        if self._closed or self.conversation.blocked:
            return 0
        requests: list[tuple[ForegroundAgent, asyncio.Future[bool]]] = []
        for entry in self._foreground.values():
            if not entry.eligible or entry.signal.is_set() or (entry.requested is not None and not entry.requested.done()):
                continue
            future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
            entry.requested = future
            requests.append((entry, future))
        if not requests:
            return 0
        try:
            await asyncio.wait([future for _, future in requests], timeout=5)
        finally:
            for entry, future in requests:
                if not entry.claimed and not future.done():
                    future.set_result(False)  # 工具或模型还没有到达可交回控制权的边界。
        return sum(await asyncio.gather(*(asyncio.shield(future) for _, future in requests)))

    async def _persist_task(self, record: RunRecord) -> None:
        if self.conversation.blocked:
            raise ToolRejected("当前会话有结果未确认的操作，未更改任务记录。")
        try:
            await self.conversation.publish_background(record, None)
        except (CommitUnconfirmedError, RollbackError):
            self.conversation.blocked = True
            raise
        except StoreError as exc:
            raise ToolRejected("任务记录保存被拒绝，未应用本次更改。") from exc
        except BaseException:
            self.conversation.blocked = True
            raise

    async def _task_record(self, task: BgTask) -> RunRecord:
        ref = RunRef(task.id, task.runId)
        view = await self.conversation.background_view()
        record = next((run for run in view.runs if run.run_ref == ref), None)
        if record is None or record.kind != task.kind or record.status != task.status:
            raise ToolRejected("任务持久身份或状态已变化，保留原记录。")
        return record

    async def send(self, task_id: str, message: str) -> bool:
        async with self._lock:
            task = self._tasks.get(task_id)
            if self._closed or task is None or task.kind == "manual" or task.status != "running":
                return False
            background = self._runs.get(task.runId)
            foreground = self._foreground.get(task.runId)
            if not ((background is not None and background.executor is not None and not background.prepared.ctx.signal.is_set())
                    or (foreground is not None and not foreground.signal.is_set())):
                return False
            record = await self._task_record(task)
            sender = asdict(self.conversation.current_tool_ref())
            inbox = record.snapshot.get("task_inbox", [])
            safe = self.conversation.redact(message)
            existing = next((entry for entry in inbox if entry["sender"] == sender), None)
            if existing is not None:
                if existing["message"] != safe:
                    raise ToolRejected("同一 TaskSend 身份的追加指令发生变化。")
                return True
            updated = replace(record, snapshot={**record.snapshot, "task_inbox": [*inbox, {"sender": sender, "message": safe}]})
            await self._persist_task(updated)
            if background is not None:
                background.record = updated
            if foreground is not None:
                foreground.record = updated
            return True

    async def create(self, description: str) -> str:
        async with self._lock:
            if self._closed or not description:
                raise ToolRejected("任务管理器已关闭或缺少任务描述。")
            safe = self.conversation.redact(description)
            self._manual_counter += 1
            ref = RunRef(f"task-{self._manual_counter}", str(uuid.uuid4()))
            started = time_ns() // 1_000_000
            await self._persist_task(RunRecord(ref, "manual", "running", False, {"description": safe, "startedAt": started}))
            self._tasks[ref.task_id] = BgTask(ref.task_id, ref.run_id, "manual", safe, "running", startedAt=started)
            return ref.task_id

    async def update(self, task_id: str, *, description: str | None = None,
                     status: Literal["completed", "failed", "canceled"] | None = None,
                     result: str | None = None) -> bool:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None or (status is not None and task.kind != "manual"):
                return False
            if self._closed:
                raise ToolRejected("任务管理器已关闭，未更改任务记录。")
            transition = status is not None and task.status == "running"
            renamed = self.conversation.redact(description) if description is not None else task.description
            if not transition and renamed == task.description:
                return status is None
            record = await self._task_record(task)
            snapshot = {**record.snapshot, "description": renamed}
            execution = snapshot.get("background_execution")
            if isinstance(execution, dict):
                snapshot["background_execution"] = {**execution, "description": renamed}
            ended = task.endedAt
            safe_result = self.conversation.redact(result) if result is not None else None
            if transition:
                ended = time_ns() // 1_000_000
                snapshot.update(endedAt=ended, result=safe_result)
            updated = replace(record, snapshot=snapshot, status=status if transition and status is not None else record.status)
            await self._persist_task(updated)
            task.description = renamed
            if live := self._runs.get(task.runId):
                live.record = updated
            if tracked := self._foreground.get(task.runId):
                tracked.record = updated
            if monitor := self._monitors.get(task.runId):
                monitor.record = updated
            if transition and status is not None:
                task.status, task.endedAt = status, ended
                if status == "completed":
                    task.result = safe_result
                else:
                    task.error = safe_result
                self._gc()
            return status is None or transition

    def _new(self, prepared: PreparedAgentRun, ref: RunRef, description: str, parent: ToolRef,
             request: Request | None, *, continuation: AgentContinuation | None = None,
             kind: Literal["agent", "fork"] = "agent") -> _Execution:
        if continuation is None and prepared.exact_tools is None:
            prepared.registry.restoreDeferredVisibility(["MessageParent"])
        material = agentRecoveryMaterial(prepared)
        material["archive_scope"] = ref.run_id
        if continuation is not None:
            validatePreparedContinuation(prepared, continuation)
            remaining = continuation.material["turnsRemaining"]
            material["turnsRemaining"] = remaining
            prepared = replace(prepared, max_turns=remaining)
        output_start = len(prepared.session.messages)
        task = BgTask(ref.task_id, ref.run_id, kind, self.conversation.redact(description), "running",
                      agentType=prepared.definition.agent_type, startedAt=time_ns() // 1_000_000)
        data: dict[str, Any] = {
            "parent_tool_ref": asdict(parent), "background_agent_epoch": self.conversation.owner_epoch,
            "background_by_definition": prepared.definition.background,
            "description": task.description, "model": prepared.session.model, "agentType": task.agentType,
            "startedAt": task.startedAt,
            "messages": copy.deepcopy(prepared.session.messages), "output_start": output_start,
            "output_raw_offset": output_start, "archive_scope": ref.run_id,
            "recovery_material": material, "background_execution": asdict(self._snapshot(task, "running")),
        }
        if continuation is not None:
            data.update(decision_ref=continuation.decision_id, continuation_of=asdict(continuation.previous.run_ref),
                        phase="continuation-running")
        return _Execution(task, RunRecord(ref, kind, "running", False, data), prepared, parent, request, material, output_start)

    async def launch(self, prepared: PreparedAgentRun, *, description: str, parent: ToolRef,
                     request: Request | None = None, parent_signal: Event | None = None,
                     kind: Literal["agent", "fork"] = "agent") -> BgTask:
        from .run_agent import closePreparedAgentMcp, openPreparedAgentMcp

        accepted = False
        try:
            await openPreparedAgentMcp(prepared)
            async with self._lock:
                if (self._closed or self.conversation.blocked or prepared.ctx.signal.is_set()
                        or parent_signal is not None and parent_signal.is_set()):
                    raise AgentFailure("后台执行入口当前不能启动新的子代理。")
                ref = RunRef(f"agent-{uuid.uuid4().hex}", str(uuid.uuid4()))
                execution = self._new(prepared, ref, description, parent, request, kind=kind)
                execution.archive_import = await prepareAgentArchive(self.conversation, prepared)
                if execution.archive_import is not None:
                    execution.record.snapshot["output_raw_offset"] = agentOutputOffset(
                        prepared.session.messages, execution.archive_import)
                await self._publish(execution, "started", "running")
                self._start(execution)
                accepted = True
                return execution.task
        finally:
            if not accepted:
                await closePreparedAgentMcp(prepared)

    async def launch_handoff(self, entry: ForegroundAgent, source: RunRecord, prepared: PreparedAgentRun,
                             parent: ToolRef, parent_signal: Event, request: Request | None, *,
                             worktree: Worktree | None = None) -> BgTask | None:
        from .run_agent import closePreparedAgentMcp, openPreparedAgentMcp

        accepted = False
        try:
            await openPreparedAgentMcp(prepared)
            async with self._lock:
                if (self._closed or self.conversation.blocked or parent_signal.is_set() or not entry.claimed
                        or self._foreground.get(entry.task.runId) is not entry):
                    return None
                remaining = source.snapshot["turnsRemaining"]
                output_start = source.snapshot["output_start"]
                prepared = replace(prepared, archive_source_scope=source.run_ref.run_id, archive_source_indices=None)
                ref = RunRef(f"agent-{uuid.uuid4().hex}", str(uuid.uuid4()))
                execution = self._new(prepared, ref, entry.task.description, parent, request,
                                      kind="fork" if source.kind == "fork" else "agent")
                execution.prepared = replace(prepared, max_turns=remaining)
                execution.output_start = output_start
                execution.worktree = worktree
                execution.material["turnsRemaining"] = remaining
                execution.archive_import = await prepareAgentArchive(self.conversation, prepared)
                raw_offset = source.snapshot.get("output_raw_offset", output_start)
                execution.material["output_raw_offset"] = raw_offset
                execution.record = replace(execution.record, snapshot={
                    **execution.record.snapshot, "foreground_handoff": asdict(source.run_ref), "output_start": output_start,
                    "output_raw_offset": raw_offset,
                    "isolation": source.snapshot.get("isolation"), "isolation_tree": source.snapshot.get("isolation_tree"),
                })
                await self._publish(execution, "started", "running")
                execution.task.messages[:] = await agentOutputMessages(self.conversation, execution.record)
                self._start(execution)
                accepted = True
                return execution.task
        finally:
            if not accepted:
                await closePreparedAgentMcp(prepared)

    async def resume_ended(self, task_id: str, instruction: str, *,
                           prepare: Callable[[AgentContinuation], Awaitable[PreparedAgentRun]], parent_signal: Event) -> None:
        from .run_agent import (
            _background_prepared,
            closePreparedAgentMcp,
            openPreparedAgentMcp,
        )

        async with self._lock:
            if self._closed or self.conversation.blocked or parent_signal.is_set():
                raise ValueError("当前会话尚有未决结果、已取消或已关闭，未恢复任务。")
            task = self._tasks.get(task_id)
            if task is None or task.kind != "agent":
                raise ValueError("只支持继续具有完整记录的普通代理。")
            if task.status == "interrupted":
                raise ValueError("中断代理须由用户 /recovery continue 明确继续。")
            if task.status not in {"completed", "failed", "canceled"}:
                raise ValueError("原代理尚未结算，或执行结果未确认。")
            source = self.conversation.current_tool_ref()
            if source.scope != "main":
                raise ValueError("只有父会话能恢复任务。")
            prior = await self._task_record(task)
            material = prior.snapshot.get("recovery_material")
            if not isinstance(material, dict) or prior.snapshot.get("handoff_to") is not None:
                raise ValueError("原代理缺少可继续的现场，或已交接给另一个任务。")
            if material.get("agentType") in {"explore", "plan"}:
                raise ValueError("一次性 agent 不支持恢复。")
            view = await self.conversation.background_view()
            messages = material.get("messages")
            if (not isinstance(messages, list) or not messages or repairToolPairs(messages) != messages
                    or view.missing_attachments or any(run.status == "unknown" for run in view.runs)
                    or any(record.state != "result_committed" for record in view.tool_records if record.tool_ref != source)):
                raise ValueError("原会话存在未决操作、缺失附件或未配对工具，未恢复任务。")
            raw_parent = prior.snapshot.get("parent_tool_ref")
            if not isinstance(raw_parent, dict) or raw_parent.get("scope") != "main" or not isinstance(raw_parent.get("tool_call_id"), str):
                raise ValueError("原代理缺少可信父Agent身份。")
            key = f"{self.conversation.session_id}:task-send:{source.tool_call_id}"
            ref = RunRef(task_id, str(uuid.uuid5(uuid.NAMESPACE_URL, key)))
            continuation = AgentContinuation(key, prior, ref, self.conversation.redact(instruction), copy.deepcopy(material))
            candidate = await prepare(continuation)
            prepared = None
            accepted = False
            try:
                validatePreparedContinuation(candidate, continuation)
                if parent_signal.is_set() or self.conversation.blocked:
                    raise ValueError("恢复请求已取消或会话需核实，未启动任务。")
                prepared = replace(_background_prepared(candidate), archive_source_scope=prior.run_ref.run_id,
                                   archive_source_indices=None)
                await openPreparedAgentMcp(prepared)
                parent = ToolRef("main", raw_parent["tool_call_id"])
                execution = self._new(prepared, ref, task.description, parent, None)
                execution.archive_import = await prepareAgentArchive(self.conversation, prepared)
                offset = agentOutputOffset(prepared.session.messages, execution.archive_import)
                execution.record.snapshot["output_raw_offset"] = offset
                execution.material["output_raw_offset"] = offset
                remaining = material["turnsRemaining"]
                execution.prepared = replace(prepared, max_turns=remaining)
                execution.material["turnsRemaining"] = remaining
                execution.record = replace(execution.record, snapshot={**execution.record.snapshot,
                    "task_send_ref": asdict(source), "resumed_from": asdict(prior.run_ref)})
                execution.task_send = source
                await self._publish(execution, "started", "running")
                self._start(execution)
                accepted = True
            finally:
                await closePreparedAgentMcp(candidate)
                if prepared is not None and not accepted:
                    await closePreparedAgentMcp(prepared)

    async def _await_task_send_result(self, execution: _Execution) -> None:
        source = execution.task_send
        if source is None:
            return
        async with asyncio.timeout(5):
            while not execution.prepared.ctx.signal.is_set():
                if self.conversation.blocked:
                    break
                view = await self.conversation.background_view()
                tool = next((tool for tool in view.tool_records if tool.tool_ref == source), None)
                if tool is None or tool.state == "outcome_unknown":
                    break
                if tool.state == "result_committed":
                    return
                await asyncio.sleep(.05)
        if execution.prepared.ctx.signal.is_set():
            raise _AgentStopped()
        raise RuntimeError("父 TaskSend 结果未确认，未调用新模型或工具。")

    async def continue_run(self, prepared: PreparedAgentRun, continuation: AgentContinuation, *,
                           request: Request | None = None) -> RunRecord:
        from .run_agent import closePreparedAgentMcp, openPreparedAgentMcp

        accepted = False
        try:
            await openPreparedAgentMcp(prepared)
            async with self._lock:
                ref = continuation.new_run
                if self._closed or ref.run_id in self._runs or prepared.ctx.signal.is_set():
                    raise ValueError("继续执行器身份已经使用或不可用。")
                raw_parent = continuation.previous.snapshot.get("parent_tool_ref")
                if not isinstance(raw_parent, dict) or raw_parent.get("scope") != "main" or not isinstance(raw_parent.get("tool_call_id"), str):
                    raise ValueError("原代理缺少可信父工具身份。")
                prepared = replace(prepared, archive_source_scope=continuation.previous.run_ref.run_id,
                                   archive_source_indices=None)
                execution = self._new(prepared, ref, str(continuation.previous.snapshot.get("description", "(恢复)")),
                                      ToolRef("main", raw_parent["tool_call_id"]), request, continuation=continuation)
                inherited = await prepareAgentArchive(self.conversation, prepared)
                offset = agentOutputOffset(prepared.session.messages, inherited)
                execution.record.snapshot["output_raw_offset"] = offset
                execution.material["output_raw_offset"] = offset
                operation_id = "agent-continue-" + uuid.uuid4().hex
                execution.record.snapshot["archive_operation_id"] = operation_id
                handle = self.conversation.stage_background(execution.record, None, operation_id=operation_id,
                                                            archive_import=inherited)
                try:
                    await handle.wait()
                except BaseException:
                    self.conversation.blocked = True
                    raise
                self._runs[ref.run_id] = execution
                accepted = True
                return execution.record
        finally:
            if not accepted:
                await closePreparedAgentMcp(prepared)

    async def activate_continuation(self, ref: RunRef, *, wait: bool = False) -> None:
        async with self._lock:
            execution = self._runs.get(ref.run_id)
            if (self._closed or execution is None or execution.record.run_ref != ref
                    or execution.executor is not None or self.conversation.blocked):
                raise ValueError("继续执行未获本次确认，禁止启动。")
            view = await self.conversation.background_view()
            persisted = next((run for run in view.runs if run.run_ref == ref), None)
            if (persisted is None or persisted.status != "running"
                    or persisted.snapshot.get("decision_ref") != execution.record.snapshot.get("decision_ref")
                    or persisted.snapshot.get("background_agent_epoch") != self.conversation.owner_epoch):
                raise ValueError("继续执行缺少本次许可与运行回执。")
            self._start(execution)
            executor = execution.executor
        if wait and executor is not None:
            await asyncio.shield(executor)

    def _start(self, execution: _Execution) -> None:
        task = execution.task
        self._tasks[task.id] = task
        self._runs[task.runId] = execution
        execution.executor = asyncio.create_task(self._execute(execution), name="ruocun-agent-" + task.runId)

    async def _publish(self, execution: _Execution, event: EventType, status: ExecutionStatus, *,
                       result: str | None = None, summary: str | None = None, attention: str | None = None,
                       event_id: str | None = None) -> None:
        task, previous = execution.task, execution.record
        snapshot = self._snapshot(task, status, result=result, summary=summary)
        record = replace(previous, status=status, cancel_requested=previous.cancel_requested or status == "canceling")
        if isTerminal(status):
            record = replace(record, snapshot={**record.snapshot, "endedAt": time_ns() // 1_000_000})
        notification = ExecutionEvent(event, snapshot, attention, attention is not None, event_id)
        if execution.archive_import is None:
            await self.background.publish(notification, record, require_commit=True)
        else:
            await self.background.publish(notification, record, require_commit=True, archive_import=execution.archive_import)
        execution.archive_import = None
        execution.record = record
        task.status, task.summary = status, snapshot.progress
        task.endedAt = record.snapshot.get("endedAt")
        if status == "completed":
            task.result = result
        elif status in {"canceled", "failed", "unknown"}:
            task.error = result

    async def _save(self, execution: _Execution, messages: list[dict[str, Any]], *, decrement: bool = False,
                    archive_rewrite: ArchiveRewrite | None = None) -> None:
        async with self._lock:
            task = execution.task
            if self._runs.get(task.runId) is not execution or task.status not in {"running", "canceling"}:
                raise _AgentStopped()
            if decrement and (task.status != "running" or execution.prepared.ctx.signal.is_set()):
                raise _AgentStopped()
            if archive_rewrite is not None and list(archive_rewrite.expected_messages) != execution.prepared.session.messages:
                raise RuntimeError("后台子代理压缩期间上下文已变化，原检查点保留。")
            pending = task_inbox_messages(execution.record.snapshot.get("task_inbox", [])) if decrement else []
            safe = self.conversation.redacted_messages([*messages, *pending] if pending else messages)
            remaining = execution.material["turnsRemaining"]
            if decrement and remaining <= 0:
                raise RuntimeError("后台代理剩余轮次已耗尽。")
            material = agentRecoveryMaterial(execution.prepared, safe)
            if any(material[key] != execution.material[key] for key in ("worktreeIdentity", "workspaceIdentity")):
                raise RuntimeError("后台代理工作区身份已变化，停止执行并保留原检查点。")
            material["turnLimit"] = execution.material["turnLimit"]
            previous = execution.record
            snapshot = agentCheckpointSnapshot(previous.snapshot, safe, material, remaining - int(decrement), pending)
            if archive_rewrite is not None:
                snapshot["archive_operation_id"] = "agent-compact-" + uuid.uuid4().hex
            execution.record = replace(previous, snapshot=snapshot)
            activity = await agentOutputMessages(self.conversation, previous)
            if archive_rewrite is None:
                activity.extend(safe[len(previous.snapshot.get("messages", [])):])
            progress = next((message["content"] for message in reversed(activity)
                             if message.get("role") == "assistant" and isinstance(message.get("content"), str)
                             and message["content"]), None)
            try:
                if archive_rewrite is not None:
                    handle = self.conversation.stage_background(execution.record, None,
                        operation_id=snapshot["archive_operation_id"], archive_rewrite=archive_rewrite)
                    await handle.wait()
                else:
                    await self._publish(execution, "progress", task.status, summary=progress[:180] if progress else None)
            except BaseException:
                execution.record = previous
                if archive_rewrite is not None:
                    self.conversation.blocked = True
                raise
            execution.material = material
            messages.extend(pending)
            task.messages[:] = await agentOutputMessages(self.conversation, execution.record)

    async def _execute(self, execution: _Execution) -> None:
        from .run_agent import (
            agentApprovalSignal,
            closePreparedAgentMcp,
            runPreparedAgent,
        )

        prepared, task = execution.prepared, execution.task

        async def boundary() -> None:
            await self._save(execution, prepared.session.messages, decrement=True)

        async def message_parent(message: str, kind: Literal["progress", "attention"]) -> bool:
            return await self.emitFromTask(execution.record.run_ref, message, requires_attention=kind == "attention",
                                           sender=self.conversation.current_tool_ref())

        prepared.ctx.messageParent = message_parent
        hooks = prepared.lifecycle_hooks
        journal = _Journal(self, execution)
        run = execution.record.run_ref
        handoff = execution.record.snapshot.get("foreground_handoff")
        lifecycle_started = False
        status: ExecutionStatus
        owner = agentApprovalSignal.set(prepared.ctx.signal)
        try:
            await self._await_task_send_result(execution)
            lifecycle_started = True
            if hooks is not None and handoff is None:
                async with self.conversation.agent_tool_batches:
                    await startAgentHooks(hooks, prepared.session, run, prepared.definition.agent_type,
                                          prepared.ctx.workspaceRoot, prepared.ctx.signal, journal)
            outcome = await runPreparedAgent(prepared, journal=journal, request=execution.request,
                                             tool_batch_scope=self.conversation.agent_tool_batches, on_boundary=boundary)
            output_view = copy.copy(prepared.session)
            output_view.messages = await agentOutputMessages(self.conversation, execution.record)
            status, result = settleAgentTurn(output_view, outcome, output_start=0)
            if status == "completed" and self.handoff is not None and prepared.parent_mode == "auto" and not prepared.ctx.signal.is_set():
                warning = await self.handoff(self.conversation.redacted_messages(prepared.session.messages), prepared.definition.agent_type)
                if warning:
                    result = warning + "\n\n" + result
        except _AgentStopped:
            status, result = "canceled", "执行器已确认停止。"
        except HookOutcomeUnknown as error:
            if isinstance(error.__cause__, _StartHookNotAdmitted):
                status, result = "canceled", "执行器已确认停止。"
            else:
                self.conversation.blocked = True
                status, result = "unknown", str(error)
        except BaseException as error:
            status, result = "unknown", f"子代理执行结果未确认（{type(error).__name__}），保留现场。"
        finally:
            agentApprovalSignal.reset(owner)
        try:
            if hooks is not None and lifecycle_started and status != "unknown" and not self.conversation.blocked:
                try:
                    async with self.conversation.agent_tool_batches:
                        await stopAgentHooks(hooks, run, prepared.definition.agent_type, prepared.ctx.workspaceRoot, journal,
                                             agent_id=handoff["task_id"] if isinstance(handoff, dict) else None)
                except HookOutcomeUnknown as error:
                    self.conversation.blocked = True
                    status, result = "unknown", str(error)
            # 子代理检查点和停止钩子均已完成。
            # Windows 上要先释放 MCP 服务的工作目录，再移除干净的隔离工作树。
            await closePreparedAgentMcp(prepared)
            async with self._lock:
                if self._runs.get(task.runId) is execution:
                    if prepared.ctx.signal.is_set() and status in {"completed", "failed"}:
                        status = "canceled"
                    if (tree := execution.worktree) is not None:
                        if status == "completed":
                            try:
                                result = await finishAgentWorktree(tree, result + "\n[remote 在同机 Git 工作树执行。]")
                            except GitMutationUnknown as error:
                                status, result = "unknown", str(error)
                        else:
                            result += f"\n[隔离目录保留：{tree.root}。]"
                    event = cast(EventType, status)
                    await self._publish(execution, event, status, result=self.conversation.redact(result))
        except BaseException as error:
            self.conversation.blocked = True
            self.background.fail(error)
        finally:
            try:
                await closePreparedAgentMcp(prepared)
            finally:
                self._runs.pop(task.runId, None)
                self._gc()

    async def cancel(self, task_id: str) -> Literal["canceling", "canceled"] | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.status != "running":
                return None
            if task.kind == "manual":
                record = await self._task_record(task)
                ended = time_ns() // 1_000_000
                await self._persist_task(replace(record, status="canceled", cancel_requested=True,
                                                 snapshot={**record.snapshot, "endedAt": ended}))
                task.status, task.endedAt = "canceled", ended
                self._gc()
                return "canceled"
            if monitor := self._monitors.get(task.runId):
                await self._publish_monitor(monitor, "canceling")
                monitor.signal.set()
                return "canceling"
            execution = self._runs.get(task.runId)
            if execution is None or execution.task is not task or execution.executor is None:
                return None
            await self._publish(execution, "progress", "canceling")
            execution.prepared.ctx.signal.set()
            return "canceling"

    async def emitFromTask(self, ref: RunRef, message: str, *, requires_attention: bool = True,
                           sender: ToolRef | None = None) -> bool:
        async with self._lock:
            execution = self._runs.get(ref.run_id)
            if (execution is None or execution.record.run_ref != ref or execution.task.status != "running"
                    or execution.prepared.ctx.signal.is_set() or sender is not None and sender.scope != ref.run_id):
                return False
            safe = self.conversation.redact(message)
            await self._publish(execution, "message" if requires_attention else "progress", "running",
                                attention=safe if requires_attention else None, summary=None if requires_attention else safe,
                                event_id=f"{ref.run_id}:message-parent:{sender.tool_call_id}" if sender is not None else None)
            return True

    async def close(self) -> None:
        from .run_agent import closePreparedAgentMcp

        self._closed = True
        monitors = tuple(self._monitors.values())
        for monitor in monitors:
            try:
                await self.cancel(monitor.task.id)
            except Exception as error:
                self.conversation.blocked = True
                self.background.fail(error)
                monitor.signal.set()
        await asyncio.gather(*(monitor.executor for monitor in monitors if monitor.executor is not None))
        active = tuple(self._runs.values())
        for execution in active:
            if execution.executor is None:
                await closePreparedAgentMcp(execution.prepared)
                continue
            try:
                await self.cancel(execution.task.id)
            except Exception as error:
                self.conversation.blocked = True
                self.background.fail(error)
                execution.prepared.ctx.signal.set()
        executors = [execution.executor for execution in active if execution.executor is not None]
        if executors:
            await asyncio.gather(*executors)
        if not self.conversation.blocked:
            for task in self.running():
                if task.kind == "manual":
                    await self.cancel(task.id)
