"""在现有受管进程树上按批交付 Monitor 的输出行，沿用受管执行的控制和回收路径。"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from time import monotonic
from typing import Literal

from ..platform.process_tree import run_foreground_plan
from ..platform.sandbox import sandboxExecutionPlan
from ..platform.shell_plan import ShellExecutionPlan


async def runMonitor(plan: ShellExecutionPlan, description: str, signal: threading.Event, *,
                     timeout_ms: int | None, emit: Callable[[str], Awaitable[None]]) -> str:
    plan = sandboxExecutionPlan(plan)
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[str] = asyncio.Queue()

    def output(stream: Literal["stdout", "stderr"], text: str) -> None:
        if stream == "stdout" and text:
            loop.call_soon_threadsafe(queue.put_nowait, text)

    execution = asyncio.create_task(asyncio.to_thread(run_foreground_plan, plan, signal, onLogOutput=output))
    end = monotonic() + timeout_ms / 1000 if timeout_ms is not None else None
    timed_out, partial = False, ""
    lines: list[str] = []
    deadline: float | None = None
    try:
        while not execution.done() or not queue.empty():
            now = monotonic()
            if end is not None and now >= end and not signal.is_set():
                timed_out = True
                signal.set()
            try:
                chunk = await asyncio.wait_for(queue.get(), .1)
            except TimeoutError:
                chunk = ""
            if chunk:
                pieces = (partial + chunk).split("\n")
                partial = pieces.pop()
                lines.extend(line.removesuffix("\r") for line in pieces if line.removesuffix("\r"))
                if lines and deadline is None:
                    deadline = monotonic() + .2
            if lines and deadline is not None and monotonic() >= deadline:
                await emit("\n".join(lines))
                lines, deadline = [], None
        result = await execution
        if partial.strip():
            lines.append(partial)
        if lines:
            await emit("\n".join(lines))
        if timed_out:
            return f"监控超时({timeout_ms}ms)已自动终止:{description}"
        if result.aborted:
            return f"监控已被取消:{description}"
        return f"监控结束(命令已退出,exit {result.code}):{description}"
    finally:
        if not execution.done():
            signal.set()
        await asyncio.shield(execution)
