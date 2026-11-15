"""经 Windows 凭据管理器读写若存账户的密钥。

上层配置给出服务名和账户名，本模块编码为精确的 TargetName，避免账户仅大小写不同就相互覆盖。
原生后端只接触指定条目，返回值区分系统保存成功、明确拒绝和结果未确认。超时后原生操作仍可能完成，上层据此决定是否可退回文件存储。
"""

from __future__ import annotations

import ctypes as C
import queue
import sys
import threading
import time
from ctypes import wintypes as W
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol

from ...config import credential as cred
from ...config.credential import SecretLookup, SecretStoreResult

NativeStatus = Literal[
    "ok", "not-found", "refused", "timeout-unconfirmed", "error-unconfirmed", "error"
]

# Windows CREDENTIALW 与 CRED_* 定义中的常量。
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168
_ERROR_ACCESS_DENIED = 5
_MAX_BLOB_BYTES = 2560  # 凭据数据块的最大字节数。



def targetName(service: str, account: str) -> str:
    """把服务名和账户名合成凭据管理器的键。

    账户按 UTF-8 转为小写十六进制，像 Profile 和 profile 这样的名称仍得到不同的编码。
    """
    return f"{service}/{account.encode('utf-8').hex()}"


@dataclass(frozen=True)
class NativeResult:
    """保留一次系统操作的状态和可用值，供调用方区分成功、拒绝和未确认。"""

    status: NativeStatus
    secret: bytes | None = field(default=None, repr=False)
    winerror: int | None = None


class CredentialBackend(Protocol):
    """抽象读、写、删三个原生操作，业务层可传入测试实现。"""

    def read(self, target: str) -> NativeResult: ...

    def write(self, target: str, secret: bytes) -> NativeResult: ...

    def delete(self, target: str) -> NativeResult: ...


@dataclass
class InjectedBackend:
    """用内存字典和显式结果覆盖模拟指定条目的读写删除。

    拒绝、超时和未知结果由各操作的 override 指定，测试无需访问机器上的凭据。
    """

    store: dict[str, bytes] = field(default_factory=dict, repr=False)
    read_override: NativeResult | None = None
    write_override: NativeResult | None = None
    delete_override: NativeResult | None = None
    calls: list[tuple[str, str]] = field(default_factory=list)

    def read(self, target: str) -> NativeResult:
        self.calls.append(("read", target))
        if self.read_override is not None:
            return self.read_override
        value = self.store.get(target)
        if value is None:
            return NativeResult("not-found", winerror=_ERROR_NOT_FOUND)
        return NativeResult("ok", value)

    def write(self, target: str, secret: bytes) -> NativeResult:
        self.calls.append(("write", target))
        if self.write_override is not None:
            return self.write_override
        self.store[target] = secret
        return NativeResult("ok")

    def delete(self, target: str) -> NativeResult:
        self.calls.append(("delete", target))
        if self.delete_override is not None:
            return self.delete_override
        self.store.pop(target, None)
        return NativeResult("ok")


class _Credential(C.Structure):
    _fields_ = [
        ("Flags", W.DWORD), ("Type", W.DWORD), ("TargetName", W.LPWSTR),
        ("Comment", W.LPWSTR), ("LastWritten", W.FILETIME),
        ("CredentialBlobSize", W.DWORD), ("CredentialBlob", C.c_void_p),
        ("Persist", W.DWORD), ("AttributeCount", W.DWORD),
        ("Attributes", C.c_void_p), ("TargetAlias", W.LPWSTR),
        ("UserName", W.LPWSTR),
    ]


def _classify(winerror: int) -> NativeStatus:
    """把 Win32 错误码映射为公开状态，明确的其它失败归为拒绝，允许上层使用文件。"""
    if winerror == _ERROR_NOT_FOUND:
        return "not-found"
    if winerror == _ERROR_ACCESS_DENIED:
        return "refused"
    return "refused"


class Win32CredentialBackend:
    """通过 ctypes 调用 Windows 凭据 API。

    读取后在 finally 中用 CredFree 释放 CREDENTIALW 指针，重复读取也不会积累原生内存。
    """

    def __init__(self) -> None:
        self._advapi = C.WinDLL("advapi32", use_last_error=True)
        self._write = self._bind("CredWriteW", W.BOOL, [C.POINTER(_Credential), W.DWORD])
        self._read = self._bind(
            "CredReadW", W.BOOL,
            [W.LPCWSTR, W.DWORD, W.DWORD, C.POINTER(C.POINTER(_Credential))],
        )
        self._delete = self._bind("CredDeleteW", W.BOOL, [W.LPCWSTR, W.DWORD, W.DWORD])
        self._free = self._bind("CredFree", None, [C.c_void_p])

    def _bind(self, name: str, restype: Any, argtypes: list[Any]) -> Any:
        fn = getattr(self._advapi, name)
        fn.restype = restype
        fn.argtypes = argtypes
        return fn

    def read(self, target: str) -> NativeResult:
        ptr = C.POINTER(_Credential)()
        ok = bool(self._read(target, _CRED_TYPE_GENERIC, 0, C.byref(ptr)))
        if not ok:
            code = C.get_last_error()
            return NativeResult(_classify(code), winerror=code)
        try:
            entry = ptr.contents
            data: bytes = C.string_at(entry.CredentialBlob, entry.CredentialBlobSize)
            return NativeResult("ok", data)
        finally:
            self._free(ptr)

    def write(self, target: str, secret: bytes) -> NativeResult:
        if len(secret) > _MAX_BLOB_BYTES:
            # 先检查字节数，避免把超过 Windows 数据块上限的请求送给写入 API。
            return NativeResult("refused", winerror=1783)
        blob = C.create_string_buffer(secret)
        entry = _Credential(
            Type=_CRED_TYPE_GENERIC, TargetName=target,
            CredentialBlobSize=len(secret), CredentialBlob=C.cast(blob, C.c_void_p),
            Persist=_CRED_PERSIST_LOCAL_MACHINE, UserName="ruocun-synthetic",
        )
        ok = bool(self._write(C.byref(entry), 0))
        if not ok:
            code = C.get_last_error()
            return NativeResult(_classify(code), winerror=code)
        return NativeResult("ok")

    def delete(self, target: str) -> NativeResult:
        ok = bool(self._delete(target, _CRED_TYPE_GENERIC, 0))
        if not ok:
            code = C.get_last_error()
            return NativeResult(_classify(code), winerror=code)
        return NativeResult("ok")


