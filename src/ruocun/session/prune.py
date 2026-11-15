"""清理旧会话时先在数据库封存会话，阻止后续接管。

目录移入私有封存区后逐项比对路径身份和数据库封存标记。无法确认时停止删除并保留现场。
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from ..platform.windows.durable_file import ensure_private_dir
from .contract import RuntimeRecord, StoreError
from .durable_store import read_prune_seal, seal_durable_session


def _identity(path: Path) -> tuple[int, int]:
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise StoreError("清理路径包含链接或重解析点，已保留。")
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
        raise StoreError("清理路径包含未识别文件类型，已保留。")
    return info.st_dev, info.st_ino


def _inventory(root: Path) -> dict[Path, tuple[int, int]]:
    paths = {Path(): _identity(root)}
    pending = [Path()]
    while pending:
        relative = pending.pop()
        directory = root / relative
        if _identity(directory) != paths[relative]:
            raise StoreError("清理目录身份变化，已保留。")
        with os.scandir(directory) as entries:
            for entry in entries:
                child = relative / entry.name
                paths[child] = _identity(root / child)
                if entry.is_dir(follow_symlinks=False):
                    pending.append(child)
    return paths


def prune_durable_session(session_dir: Path, runtime: RuntimeRecord, *, cutoff_ms: int,
                           protected_paths: tuple[str, ...] | None = None) -> bool:
    root = Path(session_dir).absolute()
    parent = root.parent
    _identity(parent)
    original = _inventory(root)
    nonce = seal_durable_session(root, runtime, cutoff_ms=cutoff_ms, protected_paths=protected_paths)
    if nonce is None:
        return False
    sealed = _inventory(root)
    sqlite_sidecars = {Path("session.db-wal"), Path("session.db-shm"), Path("session.db-journal")}
    if ({path: identity for path, identity in sealed.items() if path not in sqlite_sidecars}
            != {path: identity for path, identity in original.items() if path not in sqlite_sidecars}):
        raise StoreError("会话已封存，目录内容发生变化；清理已停止。")
    original = sealed
    trash = parent / ".trash"
    ensure_private_dir(trash)
    trash_identity = _identity(trash)
    target = trash / f"{root.name}-{nonce}"
    if target.exists():
        raise StoreError("会话封存目标已存在，已保留原位置。")
    root.rename(target)
    if _identity(trash) != trash_identity or _inventory(target) != original:
        raise StoreError("会话已移至封存目录，身份无法确认；未继续删除。")
    if read_prune_seal(target, runtime) != nonce:
        raise StoreError("会话封存标记不匹配，未继续删除。")
    checked = _inventory(target)
    if ({path: identity for path, identity in checked.items() if path not in sqlite_sidecars}
            != {path: identity for path, identity in original.items() if path not in sqlite_sidecars}):
        raise StoreError("会话封存回读后身份变化，未继续删除。")
    original = checked
    for relative in sorted(original, key=lambda path: len(path.parts), reverse=True):
        path = target / relative
        if _identity(path) != original[relative]:
            raise StoreError("封存文件身份发生变化，清理已停止。")
        if path.is_dir():
            path.rmdir()
        else:
            path.unlink()
    return True
