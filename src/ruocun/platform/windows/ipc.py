"""D18具名管道窄端口的产品适配。原生I/O仅在受监督helper角色运行。"""

from __future__ import annotations

import ctypes as C
import hashlib
import hmac
import json
import os
import queue
import re
import socket
import struct
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from ctypes import wintypes as W
from dataclasses import asdict, dataclass
from typing import IO, Any, NoReturn, cast

from ...session.contract import ProcessIdentity
from ...session.process_identity import process_identity
from ..process_tree import scrubbed_env
from .durable_file import _current_user_sid as sid

VERSION = 1
MAX_FRAME = 262144
HANDSHAKE_SECONDS = 3.0
CLEANUP_RESERVE = .5
K = C.WinDLL("kernel32", use_last_error=True)
A = C.WinDLL("advapi32", use_last_error=True)
INVALID = C.c_void_p(-1).value
PENDING_IO: list[dict[str, Any]] = []
_HELPER_MODE = False
_BOOT_HINT: tuple[str, str] | None = None

def bind(dll: Any, name: str, args: list[Any], result: Any = W.BOOL) -> Any:
    function = getattr(dll, name)
    function.argtypes, function.restype = args, result
    return function


class SecurityAttributes(C.Structure):
    _fields_ = [("length", W.DWORD), ("descriptor", C.c_void_p), ("inherit", W.BOOL)]


def new_pipe(name: str) -> Any:
    security = descriptor(f"D:P(A;;FA;;;{sid()})")
    attributes = SecurityAttributes(C.sizeof(SecurityAttributes), security, False)
    try:
        handle = K.CreateNamedPipeW(name, 0x40080003, 8, 1, 8192, 8192, 0, C.byref(attributes))
        if handle == INVALID:
            raise C.WinError(C.get_last_error())
        return handle
    finally:
        K.LocalFree(security)


class Overlapped(C.Structure):
    _fields_ = [("internal", C.c_size_t), ("internal_high", C.c_size_t),
                ("offset", W.DWORD), ("offset_high", W.DWORD), ("event", W.HANDLE)]


class PendingIoUnconfirmed(BaseException):
    """Stop all further pipe work; ordinary timeout/disconnect handlers cannot catch it."""


def stop_pending_process() -> None:
    if PENDING_IO:
        # Bypass interpreter shutdown, which would release ctypes memory too early.
        K.TerminateProcess(K.GetCurrentProcess(), 96)
        os._exit(96)


def close_pipe(handle: Any) -> None:
    if not any(owner["handle"] == handle for owner in PENDING_IO):
        checked(K.CloseHandle(handle))


def pipe_io(handle: Any, operation: str, data: bytes | int, deadline: float) -> bytes | int:
    if not _HELPER_MODE:
        raise IPCError("原生管道I/O仅允许在受监督helper中执行")
    if PENDING_IO:
        raise PendingIoUnconfirmed("process owns unconfirmed pending I/O")
    if time.monotonic() >= deadline:
        raise TimeoutError(operation)
    event = checked(K.CreateEventW(None, True, False, None))
    overlap = Overlapped()
    overlap.event = event
    count = W.DWORD()
    buffer = C.create_string_buffer(data if isinstance(data, bytes) else data)
    complete = False
    owner = {"handle": handle, "event": event, "overlap": overlap,
             "buffer": buffer, "count": count, "operation": operation}
    PENDING_IO.append(owner)
    try:
        C.set_last_error(0)
        if operation == "connect":
            ok = K.ConnectNamedPipe(handle, C.byref(overlap))
        else:
            function = K.ReadFile if operation == "read" else K.WriteFile
            size = data if isinstance(data, int) else len(data)
            ok = function(handle, buffer, size, C.byref(count), C.byref(overlap))
        error = C.get_last_error() if not ok else 0
        # Only a returned synchronous result can disarm pre-submission ownership.
        # An interruption before this decision leaves the submission uncertain.
        if ok or error != 997:
            complete = True
        if operation == "connect" and error == 535:
            return b""
        if not ok and error != 997:
            raise C.WinError(error)
        if not ok:
            remaining = max(0, int((deadline - time.monotonic() - .25) * 1000))
            status = K.WaitForSingleObject(event, remaining)
            if status == 258:
                C.set_last_error(0)
                cancelled = K.CancelIoEx(handle, C.byref(overlap))
                cancel_error = C.get_last_error() if not cancelled else 0
                if not cancelled and cancel_error != 1168:
                    raise C.WinError(cancel_error)
                # Do not free OVERLAPPED/buffer until the actual pending operation is complete.
                completed = K.WaitForSingleObject(event, max(0, int((deadline - time.monotonic()) * 1000)))
                if completed != 0:
                    raise RuntimeError("cancelled overlapped I/O did not complete before deadline")
                result = K.GetOverlappedResult(handle, C.byref(overlap), C.byref(count), False)
                result_error = C.get_last_error() if not result else 0
                # Equivalent to the Windows SDK HasOverlappedIoCompleted macro;
                # valid here only because submission returned ERROR_IO_PENDING.
                complete = overlap.internal != 0x103
                if not complete:
                    raise RuntimeError("cancel result still pending")
                if not result and result_error != 995:
                    raise C.WinError(result_error)
                raise TimeoutError(operation)
            if status != 0:
                raise C.WinError(C.get_last_error())
            result = K.GetOverlappedResult(handle, C.byref(overlap), C.byref(count), False)
            result_error = C.get_last_error() if not result else 0
            complete = overlap.internal != 0x103
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
        if not complete:
            reason = sys.exc_info()[1]
            raise PendingIoUnconfirmed(f"{operation}: completion unconfirmed; {reason}") from reason
        else:
            PENDING_IO.remove(owner)
            checked(K.CloseHandle(event))


