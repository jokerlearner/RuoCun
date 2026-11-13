"""D10 NEW-07只读剪贴板窄端口。没有EmptyClipboard/SetClipboardData路径。

原生读取只在用户显式附图动作触发；独立base-Python进程受5秒监督，
传回内存结果，不将用户剪贴板写入临时文件/日志。
"""

from __future__ import annotations

import base64
import ctypes
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MAX_BYTES = 5 * 1024 * 1024
MAX_FILES = 64


@dataclass(frozen=True)
class ClipboardPayload:
    kind: str
    data: bytes = field(default=b"", repr=False)
    paths: tuple[str, ...] = field(default=(), repr=False)
    error: str = ""


def _read_native() -> ClipboardPayload:
    if sys.platform != "win32":
        return ClipboardPayload("unavailable", error="unsupported")
    from ctypes import wintypes as W
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    user.OpenClipboard.argtypes, user.OpenClipboard.restype = [W.HWND], W.BOOL
    user.CloseClipboard.argtypes, user.CloseClipboard.restype = [], W.BOOL
    user.RegisterClipboardFormatW.argtypes, user.RegisterClipboardFormatW.restype = [W.LPCWSTR], W.UINT
    user.IsClipboardFormatAvailable.argtypes, user.IsClipboardFormatAvailable.restype = [W.UINT], W.BOOL
    user.GetClipboardData.argtypes, user.GetClipboardData.restype = [W.UINT], W.HANDLE
    kernel.GlobalSize.argtypes, kernel.GlobalSize.restype = [W.HANDLE], ctypes.c_size_t
    kernel.GlobalLock.argtypes, kernel.GlobalLock.restype = [W.HANDLE], ctypes.c_void_p
    kernel.GlobalUnlock.argtypes, kernel.GlobalUnlock.restype = [W.HANDLE], W.BOOL
    shell.DragQueryFileW.argtypes, shell.DragQueryFileW.restype = [W.HANDLE, W.UINT, W.LPWSTR, W.UINT], W.UINT
    if not user.OpenClipboard(None):
        return ClipboardPayload("unavailable", error="busy")
    result = ClipboardPayload("none")
    try:
        png = user.RegisterClipboardFormatW("PNG")
        for format_id, kind in ((png, "png"), (17, "dibv5"), (8, "dib"), (15, "files")):
            if not format_id or not user.IsClipboardFormatAvailable(format_id):
                continue
            handle = user.GetClipboardData(format_id)
            if not handle:
                return ClipboardPayload("unavailable", error="read-failed")
            size = kernel.GlobalSize(handle)
            if not size or size > MAX_BYTES:
                return ClipboardPayload("unavailable", error="oversize")
            if kind == "files":
                count = shell.DragQueryFileW(handle, 0xFFFFFFFF, None, 0)
                if count > MAX_FILES:
                    return ClipboardPayload("unavailable", error="too-many-files")
                paths = []
                for index in range(count):
                    length = shell.DragQueryFileW(handle, index, None, 0)
                    if length <= 0 or length > 32767:
                        return ClipboardPayload("unavailable", error="invalid")
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    copied = shell.DragQueryFileW(handle, index, buffer, length + 1)
                    if copied != length:
                        return ClipboardPayload("unavailable", error="invalid")
                    paths.append(buffer.value)
                result = ClipboardPayload(kind, paths=tuple(paths))
            else:
                pointer = kernel.GlobalLock(handle)
                if not pointer:
                    return ClipboardPayload("unavailable", error="read-failed")
                try:
                    result = ClipboardPayload(kind, ctypes.string_at(pointer, size))
                finally:
                    ctypes.set_last_error(0)
                    if not kernel.GlobalUnlock(handle) and ctypes.get_last_error():
                        result = ClipboardPayload("unavailable", error="unlock-failed")
            break
    finally:
        # GetClipboardData是系统所有权；不GlobalFree、DeleteObject或关闭该handle。
        if not user.CloseClipboard():
            result = ClipboardPayload("unavailable", error="close-failed")
    return result


class WindowsClipboard:
    def read(self) -> ClipboardPayload:
        if sys.platform != "win32":
            return ClipboardPayload("unavailable", error="unsupported")
        executable = getattr(sys, "_base_executable", None) or sys.executable
        environment = {"SYSTEMROOT": "C:\\Windows", "WINDIR": "C:\\Windows",
                       "PATH": "C:\\Windows\\System32", "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1"}
        try:
            # base解释器直接运行自包含stdlib文件，不经过venv转发shim或shell。
            result = subprocess.run([executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--read"],
                                    env=environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=5)
            if result.returncode or len(result.stdout) > MAX_BYTES * 2 + 65536:
                return ClipboardPayload("unavailable", error="helper-failed")
            value = json.loads(result.stdout)
            data = base64.b64decode(value.get("data", ""), validate=True)
            paths = value.get("paths", [])
            if len(data) > MAX_BYTES or not isinstance(paths, list) or len(paths) > MAX_FILES or not all(isinstance(path, str) for path in paths):
                return ClipboardPayload("unavailable", error="invalid")
            return ClipboardPayload(str(value["kind"]), data, tuple(paths), str(value.get("error", "")))
        except subprocess.TimeoutExpired:
            return ClipboardPayload("unavailable", error="timeout")
        except (OSError, ValueError, KeyError, TypeError):
            return ClipboardPayload("unavailable", error="helper-failed")


def _main() -> int:
    try:
        payload = _read_native()
    except BaseException:
        payload = ClipboardPayload("unavailable", error="native-failed")
    encoded = {"kind": payload.kind, "data": base64.b64encode(payload.data).decode("ascii"),
               "paths": payload.paths, "error": payload.error}
    sys.stdout.write(json.dumps(encoded, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main() if sys.argv[1:] == ["--read"] else 2)
