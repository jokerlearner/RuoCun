"""进程身份与 owner 存活判定（MM-597 / REC-09）。

冻结来源：``src/session/process_identity.ts`` 与 ``process_identity.test.ts``。
语义（不由 Python 实现倒推）：
- ``ProcessIdentity(host, boot, pid, start)``；start 用进程创建时间，抵御 PID 重用。
- 不同 host 明确抛错，不自动接管；boot 变化视为死 owner 可接管。
- 进程查询 ``EPERM`` / 权限错误必须原样抛出，**不冒充死亡**；
  kill(pid,0) 后进程退出（CIM 无匹配）才返回 None / False。
- 无效 PID（<=0 / 非整数 / >0x7fffffff）在查询 OS 之前拒绝。

Windows 的进程创建时间通过 kernel32 读取；系统启动身份沿用冻结来源的
PowerShell/CIM LastBootUpTime。两者均不读取真实用户会话；
``SyntheticIdentityProvider`` 供冻结测试风格的合成身份注入。
"""

from __future__ import annotations

import ctypes as _C
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from .contract import (
    CrossHostError,
    IdentityProvider,
    IdentityQueryError,
    ProcessIdentity,
)

_PID_MAX = 0x7FFFFFFF
_BOOT_CACHE: str | None = None


def hostname() -> str:
    return socket.gethostname()


def _filetime_to_text(value: Any) -> str:
    high = int(value.dwHighDateTime)
    low = int(value.dwLowDateTime)
    return str((high << 32) | low)


def current_boot() -> str:
    """从 Windows CIM 获取与冻结来源相同的可跨进程比较的启动时间。"""
    global _BOOT_CACHE
    if _BOOT_CACHE is not None:
        return _BOOT_CACHE
    if sys.platform != "win32":
        raise IdentityQueryError("当前平台无法核实系统启动身份（仅 Windows x64 已验证）。")
    powershell = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / (
        r"System32\WindowsPowerShell\v1.0\powershell.exe"
    )
    script = (
        "$ErrorActionPreference = 'Stop'; "
        "$value = (Get-CimInstance -ClassName Win32_OperatingSystem "
        "-Property LastBootUpTime).LastBootUpTime; "
        "if ($null -eq $value) { throw 'Missing boot time' }; "
        "[Console]::Write($value.ToUniversalTime().Ticks.ToString("
        "[Globalization.CultureInfo]::InvariantCulture))"
    )
    try:
        result = subprocess.run(
            [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise IdentityQueryError("无法核实 Windows 系统启动身份。") from exc
    value = result.stdout.strip()
    if not value.isascii() or not value.isdecimal():
        raise IdentityQueryError("Windows 系统启动身份无效。")
    _BOOT_CACHE = value
    return _BOOT_CACHE


def process_identity(pid: int | None = None) -> ProcessIdentity | None:
    """读取真实进程身份；进程不存在返回 None，查询错误抛 IdentityQueryError。"""
    target = os.getpid() if pid is None else pid
    if not isinstance(target, int) or isinstance(target, bool) or target <= 0 or target > _PID_MAX:
        raise IdentityQueryError("进程 ID 必须是正的 32 位整数。")
    if sys.platform != "win32":
        raise IdentityQueryError("当前平台无法核实后台进程身份（仅 Windows x64 已验证）。")
    from ctypes import wintypes as W

    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    kernel.OpenProcess.restype = W.HANDLE
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [_C.POINTER(W.FILETIME)] * 4
    kernel.GetProcessTimes.restype = W.BOOL
    kernel.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    kernel.WaitForSingleObject.restype = W.DWORD
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | 0x100000, False, target)
    if not handle:
        error = _C.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER：进程不存在
            return None
        raise IdentityQueryError(
            f"进程 {target} 身份查询失败（Win32 error {error}）；不冒充进程已死亡。"
        )
    try:
        state = kernel.WaitForSingleObject(handle, 0)
        if state == 0:  # A retained process object can outlive its process.
            return None
        if state != 258:
            raise IdentityQueryError("无法核实进程退出状态；不冒充进程已死亡。")
        creation, exit_time, kernel_time, user_time = (
            W.FILETIME(), W.FILETIME(), W.FILETIME(), W.FILETIME()
        )
        if not kernel.GetProcessTimes(
            handle, _C.byref(creation), _C.byref(exit_time),
            _C.byref(kernel_time), _C.byref(user_time),
        ):
            error = _C.get_last_error()
            raise IdentityQueryError(
                f"进程 {target} 创建时间查询失败（Win32 error {error}）；不冒充进程已死亡。"
            )
        start = _filetime_to_text(creation)
    finally:
        kernel.CloseHandle(handle)
    if not start or start == "0":
        raise IdentityQueryError(f"无法核实进程 {target} 的启动身份。")
    return ProcessIdentity(host=hostname(), boot=current_boot(), pid=target, start=start)


def identity_alive(identity: ProcessIdentity) -> bool:
    """owner 是否存活；跨 host 抛错，查询错误传播，PID 重用不误认。"""
    if identity.host != hostname():
        raise CrossHostError("会话来自另一台机器，不能自动接管。")
    if identity.boot != current_boot():
        return False
    now = process_identity(identity.pid)
    return now is not None and now.start == identity.start


class RealIdentityProvider:
    """真实进程身份提供方（demo 默认；owned child 的真实 PID/创建时间绑定）。"""

    def current(self) -> ProcessIdentity:
        identity = process_identity()
        if identity is None:
            raise IdentityQueryError("当前进程身份不可用。")
        return identity

    def alive(self, identity: ProcessIdentity) -> bool:
        return identity_alive(identity)


class SyntheticIdentityProvider:
    """冻结 durable_store.test.ts 风格的合成身份注入。

    ``alive_map`` 以 ``(boot, pid, start)`` 为键；缺省视为死亡。
    ``alive_query_error=True`` 模拟身份查询失败（必须抛错，不返回 False）。
    """

    def __init__(
        self,
        identity: ProcessIdentity,
        alive_map: dict[tuple[str, int, str], bool] | None = None,
        alive_query_error: bool = False,
    ) -> None:
        self._identity = identity
        self._alive_map = alive_map or {}
        self._alive_query_error = alive_query_error

    def current(self) -> ProcessIdentity:
        return self._identity

    def alive(self, identity: ProcessIdentity) -> bool:
        if self._alive_query_error:
            raise IdentityQueryError("合成身份查询失败；不冒充 owner 已死亡。")
        if identity.host != self._identity.host:
            raise CrossHostError("会话来自另一台机器，不能自动接管。")
        if identity.boot != self._identity.boot:
            return False
        return bool(self._alive_map.get((identity.boot, identity.pid, identity.start), False))


__all__ = [
    "hostname",
    "current_boot",
    "process_identity",
    "identity_alive",
    "RealIdentityProvider",
    "SyntheticIdentityProvider",
    "IdentityProvider",
]
