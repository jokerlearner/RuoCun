"""前台 Windows Job：先挂入再恢复，回收整个树后才返回。

窄实现沿 D17/IPC 已验证的 CREATE_SUSPENDED + KILL_ON_JOB_CLOSE 路线。
不提供持久 runner、接管、后台或进程逃逸支持。
"""

from __future__ import annotations

import ctypes as C
import importlib
import os
import subprocess
import threading
import time
from collections.abc import Callable
from ctypes import wintypes as W
from typing import Any, BinaryIO


class _Limits(C.Structure):
    _fields_ = [
        ("process_time", C.c_longlong), ("job_time", C.c_longlong),
        ("flags", W.DWORD), ("min_ws", C.c_size_t), ("max_ws", C.c_size_t),
        ("active", W.DWORD), ("affinity", C.c_size_t),
        ("priority", W.DWORD), ("scheduling", W.DWORD),
    ]


class _IO(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in (
        "read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes"
    )]


class _Extended(C.Structure):
    _fields_ = [
        ("basic", _Limits), ("io", _IO), ("process_memory", C.c_size_t),
        ("job_memory", C.c_size_t), ("peak_process", C.c_size_t), ("peak_job", C.c_size_t),
    ]


class _Accounting(C.Structure):
    _fields_ = [(name, C.c_longlong) for name in (
        "user", "kernel", "period_user", "period_kernel"
    )] + [(name, W.DWORD) for name in ("faults", "total", "active", "terminated")]


def _kernel() -> Any:
    k = C.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.argtypes = [C.c_void_p, W.LPCWSTR]
    k.CreateJobObjectW.restype = W.HANDLE
    k.SetInformationJobObject.argtypes = [W.HANDLE, C.c_int, C.c_void_p, W.DWORD]
    k.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    k.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
    k.QueryInformationJobObject.argtypes = [
        W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p
    ]
    k.ResumeThread.argtypes = [W.HANDLE]
    k.ResumeThread.restype = W.DWORD
    k.CloseHandle.argtypes = [W.HANDLE]
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    return k


def _check(value: Any) -> Any:
    if not value:
        raise C.WinError(C.get_last_error())
    return value


