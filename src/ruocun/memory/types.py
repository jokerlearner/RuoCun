"""定义记忆记录、作用域和验证结果的共享类型，供存储、注入和维护使用。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MemoryType = Literal["user", "feedback", "semantic", "procedural", "episodic"]
MemoryStatus = Literal["active", "superseded"]
Scope = Literal["project", "user", "knowledge"]


@dataclass(frozen=True)
class Memory:
    name: str
    text: str
    type: MemoryType
    created: str
    lastUsed: str
    title: str | None = None
    importance: int | float = 5
    confidence: int | float | None = None
    source: str | None = None
    sourceHash: str | None = None
    uses: int | float = 0
    status: MemoryStatus = "active"
    supersededBy: str | None = None
    validUntil: str | None = None
    locked: bool = False
    origin: str | None = None


def newMemory(
    *, name: str, text: str, type: MemoryType, today: str, title: str | None = None,
    importance: int = 5, confidence: int | float | None = None,
    source: str | None = None, sourceHash: str | None = None, origin: str | None = None,
) -> Memory:
    return Memory(
        name=name, text=text.strip(), type=type, created=today, lastUsed=today,
        title=title.strip() or None if title else None, importance=importance,
        confidence=confidence, source=source or None, sourceHash=sourceHash or None,
        origin=origin.strip() or None if origin else None,
    )
