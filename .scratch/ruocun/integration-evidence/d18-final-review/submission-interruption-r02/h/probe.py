"""D18 disposable Windows probe. No product/runtime imports, no real secrets."""
from __future__ import annotations
import ctypes as C
from ctypes import wintypes as W
import hashlib
import hmac
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import struct
import sys
import time
import uuid
from safe_env import child_env

HERE = Path(__file__).resolve()
K = C.WinDLL("kernel32", use_last_error=True)
A = C.WinDLL("advapi32", use_last_error=True)
INVALID = C.c_void_p(-1).value
READ, WRITE = 0x80000000, 0x40000000
CALLS = []


def bind(dll, name, args, result=W.BOOL):
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


bind(K, "CreateFileW", [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE], W.HANDLE)
bind(K, "CloseHandle", [W.HANDLE])
bind(K, "FlushFileBuffers", [W.HANDLE])
bind(K, "WriteFile", [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p])
bind(K, "MoveFileExW", [W.LPCWSTR, W.LPCWSTR, W.DWORD])
bind(K, "ReplaceFileW", [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, W.DWORD, C.c_void_p, C.c_void_p])
bind(K, "GetCurrentProcess", [], W.HANDLE)
bind(K, "GetProcessTimes", [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4)
bind(K, "WaitForSingleObject", [W.HANDLE, W.DWORD], W.DWORD)
bind(K, "TerminateProcess", [W.HANDLE, W.UINT])
bind(K, "LocalFree", [C.c_void_p], C.c_void_p)
bind(A, "OpenProcessToken", [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)])
bind(A, "GetTokenInformation", [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.POINTER(W.DWORD)])
bind(A, "ConvertSidToStringSidW", [C.c_void_p, C.POINTER(W.LPWSTR)])
bind(A, "ConvertStringSecurityDescriptorToSecurityDescriptorW", [W.LPCWSTR, W.DWORD, C.POINTER(C.c_void_p), C.POINTER(W.DWORD)])
bind(A, "ConvertSecurityDescriptorToStringSecurityDescriptorW", [C.c_void_p, W.DWORD, W.DWORD, C.POINTER(W.LPWSTR), C.POINTER(W.DWORD)])
bind(A, "SetFileSecurityW", [W.LPCWSTR, W.DWORD, C.c_void_p])
bind(A, "GetSecurityInfo", [W.HANDLE, C.c_int, W.DWORD] + [C.c_void_p] * 5, W.DWORD)
bind(K, "GetCurrentThread", [], W.HANDLE)
bind(A, "ImpersonateAnonymousToken", [W.HANDLE])
bind(A, "RevertToSelf", [])


class SecurityAttributes(C.Structure):
    _fields_ = [("length", W.DWORD), ("descriptor", C.c_void_p), ("inherit", W.BOOL)]


bind(K, "CreateNamedPipeW", [W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD, C.POINTER(SecurityAttributes)], W.HANDLE)


def new_pipe(name):
    security = descriptor(f"D:P(A;;FA;;;{sid()})")
    attributes = SecurityAttributes(C.sizeof(SecurityAttributes), security, False)
    try:
        handle = K.CreateNamedPipeW(name, 0x40080003, 8, 1, 8192, 8192, 0, C.byref(attributes))
        if handle == INVALID:
            raise C.WinError(C.get_last_error())
        return handle
    finally:
        K.LocalFree(security)


def attempt_open(path, directory=False, pipe=False):
    try:
        # Pipe client has read/write data but excludes FILE_CREATE_PIPE_INSTANCE (0x4).
        handle = opened(path, 0x12019b if pipe else READ, flags=0x02000000 if directory else 0)
        K.CloseHandle(handle)
        return {"success": True}
    except OSError as error:
        return {"success": False, "winerror": error.winerror, "errno": error.errno}


class Overlapped(C.Structure):
    _fields_ = [("internal", C.c_size_t), ("internal_high", C.c_size_t),
                ("offset", W.DWORD), ("offset_high", W.DWORD), ("event", W.HANDLE)]


