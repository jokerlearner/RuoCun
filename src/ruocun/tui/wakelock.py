"""Frozen tui/wakelock.ts (MIT); W5 leaves Windows power policy to the user."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import Protocol

from ..config.compat import resolve_env

WINDOWS_POWER_NOTE = "Windows 本轮无防自动休眠保证；程序不申请系统电源锁，请由用户管理系统电源设置。"


class WakeProcess(Protocol):
    pid: int
    def poll(self) -> int | None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def wait(self, timeout: float | None = None) -> int: ...


class WakeSpawn(Protocol):
    def __call__(self, argv: Sequence[str], *, env: Mapping[str, str]) -> WakeProcess: ...


def _spawn(argv: Sequence[str], *, env: Mapping[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(argv, env=dict(env), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=os.name != "nt",
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)


def getWakeLockCapability(*, platform: str | None = None) -> dict[str, str | bool]:
    current = platform or sys.platform
    return {"platform": current, "supported": current in {"darwin", "linux"}, "guaranteed": False,
            "reason": WINDOWS_POWER_NOTE if current == "win32" else "可选电源后端仅best-effort；缺失或失败时无防休眠保证。"}


class WakeLock:
    def __init__(self, status: str, process: WakeProcess | None = None, *, group_owned: bool = False,
                 platform: str | None = None) -> None:
        self._initial = status
        self._process = process
        self._released = False
        self._close_failed = False
        self._group_owned = group_owned
        self._platform = platform or sys.platform

    @property
    def status(self) -> str:
        if self._close_failed:
            return "unconfirmed"
        if self._process is None:
            return self._initial
        if self._released:
            return "released"
        return "requested" if self._process.poll() is None else "unavailable"

    @property
    def reason(self) -> str:
        return {"unsupported": WINDOWS_POWER_NOTE if self._platform == "win32" else "当前平台无可用防休眠路由。",
                "disabled": "NO_WAKELOCK=1 已关闭可选电源请求，无防休眠保证。",
                "unavailable": "可选电源后端未运行，无防休眠保证。",
                "requested": "已请求可选电源进程，不承诺系统实际持锁。",
                "released": "可选电源进程已结束。", "unconfirmed": "可选电源进程退出未确认，请核对现场。"}[self.status]

    def __call__(self) -> None:
        self.release()

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        process = self._process
        if process is None:
            return
        try:
            if process.poll() is None:
                if self._group_owned:
                    getattr(os, "killpg")(process.pid, signal.SIGTERM)
                else:
                    process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if self._group_owned:
                    getattr(os, "killpg")(process.pid, getattr(signal, "SIGKILL"))
                else:
                    process.kill()
                process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            self._close_failed = process.poll() is None


def acquireWakeLock(*, environ: Mapping[str, str] | None = None, platform: str | None = None,
                    spawn: WakeSpawn | None = None) -> WakeLock:
    environment = dict(os.environ if environ is None else environ)
    current = platform or sys.platform
    if resolve_env("NO_WAKELOCK", environment) == "1":
        return WakeLock("disabled", platform=current)
    argv: tuple[str, ...]
    if current == "darwin":
        argv = ("caffeinate", "-i")
    elif current == "linux":
        argv = ("systemd-inhibit", "--what=idle:sleep", "--why=ruocun 长任务", "--mode=block", "sleep", "infinity")
    else:
        return WakeLock("unsupported", platform=current)
    try:
        return WakeLock("requested", (spawn or _spawn)(argv, env=environment), group_owned=spawn is None and os.name != "nt")
    except OSError:
        return WakeLock("unavailable")
