"""Frozen reflect_persist.ts, through the existing native MemoryStore port (MIT)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import replace
from threading import Event
from typing import TypedDict

from ..memory.frontmatter import parseMemoryFile, serializeMemory
from ..memory.secrets import findSecrets
from ..memory.store import MemoryEntry, MemoryStore, projectIdOf, routeScope, slug
from ..memory.types import Memory, newMemory
from ..tools.types import ToolRejected
from .reflect_result import Correction, ReflectMem, ReflectResult


class ReflectApplied(TypedDict):
    added: int
    merged: int
    corrections: list[Correction]
    confirmed: int


def reflectMemToCand(memory: ReflectMem, existing: Sequence[Memory], today: str, origin: str | None = None) -> Memory:
    target = next((item for item in existing if memory.get("mergeInto")
                   and (item.title == memory["mergeInto"] or item.name == slug(memory["mergeInto"]))), None)
    candidate = newMemory(name=target.name if target else slug(memory["title"]), title=memory["title"],
                          text=memory["text"], type=target.type if target else memory["type"], today=today,
                          confidence=memory.get("confidence"), source=memory.get("source"), origin=origin)
    return replace(candidate, importance=memory.get("importance", 5))


def _target(existing: Sequence[MemoryEntry], title: str) -> MemoryEntry | None:
    return next((entry for entry in existing if entry.memory.title == title or entry.memory.name == slug(title)), None)


def _acknowledge(existing: list[MemoryEntry], entry: MemoryEntry, candidate: Memory) -> None:
    serialized = serializeMemory(candidate)
    saved = parseMemoryFile(candidate.name, serialized)
    if saved is None:
        raise RuntimeError("已确认反思写入的快照无法重建，停止后续修改。")
    existing[existing.index(entry)] = replace(entry, memory=saved,
        contentDigest=hashlib.sha256(serialized.encode("utf-8")).hexdigest())


async def applyCorrections(corrections: Sequence[Correction], existing: Sequence[MemoryEntry], store: MemoryStore,
                           today: str, cap: int = 3, *, signal: Event | None = None) -> list[Correction]:
    applied = []
    working = list(existing)
    for correction in corrections[:cap]:
        entry = _target(working, correction["target"])
        if entry is None or entry.memory.locked:
            continue
        if signal is not None and signal.is_set():
            raise InterruptedError("反思记忆写入已取消。")
        original = entry.memory
        if correction["action"] == "supersede":
            candidate = replace(original, status="superseded", supersededBy=original.name, validUntil=today)
        else:
            if findSecrets(correction["newText"]):
                raise ToolRejected("反思纠错正文包含凭据，未写入。")
            candidate = replace(original, text=correction["newText"])
        if await store.publishExpected(entry.scope, candidate, entry, signal=signal):
            _acknowledge(working, entry, candidate)
            applied.append(correction)
    return applied


async def applyConfirmed(confirmed: Sequence[str], existing: Sequence[MemoryEntry], store: MemoryStore,
                         today: str, *, signal: Event | None = None) -> int:
    touched = 0
    working = list(existing)
    for title in confirmed:
        entry = _target(working, title)
        if entry is not None:
            candidate = replace(entry.memory, lastUsed=today)
            if await store.touchConfirmed(entry, today, signal=signal):
                _acknowledge(working, entry, candidate)
                touched += 1
    return touched


async def applyReflectResult(result: ReflectResult, store: MemoryStore, *, today: str,
                             origin: str | None = None, signal: Event | None = None) -> ReflectApplied:
    """Caller journals the entire write segment. Partial failures are deliberately not swallowed."""
    existing = await store.load()
    memories = [entry.memory for entry in existing]
    added = merged = 0
    for memory in result["memories"]:
        if findSecrets(memory["text"]) or findSecrets(memory["title"]):
            raise ToolRejected("反思记忆包含凭据，未写入。")
        candidate = reflectMemToCand(memory, memories, today)
        scope = routeScope(candidate.type)
        if scope == "knowledge":
            candidate = replace(candidate, origin=origin or projectIdOf(store.cwd))
        receipt = await store.upsert(scope, candidate, signal=signal)
        if receipt.action == "updated":
            merged += 1
        else:
            added += 1
    corrections = await applyCorrections(result["corrections"], await store.load(), store, today, signal=signal)
    confirmed = await applyConfirmed(result["confirmed"], await store.load(includeSuperseded=True), store, today, signal=signal)
    return {"added": added, "merged": merged, "corrections": corrections, "confirmed": confirmed}