bind(K, "CreateEventW", [C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE)
bind(K, "ConnectNamedPipe", [W.HANDLE, C.POINTER(Overlapped)])
bind(K, "DisconnectNamedPipe", [W.HANDLE])
bind(K, "ReadFile", [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p])
bind(K, "GetOverlappedResult", [W.HANDLE, C.POINTER(Overlapped), C.POINTER(W.DWORD), W.BOOL])
bind(K, "CancelIoEx", [W.HANDLE, C.POINTER(Overlapped)])
bind(K, "GetProcessHandleCount", [W.HANDLE, C.POINTER(W.DWORD)])
bind(K, "GetHandleInformation", [W.HANDLE, C.POINTER(W.DWORD)])
IO_STATS = {"events_opened": 0, "events_closed": 0, "cancelled_pending": 0,
            "pending_owned": 0, "completions": []}
# An uncertain operation poisons this disposable process. These strong references
# survive exception unwinding and remain alive until native process termination.
PENDING_IO = []


class PendingIoUnconfirmed(BaseException):
    """Stop all further pipe work; ordinary timeout/disconnect handlers cannot catch it."""


def stop_pending_process():
    if PENDING_IO:
        # Bypass interpreter shutdown, which would release ctypes memory too early.
        K.TerminateProcess(K.GetCurrentProcess(), 96)
        os._exit(96)


def close_pipe(handle):
    if not any(owner["handle"] == handle for owner in PENDING_IO):
        checked(K.CloseHandle(handle))


def handle_count():
    count = W.DWORD()
    checked(K.GetProcessHandleCount(K.GetCurrentProcess(), C.byref(count)))
    return count.value


def pipe_io(handle, operation, data, deadline):
    if PENDING_IO:
        raise PendingIoUnconfirmed("process owns unconfirmed pending I/O")
    if time.monotonic() >= deadline:
        raise TimeoutError(operation)
    event = checked(K.CreateEventW(None, True, False, None))
    IO_STATS["events_opened"] += 1
    overlap = Overlapped()
    overlap.event = event
    count = W.DWORD()
    buffer = C.create_string_buffer(data if isinstance(data, bytes) else data)
    pending, complete = False, False
    try:
        C.set_last_error(0)
        if operation == "connect":
            ok = K.ConnectNamedPipe(handle, C.byref(overlap))
        else:
            function = K.ReadFile if operation == "read" else K.WriteFile
            size = data if isinstance(data, int) else len(data)
            ok = function(handle, buffer, size, C.byref(count), C.byref(overlap))
        error = C.get_last_error() if not ok else 0
        if operation == "connect" and error == 535:
            return b""
        if not ok and error != 997:
            raise C.WinError(error)
        if not ok:
            pending = True
            remaining = max(0, int((deadline - time.monotonic()) * 1000))
            status = K.WaitForSingleObject(event, remaining)
            if status == 258:
                C.set_last_error(0)
                cancelled = K.CancelIoEx(handle, C.byref(overlap))
                cancel_error = C.get_last_error() if not cancelled else 0
                if not cancelled and cancel_error != 1168:
                    raise C.WinError(cancel_error)
                # Do not free OVERLAPPED/buffer until the actual pending operation is complete.
                completed = K.WaitForSingleObject(event, 1500)
                if completed != 0:
                    raise RuntimeError("cancelled overlapped I/O did not complete within 1500ms")
                result = K.GetOverlappedResult(handle, C.byref(overlap), C.byref(count), False)
                result_error = C.get_last_error() if not result else 0
                # Equivalent to the Windows SDK HasOverlappedIoCompleted macro;
                # valid here only because submission returned ERROR_IO_PENDING.
                complete = overlap.internal != 0x103
                IO_STATS["completions"].append({"operation": operation, "success": bool(result),
                    "winerror": result_error, "native_status": overlap.internal, "confirmed": complete})
                if not complete:
                    raise RuntimeError("cancel result still pending")
                IO_STATS["cancelled_pending"] += 1
                if not result and result_error != 995:
                    raise C.WinError(result_error)
                raise TimeoutError(operation)
            if status != 0:
                raise C.WinError(C.get_last_error())
            result = K.GetOverlappedResult(handle, C.byref(overlap), C.byref(count), False)
            result_error = C.get_last_error() if not result else 0
            complete = overlap.internal != 0x103
            IO_STATS["completions"].append({"operation": operation, "success": bool(result),
                "winerror": result_error, "native_status": overlap.internal, "confirmed": complete})
            if not complete:
                raise RuntimeError("overlapped result still pending")
            if not result:
                raise C.WinError(result_error)
        if operation == "read":
            if not count.value:
                raise C.WinError(109)
            return buffer.raw[:count.value]
        return count.value
    finally:
        if pending and not complete:
            reason = sys.exc_info()[1]
            PENDING_IO.append({"handle": handle, "event": event, "overlap": overlap,
                               "buffer": buffer, "count": count, "operation": operation})
            IO_STATS["pending_owned"] = len(PENDING_IO)
            raise PendingIoUnconfirmed(f"{operation}: completion unconfirmed; {reason}") from reason
        else:
            checked(K.CloseHandle(event))
            IO_STATS["events_closed"] += 1


def exact(handle, length, deadline):
    parts = bytearray()
    while len(parts) < length:
        parts += pipe_io(handle, "read", length - len(parts), deadline)
    return bytes(parts)


def send(handle, data, deadline):
    frame = struct.pack("<I", len(data)) + data
    offset = 0
    while offset < len(frame):
        offset += pipe_io(handle, "write", frame[offset:], deadline)


def receive(handle, deadline, maximum=4096):
    size = struct.unpack("<I", exact(handle, 4, deadline))[0]
    if size > maximum:
        raise ValueError("too_large")
    return exact(handle, size, deadline)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def authenticated(challenge, request, key):
    mac = hmac.new(key, challenge + canonical(request), hashlib.sha256).hexdigest()
    return canonical({"request": request, "mac": mac})


def checked(result):
    if not result:
        raise C.WinError(C.get_last_error())
    return result


def sid():
    token = W.HANDLE()
    checked(A.OpenProcessToken(K.GetCurrentProcess(), 8, C.byref(token)))
    try:
        size = W.DWORD()
        A.GetTokenInformation(token, 1, None, 0, C.byref(size))
        buffer = C.create_string_buffer(size.value)
        checked(A.GetTokenInformation(token, 1, buffer, size, C.byref(size)))
        pointer = C.cast(buffer, C.POINTER(C.c_void_p))[0]
        text = W.LPWSTR()
        checked(A.ConvertSidToStringSidW(pointer, C.byref(text)))
        try:
            return text.value
        finally:
            K.LocalFree(C.cast(text, C.c_void_p))
    finally:
        K.CloseHandle(token)


def descriptor(sddl):
    value = C.c_void_p()
    checked(A.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, C.byref(value), None))
    return value


