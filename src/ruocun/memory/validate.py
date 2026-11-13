"""Frozen reference memory/validate.ts (MIT), with source reads off the business loop."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

from ..tools.paths import resolveInWorkspace
from .hash import contentHash
from .types import Memory

Verdict = Literal["ok", "changed", "stale"]
# Reflection also records evidence labels; only other source values name files.
_NON_FILE_SOURCES = frozenset({"user_stated", "inferred"})


def _sourcePath(workspaceRoot: Path, source: str) -> Path:
    return Path(resolveInWorkspace(str(workspaceRoot), source.partition("#")[0]))


def _fileHash(file: Path) -> str:
    # No universal newline conversion: the hash represents the live UTF-8 file.
    return contentHash(file.read_bytes().decode("utf-8", errors="replace"))


def _validate(memory: Memory, workspaceRoot: Path, today: str) -> Verdict:
    if memory.validUntil and memory.validUntil < today:
        return "stale"
    if not memory.source or memory.source in _NON_FILE_SOURCES:
        return "ok"
    try:
        file = _sourcePath(workspaceRoot, memory.source)
    except ValueError:
        return "ok"  # The source skips an out-of-workspace reference.
    try:
        digest = _fileHash(file)
    except OSError:
        return "stale"
    return "changed" if memory.sourceHash and memory.sourceHash != digest else "ok"


async def validateMemory(memory: Memory, workspaceRoot: Path, today: str) -> Verdict:
    return await asyncio.to_thread(_validate, memory, workspaceRoot, today)


def _sourceHash(workspaceRoot: Path, source: str) -> str | None:
    if source in _NON_FILE_SOURCES:
        return None
    try:
        return _fileHash(_sourcePath(workspaceRoot, source))
    except (OSError, ValueError):
        return None


async def hashMemorySource(workspaceRoot: Path, source: str) -> str | None:
    return await asyncio.to_thread(_sourceHash, workspaceRoot, source)
