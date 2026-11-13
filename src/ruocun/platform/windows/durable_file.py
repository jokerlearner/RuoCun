"""Windows 原子文件发布、私有 DACL 与目录同步（NEW-03 / REC-12 / MM-591）。

依据（独立来源，不从 Python 当前实现倒推）：
- ``09-storage-extension-route.md`` ``# SQLite及文件路线``：私有父目录 →
  同目录唯一临时文件 → 完整写入/flush → 同卷 ``os.replace`` → 平台目录同步与
  状态记录；权限/同步失败不降级成成功；replace 前失败保旧；replace 已发生而
  后续同步失败必须报告「发布已可见、持久确认未完成」，不伪报未执行或盲删候选；
  Windows 用显式 DACL/真实 ACL 读回，不以 chmod 数字代替。
- ``18-windows-durable-io-experiment.md`` / d18-accepted-review：共享占用与
  ACL 拒绝都可能表现为错误 5；目录 RW 句柄 flush 有本机证据；无断电保证。
- 冻结 ``src/session/durable_file.ts``：``wx`` 唯一临时、完整写入 + fsync、
  rename、父目录 fsync；其 POSIX ``open(dir)+fsync`` 在 Windows 返回 EACCES，
  不能直接照抄，故这里用 Win32 ``CreateFileW`` + ``FlushFileBuffers``。

新目录以当前用户 SID 的受保护、可继承 DACL 创建；已有目录只验证不修改。
目录同步使用可写目录句柄；仅 GENERIC_READ 在 D18 实验中返回错误 5。

runner 文件与 session DB 是两个原子域；本模块不宣称跨文件分布式原子性，
也不承诺断电不丢（无断电实证）。
"""

from __future__ import annotations

import ctypes as _C
import os
import re
import sys
import uuid
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from ..file_contract import (
    AtomicFileError,
    DurabilityUnconfirmedError,
    PublishReceipt,
)

_SDDL_REVISION_1 = 1
_SE_FILE_OBJECT = 1
_DACL_SECURITY_INFORMATION = 0x4
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_FILE_SHARE_ALL = 0x1 | 0x2 | 0x4
_OPEN_EXISTING = 3


class PublishDurabilityError(DurabilityUnconfirmedError):
    """发布已可见、持久确认未完成；保留结构化回执供上层如实报告。"""

    def __init__(self, receipt: PublishReceipt, message: str) -> None:
        super().__init__(message)
        self.receipt = receipt


class AtomicPublishPreReplaceError(AtomicFileError):
    """Pre-replace failure with explicit temporary-file cleanup outcome."""

    def __init__(
        self, retained_path: str | None, cleanup_error: BaseException | None,
        replacement_uncertain: bool, publish_receipt: PublishReceipt | None,
    ) -> None:
        message = "文件发布未确认；原错误保留在异常原因。"
        if retained_path is not None:
            message += " 临时材料清理失败，路径记录在 retained_path。"
        super().__init__(message)
        self.retained_path = retained_path
        self.cleanup_error = cleanup_error
        self.replacement_uncertain = replacement_uncertain
        self.publish_receipt = publish_receipt


def _advapi32() -> Any:
    return _C.WinDLL("Advapi32.dll", use_last_error=True)


def _local_free(handle: Any) -> None:
    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [_C.c_void_p]
    kernel.LocalFree.restype = _C.c_void_p
    kernel.LocalFree(_C.cast(handle, _C.c_void_p))