def exact(handle: Any, length: int, deadline: float) -> bytes:
    parts = bytearray()
    while len(parts) < length:
        parts += cast(bytes, pipe_io(handle, "read", length - len(parts), deadline))
    return bytes(parts)


def send(handle: Any, data: bytes, deadline: float) -> None:
    frame = struct.pack("<I", len(data)) + data
    offset = 0
    while offset < len(frame):
        offset += cast(int, pipe_io(handle, "write", frame[offset:], deadline))


def receive(handle: Any, deadline: float, maximum: int = MAX_FRAME) -> bytes:
    size = struct.unpack("<I", exact(handle, 4, deadline))[0]
    if size == 0 or size > maximum:
        raise ValueError("too_large")
    return exact(handle, size, deadline)


def checked(result: Any) -> Any:
    if not result:
        raise C.WinError(C.get_last_error())
    return result


bind(K, "CreateNamedPipeW", [W.LPCWSTR, W.DWORD, W.DWORD, W.DWORD, W.DWORD, W.DWORD,
                           W.DWORD, C.POINTER(SecurityAttributes)], W.HANDLE)
bind(K, "CreateFileW", [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p, W.DWORD, W.DWORD, W.HANDLE], W.HANDLE)
bind(K, "CloseHandle", [W.HANDLE])
bind(K, "CreateEventW", [C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR], W.HANDLE)
bind(K, "ConnectNamedPipe", [W.HANDLE, C.POINTER(Overlapped)])
bind(K, "DisconnectNamedPipe", [W.HANDLE])
bind(K, "ReadFile", [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p])
bind(K, "WriteFile", [W.HANDLE, C.c_void_p, W.DWORD, C.POINTER(W.DWORD), C.c_void_p])
bind(K, "GetOverlappedResult", [W.HANDLE, C.POINTER(Overlapped), C.POINTER(W.DWORD), W.BOOL])
bind(K, "CancelIoEx", [W.HANDLE, C.POINTER(Overlapped)])
bind(K, "WaitForSingleObject", [W.HANDLE, W.DWORD], W.DWORD)
bind(K, "OpenProcess", [W.DWORD, W.BOOL, W.DWORD], W.HANDLE)
bind(K, "TerminateProcess", [W.HANDLE, W.UINT])
bind(K, "GetCurrentProcess", [], W.HANDLE)
bind(K, "GetProcessTimes", [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4)
bind(K, "GetNamedPipeClientProcessId", [W.HANDLE, C.POINTER(W.DWORD)])
bind(K, "GetNamedPipeServerProcessId", [W.HANDLE, C.POINTER(W.DWORD)])
bind(K, "LocalFree", [C.c_void_p], C.c_void_p)
bind(A, "ConvertStringSecurityDescriptorToSecurityDescriptorW",
     [W.LPCWSTR, W.DWORD, C.POINTER(C.c_void_p), C.POINTER(W.DWORD)])
bind(A, "GetSecurityInfo", [W.HANDLE, C.c_int, W.DWORD] + [C.c_void_p] * 5, W.DWORD)
bind(A, "ConvertSecurityDescriptorToStringSecurityDescriptorW",
     [C.c_void_p, W.DWORD, W.DWORD, C.POINTER(W.LPWSTR), C.POINTER(W.DWORD)])


class IPCError(RuntimeError):
    """传输失败，调用者保留执行状态并核对原run。"""


class CleanupUnconfirmed(IPCError):
    """helper真实退出尚未确认，保留句柄并禁止新建竞争transport。"""


def descriptor(sddl: str) -> Any:
    value = C.c_void_p()
    checked(A.ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, C.byref(value), None))
    return value


