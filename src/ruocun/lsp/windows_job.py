"""LSP duplex-process binding to the existing Windows Job tree contract."""

from __future__ import annotations

import ctypes as C
import importlib
import time
from ctypes import wintypes as W
from typing import Any

from ..platform.windows.process_tree import _Accounting, _check, _Extended, _kernel


class _ThreadEntry(C.Structure):
    _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("tid", W.DWORD), ("pid", W.DWORD),
                ("priority", W.LONG), ("delta", W.LONG), ("flags", W.DWORD)]


class WindowsJob:
    def __init__(self, process: Any) -> None:
        self.kernel = k = _kernel()
        self.native = importlib.import_module("_winapi")
        self.handle = _check(k.CreateJobObjectW(None, None))
        try:
            limits = _Extended()
            limits.basic.flags = 0x2000
            _check(k.SetInformationJobObject(self.handle, 9, C.byref(limits), C.sizeof(limits)))
            # CPython 3.11 exposes the same owned Popen via SubprocessTransport extras.
            popen = process._transport.get_extra_info("subprocess")
            _check(k.AssignProcessToJobObject(self.handle, int(popen._handle)))
            self._resume_initial_thread(process.pid)
        except BaseException:
            k.TerminateJobObject(self.handle, 1)
            k.CloseHandle(self.handle)
            self.handle = None
            raise

    def _resume_initial_thread(self, pid: int) -> None:
        k = self.kernel
        k.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]
        k.CreateToolhelp32Snapshot.restype = W.HANDLE
        k.Thread32First.argtypes = [W.HANDLE, C.POINTER(_ThreadEntry)]
        k.Thread32Next.argtypes = [W.HANDLE, C.POINTER(_ThreadEntry)]
        k.OpenThread.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        k.OpenThread.restype = W.HANDLE
        snapshot = k.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == C.c_void_p(-1).value:
            raise C.WinError(C.get_last_error())
        try:
            entry = _ThreadEntry()
            entry.size = C.sizeof(entry)
            available = k.Thread32First(snapshot, C.byref(entry))
            tids = []
            while available:
                if entry.pid == pid:
                    tids.append(entry.tid)
                available = k.Thread32Next(snapshot, C.byref(entry))
            if len(tids) != 1:
                raise RuntimeError("LSP suspended进程的初始线程无法唯一核实。")
            thread = _check(k.OpenThread(2, False, tids[0]))  # THREAD_SUSPEND_RESUME
            try:
                if k.ResumeThread(thread) != 1:
                    raise RuntimeError("LSP初始线程恢复状态无法核实。")
            finally:
                k.CloseHandle(thread)
        finally:
            k.CloseHandle(snapshot)

    def close(self) -> None:
        if self.handle is None:
            return
        k, native = self.kernel, self.native
        handles = []
        try:
            capacity = 64
            while True:
                class ProcessIds(C.Structure):
                    _fields_ = [("assigned", W.DWORD), ("count", W.DWORD), ("ids", C.c_size_t * capacity)]
                members = ProcessIds()
                if k.QueryInformationJobObject(self.handle, 3, C.byref(members), C.sizeof(members), None):
                    break
                if C.get_last_error() != 234:
                    raise C.WinError(C.get_last_error())
                capacity = max(capacity * 2, int(members.assigned))
            for pid in list(members.ids)[:members.count]:
                handle = k.OpenProcess(0x100000, False, pid)
                if handle:
                    handles.append(handle)
                elif C.get_last_error() != 87:
                    raise C.WinError(C.get_last_error())
            accounting = _Accounting()
            _check(k.QueryInformationJobObject(self.handle, 1, C.byref(accounting), C.sizeof(accounting), None))
            if accounting.active:
                _check(k.TerminateJobObject(self.handle, 1))
            deadline = time.monotonic() + 10
            while True:
                _check(k.QueryInformationJobObject(self.handle, 1, C.byref(accounting), C.sizeof(accounting), None))
                if not accounting.active:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("LSP owned Job进程树退出未确认。")
                time.sleep(.01)
            for handle in handles:
                if native.WaitForSingleObject(handle, max(1, int((deadline - time.monotonic()) * 1000))) != native.WAIT_OBJECT_0:
                    raise RuntimeError("LSP子进程句柄退出未确认。")
        finally:
            for handle in handles:
                k.CloseHandle(handle)
            k.CloseHandle(self.handle)
            self.handle = None
