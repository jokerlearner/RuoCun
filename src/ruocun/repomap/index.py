"""组织代码库地图的扫描、缓存、排序和裁剪。

每个文件先提取定义和引用，提取结果按路径、大小和修改时间复用。文件排序后由 render 按调用方提供的预算生成文本。
"""

from __future__ import annotations

import asyncio
import math
import os
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config.compat import resolve_env
from ..tools.glob import walkFiles
from .extract import FileExtract, extractFileSync
from .graph import FileEntry, buildGraph
from .languages import langForFile
from .render import RenderedFile, renderRepoMap

DEFAULT_TOKEN_BUDGET = 2048
MAX_FILES = 4000
MAX_FILE_BYTES = 512 * 1024
_CACHE: dict[str, tuple[int, int, FileExtract | None]] = {}
_CACHE_LOCK = threading.Lock()


@dataclass
class RepoMapResult:
    text: str
    fileCount: int
    truncated: bool


def repoMapTokenBudget(environ: Mapping[str, str] | None = None) -> int:
    raw = resolve_env("REPO_MAP_TOKENS", os.environ if environ is None else environ)
    if raw is None:
        return DEFAULT_TOKEN_BUDGET
    try:
        value = float(raw.strip() or "0")
    except ValueError:
        return DEFAULT_TOKEN_BUDGET
    return math.floor(value) if math.isfinite(value) and value >= 0 else DEFAULT_TOKEN_BUDGET


def _build(root: str, budget: int, signal: threading.Event | None) -> RepoMapResult:
    files: list[tuple[str, str]] = []
    for absolute, relative in walkFiles(root):
        if signal is not None and signal.is_set():
            raise InterruptedError("代码地图构建已取消。")
        if langForFile(relative) is None or re.search(r"\.min\.|\.d\.ts$", relative):
            continue
        files.append((absolute, relative))
        if len(files) >= MAX_FILES:
            break
    entries = []
    for absolute, relative in files:
        if signal is not None and signal.is_set():
            raise InterruptedError("代码地图构建已取消。")
        try:
            stat = Path(absolute).stat()
            if not Path(absolute).is_file() or stat.st_size == 0 or stat.st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        with _CACHE_LOCK:
            cached = _CACHE.get(absolute)
        # 文件大小和修改时间都一致时，复用上次提取结果，避免重复解析。
        if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
            extracted = cached[2]
        else:
            extracted = extractFileSync(absolute, langForFile(relative), signal=signal)
            with _CACHE_LOCK:
                _CACHE[absolute] = (stat.st_mtime_ns, stat.st_size, extracted)
        if extracted is not None:
            entries.append(FileEntry(relative, extracted))
    truncated = len(files) >= MAX_FILES
    if not entries:
        return RepoMapResult("", 0, truncated)
    if signal is not None and signal.is_set():
        raise InterruptedError("代码地图构建已取消。")
    ranks = buildGraph(entries, signal=signal).ranks
    ranked = sorted(entries, key=lambda entry: (-ranks.get(entry.rel, 0), entry.rel))
    text = renderRepoMap([RenderedFile(entry.rel, entry.extract.defs) for entry in ranked], budget)
    return RepoMapResult(text, len(entries), truncated)


async def buildRepoMap(root: str | Path, tokenBudget: int | None = None, *,
                       environ: Mapping[str, str] | None = None, signal: threading.Event | None = None) -> RepoMapResult:
    budget = repoMapTokenBudget(environ) if tokenBudget is None else tokenBudget
    return await asyncio.to_thread(_build, str(Path(root).resolve()), budget, signal)


def wrapRepoMapNotice(mapText: str, isEn: bool, fileCount: int) -> str:
    if not mapText.strip():
        return ""
    if isEn:
        return ('<codebase-map note="startup index of definitions">\n'
                f'Scanned {fileCount} files. Entries favor definitions used elsewhere in the project. '
                '│ introduces a signature and ⋮... marks a skipped section. '
                'Open the relevant file with Read to inspect its implementation. '
                f'Run RepoMap with refresh=true if the index is out of date.\n{mapText}\n</codebase-map>')
    return ('<代码库地图 说明="启动时生成的定义索引">\n'
            f'已扫描 {fileCount} 个文件。项目其他位置依赖较多的定义排在前面。│ 后是签名，⋮... 表示略去的部分。'
            '找到目标后用 Read 查看实现。需要更新索引时，调用 RepoMap 并设置 refresh=true。'
            f'\n{mapText}\n</代码库地图>')


def resetRepoMapCacheForTest() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()
