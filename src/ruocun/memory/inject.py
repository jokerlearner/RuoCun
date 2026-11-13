"""Frozen memory/inject.ts and the startup recall path in index.ts (MIT)."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from .memory_audit import RecallCounts
from .store import MemoryStore, keepKnowledgeForProject, projectIdOf
from .types import Memory
from .validate import Verdict, validateMemory

_SMALL_N = 50
_CHANGED = "(可能已过期:来源已变,请以实时文件为准)"


@dataclass(frozen=True, slots=True)
class ValidatedMemory:
    mem: Memory
    verdict: Verdict


def _retentionScore(memory: Memory, today: str) -> float:
    try:
        age = abs((date.fromisoformat(today) - date.fromisoformat(memory.lastUsed)).days)
    except ValueError:
        age = 0
    return memory.importance * math.pow(0.995, age)


def _selectPriority(
    live: Sequence[ValidatedMemory], today: str, cap: int, *, protectLocked: bool,
) -> list[ValidatedMemory]:
    high: list[ValidatedMemory] = []
    rest: list[ValidatedMemory] = []
    for item in live:
        memory = item.mem
        if memory.type in ("user", "feedback") or (protectLocked and memory.locked):
            high.append(item)
        else:
            rest.append(item)
    rest.sort(key=lambda item: _retentionScore(item.mem, today), reverse=True)
    return high + rest[:max(0, cap - len(high))]


def buildMemorySection(items: Sequence[ValidatedMemory]) -> str:
    return "\n".join(
        f"- {item.mem.text}{_CHANGED if item.verdict == 'changed' else ''}"
        for item in items if item.verdict != "stale"
    )


def selectForInjection(
    items: Sequence[ValidatedMemory], today: str, cap: int = 150,
) -> list[ValidatedMemory]:
    """旧单层选择入口，保留来源测试和原有保序规则。"""
    live = [item for item in items if item.verdict != "stale"]
    if len(live) <= cap:
        return live
    return _selectPriority(live, today, cap, protectLocked=False)


def selectFullText(
    items: Sequence[ValidatedMemory], today: str, fullCap: int = 40,
) -> list[ValidatedMemory]:
    live = [item for item in items if item.verdict != "stale"]
    return _selectPriority(live, today, fullCap, protectLocked=True)


def selectIndexNames(
    items: Sequence[ValidatedMemory], today: str, fullText: Sequence[ValidatedMemory], indexCap: int = 200,
) -> list[str]:
    in_full = {item.mem.name for item in fullText}
    tail = [item for item in items if item.verdict != "stale" and item.mem.name not in in_full]
    tail.sort(key=lambda item: _retentionScore(item.mem, today), reverse=True)
    return [item.mem.title or item.mem.name for item in tail[:indexCap]]


def buildIndexSection(names: Sequence[str]) -> str:
    if not names:
        return ""
    header = f"\n\n[记忆索引 · 其余 {len(names)} 条(标题即概要;需要整句细节用 MemoryRead 读)]\n"
    return header + "\n".join(f"- {name}" for name in names)


async def buildStartupMemory(store: MemoryStore, *, onRecall: Callable[[RecallCounts], None] | None = None) -> str:
    """读取当前项目的一次记忆快照，供组合根放入固定系统前缀。"""
    today = store.today()
    project = projectIdOf(store.cwd)
    validated: list[ValidatedMemory] = []
    foreign = 0
    for entry in await store.load(("project", "user", "knowledge")):
        memory = entry.memory
        if entry.scope == "knowledge" and not keepKnowledgeForProject(memory, project):
            foreign += 1
            continue
        verdict = await validateMemory(memory, store.cwd, today)
        validated.append(ValidatedMemory(memory, verdict))
    small = sum(item.verdict != "stale" for item in validated) < _SMALL_N
    full = selectFullText(validated, today, _SMALL_N if small else 40)
    if onRecall is not None:
        types: dict[str, int] = {}
        for item in full:
            types[item.mem.type] = types.get(item.mem.type, 0) + 1
        try:
            onRecall({"injected": len(full), "stale": sum(item.verdict == "stale" for item in validated),
                "changed": sum(item.verdict == "changed" for item in validated), "types": types, "foreign": foreign})
        except Exception:
            pass
    return buildMemorySection(full) + ("" if small else buildIndexSection(selectIndexNames(validated, today, full)))