def _pipe_acl(handle: Any) -> str:
    security, dacl = C.c_void_p(), C.c_void_p()
    error = A.GetSecurityInfo(handle, 6, 4, None, None, C.byref(dacl), None, C.byref(security))
    if error:
        raise C.WinError(error)
    text = W.LPWSTR()
    try:
        checked(A.ConvertSecurityDescriptorToStringSecurityDescriptorW(security, 1, 4, C.byref(text), None))
        result = text.value
        if not dacl or result != f"D:P(A;;FA;;;{sid()})":
            raise IPCError("管道DACL读回与当前用户私有ACL不一致")
        return result
    finally:
        if text:
            K.LocalFree(C.cast(text, C.c_void_p))
        K.LocalFree(security)


def canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def encode_frame(value: dict[str, Any]) -> bytes:
    body = canonical(value)
    if not body or len(body) > MAX_FRAME:
        raise ValueError("IPC帧超过UTF8字节上限")
    return struct.pack("<I", len(body)) + body


def _reject_constant(value: str) -> NoReturn:
    raise ValueError("IPC不接受非法JSON数值")


def _decode(body: bytes) -> dict[str, Any]:
    result = json.loads(body.decode("utf-8"), parse_constant=_reject_constant)
    if not isinstance(result, dict):
        raise ValueError("IPC帧必须为对象")
    return result


