"""Test-only Win32 boundary faults around a real pending ConnectNamedPipe.

This separate harness is not a product/probe runtime switch. It never claims an
injected return came from Windows. A safety anchor prevents the RED implementation
from actually freeing the live OVERLAPPED or closing its event during observation.
"""
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import os
import subprocess
import sys
import time
import uuid
import threading
from safe_env import child_env

import probe as p


class Boundary:
    def __init__(self, mode):
        self.native = p.K
        self.mode = mode
        self.overlap = None
        self.early_closes = []
        self.injected = []
        self.waits = []
        self.results = []
        self.actual_pending = False

    def __getattr__(self, name):
        return getattr(self.native, name)

    def ConnectNamedPipe(self, handle, pointer):
        self.overlap = pointer._obj  # RED-only safety anchor, not application ownership.
        ok = self.native.ConnectNamedPipe(handle, pointer)
        self.actual_pending = not ok and C.get_last_error() == 997
        return ok

    def ReadFile(self, handle, buffer, size, count, pointer):
        self.overlap = pointer._obj
        self.buffer_anchor = buffer
        ok = self.native.ReadFile(handle, buffer, size, count, pointer)
        self.actual_pending = not ok and C.get_last_error() == 997
        return ok

    def WriteFile(self, handle, buffer, size, count, pointer):
        self.overlap = pointer._obj
        self.buffer_anchor = buffer
        ok = self.native.WriteFile(handle, buffer, size, count, pointer)
        self.actual_pending = not ok and C.get_last_error() == 997
        return ok

    def CancelIoEx(self, handle, pointer):
        if self.mode.endswith("cancel-fail") or self.mode == "cancel-budget":
            error = 1168 if self.mode == "cancel-budget" else 5
            self.injected.append({"api": "CancelIoEx", "return": False, "winerror": error,
                                  "native_called": False, "boundary_injection": True})
            C.set_last_error(error)
            return False
        return self.native.CancelIoEx(handle, pointer)

    def WaitForSingleObject(self, event, milliseconds):
        first = not self.waits
        if first and self.mode in {"wait-fail", "wait-raise", "result-incomplete", "result-error"}:
            status = 0xffffffff if self.mode.startswith("wait-") else 0
            self.injected.append({"api": "WaitForSingleObject", "return": status, "winerror": 6,
                                  "native_called": False, "boundary_injection": True})
            self.waits.append({"milliseconds": milliseconds, "return": status, "native_called": False})
            if self.mode == "wait-raise":
                raise OSError("injected Win32 wait adapter exception")
            C.set_last_error(6)
            return status
        started = time.monotonic()
        status = self.native.WaitForSingleObject(event, milliseconds)
        self.waits.append({"milliseconds": milliseconds, "return": status, "native_called": True,
                           "elapsed": time.monotonic() - started})
        return status

    def GetOverlappedResult(self, handle, pointer, count, wait):
        if self.mode == "result-error":
            ok, error = False, 6
            self.injected.append({"api": "GetOverlappedResult", "return": False, "winerror": error,
                                  "native_called": False, "boundary_injection": True})
        else:
            ok = self.native.GetOverlappedResult(handle, pointer, count, wait)
            error = C.get_last_error() if not ok else 0
        self.results.append({"success": bool(ok), "winerror": error, "native_status": pointer._obj.internal,
                             "native_called": self.mode != "result-error"})
        C.set_last_error(error)
        return ok

    def CloseHandle(self, handle):
        if self.actual_pending and handle == self.overlap.event and self.overlap.internal == 0x103:
            self.early_closes.append({"event": int(handle), "native_status": 0x103,
                                      "suppressed_by_test_safety_anchor": True})
            return True
        return self.native.CloseHandle(handle)