def _current_user_sid() -> str:
    from ctypes import wintypes as W

    kernel = _C.WinDLL("kernel32", use_last_error=True)
    adv = _advapi32()
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    adv.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, _C.POINTER(W.HANDLE)]
    adv.OpenProcessToken.restype = W.BOOL
    adv.GetTokenInformation.argtypes = [
        W.HANDLE, W.DWORD, _C.c_void_p, W.DWORD, _C.POINTER(W.DWORD)
    ]
    adv.GetTokenInformation.restype = W.BOOL
    adv.ConvertSidToStringSidW.argtypes = [_C.c_void_p, _C.POINTER(W.LPWSTR)]
    adv.ConvertSidToStringSidW.restype = W.BOOL
    token = W.HANDLE()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, _C.byref(token)):
        raise AtomicFileError("无法读取当前用户身份。")
    try:
        size = W.DWORD()
        adv.GetTokenInformation(token, 1, None, 0, _C.byref(size))
        if not size.value:
            raise AtomicFileError("无法读取当前用户 SID 长度。")
        data = _C.create_string_buffer(size.value)
        if not adv.GetTokenInformation(token, 1, data, size.value, _C.byref(size)):
            raise AtomicFileError("无法读取当前用户 SID。")
        sid_ptr = _C.cast(data, _C.POINTER(_C.c_void_p))[0]
        text = W.LPWSTR()
        if not adv.ConvertSidToStringSidW(sid_ptr, _C.byref(text)):
            raise AtomicFileError("无法转换当前用户 SID。")
        try:
            return str(text.value)
        finally:
            _local_free(text)
    finally:
        kernel.CloseHandle(token)


def _local_absolute_path(path: Path) -> Path:
    name = str(path)
    if name.startswith("\\\\?\\"):
        if not re.match(r"^\\\\\?\\[A-Za-z]:\\", name):
            raise AtomicFileError("不能在网络或不确定的路径启用私密持久化。")
        name = name[4:]
    absolute = Path(os.path.abspath(name))
    if not re.fullmatch(r"[A-Za-z]:", absolute.drive):
        raise AtomicFileError("不能在网络或不确定的路径启用私密持久化。")
    return absolute


def local_path(path: Path) -> Path:
    """Keep short local paths unchanged; use extended DOS names beyond MAX_PATH.

    This is only a name conversion. Fixed-volume, reparse and private ACL
    verification remain mandatory at the actual I/O boundary.
    """
    absolute = _local_absolute_path(path)
    if len(str(absolute).encode("utf-16-le")) // 2 >= 248:
        return Path("\\\\?\\" + str(absolute))
    return absolute


def _assert_safe_path(path: Path) -> None:
    """Reject network volumes and existing reparse components before use."""
    absolute = _local_absolute_path(path)
    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.GetDriveTypeW.argtypes = [_C.c_wchar_p]
    kernel.GetDriveTypeW.restype = _C.c_uint
    if kernel.GetDriveTypeW(absolute.anchor) != 3:  # DRIVE_FIXED
        raise AtomicFileError("不能在非固定本地卷启用私密持久化。")
    for part in (absolute, *absolute.parents):
        try:
            info = local_path(part).lstat()
        except FileNotFoundError:
            continue
        if getattr(info, "st_file_attributes", 0) & 0x400:
            raise AtomicFileError("路径包含重解析点，拒绝私密持久化。")


def _read_acl_sddl(path: Path) -> str:
    from ctypes import wintypes as W

    adv = _advapi32()
    adv.GetNamedSecurityInfoW.argtypes = [
        W.LPCWSTR, _C.c_int, _C.c_uint, _C.c_void_p, _C.c_void_p,
        _C.POINTER(_C.c_void_p), _C.c_void_p, _C.POINTER(_C.c_void_p),
    ]
    adv.GetNamedSecurityInfoW.restype = W.DWORD
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        _C.c_void_p, _C.c_uint, _C.c_uint, _C.POINTER(W.LPWSTR),
        _C.POINTER(_C.c_ulong),
    ]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = W.BOOL
    security, dacl = _C.c_void_p(), _C.c_void_p()
    status = adv.GetNamedSecurityInfoW(
        str(local_path(path)), _SE_FILE_OBJECT, _DACL_SECURITY_INFORMATION,
        None, None, _C.byref(dacl), None, _C.byref(security),
    )
    if status != 0 or not dacl.value:
        if security.value:
            _local_free(security)
        raise AtomicFileError(f"私有 DACL 读回失败（Win32 {status}）。")
    text = W.LPWSTR()
    try:
        if not adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(
            security, _SDDL_REVISION_1, _DACL_SECURITY_INFORMATION,
            _C.byref(text), None,
        ):
            raise AtomicFileError("私有 DACL 转换失败。")
        try:
            return str(text.value or "")
        finally:
            _local_free(text)
    finally:
        _local_free(security)