def read_frame(stream: IO[bytes]) -> dict[str, Any]:
    def read_exact(size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            part = stream.read(size - len(data))
            if not part:
                raise EOFError("IPC helper管道已关闭")
            data.extend(part)
        return bytes(data)

    size = struct.unpack("<I", read_exact(4))[0]
    if size == 0 or size > MAX_FRAME:
        raise ValueError("IPC帧长度无效")
    return _decode(read_exact(size))


def _stdio_send(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write(encode_frame(value))
    sys.stdout.buffer.flush()


class _ProcessEntry(C.Structure):
    _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("pid", W.DWORD),
                ("heap", C.c_size_t), ("module", W.DWORD), ("threads", W.DWORD),
                ("parent", W.DWORD), ("priority", W.LONG), ("flags", W.DWORD), ("exe", W.WCHAR * 260)]


bind(K, "CreateToolhelp32Snapshot", [W.DWORD, W.DWORD], W.HANDLE)
bind(K, "Process32FirstW", [W.HANDLE, C.POINTER(_ProcessEntry)])
bind(K, "Process32NextW", [W.HANDLE, C.POINTER(_ProcessEntry)])


def _parent_pid(pid: int) -> int:
    snapshot = K.CreateToolhelp32Snapshot(2, 0)
    if snapshot == INVALID:
        raise C.WinError(C.get_last_error())
    try:
        entry = _ProcessEntry()
        entry.size = C.sizeof(entry)
        available = K.Process32FirstW(snapshot, C.byref(entry))
        while available:
            if entry.pid == pid:
                return int(entry.parent)
            available = K.Process32NextW(snapshot, C.byref(entry))
        raise IPCError("无法核实helper父进程")
    finally:
        checked(K.CloseHandle(snapshot))


@dataclass(frozen=True)
class PeerIdentity:
    helper_pid: int
    parent_pid: int
    owner_pid: int
    helper_identity: ProcessIdentity
    owner_identity: ProcessIdentity


def _peer(pid: int, owner: int) -> PeerIdentity:
    parent = _parent_pid(pid)
    # Windows venv launcher有一层转发shim，最多仅接受这一层。
    if parent != owner and _parent_pid(parent) != owner:
        raise IPCError("helper与控制进程身份不匹配")
    identity, owner_identity = _identity(pid), _identity(owner)
    if identity is None or owner_identity is None:
        raise IPCError("helper或控制进程已退出")
    return PeerIdentity(pid, parent, owner, identity, owner_identity)


def _start(handle: Any) -> str:
    stamps = [W.FILETIME() for _ in range(4)]
    checked(K.GetProcessTimes(handle, *[C.byref(stamp) for stamp in stamps]))
    return str((stamps[0].dwHighDateTime << 32) | stamps[0].dwLowDateTime)


def _identity(pid: int) -> ProcessIdentity | None:
    if _BOOT_HINT is None:
        return process_identity(pid)
    handle = checked(K.OpenProcess(0x101000, False, pid))
    try:
        status = K.WaitForSingleObject(handle, 0)
        if status == 0:
            return None
        if status != 258:
            raise IPCError("无法核实进程存活身份")
        return ProcessIdentity(_BOOT_HINT[0], _BOOT_HINT[1], pid, _start(handle))
    finally:
        checked(K.CloseHandle(handle))


def _endpoint(name: str) -> None:
    if not re.fullmatch(r"\\\\\.\\pipe\\ruocun-[a-zA-Z0-9-]{16,120}", name):
        raise ValueError("仅支持本机随机RuoCun具名管道")


def _mac(capability: bytes, challenge: bytes, value: dict[str, Any]) -> str:
    return hmac.new(capability, challenge + canonical(value), hashlib.sha256).hexdigest()


def _receive_object(handle: Any, deadline: float) -> dict[str, Any]:
    return _decode(receive(handle, deadline))


def _send_object(handle: Any, value: dict[str, Any], deadline: float) -> None:
    body = encode_frame(value)[4:]
    send(handle, body, deadline)


def _server(config: dict[str, Any], owner_handle: Any) -> None:
    capability = bytes.fromhex(config["capability"])
    handle = new_pipe(config["endpoint"])
    try:
        _stdio_send({"kind": "ready", "pid": os.getpid(), "private_sid": sid(), "pipe_acl": _pipe_acl(handle)})
        while True:
            owner_status = K.WaitForSingleObject(owner_handle, 0)
            if owner_status == 0:
                return
            if owner_status != 258:
                raise IPCError("无法确认runner owner存活状态")
            try:
                pipe_io(handle, "connect", 0, time.monotonic() + .5)
            except TimeoutError:
                continue
            deadline = time.monotonic() + HANDSHAKE_SECONDS
            try:
                challenge = os.urandom(32)
                _send_object(handle, {"version": VERSION, "challenge": challenge.hex()}, deadline)
                envelope = _receive_object(handle, deadline)
                request_body = {"version": envelope.get("version"), "owner_pid": envelope.get("owner_pid"),
                                "payload": envelope.get("payload")}
                if type(envelope.get("version")) is not int or envelope["version"] != VERSION:
                    raise IPCError("IPC协议版本不匹配")
                if not isinstance(envelope.get("mac"), str) or not hmac.compare_digest(
                    envelope["mac"], _mac(capability, challenge, request_body),
                ):
                    raise IPCError("IPC认证失败")
                client = W.DWORD()
                checked(K.GetNamedPipeClientProcessId(handle, C.byref(client)))
                peer = _peer(int(client.value), int(envelope["owner_pid"]))
                if not isinstance(envelope.get("payload"), dict):
                    raise ValueError("IPC请求必须为对象")
                _stdio_send({"kind": "request", "payload": envelope["payload"], "peer": asdict(peer)})
                response = read_frame(sys.stdin.buffer)
                response_body = {"version": VERSION, "response": response["payload"]}
                _send_object(handle, {**response_body, "mac": _mac(capability, challenge, response_body)}, deadline)
                if exact(handle, 1, deadline) != b"a":
                    raise IPCError("IPC确认无效")
            except (OSError, TimeoutError, ValueError, TypeError, KeyError, IPCError):
                pass
            finally:
                if not PENDING_IO:
                    K.DisconnectNamedPipe(handle)
    finally:
        close_pipe(handle)


def _client(config: dict[str, Any]) -> dict[str, Any]:
    deadline = float(config["deadline"])
    capability = bytes.fromhex(config["capability"])
    while True:
        handle = K.CreateFileW(config["endpoint"], 0x12019b, 0, None, 3, 0x40000000, None)
        if handle != INVALID:
            break
        error = C.get_last_error()
        if error not in {2, 231} or time.monotonic() >= deadline:
            raise C.WinError(error)
        time.sleep(min(.01, max(0, deadline - time.monotonic())))
    try:
        server = W.DWORD()
        checked(K.GetNamedPipeServerProcessId(handle, C.byref(server)))
        if server.value != config["expected_server_pid"]:
            raise IPCError("管道server helper身份不匹配")
        greeting = _receive_object(handle, deadline)
        if type(greeting.get("version")) is not int or greeting["version"] != VERSION:
            raise IPCError("IPC协议版本不匹配")
        challenge = bytes.fromhex(greeting["challenge"])
        if len(challenge) != 32:
            raise IPCError("IPC挑战无效")
        body = {"version": VERSION, "owner_pid": config["owner_pid"], "payload": config["payload"]}
        _send_object(handle, {**body, "mac": _mac(capability, challenge, body)}, deadline)
        envelope = _receive_object(handle, deadline)
        signed = {"version": envelope.get("version"), "response": envelope.get("response")}
        if type(envelope.get("version")) is not int or envelope["version"] != VERSION:
            raise IPCError("IPC响应版本不匹配")
        if not isinstance(envelope.get("mac"), str) or not hmac.compare_digest(
            envelope["mac"], _mac(capability, challenge, signed),
        ):
            raise IPCError("IPC响应认证失败")
        if not isinstance(envelope.get("response"), dict):
            raise ValueError("IPC响应必须为对象")
        pipe_io(handle, "write", b"a", deadline)
        return cast(dict[str, Any], envelope["response"])
    finally:
        close_pipe(handle)


def helper_main() -> int:
    global _HELPER_MODE, _BOOT_HINT
    _HELPER_MODE = True
    owner_handle: Any = None
    try:
        _stdio_send({"kind": "identity", "pid": os.getpid(), "start": _start(K.GetCurrentProcess())})
        config = read_frame(sys.stdin.buffer)
        if config["host"] != socket.gethostname() or not isinstance(config["boot"], str):
            raise IPCError("helper启动身份缓存无效")
        # 私有父子stdio复用父端已经OS核验的boot，不从具名管道请求取该信息。
        _BOOT_HINT = (config["host"], config["boot"])
        _endpoint(config["endpoint"])
        peer = _peer(os.getpid(), config["owner_pid"])
        owner_handle = checked(K.OpenProcess(0x101000, False, peer.owner_pid))
        if _start(owner_handle) != peer.owner_identity.start:
            raise IPCError("IPC owner进程创建身份已变化")
        if len(bytes.fromhex(config["capability"])) != 32:
            raise ValueError("capability必须为32字节")
        if config["mode"] == "server":
            _server(config, owner_handle)
        elif config["mode"] == "client":
            _stdio_send({"kind": "result", "payload": _client(config)})
        else:
            raise ValueError("未知helper角色")
        return 0
    except Exception as exc:
        _stdio_send({"kind": "error", "type": type(exc).__name__, "winerror": getattr(exc, "winerror", None)})
        return 1
    finally:
        try:
            if owner_handle is not None:
                checked(K.CloseHandle(owner_handle))
        finally:
            stop_pending_process()


_UNCONFIRMED_HELPERS: list[_Helper] = []


class _Helper:
    def __init__(self, command: Sequence[str] | None, environ: Mapping[str, str] | None, deadline: float) -> None:
        for previous in tuple(_UNCONFIRMED_HELPERS):
            previous.close(deadline)
        argv = list(command) if command is not None else [
            sys.executable, "-I", "-X", "utf8", "-m", "ruocun", "--ruocun-ipc-helper",
        ]
        self._messages: queue.Queue[dict[str, Any] | BaseException] = queue.Queue(maxsize=4)
        self._closed = threading.Event()
        self._send_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._finished = False
        self._close_error: BaseException | None = None
        self._writers: list[threading.Thread] = []
        self._handle: Any = None
        self.identity: ProcessIdentity | None = None
        self.process = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=scrubbed_env(environ), creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True,
        )
        self._reader = threading.Thread(target=self._read, name="ruocun-ipc-stdio", daemon=True)
        self._reader.start()
        try:
            message = self.take(deadline)
            if message.get("kind") != "identity":
                raise IPCError("IPC helper身份握手失败")
            pid = message["pid"]
            self._handle = checked(K.OpenProcess(0x101001, False, pid))
            actual_start = _start(self._handle)
            actual = _peer(pid, os.getpid()).helper_identity
            if actual_start != actual.start or message["start"] != actual.start:
                raise IPCError("IPC helper实际进程身份不匹配")
            self.identity = actual
        except BaseException:
            self.close(deadline)
            raise

    def _read(self) -> None:
        assert self.process.stdout is not None
        try:
            while not self._closed.is_set():
                value = read_frame(self.process.stdout)
                self._messages.put(value, timeout=HANDSHAKE_SECONDS)
        except BaseException as exc:
            try:
                self._messages.put_nowait(exc)
            except queue.Full:
                pass

    def take(self, deadline: float | None) -> dict[str, Any]:
        while not self._closed.is_set():
            remaining = HANDSHAKE_SECONDS if deadline is None else deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("IPC helper总期限已到")
            try:
                value = self._messages.get(timeout=min(.1, remaining))
            except queue.Empty:
                continue
            if isinstance(value, BaseException):
                raise IPCError("IPC helper传输已停止") from value
            if value.get("kind") == "error":
                raise IPCError(f"IPC helper拒绝请求（{value.get('type')}，Win32 {value.get('winerror')}）")
            return value
        raise IPCError("IPC helper已关闭")

    def send(self, value: dict[str, Any], deadline: float) -> None:
        data = encode_frame(value)
        result: queue.Queue[Exception | None] = queue.Queue(maxsize=1)
        if not self._send_lock.acquire(timeout=max(0, deadline - time.monotonic())):
            raise TimeoutError("IPC helper发送队列超时")
        try:
            if self._closed.is_set():
                raise IPCError("IPC helper已关闭")

            def write() -> None:
                try:
                    assert self.process.stdin is not None
                    self.process.stdin.write(data)
                    self.process.stdin.flush()
                    result.put(None)
                except Exception as exc:
                    result.put(exc)

            worker = threading.Thread(target=write, name="ruocun-ipc-write", daemon=True)
            self._writers.append(worker)
            worker.start()
            try:
                error = result.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TimeoutError("IPC helper发送超时") from exc
            if error is not None:
                raise IPCError("IPC helper发送失败") from error
            worker.join(timeout=max(0, deadline - time.monotonic()))
            if worker.is_alive():
                raise CleanupUnconfirmed("IPC helper写入线程收尾未确认")
            self._writers.remove(worker)
        finally:
            self._send_lock.release()

    def configure(self, config: dict[str, Any], deadline: float) -> None:
        assert self.identity is not None
        self.send({**config, "owner_pid": os.getpid(), "host": self.identity.host,
                   "boot": self.identity.boot}, deadline)

    def close(self, deadline: float) -> None:
        if not self._close_lock.acquire(timeout=max(0, deadline - time.monotonic())):
            raise CleanupUnconfirmed("IPC helper收尾正在进行，尚未确认完成")
        try:
            if self._finished and self._close_error is None:
                return
            try:
                self._close(deadline)
                self._close_error = None
                if self in _UNCONFIRMED_HELPERS:
                    _UNCONFIRMED_HELPERS.remove(self)
            except BaseException as exc:
                self._close_error = exc
                raise
            finally:
                self._finished = True
        finally:
            self._close_lock.release()

    def _close(self, deadline: float) -> None:
        self._closed.set()
        try:
            if self._handle is not None:
                status = K.WaitForSingleObject(self._handle, 0)
                if status == 258:
                    checked(K.TerminateProcess(self._handle, 97))
                elif status != 0:
                    raise C.WinError(C.get_last_error())
                if K.WaitForSingleObject(self._handle, max(0, int((deadline - time.monotonic()) * 1000))) != 0:
                    raise CleanupUnconfirmed("IPC helper退出未确认")
            elif self.process.poll() is None:
                # 未发配置前helper不能创建原生端点。关闭stdin令其bootstrap退出。
                assert self.process.stdin is not None
                self.process.stdin.close()
            self.process.wait(timeout=max(.001, deadline - time.monotonic()))
            self._reader.join(timeout=max(0, deadline - time.monotonic()))
            for writer in self._writers:
                writer.join(timeout=max(0, deadline - time.monotonic()))
            if self._reader.is_alive() or any(writer.is_alive() for writer in self._writers):
                raise CleanupUnconfirmed("IPC helper stdio收口未确认")
        except BaseException as exc:
            if self not in _UNCONFIRMED_HELPERS:
                _UNCONFIRMED_HELPERS.append(self)
            raise CleanupUnconfirmed("IPC helper退出/资源收口尚未确认，句柄已保留") from exc
        if self._handle is not None:
            checked(K.CloseHandle(self._handle))
            self._handle = None
        if self.process.stdin is not None:
            self.process.stdin.close()
        if self.process.stdout is not None:
            self.process.stdout.close()