def worker(mode, root):
    boundary = Boundary(mode)
    p.K = boundary
    name = "\\\\.\\pipe\\ruocun-d18-fault-" + uuid.uuid4().hex
    handle = p.new_pipe(name)
    p.dump(root / "ready.json", {"pid": os.getpid(), "creation_time": p.creation_time(p.K.GetCurrentProcess()),
                                 "pipe_name": name})
    error = None
    closer = None
    try:
        if mode in {"broken-read", "read-cancel-fail", "write-cancel-fail"}:
            client = p.opened(name, 0x12019b, flags=0x40000000)
            p.pipe_io(handle, "connect", 0, time.monotonic() + .5)
            if mode == "broken-read":
                def disconnect():
                    time.sleep(.05)
                    boundary.native.CloseHandle(client)
                closer = threading.Thread(target=disconnect)
                closer.start()
            p.pipe_io(handle, "write" if mode.startswith("write-") else "read",
                      b"x" * 1048576 if mode.startswith("write-") else 16, time.monotonic() + .1)
        else:
            p.pipe_io(handle, "connect", 0, time.monotonic() + .03)
    except BaseException as caught:
        error = {"type": type(caught).__name__, "winerror": getattr(caught, "winerror", None), "text": str(caught)}
    overlap = boundary.overlap
    if closer:
        closer.join(timeout=1)
    flags = W.DWORD()
    event_open = bool(boundary.native.GetHandleInformation(overlap.event, C.byref(flags)))
    retained = [owner for owner in getattr(p, "PENDING_IO", []) if owner["overlap"] is overlap
                and owner["event"] == overlap.event and owner["handle"] == handle]
    material_owned = bool(retained) and (not hasattr(boundary, "buffer_anchor") or
                                         retained[0]["buffer"] is boundary.buffer_anchor)
    reuse_blocked = False
    if material_owned:
        events = p.IO_STATS["events_opened"]
        try:
            p.pipe_io(handle, "connect", 0, time.monotonic() + .1)
        except p.PendingIoUnconfirmed:
            reuse_blocked = p.IO_STATS["events_opened"] == events
    p.dump(root / "observation.json", {"error": error, "native_still_pending": overlap.internal == 0x103,
        "event_open": event_open, "early_event_close_attempts": boundary.early_closes,
        "owner_retained": material_owned and p.IO_STATS.get("pending_owned", 0) == 1,
        "poisoned_process_reuse_blocked": reuse_blocked,
        "native_overlap_address": C.addressof(overlap),
        "native_buffer_address": C.addressof(boundary.buffer_anchor) if hasattr(boundary, "buffer_anchor") else None,
        "injections": boundary.injected, "waits": boundary.waits, "results": boundary.results,
        "completion_records": p.IO_STATS.get("completions", []),
        "evidence_kind": "Win32-adapter-boundary-injection" if boundary.injected else "real-Win32-pipe",
        "real_driver_cancel_timeout_tested": False})
    if p.IO_STATS.get("pending_owned", 0):
        p.stop_pending_process()
    elif overlap.internal != 0x103:
        p.close_pipe(handle)
    else:
        # RED baseline has no fail-stop helper; keep its test safety anchors alive.
        while True:
            time.sleep(.05)


def supervise(mode, root):
    command = [sys._base_executable, str(Path(__file__).resolve()), "worker", mode, str(root)]
    with (root / "worker.stdout.txt").open("wb") as out, (root / "worker.stderr.txt").open("wb") as err:
        process = subprocess.Popen(command, stdout=out, stderr=err, creationflags=subprocess.CREATE_NO_WINDOW, env=child_env())
        start = p.creation_time(process._handle)
        record = {"pid": process.pid, "creation_time": start, "command": command}
        p.dump(root / "process.json", record)
        try:
            ready = p.wait_json(root / "ready.json")
            assert (ready["pid"], ready["creation_time"]) == (process.pid, start)
            observation = p.wait_json(root / "observation.json")
        finally:
            same = p.creation_time(process._handle) == start
            assert same
            forced, wait_expired = False, False
            try:
                process.wait(timeout=.3)
            except subprocess.TimeoutExpired:
                p.checked(p.K.TerminateProcess(process._handle, 96))
                forced = True
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    wait_expired = True
            signaled = p.K.WaitForSingleObject(process._handle, 0) == 0
            cleanup = {**record, "same_creation_time": same, "forced": forced,
                       "held_handle_signaled": signaled, "termination_wait_expired": wait_expired,
                       "returncode": process.returncode,
                       "pending_reclaimed_by_os_after_process_exit": signaled and process.returncode == 96}
            handle = int(process._handle)
            process._handle.Close()
            flags = W.DWORD()
            C.set_last_error(0)
            cleanup["process_handle_closed"] = not p.K.GetHandleInformation(handle, C.byref(flags)) and C.get_last_error() == 6
            p.dump(root / "cleanup.json", cleanup)
        absent = p.attempt_open(ready["pipe_name"], pipe=True)
        cleanup["pipe_absent"] = not absent["success"] and absent["winerror"] == 2
        p.dump(root / "cleanup.json", cleanup)
        p.dump(root / "result.json", {"ready": ready, "observation": observation, "cleanup": cleanup})


if __name__ == "__main__":
    if sys.argv[1] == "worker":
        worker(sys.argv[2], Path(sys.argv[3]))
    else:
        supervise(sys.argv[1], Path(sys.argv[2]))
