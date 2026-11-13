"""Frozen reference memory/gc.ts (MIT), scoped to confirmed native deletions."""

from __future__ import annotations

from datetime import date, timedelta
from threading import Event

from ..tools.types import ToolRejected
from .audit import daysBetween, retention
from .store import MemoryStore
from .types import Memory, Scope

__all__ = ["MemoryPruneUnconfirmed", "daysBetween", "gcMemories", "retention", "shouldPrune"]


class MemoryPruneUnconfirmed(RuntimeError):
    """A scope was stopped after an unconfirmed deletion receipt."""

    def __init__(self, pruned: list[str]) -> None:
        super().__init__("记忆清理结果未确认，已停止本作用域。")
        self.pruned = tuple(pruned)


def _expired(validUntil: str, today: str) -> bool:
    try:
        deadline = date.fromisoformat(validUntil) + timedelta(days=7)
        return deadline < date.fromisoformat(today)
    except (ValueError, OverflowError):
        return False


def shouldPrune(memory: Memory, today: str, *, provisionalDays: float = 7) -> bool:
    if memory.locked:
        return False
    if memory.title == "[DELETED]":
        return True
    if memory.status == "superseded" and memory.validUntil and _expired(memory.validUntil, today):
        return True

    confidence = memory.confidence if memory.confidence is not None else 1
    low_value_user = (memory.type == "user" and confidence < 0.5
                      and memory.uses == 0 and memory.importance < 6)
    if memory.type == "feedback" or (memory.type == "user" and not low_value_user):
        return False
    if memory.importance >= 6:
        return False
    if retention(memory, today) < 0.3:
        return True
    return (memory.uses == 0 and confidence < 0.8
            and daysBetween(memory.created, today) > provisionalDays)


async def gcMemories(
    store: MemoryStore, scope: Scope, today: str, *,
    provisionalDays: float = 7, signal: Event | None = None,
) -> list[str]:
    if signal is not None and signal.is_set():
        return []
    pruned: list[str] = []
    for entry in await store.loadNative(scope, includeSuperseded=True):
        if signal is not None and signal.is_set():
            break
        if not shouldPrune(entry.memory, today, provisionalDays=provisionalDays):
            continue
        try:
            deleted = await store.deleteExpected(entry, signal=signal)
        except ToolRejected:
            continue
        except Exception as exc:
            raise MemoryPruneUnconfirmed(pruned) from exc
        if deleted:
            pruned.append(entry.memory.name)
    return pruned