def _read_owner_sid(path: Path) -> str:
    """Read the file owner from Windows; do not infer owner from the DACL."""
    from ctypes import wintypes as W

    adv = _advapi32()
    adv.GetNamedSecurityInfoW.argtypes = [
        W.LPCWSTR, _C.c_int, _C.c_uint, _C.POINTER(_C.c_void_p),
        _C.c_void_p, _C.c_void_p, _C.c_void_p, _C.POINTER(_C.c_void_p),
    ]
    adv.GetNamedSecurityInfoW.restype = W.DWORD
    adv.ConvertSidToStringSidW.argtypes = [_C.c_void_p, _C.POINTER(W.LPWSTR)]
    adv.ConvertSidToStringSidW.restype = W.BOOL
    owner, security = _C.c_void_p(), _C.c_void_p()
    status = adv.GetNamedSecurityInfoW(
        str(local_path(path)), _SE_FILE_OBJECT, 1, _C.byref(owner), None, None, None,
        _C.byref(security),
    )
    if status != 0 or not owner.value:
        if security.value:
            _local_free(security)
        raise AtomicFileError(f"读取对象所有者失败（Win32 {status}）。")
    text = W.LPWSTR()
    try:
        if not adv.ConvertSidToStringSidW(owner, _C.byref(text)):
            raise AtomicFileError("转换对象所有者 SID 失败。")
        try:
            return str(text.value or "")
        finally:
            _local_free(text)
    finally:
        _local_free(security)


def _assert_private_acl(path: Path, *, directory: bool) -> str:
    """Verify protected, exact current-user ACL and directory inheritance."""
    _assert_safe_path(path)
    sddl = _read_acl_sddl(path)
    sid = _current_user_sid()
    if _read_owner_sid(path) != sid:
        raise AtomicFileError("对象所有者不是当前用户，拒绝私密持久化。")
    aces = re.findall(r"\(([^()]*)\)", sddl)
    if len(aces) != 1:
        raise AtomicFileError("私有 DACL 存在额外或缺失的访问主体。")
    fields = aces[0].split(";")
    if len(fields) != 6 or fields[0] != "A" or fields[2] != "FA" or fields[5] != sid:
        raise AtomicFileError("私有 DACL 与当前用户完整权限不一致。")
    flags = fields[1]
    if directory:
        if not sddl.startswith("D:P") or "OI" not in flags or "CI" not in flags:
            raise AtomicFileError("私有目录缺少受保护或可继承 DACL。")
    elif flags not in ("", "ID"):
        raise AtomicFileError("私有文件继承标志无效。")
    return sddl


def _ensure_private_dir_unpinned(path: Path) -> str:
    """Create a private directory, or verify an existing one without editing it."""
    if sys.platform != "win32":
        raise AtomicFileError("私有 DACL 仅在 Windows 已验证。")
    from ctypes import wintypes as W

    path = local_path(path)
    _assert_safe_path(path)
    if path.exists():
        if not path.is_dir():
            raise AtomicFileError("私有目录路径不是目录。")
        return _assert_private_acl(path, directory=True)
    if not path.parent.is_dir():
        raise AtomicFileError("私有目录的父目录不存在；不会递归接管已有目录。")

    class SecurityAttributes(_C.Structure):
        _fields_ = [("nLength", W.DWORD), ("lpSecurityDescriptor", _C.c_void_p),
                    ("bInheritHandle", W.BOOL)]

    adv = _advapi32()
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        W.LPCWSTR, W.DWORD, _C.POINTER(_C.c_void_p), _C.POINTER(W.DWORD)
    ]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = W.BOOL
    descriptor = _C.c_void_p()
    sddl = f"D:P(A;OICI;FA;;;{_current_user_sid()})"
    if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl, _SDDL_REVISION_1, _C.byref(descriptor), None
    ):
        raise AtomicFileError("无法构造私有目录安全描述符。")
    try:
        kernel = _C.WinDLL("kernel32", use_last_error=True)
        kernel.CreateDirectoryW.argtypes = [W.LPCWSTR, _C.POINTER(SecurityAttributes)]
        kernel.CreateDirectoryW.restype = W.BOOL
        attrs = SecurityAttributes(_C.sizeof(SecurityAttributes), descriptor, False)
        if not kernel.CreateDirectoryW(str(path), _C.byref(attrs)):
            error = _C.get_last_error()
            if error != 183:  # A racing creator: verify its result without modifying it.
                raise AtomicFileError(f"无法创建私有目录（Win32 {error}）。")
    finally:
        _local_free(descriptor)
    return _assert_private_acl(path, directory=True)


