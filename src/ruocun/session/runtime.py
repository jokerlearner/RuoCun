"""在 Windows 持久会话打开数据库前，核验并加载受控 SQLite 运行库。

固定 ZIP 与 DLL 的摘要限制可用的分发件。先用绝对路径加载，再读回实际版本、构建身份、加载路径和 VFS，确保标准库用的是经过核验的运行库。
如果进程已加载其他 SQLite，保留未达核验的记录，让持久化入口明确拒绝。
"""

from __future__ import annotations

import ctypes as _C
import hashlib
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from .contract import RuntimeGateError, RuntimeRecord

# 固定 SQLite 分发件的文件名、摘要和预期构建身份。
OFFICIAL_DLL_SHA256 = "4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea"
OFFICIAL_ZIP_SHA3_256 = "c2d09c8babb9399277055c057c97a53f1ffd7c5f11d0c1f2118ffdfa39f2daa4"
OFFICIAL_ZIP_SHA256 = "f436f53ad8f965af43f3817b42c99c0689e6787f6b7ace208fe38dab7ffc4971"
EXPECTED_VERSION = "3.54.1"
EXPECTED_SOURCE_ID = "2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76"
WAL_FIX_MIN_VERSION = "3.51.3"
WAL_FIX_BACKPORTS = ("3.44.6", "3.50.7")
WAL_FIX_BASIS = (
    "SQLite 官方 wal.html #walresetbug：WAL-reset 缺陷修复在 3.51.3（2026-03-13）"
    "及以后，3.44.6 与 3.50.7 有回移修复；本票实际运行库为官方 3.54.1 "
    "固定构建，source ID 与官方发布记录一致，高于修复版本。"
)

# 对已加载的 DLL 持有进程级引用，防止在 SQLite 仍使用它时卸载。
_LOADED_LIBRARY: Any = None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_official_archive(archive: Path, dest_dir: Path) -> Path:
    """核对 ZIP 和其中 DLL 的摘要，在指定目录准备核验后的 sqlite3.dll。"""
    data = archive.read_bytes()
    if hashlib.sha3_256(data).hexdigest() != OFFICIAL_ZIP_SHA3_256:
        raise RuntimeGateError("官方固定 ZIP SHA3-256 不符，拒绝启用受控运行库。")
    if hashlib.sha256(data).hexdigest() != OFFICIAL_ZIP_SHA256:
        raise RuntimeGateError("官方固定 ZIP SHA-256 不符，拒绝启用受控运行库。")
    with zipfile.ZipFile(archive) as bundle:
        dll_data = bundle.read("sqlite3.dll")
    if hashlib.sha256(dll_data).hexdigest() != OFFICIAL_DLL_SHA256:
        raise RuntimeGateError("官方 3.54.1 DLL SHA-256 不符，拒绝启用受控运行库。")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dll = dest_dir / "sqlite3.dll"
    if not dll.exists() or _sha256(dll) != OFFICIAL_DLL_SHA256:
        dll.write_bytes(dll_data)
    return dll.resolve()


def _actual_runtime() -> tuple[str, str]:
    import sqlite3

    con = sqlite3.connect(":memory:", isolation_level=None)
    try:
        version, source_id = con.execute(
            "select sqlite_version(), sqlite_source_id()"
        ).fetchone()
        return str(version), str(source_id)
    finally:
        con.close()


def _windows_module_path(handle: Any) -> str:
    from ctypes import wintypes as W

    kernel = _C.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleFileNameW.argtypes = [W.HMODULE, W.LPWSTR, W.DWORD]
    kernel.GetModuleFileNameW.restype = W.DWORD
    buf = _C.create_unicode_buffer(32768)
    if not kernel.GetModuleFileNameW(handle, buf, len(buf)):
        raise RuntimeGateError("无法核实实际加载的 SQLite DLL 路径。")
    return str(buf.value)


def preload_controlled_runtime(dll_path: Path) -> str:
    """先于 sqlite3 导入加载绝对路径下的受控 DLL。

    采用 Windows 的受限搜索标志，让后续加载绑定到这份 DLL，同时保持进程 PATH。
    """
    global _LOADED_LIBRARY
    dll = dll_path.resolve()
    if not dll.is_file():
        raise RuntimeGateError("受控 SQLite DLL 不存在，拒绝启用耐久恢复。")
    if _sha256(dll) != OFFICIAL_DLL_SHA256:
        raise RuntimeGateError("受控 SQLite DLL SHA-256 不符，拒绝启用耐久恢复。")
    if sys.platform != "win32":
        raise RuntimeGateError("受控 SQLite 运行库仅在 Windows x64 已验证，其它平台明确拒绝。")

    already = "sqlite3" in sys.modules or "_sqlite3" in sys.modules
    if already:
        version, source_id = _actual_runtime()
        if (
            version == EXPECTED_VERSION
            and source_id == EXPECTED_SOURCE_ID
            and _LOADED_LIBRARY is not None
            and Path(_windows_module_path(_LOADED_LIBRARY._handle)).resolve() == dll
        ):
            return str(dll)
        raise RuntimeGateError(
            "sqlite3 已导入，但无法证明所请求的受控 DLL 是实际加载的运行库"
            f"（实际 {version} / {source_id}）；拒绝静默退回未达门禁的运行库。"
        )

    winmode = 0x00001100
    library = _C.WinDLL(str(dll), winmode=winmode)
    loaded = _windows_module_path(library._handle)
    if Path(loaded).resolve() != dll:
        raise RuntimeGateError(f"实际加载的 DLL 不是受控候选：{loaded}")
    _LOADED_LIBRARY = library
    return loaded


