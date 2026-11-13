"""NEW-04 · Windows 系统凭据窄端口（R-14「凭据」/ WIN-05 / CFG-04）。

按 D09:152-156 与 ADR-0005 的唯一凭据契约：
- 新写服务 ``ruocun-api-key``、账户 ``ruocun/<profile原始名称>``；
- TargetName 以服务名及原账户 **UTF-8 hex** 编码，保留 ``Profile``/``profile``
  区别，不依赖系统 TargetName 大小写敏感（D17 已验证 Credential Manager
  的 TargetName 为大小写不敏感）；
- 准确区分 ``stored=system/file`` 与 ``not-found/refused/timeout-unconfirmed``；
  系统写结果不明不伪报已存；删除 RuoCun 账户不得删除旧服务 secret；
- 秘密不入日志/证据/输出，仅留状态、长度与 hash；不读、不复制、不展示
  任何真实现存密钥。

窄端口按 D17 ``experiments/windows/native.py`` 的 ctypes 候选封装
``CredWriteW/CredReadW/CredDeleteW/CredFree``（纯标准库，不引入未经验证的
keyring 自动 backend、不依赖 pywin32）；系统边界用可注入的窄端口 fake
确定性复现拒绝/超时/未知结果。普通入口按配置精确解析单个keyRef，不枚举其它账户。
真实验收仅操作本次新建合成TargetName，精确清理并回读1168。
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

# CREDENTIALW / CRED_*（D17 native.py、MSDN CREDENTIALW）。
_CRED_TYPE_GENERIC = 1
_CRED_PERSIST_LOCAL_MACHINE = 2
_ERROR_NOT_FOUND = 1168
_ERROR_ACCESS_DENIED = 5
_MAX_BLOB_BYTES = 2560  # D17 e/cred.json: 2560 成功、2561 真实拒绝



def targetName(service: str, account: str) -> str:
    """TargetName = 服务名 + "/" + 原账户 UTF-8 hex（小写、可逆、保留大小写）。

    D17 ``probe.py:24-26`` ``cred_target``；D09:152。hex 全为小写 ASCII，
    把原账户的大小写差异编码进字符本身，规避 Win32 TargetName 大小写不敏感
    造成的 ``Profile``/``profile`` 碰撞与互相覆盖。
    """
    return f"{service}/{account.encode('utf-8').hex()}"


@dataclass(frozen=True)
class NativeResult:
    """窄端口一次调用的结果；秘密字节不得写入日志或作为 repr 展示。"""

    status: NativeStatus
    secret: bytes | None = field(default=None, repr=False)
    winerror: int | None = None


class CredentialBackend(Protocol):
    """系统边界窄端口：只暴露三个 Win32 凭据操作，便于注入 fake。"""

    def read(self, target: str) -> NativeResult: ...

    def write(self, target: str, secret: bytes) -> NativeResult: ...

    def delete(self, target: str) -> NativeResult: ...


@dataclass
class InjectedBackend:
    """可注入窄端口 fake：内存字典 + 每操作结果覆盖，确定性复现边界。

    拒绝/超时/未知结果由 ``*_override`` 精确注入，不依赖系统状态、不碰
    真实 Credential Manager；用于产品自动测试，不冒充真实系统后端通过。
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
    """把 Win32 错误码归入 04 的状态集合；其它明确失败按 refused → file fallback。"""
    if winerror == _ERROR_NOT_FOUND:
        return "not-found"
    if winerror == _ERROR_ACCESS_DENIED:
        return "refused"
    return "refused"


class Win32CredentialBackend:
    """D17 已验证的 ctypes 窄端口：真实调用 CredWriteW/ReadW/DeleteW/CredFree。

    纯标准库，不依赖 pywin32，不引入未经验证的 keyring 自动 backend。
    所有读回的 ``CREDENTIALW*`` 在 finally 中 ``CredFree``，避免句柄/内存泄漏。
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
            # D17 实测 2561 字节被真实拒绝（本机 1783）；明确失败，不伪报已存。
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
    """平台与系统凭据 API 可用性：仅 win32 且 advapi32 可加载。

    冻结 ``keychain.ts:17-20`` 的平台可用性；不可用时按明确 file fallback，
    不静默当系统保存成功。
    """
    if sys.platform != "win32":
        return False
    try:
        C.WinDLL("advapi32", use_last_error=True)
    except OSError:
        return False
    return True


def _as_lookup(result: NativeResult) -> SecretLookup:
    """native 结果 → 04 的 SecretLookup；秘密只在 found 且合法 UTF-8 时带出。"""
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
    """native 结果 → 04 的 SecretStoreResult；只有确认 ok 才报 system/stored。"""
    if result.status == "ok":
        return SecretStoreResult("system", "stored")
    if result.status == "timeout-unconfirmed":
        return SecretStoreResult("unknown", "timeout-unconfirmed")
    if result.status in ("error-unconfirmed", "error"):
        return SecretStoreResult("unknown", "error-unconfirmed")
    # 明确 refused / not-found 才允许上层选择文件 fallback。
    return SecretStoreResult("file", "refused")


class WindowsCredentialStore:
    """实现 04 的 ``KeychainPort``：把窄端口 native 结果映射为公开状态。

    构造时注入 ``CredentialBackend``；真实路径传 ``Win32CredentialBackend``，
    测试/演示的确定性边界传 ``InjectedBackend``。delete 只对自己的精确
    TargetName 调用一次，不枚举其它账户、不删除旧服务 secret。
    """

    def __init__(self, backend: CredentialBackend, *, timeout_seconds: float = 8.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._backend = backend
        self._timeout_seconds = timeout_seconds
        self._in_flight = threading.Lock()
        self.last_lookup: SecretLookup | None = None

    def _call(self, operation: Callable[[], NativeResult]) -> NativeResult:
        """等待至多指定时间；超时不声称原生调用已停止或写入失败。

        尚未返回的原生调用持有本端口唯一执行槽，避免反复超时产生无界线程。
        不能取消 Win32 调用；迟到的写入结果始终视为未知，不自动重放。
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
                    # 后端可能先完成系统调用再抛错；不能据此声称明确拒绝。
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