def _kernel() -> Any:
    from ctypes import wintypes as W

    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        W.LPCWSTR, W.DWORD, W.DWORD, _C.c_void_p, W.DWORD, W.DWORD, W.HANDLE,
    ]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    kernel.GetFileInformationByHandleEx.argtypes = [W.HANDLE, _C.c_int, _C.c_void_p, W.DWORD]
    kernel.GetFileInformationByHandleEx.restype = W.BOOL
    return kernel


def _open_plain_file(path: Path, *, create_guard: bool) -> Any:
    """Atomically reject reparses while opening an absolute local NT name.

    OBJECT_ATTRIBUTES/UNICODE_STRING/IO_STATUS_BLOCK follow the documented
    native ABI with natural alignment. RootDirectory is NULL: no relative
    create or rename, variable-layout name structure, or native asynchronous
    buffer is used. No caller content is written by this function.
    """
    from ctypes import wintypes as W

    class UnicodeString(_C.Structure):
        _fields_ = [("Length", W.USHORT), ("MaximumLength", W.USHORT), ("Buffer", W.LPWSTR)]

    class ObjectAttributes(_C.Structure):
        _fields_ = [
            ("Length", W.ULONG), ("RootDirectory", W.HANDLE),
            ("ObjectName", _C.POINTER(UnicodeString)), ("Attributes", W.ULONG),
            ("SecurityDescriptor", _C.c_void_p), ("SecurityQualityOfService", _C.c_void_p),
        ]

    class StatusUnion(_C.Union):
        _fields_ = [("Status", W.LONG), ("Pointer", _C.c_void_p)]

    class IoStatusBlock(_C.Structure):
        _fields_ = [("Result", StatusUnion), ("Information", _C.c_size_t)]

    if sys.platform != "win32" or (
        _C.sizeof(_C.c_void_p), _C.sizeof(UnicodeString),
        _C.sizeof(ObjectAttributes), _C.sizeof(IoStatusBlock),
        ObjectAttributes.ObjectName.offset, ObjectAttributes.Attributes.offset,
    ) != (8, 16, 48, 16, 16, 24):
        raise AtomicFileError("原生私密文件端口只接受已核验的 Windows x64 ABI。")
    _assert_safe_path(path)
    absolute = _local_absolute_path(path)
    name = "\\??\\" + str(absolute)
    encoded_length = len(name.encode("utf-16-le"))
    if encoded_length > 65530:
        raise AtomicFileError("私密文件路径超出原生名称长度。")
    buffer = _C.create_unicode_buffer(name)
    unicode_name = UnicodeString(encoded_length, encoded_length + 2, _C.cast(buffer, W.LPWSTR))
    attributes = ObjectAttributes(
        _C.sizeof(ObjectAttributes), None, _C.pointer(unicode_name),
        0x40 | 0x1000, None, None,  # OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE
    )
    status_block = IoStatusBlock()
    handle = W.HANDLE()
    native = _C.WinDLL("ntdll", use_last_error=True)
    native.NtCreateFile.argtypes = [
        _C.POINTER(W.HANDLE), W.DWORD, _C.POINTER(ObjectAttributes),
        _C.POINTER(IoStatusBlock), _C.c_void_p, W.ULONG, W.ULONG, W.ULONG,
        W.ULONG, _C.c_void_p, W.ULONG,
    ]
    native.NtCreateFile.restype = W.LONG
    # FILE_READ_DATA participates in sharing checks; attributes-only opens do
    # not protect against another handle deleting the anchor. No data is read.
    access = 0x100000 | 0x80 | 1 | (0x10000 if create_guard else 0)
    options = 0x20 | 0x40 | 0x200000 | (0x1000 if create_guard else 0)
    status = native.NtCreateFile(
        _C.byref(handle), access, _C.byref(attributes), _C.byref(status_block),
        None, 0x80, 1 if create_guard else 3, 2 if create_guard else 1,
        options, None, 0,
    )
    if (
        status != 0 or status_block.Result.Status != 0
        or status_block.Information != (2 if create_guard else 1)
        or not handle.value
    ):
        if handle.value:
            _kernel().CloseHandle(handle)
        raise AtomicFileError(f"私密文件原子打开被拒绝（NTSTATUS {status & 0xffffffff:08x}）。")
    return handle