def run_managed(
    argv: list[str], cwd: str, env: dict[str, str], signal: threading.Event, cap: int,
    *, commandLine: str | None = None, onChunk: Callable[[int, bytes], None] | None = None,
    captureOutput: bool = True, stdinData: bytes | None = None, perStreamLimit: bool = False,
) -> tuple[bytes, bytes, int, bool, bool]:
    """返回 stdout/stderr/code/aborted/capped；异常不冒充已取消。"""
    import msvcrt

    from ..process_tree import _write_process_input

    native = importlib.import_module("_winapi")
    k = _kernel()
    job = _check(k.CreateJobObjectW(None, None))
    process: Any = None
    pipes: list[int] = []
    readers: list[threading.Thread] = []
    output = [bytearray(), bytearray()]
    lock = threading.Lock()
    capped = threading.Event()
    read_errors: list[BaseException] = []

    def active() -> int:
        info = _Accounting()
        _check(k.QueryInformationJobObject(job, 1, C.byref(info), C.sizeof(info), None))
        return int(info.active)

    def stop_tree() -> None:
        # ActiveProcesses归零与各进程对象signaled并非同一个观察点；
        # 先绑定当前Job成员的句柄，再终止并等句柄，避免仅凭计数宣称退出。
        handles: list[Any] = []
        capacity = 64
        try:
            while True:
                class ProcessIds(C.Structure):
                    _fields_ = [("assigned", W.DWORD), ("count", W.DWORD),
                                ("ids", C.c_size_t * capacity)]

                ids = ProcessIds()
                if k.QueryInformationJobObject(job, 3, C.byref(ids), C.sizeof(ids), None):
                    break
                if C.get_last_error() != 234:  # ERROR_MORE_DATA
                    raise C.WinError(C.get_last_error())
                capacity = max(capacity * 2, int(ids.assigned))
            for pid in list(ids.ids)[:ids.count]:
                handle = k.OpenProcess(0x100000, False, int(pid))  # SYNCHRONIZE
                if handle:
                    handles.append(handle)
                elif C.get_last_error() != 87:  # 已不存在不需要等待
                    raise C.WinError(C.get_last_error())
            if active():
                _check(k.TerminateJobObject(job, 1))
            deadline = time.monotonic() + 10
            while active():
                if time.monotonic() >= deadline:
                    raise RuntimeError("Shell进程树退出未确认，不能报告已取消。")
                time.sleep(.01)
            for handle in handles:
                if native.WaitForSingleObject(handle, 10000) != native.WAIT_OBJECT_0:
                    raise RuntimeError("Shell子孙进程退出未确认，不能报告已取消。")
        finally:
            for handle in handles:
                k.CloseHandle(handle)

    def drain(fd: int, index: int) -> None:
        try:
            with os.fdopen(fd, "rb", buffering=0) as stream:
                while chunk := stream.read(65536):
                    with lock:
                        used = len(output[index]) if perStreamLimit else len(output[0]) + len(output[1])
                        remaining = cap - used if captureOutput else len(chunk)
                        if captureOutput:
                            output[index].extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            capped.set()
                    if onChunk is not None and chunk[:remaining]:
                        onChunk(index, chunk[:remaining])
        except BaseException as error:
            read_errors.append(error)

    try:
        limits = _Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        _check(k.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)))
        startup = subprocess.STARTUPINFO()
        startup.dwFlags = subprocess.STARTF_USESHOWWINDOW | subprocess.STARTF_USESTDHANDLES
        startup.wShowWindow = subprocess.SW_HIDE
        for _ in range(2):
            pipes.extend(os.pipe())
        input_fd = None
        stdin: BinaryIO
        if stdinData is None:
            stdin = open(os.devnull, "rb")
        else:
            read_fd, input_fd = os.pipe()
            pipes.append(input_fd)
            stdin = os.fdopen(read_fd, "rb", buffering=0)
        with stdin:
            handles = [msvcrt.get_osfhandle(fd) for fd in (stdin.fileno(), pipes[1], pipes[3])]
            for handle in handles:
                os.set_handle_inheritable(handle, True)
            startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
            startup.lpAttributeList = {"handle_list": handles}
            thread: Any = None
            try:
                process, thread, _, _ = native.CreateProcess(
                    argv[0], commandLine if commandLine is not None else subprocess.list2cmdline(argv), None, None, True,
                    0x4 | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
                    env, cwd, startup,
                )
                try:
                    _check(k.AssignProcessToJobObject(job, process))
                    if k.ResumeThread(thread) == 0xFFFFFFFF:
                        raise C.WinError(C.get_last_error())
                except BaseException:
                    native.TerminateProcess(process, 1)
                    native.WaitForSingleObject(process, 10000)
                    raise
            finally:
                if thread is not None:
                    native.CloseHandle(thread)
                for handle in handles:
                    os.set_handle_inheritable(handle, False)
        for index in (3, 1):
            os.close(pipes[index])
        read_fds = [pipes[0], pipes[2]]
        pipes[:] = [input_fd] if input_fd is not None else []
        for index, fd in enumerate(read_fds):
            reader = threading.Thread(target=drain, args=(fd, index), daemon=True)
            reader.start()
            readers.append(reader)
        if input_fd is not None:
            writer = threading.Thread(target=_write_process_input,
                                      args=(os.fdopen(input_fd, "wb", buffering=0), stdinData, read_errors), daemon=True)
            pipes.remove(input_fd)
            writer.start()
            readers.append(writer)
        aborted = False
        while native.WaitForSingleObject(process, 20) != native.WAIT_OBJECT_0:
            if signal.is_set() or capped.is_set() or read_errors:
                aborted = signal.is_set()
                stop_tree()
                break
        native.WaitForSingleObject(process, 10000)
        code = int(native.GetExitCodeProcess(process))
        # 首版没有后台语义；Shell已退出后留下的子孙也必须回收。
        stop_tree()
        native.WaitForSingleObject(process, 10000)
        for reader in readers:
            reader.join(10)
            if reader.is_alive():
                raise RuntimeError("Shell输出管道退出未确认。")
        if read_errors:
            raise RuntimeError("无法读取Shell输出。") from read_errors[0]
        return bytes(output[0]), bytes(output[1]), code, aborted, capped.is_set()
    finally:
        try:
            stop_tree()
        finally:
            k.CloseHandle(job)
            if process is not None:
                native.CloseHandle(process)
            for fd in pipes:
                try:
                    os.close(fd)
                except OSError:
                    pass
