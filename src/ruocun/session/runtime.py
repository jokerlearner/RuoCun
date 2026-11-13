"""受控 SQLite 运行库门禁（REC-15 / MM-601 / NEW-03 相关）。

依据（均为已收录的独立来源，不从当前 Python 输出回填预期）：
- ``09-storage-extension-route.md`` ``# SQLite及文件路线``：固定供应源
  ``sqlite-dll-win-x64-3540100.zip``、官方 3.54.1 DLL SHA-256 与 source ID，
  WAL/FULL/busy_timeout、专属线程、缺库/hash 不符/旧库已加载/实际库不符明确失败。
- ``sqlite-runtime/candidate.json``：官方 ZIP SHA3-256、ZIP SHA-256、DLL SHA-256、
  expected_runtime、expected_source_id。
- ``sqlite-runtime/sources/wal.html`` ``#walresetbug``：官方 WAL-reset 修复在
  3.51.3 及以后，3.44.6 / 3.50.7 有回移修复；3.54.1 官方构建高于修复版本。
- D19 决策票与独立复核：CPython 3.11.9 x64 + stdlib + 该 DLL 为已验证候选；
  本机默认 3.45.1 不达产品门禁。

关键边界：
- 进程若在导入 ``sqlite3`` 之前预加载本 DLL，``_sqlite3`` 绑定到受控 3.54.1；
  若 ``sqlite3`` 已导入且实际库不是官方候选，明确拒绝（不静默退回 3.45.1）。
- 普通压力通过不作为修复证明；修复依据来自官方版本/构建来源与固定摘要。
- wheel / standalone / 仓库外产物的运行库清单属发布票（79-81 / D13），本票
  只覆盖开发期产品路径；不宣称全产物通过。
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

# 官方固定供应源（candidate.json / 09 报告）
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

# 预加载的 DLL 句柄必须活到进程结束，不能被 GC 提前 FreeLibrary。
_LOADED_LIBRARY: Any = None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_official_archive(archive: Path, dest_dir: Path) -> Path:
    """核验官方 ZIP 的三个摘要并解出 DLL；返回受控 DLL 绝对路径。

    固定供应源与摘要来自 candidate.json（已收录的独立来源），不是本次产物回填。
    """
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
    """在导入 sqlite3 之前按绝对路径/受限搜索预加载受控 DLL。

    winmode=0x1100 = LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR，
    不修改 PATH、不写全局安装、不追随下载页漂移。返回实际加载的模块路径。
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
    """用同一 DLL 的公共 C API sqlite3_file_control(SQLITE_FCNTL_VFSNAME=12) 读 VFS。"""
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
    """核验并返回产品实际使用的运行库清单（REC-15 结构化证据）。"""
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
    """门禁未达时的结构化记录：读回实际（本机默认）运行库，绝不伪称已修复。"""
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