def isAvailable() -> bool:
    """仅在 Windows 上且能加载 advapi32 时使用系统凭据后端。"""
    if sys.platform != "win32":
        return False
    try:
        C.WinDLL("advapi32", use_last_error=True)
    except OSError:
        return False
    return True


def _as_lookup(result: NativeResult) -> SecretLookup:
    """把原生读取结果转成 SecretLookup，仅在找到合法 UTF-8 值时返回密钥。"""
    if result.status == "ok" and result.secret is not None:
        try:
            return SecretLookup("found", result.secret.decode("utf-8"))
        except UnicodeDecodeError:
            return SecretLookup("refused")
    if result.status == "ok":
        return SecretLookup("not-found")
    if result.status == "timeout-unconfirmed":
        return SecretLookup("timeout-unconfirmed")
    if result.status in ("error-unconfirmed", "error"):
        return SecretLookup("error-unconfirmed")
    if result.status == "not-found":
        return SecretLookup("not-found")
    return SecretLookup("refused")


def _as_store_result(result: NativeResult) -> SecretStoreResult:
    """把原生写入结果转成 SecretStoreResult，收到成功状态后才报告系统已保存。"""
    if result.status == "ok":
        return SecretStoreResult("system", "stored")
    if result.status == "timeout-unconfirmed":
        return SecretStoreResult("unknown", "timeout-unconfirmed")
    if result.status in ("error-unconfirmed", "error"):
        return SecretStoreResult("unknown", "error-unconfirmed")
    # 只有明确拒绝或条目不存在时才可退回文件，结果未确认时保留未知状态。
    return SecretStoreResult("file", "refused")


class WindowsCredentialStore:
    """把凭据后端的结果转换为配置层使用的状态。

    上层传入系统后端或测试后端。删除只操作当前服务和指定账户组成的键。
    """

    def __init__(self, backend: CredentialBackend, *, timeout_seconds: float = 8.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._backend = backend
        self._timeout_seconds = timeout_seconds
        self._in_flight = threading.Lock()
        self.last_lookup: SecretLookup | None = None

    def _call(self, operation: Callable[[], NativeResult]) -> NativeResult:
        """等待原生调用返回，超时后把结果标记为未确认。

        未返回的调用仍持有同一个执行槽，避免每次重试都创建新线程。调用发出后无法在此取消，迟到的写入结果也不会触发重放。
        """
        deadline = time.monotonic() + self._timeout_seconds
        if not self._in_flight.acquire(timeout=self._timeout_seconds):
            return NativeResult("timeout-unconfirmed")
        result_queue: queue.Queue[NativeResult] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                try:
                    result = operation()
                except Exception:
                    # 异常可能发生在系统操作完成后，此时只能报告结果未确认。
                    result = NativeResult("error-unconfirmed")
                result_queue.put(result)
            finally:
                self._in_flight.release()

        worker = threading.Thread(target=invoke, daemon=True, name="ruocun-credential")
        try:
            worker.start()
        except Exception:
            self._in_flight.release()
            return NativeResult("refused")
        try:
            return result_queue.get(timeout=max(0.0, deadline - time.monotonic()))
        except queue.Empty:
            return NativeResult("timeout-unconfirmed")

    def get(self, service: str, account: str) -> SecretLookup:
        if service != cred.NEW_KEYCHAIN_SERVICE:
            self.last_lookup = SecretLookup("refused")
            return self.last_lookup
        target = targetName(service, account)
        self.last_lookup = _as_lookup(self._call(lambda: self._backend.read(target)))
        return self.last_lookup

    def set(self, service: str, account: str, secret: str) -> SecretStoreResult:
        if service != cred.NEW_KEYCHAIN_SERVICE:
            raise ValueError("仅可写入若存凭据服务")
        target = targetName(service, account)
        return _as_store_result(self._call(
            lambda: self._backend.write(target, secret.encode("utf-8"))))

    def delete(self, service: str, account: str) -> None:
        if service != cred.NEW_KEYCHAIN_SERVICE:
            raise ValueError("仅可删除若存凭据服务中的条目")
        target = targetName(service, account)
        result = self._call(lambda: self._backend.delete(target))
        if result.status in ("timeout-unconfirmed", "error-unconfirmed", "error"):
            raise cred.CredentialWriteUnconfirmed("系统凭据删除结果未确认，请核对后再操作")
        if result.status not in ("ok", "not-found"):
            raise RuntimeError("系统凭据删除被拒绝")