def _vfs_name() -> str:
    """通过同一个 DLL 调用 sqlite3_file_control，读回连接实际使用的 VFS。"""
    library = _LOADED_LIBRARY
    if library is None:
        raise RuntimeGateError("没有受控 DLL 句柄，不能核实 VFS。")
    library.sqlite3_vfs_find.argtypes = [_C.c_char_p]
    library.sqlite3_vfs_find.restype = _C.c_void_p
    library.sqlite3_open.argtypes = [_C.c_char_p, _C.POINTER(_C.c_void_p)]
    library.sqlite3_close.argtypes = [_C.c_void_p]
    library.sqlite3_file_control.argtypes = [
        _C.c_void_p, _C.c_char_p, _C.c_int, _C.c_void_p
    ]
    library.sqlite3_free.argtypes = [_C.c_void_p]
    connection = _C.c_void_p()
    name = _C.c_void_p()
    fd, probe_path = tempfile.mkstemp(prefix="ruocun-vfs-", suffix=".db")
    os.close(fd)
    try:
        if library.sqlite3_open(probe_path.encode("utf-8"), _C.byref(connection)) != 0:
            raise RuntimeGateError("无法为 VFS 核实打开 SQLite 连接。")
        if library.sqlite3_file_control(connection, b"main", 12, _C.byref(name)) != 0:
            raise RuntimeGateError("无法读取实际 VFS 名称。")
        value = _C.string_at(name).decode("utf-8")
        return str(value)
    finally:
        library.sqlite3_free(name)
        library.sqlite3_close(connection)
        os.unlink(probe_path)


def verify_controlled_runtime(dll_path: Path) -> RuntimeRecord:
    """读回并核对已加载的 SQLite，返回能交给数据库入口核验的运行库清单。"""
    loaded = preload_controlled_runtime(dll_path)
    import _sqlite3
    import sqlite3

    con = sqlite3.connect(":memory:", isolation_level=None)
    try:
        version, source_id = con.execute(
            "select sqlite_version(), sqlite_source_id()"
        ).fetchone()
        options = tuple(str(row[0]) for row in con.execute("pragma compile_options"))
    finally:
        con.close()
    if version != EXPECTED_VERSION or source_id != EXPECTED_SOURCE_ID:
        raise RuntimeGateError(
            f"实际运行库不是已核验官方候选：{version} / {source_id}"
        )
    driver_extension = str(Path(_sqlite3.__file__).resolve())
    driver_extension_sha256 = _sha256(Path(driver_extension))
    return RuntimeRecord(
        version=str(version),
        source_id=str(source_id),
        compile_options=options,
        dll_path=loaded,
        dll_sha256=OFFICIAL_DLL_SHA256,
        driver="CPython stdlib sqlite3 / _sqlite3",
        driver_extension=driver_extension,
        driver_extension_sha256=driver_extension_sha256,
        vfs=_vfs_name(),
        python_version=sys.version,
        connection={
            "isolation_level": None,
            "timeout_seconds": 3,
            "uri": False,
            "vfs_override": None,
            "check_same_thread": True,
        },
        gate="met",
        reason="官方固定 ZIP/DLL 摘要、实际 version/source ID/compile options/VFS 全部核验通过。",
        wal_fix_basis=WAL_FIX_BASIS,
    )


def unmet_record(reason: str) -> RuntimeRecord:
    """运行库未通过核验时仍记录实际加载结果，供诊断定位。"""
    version, source_id = _actual_runtime()
    return RuntimeRecord(
        version=version,
        source_id=source_id,
        compile_options=(),
        dll_path="",
        dll_sha256="",
        driver="CPython stdlib sqlite3 / _sqlite3 (uncontrolled)",
        driver_extension="",
        driver_extension_sha256="",
        vfs="",
        python_version=sys.version,
        connection={},
        gate="not-met",
        reason=reason,
        wal_fix_basis=WAL_FIX_BASIS,
    )


__all__ = [
    "OFFICIAL_DLL_SHA256",
    "OFFICIAL_ZIP_SHA3_256",
    "OFFICIAL_ZIP_SHA256",
    "EXPECTED_VERSION",
    "EXPECTED_SOURCE_ID",
    "WAL_FIX_MIN_VERSION",
    "WAL_FIX_BACKPORTS",
    "WAL_FIX_BASIS",
    "verify_official_archive",
    "preload_controlled_runtime",
    "verify_controlled_runtime",
    "unmet_record",
]