class PipeServer:
    def __init__(
        self, pipe_name: str, capability: bytes,
        handler: Callable[[dict[str, Any], PeerIdentity], dict[str, Any]], *,
        helper_command: Sequence[str] | None = None, environ: Mapping[str, str] | None = None,
    ) -> None:
        _endpoint(pipe_name)
        if len(capability) != 32:
            raise ValueError("capability必须为32字节")
        self.pipe_name, self._capability, self._handler = pipe_name, capability, handler
        self._command, self._environment = helper_command, environ
        self._helper: _Helper | None = None
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()
        self.error: BaseException | None = None
        self.helper_identity: ProcessIdentity | None = None
        self.helper_pid = 0
        self.private_sid = ""
        self.pipe_acl = ""

    @property
    def alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stopped.is_set() and self.error is None

    def start(self, deadline: float) -> PipeServer:
        if self._helper is not None:
            raise IPCError("IPC server已经启动，故障后需新nonce端点")
        helper = self._helper = _Helper(self._command, self._environment, deadline)
        try:
            helper.configure({"mode": "server", "endpoint": self.pipe_name,
                              "capability": self._capability.hex()}, deadline)
            ready = helper.take(deadline)
            if ready.get("kind") != "ready" or helper.identity is None or ready.get("pid") != helper.identity.pid:
                raise IPCError("IPC server就绪身份不匹配")
            self.helper_identity = helper.identity
            self.helper_pid = helper.identity.pid
            self.private_sid = ready["private_sid"]
            self.pipe_acl = ready["pipe_acl"]
            self._thread = threading.Thread(target=self._pump, name="ruocun-ipc-server", daemon=True)
            self._thread.start()
            return self
        except BaseException:
            helper.close(deadline)
            raise

    def _pump(self) -> None:
        assert self._helper is not None
        try:
            while not self._stopped.is_set():
                message = self._helper.take(None)
                if message.get("kind") != "request":
                    raise IPCError("IPC helper请求类型无效")
                data = message["peer"]
                peer = _peer(data["helper_pid"], data["owner_pid"])
                if asdict(peer) != data:
                    raise IPCError("IPC客户端进程身份已变化")
                response = self._handler(message["payload"], peer)
                self._helper.send({"payload": response}, time.monotonic() + HANDSHAKE_SECONDS - CLEANUP_RESERVE)
        except BaseException as exc:
            if not self._stopped.is_set():
                self.error = exc
        finally:
            self._helper.close(time.monotonic() + HANDSHAKE_SECONDS)

    def close(self) -> None:
        self._stopped.set()
        deadline = time.monotonic() + HANDSHAKE_SECONDS
        if self._helper is not None:
            self._helper.close(deadline)
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=max(0, deadline - time.monotonic()))
            if self._thread.is_alive():
                raise CleanupUnconfirmed("IPC server处理线程收口未确认")


def request(
    pipe_name: str, capability: bytes, payload: dict[str, Any], *, expected_server_pid: int,
    deadline: float, helper_command: Sequence[str] | None = None, environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    _endpoint(pipe_name)
    if len(capability) != 32:
        raise ValueError("capability必须为32字节")
    operation_deadline = deadline - CLEANUP_RESERVE
    if operation_deadline <= time.monotonic():
        raise TimeoutError("IPC请求没有足够期限")
    helper = _Helper(helper_command, environ, operation_deadline)
    try:
        helper.configure({"mode": "client", "endpoint": pipe_name, "capability": capability.hex(),
                          "payload": payload, "expected_server_pid": expected_server_pid,
                          "deadline": operation_deadline}, operation_deadline)
        value = helper.take(operation_deadline)
        if value.get("kind") != "result" or not isinstance(value.get("payload"), dict):
            raise IPCError("IPC helper响应无效")
        return cast(dict[str, Any], value["payload"])
    finally:
        helper.close(deadline)