def _open_directory_pin(
    path: Path, *, exclusive_write: bool = False, readonly: bool = False,
) -> Any:
    """Open the final component itself; never follow a reparse point."""
    kernel = _kernel()
    access = _GENERIC_READ | _GENERIC_WRITE if exclusive_write else 0x80
    sharing = 1 if exclusive_write or readonly else 1 | 2  # never FILE_SHARE_DELETE
    handle = kernel.CreateFileW(
        str(local_path(path)), access, sharing, None, _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | 0x00200000, None,
    )
    if handle in (None, 0, _C.c_void_p(-1).value):
        raise AtomicFileError(f"无法固定私密目录边界（Win32 {_C.get_last_error()}）。")
    attributes = (_C.c_ulong * 2)()
    if not kernel.GetFileInformationByHandleEx(handle, 9, attributes, _C.sizeof(attributes)):
        error = _C.get_last_error()
        kernel.CloseHandle(handle)
        raise AtomicFileError(f"无法核验目录句柄（Win32 {error}）。")
    if not attributes[0] & 0x10 or attributes[0] & 0x400:
        kernel.CloseHandle(handle)
        raise AtomicFileError("目录句柄不是普通目录，拒绝重解析点。")
    return handle


class PrivateDirectory:
    """Keep a validated namespace stable for the complete I/O lifetime.

    Each ancestor denies DELETE sharing. An unremovable empty guard keeps the
    final directory nonempty, so FSCTL_SET_REPARSE_POINT cannot turn it into a
    junction. Atomic OBJ_DONT_REPARSE name parsing closes the empty-to-guard
    window. Readonly mode instead holds a required existing file. No relative
    creation or native rename structures are involved.
    """

    def __init__(
        self, path: Path, *, readonly: bool = False, anchor_file: str | None = None,
    ) -> None:
        self.path = local_path(path)
        self.acl = ""
        self._handles: list[Any] = []
        self._guard: Any = None
        self._readonly = readonly
        self._anchor_file = anchor_file

    def __enter__(self) -> "PrivateDirectory":
        _assert_safe_path(self.path)
        try:
            for ancestor in reversed(self.path.parents):
                self._handles.append(_open_directory_pin(ancestor))
            if self._readonly:
                self._handles.append(_open_directory_pin(self.path, readonly=True))
                if (
                    self._anchor_file is None
                    or not re.fullmatch(r"[\w.-]+", self._anchor_file)
                    or self._anchor_file in (".", "..")
                ):
                    raise AtomicFileError("只读目录必须指定一个已存在的普通文件锚。")
                anchor = self.path / self._anchor_file
                self._handles.append(_open_plain_file(anchor, create_guard=False))
                self.acl = _assert_private_acl(self.path, directory=True)
                verify_private_file(anchor)
                return self
            _ensure_private_dir_unpinned(self.path)
            self._handles.append(_open_directory_pin(self.path))
            self.acl = _assert_private_acl(self.path, directory=True)
            guard = self.path / f".ruocun-guard-{uuid.uuid4().hex}.tmp"
            self._guard = _open_plain_file(guard, create_guard=True)
            _assert_safe_path(self.path)
            return self
        except BaseException as error:
            try:
                self.close()
            except AtomicFileError as close_error:
                error.directory_close_error = close_error  # type: ignore[attr-defined]
            raise

    def close(self) -> None:
        kernel = _kernel()
        errors: list[int] = []
        if self._guard is not None:
            if not kernel.CloseHandle(self._guard):
                errors.append(_C.get_last_error())
            else:
                self._guard = None
        retained: list[Any] = []
        for handle in reversed(self._handles):
            if not kernel.CloseHandle(handle):
                errors.append(_C.get_last_error())
                retained.append(handle)
        self._handles = list(reversed(retained))
        if errors:
            raise AtomicFileError(f"目录边界句柄关闭未确认（Win32 {errors}）。")

    def __exit__(self, _kind: object, error: BaseException | None, _trace: object) -> None:
        try:
            self.close()
        except AtomicFileError as close_error:
            if error is None:
                raise
            error.directory_close_error = close_error  # type: ignore[attr-defined]