def set_acl(path, deny=0, directory=False):
    user = sid()
    flags = "OICI" if directory else ""
    sddl = "D:P" + (f"(D;;0x{deny:x};;;{user})" if deny else "") + f"(A;{flags};FA;;;{user})"
    value = descriptor(sddl)
    try:
        checked(A.SetFileSecurityW(str(path), 0x80000004, value))
    finally:
        K.LocalFree(value)
    return sddl


def acl(handle, object_type=1):
    security, dacl = C.c_void_p(), C.c_void_p()
    error = A.GetSecurityInfo(handle, object_type, 7, None, None, C.byref(dacl), None, C.byref(security))
    if error:
        raise C.WinError(error)
    text = W.LPWSTR()
    try:
        checked(A.ConvertSecurityDescriptorToStringSecurityDescriptorW(security, 1, 7, C.byref(text), None))
        return {"sddl": text.value, "null_dacl": not bool(dacl.value), "read_back": True}
    finally:
        if text:
            K.LocalFree(C.cast(text, C.c_void_p))
        K.LocalFree(security)


def creation_time(handle):
    values = [W.FILETIME() for _ in range(4)]
    checked(K.GetProcessTimes(handle, *[C.byref(value) for value in values]))
    return str((values[0].dwHighDateTime << 32) | values[0].dwLowDateTime)


