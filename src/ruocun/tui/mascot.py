"""根据终端能力、尺寸和焦点决定何时显示吉祥物动画。通过注入的输出入口绘制，窗口变化后重新计算布局。"""

from __future__ import annotations

import asyncio
import math
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol

from .mascot_frames import MASCOT_FRAMES, MASCOT_IMAGE, MASCOT_TIMELINE
from .welcome import WelcomeMascotLayout, getWelcomeLayout


class MotionReports(Protocol):
    async def probe(self) -> dict[str, int] | None: ...
    async def cursor(self) -> dict[str, int] | None: ...


def motionPauseReason(state: Mapping[str, Any] | None, focused: bool, resized: bool) -> str:
    if resized:
        return "resize"
    if not state or not state.get("enabled"):
        return "disabled"
    if not focused:
        return "focus"
    if not state["home"]:
        return "history"
    if not state["inputEmpty"]:
        return "input"
    if state["busy"] or state["backgroundRunning"]:
        return "task"
    return "modal" if state["modalOpen"] else "idle"


def imageAnchor(cursorRow: int, dynamicRows: int, extraStaticRows: int,
                columns: int, terminalRows: int, mascot: WelcomeMascotLayout, *,
                fit_viewport: bool = False, require_top: bool = False) -> dict[str, int] | None:
    box = getWelcomeLayout(columns, mascot, terminalRows=terminalRows if fit_viewport else None)
    top = cursorRow - dynamicRows - extraStaticRows - box["cardHeight"]
    if (not box["sideBySide"] or top < 1 or dynamicRows < 1 or top + box["cardHeight"] - 1 > terminalRows
            or require_top and top != 1):
        return None
    return {"row": top + box["imageTop"], "column": box["imageLeft"] + 1}


def _frame_at(row: int, column: int, frame: int) -> str:
    return f"\x1b7\x1b[{row};{column}H{MASCOT_FRAMES[frame]}\x1b8"