def ensure_private_dir(path: Path) -> str:
    """Create/verify without taking over an existing directory's ACL."""
    with PrivateDirectory(path) as directory:
        return directory.acl


def verify_private_file(path: Path) -> str:
    """Reject reparse, non-files, hardlink aliases and non-private ACLs."""
    path = local_path(path)
    _assert_safe_path(path)
    info = path.lstat()
    if not path.is_file() or info.st_nlink != 1:
        raise AtomicFileError("私密文件不是单一链接的普通文件。")
    return _assert_private_acl(path, directory=False)

def sync_directory(path: Path) -> str:
    """Win32 目录 RW 句柄 FlushFileBuffers；失败由调用方升级为「持久确认未完成」。

    本机实测：仅 GENERIC_READ 的目录句柄 FlushFileBuffers 返回错误 5；
    GENERIC_READ|GENERIC_WRITE 返回成功。这是本机事实，不推广为断电保证。
    """
    if sys.platform != "win32":
        raise AtomicFileError("目录同步仅在 Windows 已验证。")
    from ctypes import wintypes as W

    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        W.LPCWSTR, W.DWORD, W.DWORD, _C.c_void_p, W.DWORD, W.DWORD, W.HANDLE
    ]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.FlushFileBuffers.argtypes = [W.HANDLE]
    kernel.FlushFileBuffers.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    handle = kernel.CreateFileW(
        str(local_path(path)), _GENERIC_READ | _GENERIC_WRITE, _FILE_SHARE_ALL, None,
        _OPEN_EXISTING, _FILE_FLAG_BACKUP_SEMANTICS, None,
    )
    invalid = _C.c_void_p(-1).value
    if handle is None or handle in (0, invalid):
        raise AtomicFileError(
            f"无法以目录 RW 句柄打开父目录（Win32 {_C.get_last_error()}）。"
        )
    try:
        if not kernel.FlushFileBuffers(handle):
            raise AtomicFileError(
                f"目录 FlushFileBuffers 失败（Win32 {_C.get_last_error()}）。"
            )
    finally:
        kernel.CloseHandle(handle)
    return "win32:CreateFileW(GENERIC_READ|GENERIC_WRITE,FILE_FLAG_BACKUP_SEMANTICS)+FlushFileBuffers"


def atomic_publish(
    file: Path,
    data: bytes | Iterable[bytes],
    *,
    require_durability: bool = True,
    sync_directory_fn: Callable[[Path], str] | None = None,
) -> PublishReceipt:
    """原子发布：私有父目录 → 唯一临时 → 完整写入/flush → os.replace → 目录同步。

    - replace 前任何失败：删除临时文件、保留旧文件、抛 AtomicFileError。
    - replace 已发生而目录同步/ACL 失败：报告「发布已可见、持久确认未完成」，
      不伪报未执行、不删除已发布候选；require_durability=True 时抛
      PublishDurabilityError 并附带结构化回执。
    - ``sync_directory_fn`` 是登记过的测试故障注入 seam（仅显式传参可达），
      缺省使用真实 Win32 目录同步；不通过隐藏全局变量改写产品行为。
    """
    with PrivateDirectory(file.parent) as directory:
        return _atomic_publish_pinned(
            file.absolute(), data, directory.acl,
            require_durability=require_durability,
            sync_directory_fn=sync_directory_fn,
        )


