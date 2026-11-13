"""Frozen BackgroundRuntime/WaitControl (MIT); SQLite writes use the existing worker."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from ..session.contract import ArchiveImport, OutboxEvent, RunRecord, RunRef
from ..tools.spill import spillOutput
from .background_types import (
    BackgroundEvent,
    ExecutionEvent,
    ExecutionSnapshot,
    WaitHandle,
    WaitRequest,
    WaitTarget,
    isTerminal,
)

if TYPE_CHECKING:
    from ..session.conversation import Conversation


def decode_snapshot(value: dict[str, Any]) -> ExecutionSnapshot:
    return ExecutionSnapshot(**value)


def decode_wait(value: dict[str, Any]) -> WaitHandle:
    raw = dict(value)
    raw["targets"] = tuple(WaitTarget(**target) for target in raw["targets"])
    return WaitHandle(**raw)


class BackgroundRuntime:
    def __init__(
        self, *, store: Conversation | None = None, workspaceRoot: str | Path = "."
    ) -> None:
        self.store, self.workspaceRoot = store, Path(workspaceRoot)
        self.sessionId = store.session_id if store is not None else str(uuid.uuid4())
        self.fault: BaseException | None = None
        self._materialFault: BaseException | None = None
        self.checkpointUnknown = False
        self.materialsVerified = store is None
        self._state = "idle"
        self._closed = False
        self._seq = 0
        self._runs: dict[str, ExecutionSnapshot] = {}
        self._latest: dict[str, str] = {}
        self._inbox: dict[str, BackgroundEvent] = {}
        self._waits: dict[str, WaitHandle] = {}
        self._ready: set[str] = set()
        self._readyResults: dict[str, tuple[str, tuple[tuple[str, int], ...]]] = {}
        self._consumed: set[str] = set()
        self._listeners: set[Callable[[], None]] = set()
        self._activated: dict[str, float] = {}
        self._attachments: dict[str, str] = {}
        self._delivery: dict[str, tuple[str, ...]] = {}
        self.recoveredWait: WaitHandle | None = None
        self.counters = dict.fromkeys(
            [
                "waitsRegistered",
                "waitsReleased",
                "eventsDelivered",
                "eventsDeduplicated",
                "modelRequests",
                "modelRequestsWhileWaiting",
            ],
            0,
        )

    async def bind(self) -> dict[str, Any] | None:
        if self.store is None:
            return None
        view = await self.store.background_view()
        if view.missing_attachments:
            self._materialFault = RuntimeError("后台结果附件缺失或变化，保留现场。")
            self.fault = self._materialFault
            return None
        if self.fault is self._materialFault:
            self.fault = None
            self._materialFault = None
        self._runs.clear()
        self._latest.clear()
        self._inbox.clear()
        self._waits.clear()
        for record in view.runs:
            raw = record.snapshot.get("background_execution")
            if isinstance(raw, dict):
                snapshot = decode_snapshot(raw)
                if (
                    snapshot.runId != record.run_ref.run_id
                    or snapshot.taskId != record.run_ref.task_id
                ):
                    raise ValueError("后台检查点执行身份不匹配。")
                self._runs[snapshot.runId] = snapshot
                self._latest[snapshot.taskId] = snapshot.runId
        for event in view.pending_events:
            raw = event.snapshot
            snapshot = decode_snapshot(raw["execution"])
            if (
                snapshot.runId != event.run_ref.run_id
                or snapshot.taskId != event.run_ref.task_id
            ):
                raise ValueError("后台事件执行身份不匹配。")
            self._inbox[event.event_id] = BackgroundEvent(
                self.sessionId,
                event.event_id,
                event.seq,
                cast(Any, event.event_type),
                snapshot,
                raw.get("message"),
                bool(raw.get("requiresAttention")),
            )
            self._seq = max(self._seq, event.seq)
        saved = view.checkpoint.background if view.checkpoint is not None else None
        if saved:
            self._state = saved["state"]
            self._seq = max(self._seq, saved.get("seq", 0))
            if saved.get("wait"):
                handle = decode_wait(saved["wait"])
                if handle.sessionId != self.sessionId:
                    raise ValueError("等待会话身份不匹配。")
                self._waits[handle.waitId] = handle
                self.recoveredWait = handle
        self.materialsVerified = True
        self.store.bind_background(self)
        return saved

    def checkpoint(self) -> dict[str, Any]:
        wait = next(
            (handle for key, handle in self._waits.items() if key not in self._ready),
            None,
        )
        return {
            "sessionId": self.sessionId,
            "state": "waiting" if wait else self._state,
            "wait": asdict(wait) if wait else None,
            "seq": self._seq,
            "consumed": sorted(self._consumed),
        }

    def setState(self, state: str) -> None:
        self._state = state

    @property
    def consumed(self) -> tuple[str, ...]:
        return tuple(sorted(self._consumed))

    def stageConsumed(self, ids: list[str]) -> None:
        self._consumed.update(ids)

    def unstageConsumed(self, ids: list[str]) -> None:
        self._consumed.difference_update(ids)

    def stageDelivery(self, ids: list[str], message: dict[str, Any]) -> None:
        self.stageConsumed(ids)
        self._delivery[str(message["content"])] = tuple(ids)

    def consumedForMessages(self, messages: list[dict[str, Any]]) -> tuple[str, ...]:
        if not self._consumed:
            return ()
        represented: set[str] = set()
        names = {
            call["id"]: call.get("function", {}).get("name")
            for message in messages
            for call in message.get("tool_calls", [])
        }
        for message in messages:
            content = message.get("content")
            if not isinstance(content, str):
                continue
            if message.get("role") == "user":
                represented.update(self._delivery.get(content, ()))
            elif (
                message.get("role") == "tool"
                and names.get(message.get("tool_call_id")) == "TaskWait"
            ):
                try:
                    result = json.loads(content)
                    handle = self._waits.get(result.get("waitId"))
                    if (
                        handle is not None
                        and handle.waitId in self._ready
                        and result.get("status") == "ready"
                        and [target.get("runId") for target in result["targets"]]
                        == [target.runId for target in handle.targets]
                    ):
                        expected = self._readyResults.get(handle.waitId)
                        if expected is not None and content == expected[0]:
                            represented.update(
                                event_id
                                for event_id, seq in expected[1]
                                if event_id in self._inbox
                                and self._inbox[event_id].seq == seq
                            )
                except (TypeError, ValueError, KeyError, AttributeError):
                    continue
        return tuple(sorted(represented & self._consumed))

    def renderResult(self, text: str) -> str:
        if self.store is None:
            return spillOutput(text, str(self.workspaceRoot), 24000)
        text = self.store.redact(text)
        if len(text.encode("utf-16-le")) // 2 <= 24000:
            return text
        from ..platform.windows.durable_file import atomic_publish, ensure_private_dir

        payload = text.encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        directory = self.store.directory / "results"
        ensure_private_dir(directory)
        file = directory / (digest + ".txt")
        atomic_publish(file, payload)
        self._attachments[str(file)] = digest
        return (
            spillOutput(text, str(self.workspaceRoot), 24000, persist=False)
            + f"\n[完整输出已持久保存：{file}]"
        )

    async def flushAttachments(self) -> None:
        if self.store is not None:
            for file, digest in tuple(self._attachments.items()):
                await self.store.register_background_attachment(file, digest)
                self._attachments.pop(file, None)

    def subscribe(self, callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(callback)
        return lambda: self._listeners.discard(callback)

    def fail(self, error: BaseException) -> None:
        self.fault = error
        self._notify()

    async def attachFile(self, file: Path, expected: str) -> None:
        if self.store is None:
            return

        def verify() -> None:
            from ..platform.windows.durable_file import verify_private_file

            verify_private_file(file)
            digest = hashlib.sha256()
            with file.open("rb") as data:
                while chunk := data.read(65536):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                raise ValueError("后台结果附件与关闭收据摘要不符。")

        await asyncio.to_thread(verify)
        await self.store.register_background_attachment(str(file), expected)

    def _notify(self) -> None:
        for callback in tuple(self._listeners):
            callback()

    async def publish(
        self,
        event: ExecutionEvent,
        record: RunRecord | None = None,
        *,
        import_receipt: bool = False,
        require_commit: bool = False,
        archive_import: ArchiveImport | None = None,
    ) -> None:
        if self._closed or not event.snapshot.background:
            if require_commit:
                raise RuntimeError("后台事件通道不可用，未确认运行变更。")
            return
        snapshot = event.snapshot
        old = self._runs.get(snapshot.runId)
        if import_receipt and (
            record is None
            or record.kind != "shell"
            or record.status != snapshot.status
            or event.type != snapshot.status
            or not record.snapshot.get("receipt_digest")
        ):
            raise ValueError("Shell终态导入缺少原运行关闭收据。")
        if event.type != "started" and old is None and not import_receipt:
            if require_commit:
                raise RuntimeError("后台事件缺少已登记的同一运行。")
            return
        if (
            old
            and isTerminal(old.status)
            and old.status != "interrupted"
            and event.type != "unknown"
            and not import_receipt
        ):
            self.counters["eventsDeduplicated"] += 1
            if require_commit:
                raise RuntimeError("后台运行已结算，拒绝新变更。")
            return
        if self.store is not None and snapshot.kind == "shell" and record is None:
            raise ValueError("持久Shell事件需要实际执行器的完整RunRecord。")
        produces = event.type not in {"started", "progress"} and (
            event.type != "message" or event.requiresAttention
        )
        try:
            snapshot = replace(
                snapshot,
                result=self.renderResult(snapshot.result)
                if snapshot.result is not None
                else None,
            )
            message = (
                self.renderResult(event.message) if event.message is not None else None
            )
            seq = self._seq + 1
            event_id = event.eventId or (
                snapshot.runId + ":terminal"
                if event.type in {"completed", "failed", "canceled"}
                else snapshot.runId + ":" + event.type + ":" + uuid.uuid4().hex
            )
            output = OutboxEvent(
                event_id,
                self.sessionId,
                RunRef(snapshot.taskId, snapshot.runId),
                event.type,
                {
                    "execution": asdict(snapshot),
                    "message": message,
                    "requiresAttention": event.requiresAttention,
                },
                self.store.owner_epoch if self.store is not None else 0,
            )
            run = record or RunRecord(
                output.run_ref, snapshot.kind, snapshot.status, False, {}
            )
            run = replace(
                run, snapshot={**run.snapshot, "background_execution": asdict(snapshot)}
            )
            if self.store is not None:
                await self.flushAttachments()
                if archive_import is None:
                    saved = await self.store.publish_background(run, output if produces else None)
                else:
                    saved = await self.store.publish_background(run, output if produces else None,
                                                                archive_import=archive_import)
                if saved is not None:
                    output = saved
                    seq = output.seq
            self._runs[snapshot.runId] = snapshot
            if event.type == "started" or snapshot.taskId not in self._latest:
                self._latest[snapshot.taskId] = snapshot.runId
            if produces:
                self._seq = max(self._seq, seq)
                if output.delivered_revision is None:
                    self._inbox[event_id] = BackgroundEvent(
                        self.sessionId,
                        event_id,
                        seq,
                        event.type,
                        snapshot,
                        message,
                        event.requiresAttention,
                    )
            self._gc()
            self._notify()
        except BaseException as error:
            self.fail(error)
            if require_commit or isinstance(error, asyncio.CancelledError):
                raise

    def snapshot(self, task_id: str) -> ExecutionSnapshot | None:
        snapshot = self._runs.get(self._latest.get(task_id, ""))
        alias = self._runs.get(task_id)
        return snapshot or (
            alias if alias is not None and alias.kind == "shell" else None
        )

    def snapshots(self) -> list[ExecutionSnapshot]:
        return [
            self._runs[run_id]
            for run_id in self._latest.values()
            if run_id in self._runs
        ]

    def running(self) -> list[ExecutionSnapshot]:
        return [
            snapshot
            for snapshot in self.snapshots()
            if snapshot.status in {"running", "canceling"}
        ]

    def events(self) -> list[BackgroundEvent]:
        return list(self._inbox.values())

    def acknowledge(self, ids: list[str]) -> None:
        self._consumed.difference_update(ids)
        for event_id in ids:
            if self._inbox.pop(event_id, None) is not None:
                self.counters["eventsDelivered"] += 1
        self._delivery = {
            message: ids
            for message, ids in self._delivery.items()
            if any(event_id in self._consumed for event_id in ids)
        }
        self._gc()

    def prepare(self, request: WaitRequest) -> tuple[WaitHandle, bool]:
        ids = list(dict.fromkeys(request["ids"]))
        if not ids or len(ids) > 32 or request["mode"] not in {"any", "all"}:
            raise ValueError("TaskWait 需要 1–32 个不同任务 ID及any/all模式。")
        targets = []
        for task_id in ids:
            snapshot = self.snapshot(task_id)
            if snapshot is None or not snapshot.background:
                raise ValueError(f"不可等待任务 {task_id}:不是当前会话的后台执行。")
            if snapshot.status in {"unknown", "interrupted"}:
                raise ValueError(f"任务 {task_id} 需要恢复核实，不能等待未知执行。")
            target = WaitTarget(snapshot.taskId, snapshot.runId)
            if target not in targets:
                targets.append(target)
        handle = WaitHandle(
            str(uuid.uuid4()),
            self.sessionId,
            tuple(targets),
            request["mode"],
            self._seq,
        )
        self._waits[handle.waitId] = handle
        self.counters["waitsRegistered"] += 1
        return handle, self.ready(handle)

    def ready(self, handle: WaitHandle) -> bool:
        if handle.waitId not in self._waits or handle.sessionId != self.sessionId:
            raise ValueError("等待已失效。")
        targets = [self._runs.get(target.runId) for target in handle.targets]
        if any(snapshot is None for snapshot in targets):
            raise ValueError("等待目标已失效。")
        if any(
            snapshot is not None
            and snapshot.status in {"failed", "canceled", "interrupted", "unknown"}
            for snapshot in targets
        ):
            return True
        if any(
            event.requiresAttention or event.type in {"failed", "canceled"}
            for event in self.events()
        ):
            return True
        completed = [
            snapshot is not None and snapshot.status == "completed"
            for snapshot in targets
        ]
        return all(completed) if handle.mode == "all" else any(completed)

    def result(self, handle: WaitHandle) -> list[ExecutionSnapshot]:
        return [self._runs[target.runId] for target in handle.targets]

    def resultEventIds(self, handle: WaitHandle) -> list[str]:
        return [
            event.eventId
            for event in self.events()
            if event.type != "message"
            and any(target.runId == event.snapshot.runId for target in handle.targets)
        ]

    def markReady(self, handle: WaitHandle) -> None:
        self._ready.add(handle.waitId)

    def rememberReadyResult(
        self, handle: WaitHandle, body: str, ids: list[str]
    ) -> None:
        self._readyResults[handle.waitId] = (
            body,
            tuple((event_id, self._inbox[event_id].seq) for event_id in ids),
        )

    def activate(self, handle: WaitHandle) -> None:
        if handle.waitId not in self._waits:
            raise ValueError("等待已失效。")
        self._activated[handle.waitId] = time.monotonic()

    def modelRequested(self) -> None:
        self.counters["modelRequests"] += 1
        if self._activated:
            self.counters["modelRequestsWhileWaiting"] += 1

    def release(self, handle: WaitHandle) -> None:
        self._ready.discard(handle.waitId)
        self._readyResults.pop(handle.waitId, None)
        self._activated.pop(handle.waitId, None)
        if self._waits.pop(handle.waitId, None) is not None:
            self.counters["waitsReleased"] += 1
        self._gc()

    @property
    def activeWaits(self) -> int:
        return len(self._waits)

    def _gc(self) -> None:
        pinned = {
            target.runId for wait in self._waits.values() for target in wait.targets
        }
        pinned.update(event.snapshot.runId for event in self.events())
        finished = [
            snapshot
            for snapshot in self._runs.values()
            if isTerminal(snapshot.status) and snapshot.runId not in pinned
        ]
        for snapshot in finished[: max(0, len(finished) - 200)]:
            self._runs.pop(snapshot.runId, None)
            if self._latest.get(snapshot.taskId) == snapshot.runId:
                self._latest.pop(snapshot.taskId, None)

    def reset(self) -> None:
        for handle in tuple(self._waits.values()):
            self.release(handle)
        self._consumed.clear()
        self._ready.clear()
        self._activated.clear()
        self._waits.clear()
        self._inbox.clear()
        self._runs.clear()
        self._latest.clear()
        self._notify()

    def dispose(self) -> None:
        self._closed = True
        self.reset()
        self._listeners.clear()


class WaitControl:
    def __init__(self, runtime: BackgroundRuntime) -> None:
        self.runtime = runtime
        self.handle: WaitHandle | None = None
        self._ready = False
        self._consumed: list[str] = []

    def request(self, request: WaitRequest) -> str:
        self.rollback()
        self.handle, self._ready = self.runtime.prepare(request)
        self._consumed = self.runtime.resultEventIds(self.handle) if self._ready else []
        if self._ready:
            self.runtime.markReady(self.handle)
        self.runtime.stageConsumed(self._consumed)
        body = json.dumps(
            {
                "status": "ready" if self._ready else "waiting",
                "waitId": self.handle.waitId,
                "mode": self.handle.mode,
                "targets": [
                    asdict(snapshot) for snapshot in self.runtime.result(self.handle)
                ],
            },
            ensure_ascii=False,
        )
        if self._ready:
            self.runtime.rememberReadyResult(self.handle, body, self._consumed)
        return body

    def commit(self) -> WaitHandle | None:
        if self.runtime.store is not None and any(
            event.eventId in self._consumed for event in self.runtime.events()
        ):
            raise RuntimeError("TaskWait结果尚未获得已保存消息确认。")
        handle, self.handle = self.handle, None
        self.runtime.acknowledge(self._consumed)
        self._consumed = []
        if handle is not None and self._ready:
            self.runtime.release(handle)
            return None
        return handle

    def rollback(self) -> None:
        self.runtime.unstageConsumed(self._consumed)
        if self.handle is not None:
            self.runtime.release(self.handle)
        self.handle = None
        self._consumed = []

    @property
    def pending(self) -> bool:
        return self.handle is not None


_current: ContextVar[WaitControl | None] = ContextVar("ruocun-task-wait", default=None)


def currentWaitControl() -> WaitControl | None:
    return _current.get()


@contextmanager
def wait_scope(runtime: BackgroundRuntime) -> Iterator[WaitControl]:
    control = WaitControl(runtime)
    token = _current.set(control)
    try:
        yield control
    finally:
        if not runtime.checkpointUnknown:
            control.rollback()
        _current.reset(token)
