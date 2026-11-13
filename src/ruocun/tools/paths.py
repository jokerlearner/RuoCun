"""冻结 paths.ts、file_lock.ts、fs_atomic.ts 的首版路径/写入支撑（MIT）。"""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import unicodedata
import weakref
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, NamedTuple

from .types import ToolContext, ToolRejected


class ClassifiedPath(NamedTuple):
    abs: str
    external: bool


def _within(root: str, path: str) -> bool:
    try:
        return os.path.commonpath([root, path]) == root
    except ValueError:
        return False


def classifyPath(workspaceRoot: str, p: str) -> ClassifiedPath:
    root = os.path.abspath(workspaceRoot)
    suspicious = unicodedata.normalize("NFKC", p) != p or any(
        char not in "\t\n\r" and unicodedata.category(char) in {"Cf", "Co", "Cn", "Cc"}
        for char in p
    )
    absolute = os.path.abspath(os.path.join(root, p.replace("\0", "")))
    external = suspicious or not _within(os.path.normcase(root), os.path.normcase(absolute))
    if os.path.exists(root):
        external |= not _within(os.path.normcase(os.path.realpath(root)),
                                os.path.normcase(os.path.realpath(absolute)))
    return ClassifiedPath(absolute, external)


def resolveInWorkspace(workspaceRoot: str, p: str) -> str:
    absolute, external = classifyPath(workspaceRoot, p)
    if external:
        raise ValueError(f"路径越界:{p} 超出工作区")
    return absolute


def resolveWritePath(workspaceRoot: str, p: str) -> str:
    return classifyPath(workspaceRoot, p).abs


def isImagePath(p: str) -> bool:
    return Path(p).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def detectImageFormat(data: bytes) -> str | None:
    """冻结paths.ts按magic前缀判断真实格式，不依赖文件扩展名。"""
    for prefix, mediaType in ((b"\x89PNG", "image/png"), (b"\xff\xd8", "image/jpeg"),
                              (b"GIF", "image/gif"), (b"RIFF", "image/webp")):
        if data.startswith(prefix):
            return mediaType
    return None


async def approvedPath(ctx: ToolContext, p: str, *, write: bool = False) -> str:
    absolute, external = await asyncio.to_thread(classifyPath, ctx.cwd or ctx.workspaceRoot, p)
    if ctx.signal.is_set():
        raise InterruptedError("工具调用已取消")
    if external:
        approve = ctx.approveExternalWrite if write else ctx.approveExternalRead
        if approve is None or not await approve(absolute):
            raise ToolRejected(f"Error: {p} 在工作区之外,未获授权访问。")
    return absolute


def fileMeta(absolute: str) -> dict[str, float | int]:
    stat = os.stat(absolute)
    return {"mtime": stat.st_mtime_ns / 1_000_000, "size": stat.st_size}


def checkReadBaseline(absolute: str, path: str, ctx: ToolContext) -> None:
    meta = ctx.readMeta.get(absolute)
    if meta is not None:
        try:
            current = fileMeta(absolute)
        except OSError as exc:
            raise ToolRejected(f"写入前无法核对文件:{path}。请重新 Read。{exc}") from exc
        if current != meta:
            raise ToolRejected(f"文件自上次 Read 后已被外部改动:{path}。请重新 Read 看最新内容再写,以免覆盖他人改动。")


def refreshReadBaseline(absolute: str, ctx: ToolContext) -> None:
    stat = os.stat(absolute)
    ctx.readMeta[absolute] = {"mtime": stat.st_mtime_ns / 1_000_000, "size": stat.st_size}
    ctx.readFiles.add(absolute)


_locks: weakref.WeakValueDictionary[str, threading.Lock] = weakref.WeakValueDictionary()
_lock_guard = threading.Lock()


@contextmanager
def fileLock(absolute: str) -> Iterator[None]:
    key = os.path.normcase(os.path.realpath(absolute))
    with _lock_guard:
        lock = _locks.setdefault(key, threading.Lock())
    with lock:
        yield


def atomicWrite(absolute: str, content: str) -> None:
    parent = os.path.dirname(absolute)
    os.makedirs(parent, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{Path(absolute).name}.ruocun-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content.encode("utf-8"))
        os.replace(temporary, absolute)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
