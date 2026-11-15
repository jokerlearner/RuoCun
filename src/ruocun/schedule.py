"""管理会话外的系统定时任务，供命令行和定时工具共用。

入口先检查平台能力，再读写本操作系统的调度配置。会话内的 /loop 由会话运行时负责。
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
import signal as signals
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from .tools.tool_batch import UnknownToolOutcome
from .tools.types import ToolRejected

MARK = "# ruocun-schedule"
WINDOWS_UNSUPPORTED = "Windows 本轮不支持系统级定时任务；未创建、查询或删除系统任务。会话内 /loop 不等于系统定时。"


def _quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def buildCronLine(cron: str, prompt: str, cwd: str, ruocunBin: str, *, launcherArgs: Sequence[str] = ()) -> str:
    launcher = " ".join(_quote(item) for item in (ruocunBin, *launcherArgs))
    return f'{cron.strip()} cd {_quote(cwd)} && {launcher} {_quote(prompt)} >> "$HOME/.ruocun/schedule.log" 2>&1 {MARK}'


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str = ""


class ScheduleRunner(Protocol):
    async def __call__(self, argv: tuple[str, ...], stdin: str | None, *,
                       environ: Mapping[str, str] | None, signal: threading.Event | None) -> CommandResult: ...


async def runScheduleCommand(argv: tuple[str, ...], stdin: str | None, *,
                             environ: Mapping[str, str] | None, signal: threading.Event | None) -> CommandResult:
    if signal is not None and signal.is_set():
        raise ToolRejected("系统定时操作已取消，未执行。")
    try:
        process = await asyncio.create_subprocess_exec(*argv,
            stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env=None if environ is None else dict(environ), start_new_session=os.name != "nt")
    except OSError as error:
        raise ToolRejected(f"crontab 无法启动（{type(error).__name__}），未写入。") from error
    work = asyncio.create_task(process.communicate(None if stdin is None else stdin.encode("utf-8")))
    try:
        while not work.done():
            if signal is not None and signal.is_set():
                raise InterruptedError("系统定时操作已取消。")
            await asyncio.wait({work}, timeout=.05)
        out, err = work.result()
        return CommandResult(process.returncode or 0, out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace"))
    except (InterruptedError, asyncio.CancelledError) as error:
        if stdin is not None:
            raise UnknownToolOutcome("crontab 写入结果未确认，原现场保留，未自动重放。") from error
        raise ToolRejected("crontab 查询已取消，未写入。") from error
    finally:
        if not work.done():
            if process.returncode is None:
                with contextlib.suppress(ProcessLookupError):
                    if os.name != "nt":
                        getattr(os, "killpg")(process.pid, signals.SIGTERM)
                    else:
                        process.terminate()
                try:
                    await asyncio.wait_for(asyncio.shield(work), 1)
                except TimeoutError:
                    with contextlib.suppress(ProcessLookupError):
                        if os.name != "nt":
                            getattr(os, "killpg")(process.pid, getattr(signals, "SIGKILL"))
                        else:
                            process.kill()
            await work


def _supported(platform: str | None, write: Callable[[str], None]) -> bool:
    if (platform or sys.platform) == "win32":
        write("Error: " + WINDOWS_UNSUPPORTED + "\n")
        return False
    return True


async def _read(runner: ScheduleRunner | None, environ: Mapping[str, str] | None,
                signal: threading.Event | None) -> list[str]:
    result = await (runner or runScheduleCommand)(("crontab", "-l"), None, environ=environ, signal=signal)
    if result.returncode != 0:
        if result.returncode == 1 and re.search(r"\bno crontab for\b", result.stderr, re.I):
            return []
        raise ToolRejected(f"crontab 读取失败（退出码{result.returncode}），原任务保留，未写入。")
    return [line for line in result.stdout.split("\n") if line]


async def _write(lines: list[str], runner: ScheduleRunner | None, environ: Mapping[str, str] | None,
                 signal: threading.Event | None) -> None:
    result = await (runner or runScheduleCommand)(("crontab", "-"), "\n".join(lines) + "\n", environ=environ, signal=signal)
    if result.returncode != 0:
        raise UnknownToolOutcome(f"crontab 写入未获成功确认（退出码{result.returncode}），保留现场，不自动重放。")


async def scheduleAdd(cron: str, prompt: str, cwd: str, ruocunBin: str, write: Callable[[str], None], *,
                      launcherArgs: Sequence[str] = (), platform: str | None = None, runner: ScheduleRunner | None = None,
                      environ: Mapping[str, str] | None = None, signal: threading.Event | None = None) -> bool:
    if not _supported(platform, write):
        return False
    if not re.match(r"^(\S+\s+){4}\S+", cron.strip()):
        write(f'cron 表达式应为 5 字段(分 时 日 月 周),如 "0 9 * * *"。收到:{cron}\n')
        return False
    lines = await _read(runner, environ, signal)
    lines.append(buildCronLine(cron, prompt, cwd, ruocunBin, launcherArgs=launcherArgs))
    await _write(lines, runner, environ, signal)
    write(f'✓ 已添加定时任务:[{cron.strip()}] 在 {cwd} 跑 ruocun "{prompt}"\n'
          '  输出 → ~/.ruocun/schedule.log;查看 /用 ruocun schedule list,删 ruocun schedule remove <n>\n')
    return True


async def scheduleList(write: Callable[[str], None], *, platform: str | None = None,
                       runner: ScheduleRunner | None = None, environ: Mapping[str, str] | None = None,
                       signal: threading.Event | None = None) -> bool:
    if not _supported(platform, write):
        return False
    own = [line for line in await _read(runner, environ, signal) if MARK in line]
    if not own:
        write("(暂无 ruocun 定时任务)\n")
    else:
        write("ruocun 定时任务:\n" + "\n".join(f"  {i + 1}. {line.replace(MARK, '', 1).strip()}" for i, line in enumerate(own)) + "\n")
    return True


async def scheduleRemove(n: int, write: Callable[[str], None], *, platform: str | None = None,
                         runner: ScheduleRunner | None = None, environ: Mapping[str, str] | None = None,
                         signal: threading.Event | None = None) -> bool:
    if not _supported(platform, write):
        return False
    lines = await _read(runner, environ, signal)
    indexes = [i for i, line in enumerate(lines) if MARK in line]
    if n < 1 or n > len(indexes):
        write(f"序号越界(共 {len(indexes)} 条)。先 ruocun schedule list 看序号。\n")
        return False
    await _write([line for i, line in enumerate(lines) if i != indexes[n - 1]], runner, environ, signal)
    write(f"✓ 已删除第 {n} 条定时任务。\n")
    return True


@dataclass(frozen=True)
class ScheduleService:
    """为命令行和定时工具提供共用的调度接口。"""
    platform: str | None = None
    runner: ScheduleRunner | None = None
    environ: Mapping[str, str] | None = None
    executable: str | None = None
    launcherArgs: tuple[str, ...] = ("-m", "ruocun")

    async def add(self, cron: str, prompt: str, cwd: str, write: Callable[[str], None],
                  signal: threading.Event | None = None) -> bool:
        return await scheduleAdd(cron, prompt, cwd, self.executable or sys.executable, write,
            launcherArgs=self.launcherArgs, platform=self.platform, runner=self.runner, environ=self.environ, signal=signal)

    async def list(self, write: Callable[[str], None], signal: threading.Event | None = None) -> bool:
        return await scheduleList(write, platform=self.platform, runner=self.runner, environ=self.environ, signal=signal)

    async def remove(self, index: int, write: Callable[[str], None], signal: threading.Event | None = None) -> bool:
        return await scheduleRemove(index, write, platform=self.platform, runner=self.runner, environ=self.environ, signal=signal)
