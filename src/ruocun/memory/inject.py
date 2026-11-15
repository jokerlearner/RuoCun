"""从存储读取当前作用域的记忆，为启动时的系统输入构建可注入文本和来源快照。文本和校验标识来自同一次读取。"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from .memory_audit import RecallCounts
from .store import MemoryStore, keepKnowledgeForProject, projectIdOf
from .types import Memory, Scope
from .validate import Verdict, validateMemory

_SMALL_N = 50
_CHANGED = "(可能已过期:来源已变,请以实时文件为准)"


@dataclass(frozen=True, slots=True)
class ValidatedMemory:
    mem: Memory
    verdict: Verdict
    scope: Scope | None = None
    content_hash: str = ""


@dataclass(frozen=True, slots=True)
class StartupMemoryEntry:
    scope: Scope
    name: str
    content_hash: str

    @property
    def identity(self) -> tuple[Scope, str]:
        return self.scope, self.name


@dataclass(frozen=True, slots=True)
class StartupMemorySnapshot:
    text: str = ""
    full_entries: tuple[StartupMemoryEntry, ...] = ()
    index_entries: tuple[StartupMemoryEntry, ...] = ()

    @property
    def full_ids(self) -> frozenset[tuple[Scope, str]]:
        return frozenset(entry.identity for entry in self.full_entries)

    @property
    def index_ids(self) -> frozenset[tuple[Scope, str]]:
        return frozenset(entry.identity for entry in self.index_entries)


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
    """旧版单层选择入口，保留原有顺序。"""
    live = [item for item in items if item.verdict != "stale"]
    if len(live) <= cap:
        return live
    return _selectPriority(live, today, cap, protectLocked=False)


def selectFullText(
    items: Sequence[ValidatedMemory], today: str, fullCap: int = 40,
) -> list[ValidatedMemory]:
    live = [item for item in items if item.verdict != "stale"]
    return _selectPriority(live, today, fullCap, protectLocked=True)


def _selectIndexEntries(
    items: Sequence[ValidatedMemory], today: str, fullText: Sequence[ValidatedMemory], indexCap: int = 200,
) -> list[ValidatedMemory]:
    in_full = {item.mem.name for item in fullText}
    tail = [item for item in items if item.verdict != "stale" and item.mem.name not in in_full]
    tail.sort(key=lambda item: _retentionScore(item.mem, today), reverse=True)
    return tail[:indexCap]


def selectIndexNames(
    items: Sequence[ValidatedMemory], today: str, fullText: Sequence[ValidatedMemory], indexCap: int = 200,
) -> list[str]:
    return [item.mem.title or item.mem.name for item in _selectIndexEntries(items, today, fullText, indexCap)]


def buildIndexSection(names: Sequence[str]) -> str:
    if not names:
        return ""
    header = f"\n\n[记忆索引 · 其余 {len(names)} 条(标题即概要;需要整句细节用 MemoryRead 读)]\n"
    return header + "\n".join(f"- {name}" for name in names)


async def buildStartupMemorySnapshot(
    store: MemoryStore, *, onRecall: Callable[[RecallCounts], None] | None = None,
) -> StartupMemorySnapshot:
    """从同一次读取和筛选生成启动文本与对应的记录身份。

    摘要是 MemoryStore 当时读取的 Markdown 原文哈希，避免再次读取时把较新版本写进审计。索引文件仍按名称排除。
    """
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
        validated.append(ValidatedMemory(memory, verdict, entry.scope, entry.contentDigest))
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
    index = [] if small else _selectIndexEntries(validated, today, full)
    text = buildMemorySection(full) + buildIndexSection([item.mem.title or item.mem.name for item in index])

    def identities(items: Sequence[ValidatedMemory]) -> tuple[StartupMemoryEntry, ...]:
        return tuple(StartupMemoryEntry(item.scope, item.mem.name, item.content_hash)
                     for item in items if item.scope is not None)

    return StartupMemorySnapshot(text, identities(full), identities(index))


async def buildStartupMemory(store: MemoryStore, *, onRecall: Callable[[RecallCounts], None] | None = None) -> str:
    """返回沿用原格式渲染的启动记忆文本。"""
    return (await buildStartupMemorySnapshot(store, onRecall=onRecall)).text