def _atomic_publish_pinned(
    file: Path, data: bytes | Iterable[bytes], acl: str, *, require_durability: bool,
    sync_directory_fn: Callable[[Path], str] | None,
) -> PublishReceipt:
    parent = file.parent
    _assert_safe_path(file)
    tmp = parent / f".{file.name}.{uuid.uuid4().hex}.tmp"
    fd = -1
    created = False
    replacement_attempted = False
    written = 0
    try:
        fd = os.open(local_path(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        created = True
        # Verify inherited private ACL before writing any sensitive bytes.
        _assert_private_acl(tmp, directory=False)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            for chunk in (data,) if isinstance(data, bytes) else data:
                stream.write(chunk)
                written += len(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        replacement_attempted = True
        os.replace(local_path(tmp), local_path(file))
    except BaseException as exc:
        close_error: BaseException | None = None
        if fd != -1:
            try:
                os.close(fd)
            except BaseException as close_exc:
                close_error = close_exc
        retained_path: str | None = None
        cleanup_error: BaseException | None = close_error
        if created:
            try:
                local_path(tmp).unlink()
            except FileNotFoundError:
                pass
            except BaseException as cleanup_exc:
                retained_path = str(tmp)
                cleanup_error = cleanup_exc
        receipt = None
        if replacement_attempted:
            receipt = PublishReceipt(
                file=str(file), tmp_file=str(tmp), replaced=None,
                durability="unconfirmed", bytes_written=written,
                directory_sync="not confirmed",
                note="替换调用未返回，发布结果未知；不得假设旧值仍在。",
            )
        if not isinstance(exc, Exception):
            exc.retained_path = retained_path  # type: ignore[attr-defined]
            exc.cleanup_error = cleanup_error  # type: ignore[attr-defined]
            exc.replacement_uncertain = replacement_attempted  # type: ignore[attr-defined]
            exc.publish_receipt = receipt  # type: ignore[attr-defined]
            raise
        raise AtomicPublishPreReplaceError(
            retained_path, cleanup_error, replacement_attempted, receipt
        ) from exc

    # replace 已完成：从这里开始只能是「发布已可见」或「持久确认完成」。
    sync_fn = sync_directory_fn or sync_directory
    try:
        sync_note = sync_fn(parent)
        file_acl = _assert_private_acl(file, directory=False)
    except BaseException as exc:
        receipt = PublishReceipt(
            file=str(file),
            tmp_file=str(tmp),
            replaced=True,
            durability="unconfirmed",
            bytes_written=written,
            directory_sync="failed",
            note="发布已可见、持久确认未完成；不伪报未执行、不盲删候选。",
        )
        if not isinstance(exc, Exception):
            # Preserve cancellation/system-exit identity, while making the
            # already-visible publication discoverable to the caller.
            exc.publish_receipt = receipt  # type: ignore[attr-defined]
            raise
        if require_durability:
            raise PublishDurabilityError(
                receipt, "发布已可见、持久确认未完成（同步/ACL 失败）。"
            ) from exc
        return receipt

    return PublishReceipt(
        file=str(file),
        tmp_file=str(tmp),
        replaced=True,
        durability="confirmed",
        bytes_written=written,
        directory_sync=f"{sync_note}; parent_acl={acl}; file_acl={file_acl}",
        note="原子替换与目录持久确认完成；不承诺断电不丢。",
    )


__all__ = [
    "PublishDurabilityError",
    "AtomicPublishPreReplaceError",
    "ensure_private_dir",
    "sync_directory",
    "atomic_publish",
    "PrivateDirectory",
    "verify_private_file",
    "local_path",
]
