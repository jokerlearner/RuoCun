"""冻结session_scheduler.ts前台调度（MIT）；队列持久化由Conversation承担。

复用后台收件箱与持久输入：TaskWait让出本轮，事件或用户输入唤醒。
"""

from __future__ import annotations

import asyncio
import copy
import threading
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal, Protocol

from ..client.types import ContentPart
from ..session.contract import AcceptedInput
from ..session.inputs import originalInput
from .background_runtime import BackgroundRuntime
from .background_types import WaitHandle

Content = str | list[ContentPart]
Boundary = Callable[[], Awaitable[None]]
State = Literal["idle", "running", "waiting", "paused", "closed", "recovering"]


class TurnOutcome(Protocol):
    @property
    def status(self) -> str: ...
    @property
    def error(self) -> str: ...


Run = Callable[[threading.Event, Boundary, int], Awaitable[TurnOutcome]]
QueueUser = Callable[[Content], Awaitable[AcceptedInput]]


@dataclass(frozen=True)
class SchedulerStatus:
    state: State
    queued: int
    runningTasks: int = 0
    waiting: dict[str, int | str] | None = None


class SessionScheduler:
    def __init__(
        self, *, queued_inputs: Callable[[], tuple[AcceptedInput, ...]],
        queue_user: QueueUser,
        consume_user: Callable[[str], Awaitable[bool]],
        discard_queued: Callable[[str], Awaitable[None]],
        set_state: Callable[[str], Awaitable[None]], run: Run,
        notice: Callable[[str], None] | None = None,
        background_runtime: BackgroundRuntime | None = None,
        deliver_background: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._queued, self._queue, self._consume = queued_inputs, queue_user, consume_user
        self._discard, self._persist_state, self._run = discard_queued, set_state, run
        self._notice = notice
        self._background, self._deliver_background = background_runtime, deliver_background
        self._wait: WaitHandle | None = None
        self._preserving_wait = False
        self._unsubscribe = background_runtime.subscribe(self._on_background) if background_runtime is not None else lambda: None
        self._state: State = "idle"
        self._generation = 0
        self._active_generation: int | None = None
        self._signal: threading.Event | None = None
        self._active = self._scheduled = False
        self._pump_task: asyncio.Task[None] | None = None
        self._control = asyncio.Lock()
        self._loop: tuple[asyncio.Event, asyncio.Task[None]] | None = None
        self._listeners: set[Callable[[SchedulerStatus], None]] = set()
        self._waiters: set[asyncio.Future[None]] = set()
        self.lastError: Exception | None = None
        self.counters = {"runCalls": 0, "failures": 0}

    def status(self) -> SchedulerStatus:
        return SchedulerStatus(self._state, len(self._queued()),
                               len(self._background.running()) if self._background is not None else 0,
                               {"count": len(self._wait.targets), "mode": self._wait.mode} if self._wait else None)

    async def run_when_idle(self, action: Callable[[], Awaitable[None]]) -> bool:
        if self._control.locked():
            return False
        async with self._control:
            if (self._state not in {"idle", "paused"} or self._active or self._scheduled
                    or self._queued() or self._has_events()
                    or self._background is not None and self._background.running()):
                return False
            await action()
            return True

    async def _set_state(self, state: str) -> None:
        if self._background is not None:
            self._background.setState(state)
        await self._persist_state(state)

    def _release_wait(self) -> None:
        if self._wait is not None and self._background is not None:
            self._background.release(self._wait)
        self._wait = None

    def _on_background(self) -> None:
        if self._state == "closed":
            return
        if self._background is not None and self._background.fault is not None:
            self._state = "paused"
            self._record_error(RuntimeError("后台结果未确认，保留现场。"))
            if self._signal is not None:
                self._signal.set()
        self._schedule()
        self._notify()

    def _has_events(self) -> bool:
        return bool(self._background is not None and self._background.events())

    def subscribe(self, callback: Callable[[SchedulerStatus], None]) -> Callable[[], None]:
        self._listeners.add(callback)
        callback(self.status())
        return lambda: self._listeners.discard(callback)

    def _record_error(self, error: Exception) -> None:
        self.lastError = error
        if self._loop is not None:
            self._loop[0].set()

    def _notify(self) -> None:
        for callback in tuple(self._listeners):
            callback(self.status())
        for waiter in tuple(self._waiters):
            if not waiter.done():
                waiter.set_result(None)

    def hasQueued(self, text: str) -> bool:
        return any(originalInput(item.payload) == text for item in self._queued())

    @property
    def active_signal(self) -> threading.Event | None:
        return self._signal

    def is_current(self, generation: int) -> bool:
        return (self._active and self._active_generation == generation == self._generation
                and self._state == "running" and self._signal is not None and not self._signal.is_set())

    async def submit(self, content: Content, *, queue_user: QueueUser | None = None) -> AcceptedInput | None:
        return await self._submit(content, queue_user=queue_user)

    async def _submit(self, content: Content, *, loop_stop: asyncio.Event | None = None,
                      queue_user: QueueUser | None = None) -> AcceptedInput | None:
        async with self._control:
            if self._state == "closed":
                return None
            if loop_stop is not None and (loop_stop.is_set() or self.lastError is not None
                    or isinstance(content, str) and self.hasQueued(content)):
                return None
            generation = self._generation
            try:
                item = await (queue_user or self._queue)(copy.deepcopy(content))
            except Exception as exc:
                self._record_error(exc)
                if self.status().state != "closed":
                    self._generation += 1
                    self._state = "paused"
                if self._signal is not None:
                    self._signal.set()
                self._notify()
                raise
            self.lastError = None
            # pause在排队提交期间发生时，不能由迟到的ack把暂停改回idle。
            if (generation == self._generation and not self._preserving_wait
                    and (not self._active or self._state == "paused")):
                self._release_wait()
                self._state = "idle"
            self._schedule()
            self._notify()
            return item

    async def start_loop(self, seconds: float, prompt: str) -> None:
        await self.stop_loop()
        if self._state != "closed":
            self.lastError = None  # An explicit command authorizes future inputs.
            stop = asyncio.Event()
            self._loop = stop, asyncio.create_task(self._repeat(seconds, prompt, stop))

    async def stop_loop(self) -> bool:
        running = self._loop
        if running is None:
            return False
        stop, task = running
        active = not task.done()
        stop.set()
        await task
        if self._loop is running:
            self._loop = None
        return active

    async def _repeat(self, seconds: float, prompt: str, stop: asyncio.Event) -> None:
        while not stop.is_set() and self._state != "closed" and self.lastError is None:
            try:
                await asyncio.wait_for(stop.wait(), timeout=seconds)
            except TimeoutError:
                try:
                    await self._submit(prompt, loop_stop=stop)
                except Exception:
                    if self._notice is not None:
                        self._notice("[会话循环已停止] 输入保存未确认，请核对后继续。")
                    return

    def _schedule(self) -> None:
        if self._active or self._scheduled or self._preserving_wait:
            return
        if self._state == "waiting" and self._wait is not None and self._background is not None:
            try:
                ready = self._background.ready(self._wait)
            except ValueError as error:
                self._record_error(error)
                self._state = "paused"
                return
            if self._queued() or ready:
                self._release_wait()
                self._state = "idle"
        if self._state != "idle" or not (self._queued() or self._has_events()):
            return
        self._scheduled = True
        self._pump_task = asyncio.create_task(self._pump())

    async def _boundary(self, generation: int) -> bool:
        accepted = False
        while self.is_current(generation):
            async with self._control:
                if not self.is_current(generation):
                    break
                queued = sorted(self._queued(), key=lambda item: item.seq)
                if not queued:
                    break
                accepted = await self._consume(queued[0].input_id) or accepted
        if self.is_current(generation) and self._has_events() and self._deliver_background is not None:
            await self._deliver_background()
            accepted = True
        return accepted and self.is_current(generation)

    async def _pump(self) -> None:
        self._scheduled = False
        if self._active or self._state != "idle" or not (self._queued() or self._has_events()):
            self._notify()
            return
        self._active = True
        self._generation += 1
        generation = self._generation
        self._active_generation = generation
        signal = self._signal = threading.Event()
        self._state = "running"
        self._notify()

        async def boundary() -> None:
            await self._boundary(generation)

        try:
            await self._set_state("running")
            work = await self._boundary(generation)
            if work and self.is_current(generation):
                self.counters["runCalls"] += 1
                result = await self._run(signal, boundary, generation)
                if generation != self._generation or self._state in {"paused", "closed"}:
                    return
                if result.status in {"cancelled", "interrupted"} or signal.is_set():
                    self._state = "idle" if self._queued() else "paused"
                    await self._set_state(self._state)
                    return
                if result.status == "waiting":
                    handle = getattr(result, "wait", None)
                    if handle is None or self._background is None:
                        raise RuntimeError("等待缺少当前会话运行时。")
                    self._wait = handle
                    self._state = "waiting"
                    self._background.activate(handle)
                    await self._set_state("waiting")
                    return
                if result.status != "complete":
                    raise RuntimeError(result.error or "本轮未完成，已暂停。")
            if generation == self._generation and self._state == "running":
                self._state = "paused" if signal.is_set() else "idle"
                await self._set_state(self._state)
        except Exception as exc:
            if generation == self._generation and self.status().state != "closed":
                self.counters["failures"] += 1
                self._record_error(exc)
                self._state = "paused"
                signal.set()
                try:
                    await self._set_state("paused")
                except Exception:
                    pass  # 原错保留；Conversation.blocked禁止绕过未确认提交。
                if self._notice is not None:
                    self._notice("[会话已暂停] 本轮或保存未完成，请核对后继续。")
        finally:
            self._active = False
            self._signal = None
            self._active_generation = None
            self._schedule()
            self._notify()

    async def _wait_until(self, predicate: Callable[[], bool]) -> None:
        await asyncio.sleep(0)
        while not predicate():
            waiter = asyncio.get_running_loop().create_future()
            self._waiters.add(waiter)
            try:
                await waiter
            finally:
                self._waiters.discard(waiter)

    async def settled(self) -> None:
        await self._wait_until(lambda: not self._active and not self._scheduled)

    @asynccontextmanager
    async def preserve_wait(self) -> AsyncIterator[bool]:
        """Keep the same wait while the CLI replaces its conversation context."""
        handle = self._wait
        if self._state not in {"waiting", "paused"} or handle is None:
            yield False
            return
        was_paused = self._state == "paused"
        self._preserving_wait = True
        try:
            await self.settled()
            yield self._state in {"waiting", "paused"} and self._wait is handle
        except (Exception, asyncio.CancelledError) as error:
            if self._wait is handle and self.status().state != "closed":
                self._state = "paused"
                self._record_error(error if isinstance(error, Exception) else RuntimeError("压缩已取消。"))
                try:
                    await self._set_state("paused")
                except Exception as save_error:
                    self._record_error(save_error)
            raise
        else:
            if (was_paused and self._state == "paused" and self._wait is handle
                    and self._background is not None and self._background.fault is None):
                await self._set_state("waiting")
                self.lastError = None
                self._state = "waiting"
        finally:
            self._preserving_wait = False
            self._schedule()
            self._notify()

    async def finished(self) -> None:
        await self._wait_until(lambda: not self._active and not self._scheduled
                               and (self._state in {"closed", "paused"} or self._state != "waiting" and not self._queued() and not self._has_events()))

    async def _halt(self, state: Literal["paused", "closed", "idle"]) -> None:
        if self._state == "closed":
            return
        self._generation += 1
        generation = self._generation
        self._release_wait()
        self._state = "closed" if state == "closed" else "paused"
        if self._signal is not None:
            self._signal.set()
        self._notify()
        async with self._control:
            try:
                await self._discard(state)
            except Exception as exc:
                self._record_error(exc)
                if self._notice is not None:
                    self._notice("[暂停未能保存] 已停止当前轮，队列处置尚未确认。")
                raise
            if generation == self._generation:
                self._state = state
                self._schedule()
            self._notify()

    async def close(self) -> None:
        try:
            await self._halt("closed")
            # 重复close也等待前一个close正在提交的处置。
            async with self._control:
                pass
        finally:
            await self.stop_loop()
            await self.settled()
            self._unsubscribe()
            self._listeners.clear()

    async def pause(self) -> None:
        await self._halt("paused")

    async def clear_pending(self) -> int:
        """Esc处置尚未消费的输入，保留当前轮次和取消信号。"""
        async with self._control:
            count = len(self._queued())
            if not count or self._state == "closed":
                return 0
            try:
                await self._discard(self._state)
            except Exception as exc:
                self._record_error(exc)
                if self.status().state != "closed":
                    self._generation += 1
                    self._state = "paused"
                if self._signal is not None:
                    self._signal.set()
                self._notify()
                raise
            self._notify()
            return count

    async def reset(self) -> None:
        await self._halt("idle")
        if self._state != "closed":
            self.lastError = None

    async def recover(self, state: str = "foreground-only") -> None:
        if self._state == "closed":
            return
        if self._active or self._scheduled:
            raise RuntimeError("请先等待当前调度轮次停止，再恢复状态。")
        async with self._control:
            self._state = "recovering"
            self._generation += 1
            self._notify()
            recovered: State = "idle" if state in {"foreground-only", "idle", "closed"} else "paused"
            if self._background is not None:
                handle = self._background.recoveredWait
                if state in {"waiting", "paused"} and handle is not None:
                    self._background.ready(handle)
                    self._wait = handle
                    self._background.activate(handle)
                    recovered = "waiting" if state == "waiting" and not self._queued() else "paused"
                elif self._has_events():
                    recovered = "paused"
            try:
                await self._set_state(recovered)
            except Exception as exc:
                self._record_error(exc)
                self._state = "paused"
                self._notify()
                raise
            self._state = recovered
            self._schedule()
            self._notify()