class WelcomeMotion:
    def __init__(self, *, reports: MotionReports,
                 write: Callable[[str, Callable[[], bool]], Awaitable[bool]],
                 dimensions: Callable[[], tuple[int, int]],
                 waitUntilRenderFlush: Callable[[], Awaitable[None]],
                 cell: dict[str, int] | None = None,
                 observe: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.reports, self._write, self._dimensions = reports, write, dimensions
        self._flush, self._observe = waitUntilRenderFlush, observe
        self.layout = self._layout(cell)
        self._state: dict[str, Any] | None = None
        self._focused, self._resized, self._disposed = True, False, False
        self._needs_still, self._awaiting_epoch = True, False
        self._generation, self._reset_sequence, self._active_epoch = 0, 0, -1
        self._step = self._frame = self._frames = 0
        self._anchor: dict[str, int] | None = None
        self._timer: asyncio.TimerHandle | None = None
        self._tasks: set[asyncio.Task[None]] = set()
        self._advancing = False

    @staticmethod
    def _layout(cell: dict[str, int] | None) -> WelcomeMascotLayout | None:
        if not cell or cell.get("cell_width", 0) <= 0 or cell.get("cell_height", 0) <= 0:
            return None
        return {"columns": math.ceil(MASCOT_IMAGE["width"] / cell["cell_width"]),
                "rows": math.ceil(MASCOT_IMAGE["height"] / cell["cell_height"])}

    @property
    def reason(self) -> str:
        return "disposed" if self._disposed else motionPauseReason(self._state, self._focused, self._resized)

    def _report(self) -> None:
        if self._observe:
            self._observe({"reason": self.reason, "frames": self._frames, "frame": self._frame,
                           "epoch": self._state["epoch"] if self._state else -1,
                           "anchor": self._anchor, "state": self._state, "layout": self.layout})

    def _stop(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def pause(self) -> None:
        self._generation += 1
        self._stop()
        self._anchor = None
        self._report()

    def resized(self) -> None:
        self._resized = True
        self.pause()

    def setFocused(self, focused: bool) -> None:
        if self._disposed or focused == self._focused:
            return
        self._focused = focused
        self.pause()
        self._schedule()

    def _can_present(self) -> bool:
        return bool(not self._disposed and not self._resized and not self._awaiting_epoch
                    and self.layout and self._state and self._state["enabled"] and self._state["dynamicRows"] > 0)

    def _has_work(self) -> bool:
        return self._can_present() and (self._needs_still or self.reason == "idle")

    def _schedule(self, delay: float = .25) -> None:
        if self._timer or not self._has_work():
            return
        def tick() -> None:
            self._timer = None
            task = asyncio.create_task(self.advance())
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
        self._timer = asyncio.get_running_loop().call_later(delay, tick)

    def update(self, state: Mapping[str, Any]) -> None:
        if self._disposed:
            return
        old, previous = self._state, self.reason
        self._state = dict(state)
        if state["epoch"] != self._active_epoch:
            self._active_epoch = state["epoch"]
            still_presented = bool(state.get("stillPresented"))
            self._needs_still, self._awaiting_epoch = not still_presented, False
            if still_presented:
                self._frames += 1
            self.pause()
        if old and any(old[key] != state[key] for key in ("dynamicRows", "extraStaticRows")):
            self.pause()
        columns, rows = self._dimensions()
        if self.layout:
            box = getWelcomeLayout(columns, self.layout, terminalRows=rows)
            if not box["sideBySide"] or state["dynamicRows"] + state["extraStaticRows"] + box["cardHeight"] >= rows:
                self._resized = True
        if self.reason != "idle":
            if previous == "idle":
                self.pause()
            else:
                self._stop()
                self._anchor = None
        self._report()
        self._schedule()

    async def advance(self) -> None:
        if self._advancing or not self._has_work() or not self.layout or not self._state:
            return
        self._advancing = True
        ticket, epoch = self._generation, self._state["epoch"]
        try:
            def valid() -> bool:
                return ticket == self._generation and self._has_work() and self._state is not None and epoch == self._state["epoch"]
            if self._anchor is None:
                before = dict(self._state)
                await self._flush()
                if not valid():
                    return
                cursor = await self.reports.cursor()
                if not valid():
                    return
                columns, rows = self._dimensions()
                require_top = bool(before.get("viewportStartsAtTop"))
                if cursor and (not require_top or cursor["column"] == 1):
                    self._anchor = imageAnchor(cursor["row"], before["dynamicRows"], before["extraStaticRows"],
                                               columns, rows, self.layout, fit_viewport=True, require_top=require_top)
                if self._anchor is None:
                    self._resized = True
                    self._report()
                    return
                self._step = self._frame = 0
                still = self._needs_still
                self._needs_still = False
            else:
                self._step = (self._step + 1) % len(MASCOT_TIMELINE)
                still = False
            target = MASCOT_TIMELINE[self._step]["frame"]
            if still or target != self._frame or self._frames == 0:
                anchor = self._anchor
                def fresh() -> bool:
                    return (ticket == self._generation and self._can_present() and self._state is not None
                            and epoch == self._state["epoch"] and (still or self.reason == "idle"))
                text = _frame_at(anchor["row"], anchor["column"], target)
                if await self._write(text, fresh):
                    self._frame = target
                    self._frames += 1
                    self._report()
                if not valid():
                    return
            if self.reason == "idle":
                self._schedule(MASCOT_TIMELINE[self._step]["duration"] / 1000)
        except Exception:
            self.layout = None
            self._resized = True
            self._report()  # 图形路径失败时继续保留已经显示的文本卡片。
        finally:
            self._advancing = False
            if self._has_work() and self._timer is None:
                self._schedule(.05)

    async def reset(self) -> WelcomeMascotLayout | None:
        self._reset_sequence += 1
        ticket = self._reset_sequence
        self._resized = self._awaiting_epoch = True
        self.pause()
        cell = await self.reports.probe()
        if self._disposed or ticket != self._reset_sequence:
            return None
        self.layout = self._layout(cell)
        self._resized = False
        self._needs_still = True
        self._step = self._frame = 0
        return self.layout

    def still_at_viewport_top(self, columns: int, rows: int) -> str | None:
        if self._disposed or self.layout is None:
            return None
        box = getWelcomeLayout(columns, self.layout, terminalRows=rows)
        if not box["sideBySide"]:
            return None
        return _frame_at(box["imageTop"] + 1, box["imageLeft"] + 1, MASCOT_TIMELINE[0]["frame"])

    async def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        self.pause()
        if self._tasks:
            await asyncio.gather(*tuple(self._tasks), return_exceptions=True)


def createWelcomeMotion(**options: Any) -> WelcomeMotion:
    return WelcomeMotion(**options)