def wait_json(path, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            return load(path)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            time.sleep(.01)
    raise TimeoutError(str(path))


class Worker:
    """Single direct base-interpreter worker; hold its process handle until final wait."""
    def __init__(self, root, *args):
        self.root = Path(root)
        self.out = (self.root / "worker.stdout.txt").open("wb")
        self.err = (self.root / "worker.stderr.txt").open("wb")
        self.command = [sys._base_executable, str(HERE), "worker", *map(str, args), str(root)]
        self.process = subprocess.Popen(self.command, stdout=self.out, stderr=self.err,
                                        creationflags=subprocess.CREATE_NO_WINDOW, env=child_env())
        self.start = creation_time(self.process._handle)
        self.record = {"pid": self.process.pid, "creation_time": self.start,
                       "command": self.command, "base_interpreter": True}
        dump(self.root / "process.json", self.record)

    def ready(self):
        value = wait_json(self.root / "ready.json")
        assert value["pid"] == self.process.pid and value["creation_time"] == self.start, value
        return value

    def close(self):
        # Stop file is only a graceful request; confirmed dead requires the held handle.
        (self.root / "stop").touch()
        forced = False
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            assert creation_time(self.process._handle) == self.start
            checked(K.TerminateProcess(self.process._handle, 91))
            forced = True
            self.process.wait(timeout=3)
        stopped = K.WaitForSingleObject(self.process._handle, 0) == 0
        record = {**self.record, "forced": forced, "returncode": self.process.returncode,
                  "held_handle_signaled": stopped, "same_creation_time": creation_time(self.process._handle) == self.start}
        dump(self.root / "cleanup.json", record)
        self.out.close()
        self.err.close()
        assert stopped
        old_handle = int(self.process._handle)
        self.process._handle.Close()
        flags = W.DWORD()
        C.set_last_error(0)
        usable = K.GetHandleInformation(old_handle, C.byref(flags))
        record["process_handle_closed"] = not usable and C.get_last_error() == 6
        assert record["process_handle_closed"]
        dump(self.root / "cleanup.json", record)
        return record

    def kill(self):
        assert creation_time(self.process._handle) == self.start
        checked(K.TerminateProcess(self.process._handle, 92))
        self.process.wait(timeout=3)
        dump(self.root / "kill.json", {**self.record, "requested_on_held_handle": True,
                                      "wait_signaled": K.WaitForSingleObject(self.process._handle, 0) == 0})


def native(name, *args):
    C.set_last_error(0)
    result = getattr(K, name)(*args)
    error = C.get_last_error() if not result else 0
    CALLS.append({"api": name, "success": bool(result), "winerror": error})
    if not result:
        raise C.WinError(error)
    return result


def opened(path, access=READ, share=7, disposition=3, flags=0, security=None):
    C.set_last_error(0)
    handle = K.CreateFileW(str(path), access, share, security, disposition, flags, None)
    if handle == INVALID:
        raise C.WinError(C.get_last_error())
    return handle


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def publish(target, value, method="flush-osreplace", timeout=.8, retry_denied=False):
    target = Path(target)
    candidate = target.with_name(target.name + ".candidate")
    data = (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")
    if method == "fsync-osreplace":
        with candidate.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        CALLS.append({"api": "os.fsync", "success": True})
    else:
        flags = 0x80000000 if method == "writethrough-move" else 0
        handle = opened(candidate, WRITE, 7, 1, flags)
        try:
            size = W.DWORD()
            native("WriteFile", handle, data, len(data), C.byref(size), None)
            if size.value != len(data):
                raise IOError("short write")
            native("FlushFileBuffers", handle)
        finally:
            K.CloseHandle(handle)
    attempts = []
    start = time.monotonic()
    while True:
        try:
            if method in {"fsync-osreplace", "flush-osreplace"}:
                os.replace(candidate, target)
            elif method == "flush-replacefile":
                native("ReplaceFileW", str(target), str(candidate), str(target) + ".backup", 0, None, None)
            elif method == "writethrough-move":
                native("MoveFileExW", str(candidate), str(target), 9)
            else:
                raise ValueError(method)
            attempts.append({"success": True, "elapsed": time.monotonic() - start})
            return {"published": True, "attempts": attempts, "elapsed": time.monotonic() - start}
        except OSError as error:
            attempts.append({"success": False, "winerror": error.winerror, "errno": error.errno,
                             "elapsed": time.monotonic() - start})
            retryable = error.winerror in {32, 33} or (error.winerror == 5 and retry_denied)
            if not retryable or time.monotonic() - start >= timeout:
                return {"published": False, "attempts": attempts, "elapsed": time.monotonic() - start,
                        "candidate": str(candidate), "error_class": "retry_exhausted" if retryable else "permanent"}
            time.sleep(min(.04, max(0, timeout - (time.monotonic() - start))))


def paths_case(root):
    set_acl(root, directory=True)
    paths = {}
    for method in ["fsync-osreplace", "flush-osreplace", "flush-replacefile", "writethrough-move"]:
        target = root / (method + ".json")
        dump(target, {"version": 1})
        result = publish(target, {"version": 2, "status": "completed", "text": "合成回执"}, method)
        result["receipt"] = load(target)
        handle = opened(target)
        try:
            result["published_acl"] = acl(handle)
        finally:
            K.CloseHandle(handle)
        paths[method] = result
    directory = {}
    for access in [READ, READ | WRITE]:
        try:
            handle = opened(root, access, flags=0x02000000)
            try:
                native("FlushFileBuffers", handle)
                directory[str(access)] = {"success": True}
            finally:
                K.CloseHandle(handle)
        except OSError as error:
            directory[str(access)] = {"success": False, "winerror": error.winerror, "errno": error.errno}
    try:
        descriptor = os.open(root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        directory["posix_fsync"] = {"success": True}
    except OSError as error:
        directory["posix_fsync"] = {"success": False, "winerror": getattr(error, "winerror", None), "errno": error.errno}
    return {"paths": paths, "native_directory_flush": directory, "power_loss_tested": False}


def file_worker(mode, duration, root):
    target = root / "receipt.json"
    handle = None
    try:
        if mode == "sharing":
            handle = opened(target, READ, share=1)
        else:
            set_acl(root, deny=0x40, directory=True)
            set_acl(target, deny=0x10000)
        dump(root / "ready.json", {"pid": os.getpid(), "creation_time": creation_time(K.GetCurrentProcess()), "mode": mode})
        deadline = time.monotonic() + float(duration)
        while time.monotonic() < deadline and not (root / "stop").exists():
            time.sleep(.01)
    finally:
        if handle:
            K.CloseHandle(handle)
        if mode == "denied":
            set_acl(root, directory=True)
            set_acl(target)


def refusals_case(root):
    results, cleanup = {}, []
    for name in ["sharing-release", "denied-release", "sharing-permanent", "denied-permanent"]:
        folder = root / name
        folder.mkdir()
        target = folder / "receipt.json"
        dump(target, {"version": 1})
        mode = name.split("-")[0]
        worker = Worker(folder, mode, ".25" if name.endswith("release") else "10")
        try:
            worker.ready()
            # MoveFileEx/os.replace can report 5 for a sharing refusal too. Error 5 alone
            # cannot distinguish ACL from temporary interference; only known scenarios opt in.
            result = publish(target, {"version": 2}, timeout=.35,
                             retry_denied=mode == "sharing" or name == "denied-release")
            result["receipt"] = load(target)
            result["candidate_is_not_terminal"] = not result["published"] and target.with_name("receipt.json.candidate").exists()
            results[name] = result
        finally:
            cleanup.append(worker.close())
            if mode == "denied":
                set_acl(folder, directory=True)
                set_acl(target)
    return {**results, "cleanup": {"all_workers_stopped": all(item["held_handle_signaled"] for item in cleanup), "workers": cleanup}}


def acl_case(root):
    private = root / "private"
    private.mkdir()
    set_acl(private, directory=True)
    material = private / "capability.json"
    dump(material, {"key": "synthetic-d18-never-used-for-real-auth"})
    set_acl(material)
    name = "\\\\.\\pipe\\ruocun-d18-" + uuid.uuid4().hex
    server = new_pipe(name)
    acls = {}
    try:
        for label, path, directory in [("directory", private, True), ("capability", material, False)]:
            handle = opened(path, flags=0x02000000 if directory else 0)
            try:
                acls[label] = acl(handle)
            finally:
                K.CloseHandle(handle)
        acls["pipe"] = acl(server, 6)
        # Actual anonymous thread token access attempts; no account/password/policy changes.
        checked(A.ImpersonateAnonymousToken(K.GetCurrentThread()))
        try:
            anonymous = {"directory": attempt_open(private, directory=True),
                         "capability": attempt_open(material), "pipe": attempt_open(name, pipe=True)}
        finally:
            checked(A.RevertToSelf())
        positive = {"directory": attempt_open(private, directory=True),
                    "capability": attempt_open(material), "pipe": attempt_open(name, pipe=True)}
    finally:
        K.CloseHandle(server)
    absent = attempt_open(name, pipe=True)
    return {"acl": acls, "target_sid": sid(), "target_identity": positive,
            "anonymous_attempt": anonymous, "pipe_name": name,
            "independent_account": {"status": "not-run", "reason": "No independent test account/token supplied; anonymous impersonation is not cross-account validation."},
            "cleanup": {"pipe_absent": not absent["success"] and absent["winerror"] == 2, "open_after_close": absent}}


def pipe_worker(root):
    config = load(root / "config.json")
    key = bytes.fromhex(config["key"])
    epoch = 1
    # BCrypt's first random call may initialize a cached process handle; warm it
    # before resource accounting so per-connection leaks remain observable.
    os.urandom(32)
    baseline = handle_count()
    server = new_pipe(config["name"])
    after_create = handle_count()
    records = []
    try:
        dump(root / "ready.json", {"pid": os.getpid(), "creation_time": creation_time(K.GetCurrentProcess()),
                                  "pipe_acl": acl(server, 6), "name": config["name"], "timeout": .35})
        ready_handles = handle_count()
        while not (root / "stop").exists():
            try:
                pipe_io(server, "connect", 0, time.monotonic() + .1)
            except TimeoutError:
                continue
            start = time.monotonic()
            record = {"connection": len(records) + 1}
            deadline = start + .35
            try:
                challenge = os.urandom(32)
                send(server, challenge, deadline)
                try:
                    data = receive(server, deadline)
                    envelope = json.loads(data)
                    request = envelope["request"]
                    expected = hmac.new(key, challenge + canonical(request), hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(envelope["mac"], expected):
                        response = {"error": "auth"}
                    elif request.get("run") != config["run"]:
                        response = {"error": "run"}
                    elif type(request.get("epoch")) is not int or request["epoch"] < epoch:
                        response = {"error": "epoch"}
                    else:
                        epoch = request["epoch"]
                        response = {"ok": True, "epoch": epoch, "request_bytes": len(data)}
                except ValueError as error:
                    response = {"error": str(error)}
                record["response"] = response
                send(server, canonical(response), deadline)
                # A bounded ack replaces unbounded server FlushFileBuffers on the pipe.
                record["ack"] = exact(server, 1, deadline).decode("ascii")
            except TimeoutError:
                record["error"] = "timeout"
            except OSError as error:
                record.update(error="disconnected", winerror=error.winerror, errno=error.errno)
            finally:
                if not PENDING_IO:
                    K.DisconnectNamedPipe(server)
                record["elapsed"] = time.monotonic() - start
                records.append(record)
                dump(root / "connections.json", records)
    finally:
        close_pipe(server)
        dump(root / "server.json", {"connections": records, **IO_STATS,
                                   "handles_before": baseline, "handles_after_create": after_create,
                                   "handles_ready": ready_handles, "handles_after": handle_count(), "epoch": epoch})


def pipe_client(config, mode):
    start = time.monotonic()
    deadline = start + 1.3
    while True:
        try:
            handle = opened(config["name"], 0x12019b, flags=0x40000000)
            break
        except OSError as error:
            if error.winerror not in {2, 231} or time.monotonic() >= deadline:
                raise
            time.sleep(.01)
    try:
        challenge = receive(handle, deadline)
        if mode == "silent":
            time.sleep(.5)
            try:
                receive(handle, deadline)
            except (OSError, TimeoutError) as error:
                return {"elapsed": time.monotonic() - start, "error": type(error).__name__, "winerror": getattr(error, "winerror", None)}
        if mode == "partial":
            pipe_io(handle, "write", struct.pack("<I", 200) + b"{bad", deadline)
            return {"closed_mid_frame": True}
        if mode == "oversize":
            pipe_io(handle, "write", struct.pack("<I", 4097), deadline)
        else:
            request = {"run": "wrong" if mode == "wrong-run" else config["run"],
                       "epoch": 2 if mode in {"advance", "maximum"} else 1, "action": "inspect"}
            key = b"wrong-synthetic-key" if mode == "wrong-key" else bytes.fromhex(config["key"])
            data = authenticated(challenge, request, key)
            if mode == "maximum":
                request["padding"] = ""
                missing = 4096 - len(authenticated(challenge, request, key))
                request["padding"] = "x" * missing
                data = authenticated(challenge, request, key)
                assert len(data) == 4096
            send(handle, data, deadline)
        response = json.loads(receive(handle, deadline))
        pipe_io(handle, "write", b"a", deadline)
        return {"response": response, "elapsed": time.monotonic() - start}
    finally:
        close_pipe(handle)


def pipe_case(root):
    set_acl(root, directory=True)
    config = {"name": "\\\\.\\pipe\\ruocun-d18-" + uuid.uuid4().hex,
              "run": uuid.uuid4().hex, "key": hashlib.sha256(b"D18 synthetic key").hexdigest()}
    dump(root / "config.json", config)
    set_acl(root / "config.json")
    worker = Worker(root, "pipe", "0")
    responses = {}
    try:
        ready = worker.ready()
        for mode in ["valid", "wrong-key", "wrong-run", "advance", "stale-epoch", "maximum", "oversize", "silent", "partial"]:
            responses[mode] = pipe_client(config, mode)
        # The last disconnect must be observed before a stop request.
        deadline = time.monotonic() + 2
        while len(wait_json(root / "connections.json")) < 9 and time.monotonic() < deadline:
            time.sleep(.01)
    finally:
        cleanup = worker.close()
    absent = attempt_open(config["name"], pipe=True)
    return {"responses": responses, "ready": ready, "server": load(root / "server.json"),
            "cleanup": cleanup, "pipe_absent": not absent["success"] and absent["winerror"] == 2,
            "client_io": IO_STATS}


def shared_read(path):
    handle = opened(path, READ, 7)
    try:
        buffer = C.create_string_buffer(16384)
        count = W.DWORD()
        checked(K.ReadFile(handle, buffer, 16384, C.byref(count), None))
        return json.loads(buffer.raw[:count.value])
    finally:
        K.CloseHandle(handle)


def observer_worker(root):
    reads, versions, malformed, open_errors = 0, set(), [], []
    dump(root / "ready.json", {"pid": os.getpid(), "creation_time": creation_time(K.GetCurrentProcess())})
    while not (root / "stop").exists():
        try:
            value = shared_read(root / "receipt.json")
            if value["payload"] != "x" * 4096 or type(value["version"]) is not int or not 0 <= value["version"] <= 40:
                malformed.append({"error": "unexpected_payload"})
            versions.add(value["version"])
            reads += 1
        except OSError as error:
            # This is an observed pathname-availability refusal, not a partial JSON read.
            open_errors.append({"error": type(error).__name__, "winerror": error.winerror})
        except (ValueError, KeyError) as error:
            malformed.append({"error": type(error).__name__, "winerror": getattr(error, "winerror", None)})
        time.sleep(.001)
    dump(root / "observer.json", {"reads": reads, "versions": sorted(versions), "malformed": malformed, "open_errors": open_errors})


def stage_worker(stage, root):
    target = root / "receipt.json"
    if stage == "before-replace":
        candidate = target.with_name("receipt.json.candidate")
        handle = opened(candidate, WRITE, disposition=1)
        try:
            data = b'{"version":2}\n'
            count = W.DWORD()
            native("WriteFile", handle, data, len(data), C.byref(count), None)
            native("FlushFileBuffers", handle)
        finally:
            K.CloseHandle(handle)
    else:
        assert publish(target, {"version": 2})["published"]
    dump(root / "ready.json", {"pid": os.getpid(), "creation_time": creation_time(K.GetCurrentProcess()), "stage": stage})
    while not (root / "stop").exists():
        time.sleep(.01)


def crash_case(root):
    result, crashes, observers = {}, {}, {}
    for stage in ["before-replace", "after-replace"]:
        folder = root / stage
        folder.mkdir()
        dump(folder / "receipt.json", {"version": 1})
        worker = Worker(folder, stage, "0")
        try:
            worker.ready()
            worker.kill()
        finally:
            cleanup = worker.close()
        command = [sys._base_executable, str(HERE), "read", str(folder / "receipt.json")]
        cold = subprocess.run(command, capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW, env=child_env())
        (folder / "cold.stdout.txt").write_bytes(cold.stdout)
        (folder / "cold.stderr.txt").write_bytes(cold.stderr)
        assert cold.returncode == 0
        result[stage] = {"cold_read": json.loads(cold.stdout), "command": command,
                         "candidate_present": (folder / "receipt.json.candidate").exists()}
        crashes[stage] = {"cleanup": cleanup}
    for method in ["fsync-osreplace", "flush-osreplace", "flush-replacefile", "writethrough-move"]:
        folder = root / method
        folder.mkdir()
        dump(folder / "receipt.json", {"version": 0, "payload": "x" * 4096})
        worker = Worker(folder, "observer", "0")
        try:
            worker.ready()
            # Give the independent reader an opportunity to observe both endpoints.
            time.sleep(.03)
            publications = []
            for version in range(1, 41):
                publication = publish(folder / "receipt.json", {"version": version, "payload": "x" * 4096},
                                      method=method, retry_denied=True)
                assert publication["published"], publication
                publications.append(publication)
                time.sleep(.002)
            time.sleep(.03)
        finally:
            cleanup = worker.close()
        observers[method] = {**load(folder / "observer.json"), "cleanup": cleanup, "publications": publications}
    return {**result, "crashes": crashes, "observers": observers, "power_loss_tested": False}


def main():
    if sys.argv[1] == "case":
        root = Path(sys.argv[3])
        result = {"paths": paths_case, "refusals": refusals_case, "acl": acl_case, "pipe": pipe_case, "crash": crash_case}[sys.argv[2]](root)
        result["calls"] = CALLS
        dump(root / "result.json", result)
    elif sys.argv[1] == "worker":
        if sys.argv[2] == "pipe":
            pipe_worker(Path(sys.argv[4]))
        elif sys.argv[2] == "observer":
            observer_worker(Path(sys.argv[4]))
        elif sys.argv[2] in {"before-replace", "after-replace"}:
            stage_worker(sys.argv[2], Path(sys.argv[4]))
        else:
            file_worker(sys.argv[2], sys.argv[3], Path(sys.argv[4]))
    elif sys.argv[1] == "read":
        print(json.dumps({"receipt": load(sys.argv[2]), "pid": os.getpid(),
                          "creation_time": creation_time(K.GetCurrentProcess())}))
    else:
        raise SystemExit("unknown case")


if __name__ == "__main__":
    try:
        main()
    finally:
        stop_pending_process()
