"""解析和生成记忆 Markdown 的文件头元数据，兼容 Windows 的 CRLF 换行。"""

from __future__ import annotations

import math
import re
from typing import cast

from .types import Memory, MemoryStatus, MemoryType

_FRAME = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.DOTALL)


def _number(value: str | None) -> int | float | None:
    if value is None:
        return None
    if not value:
        return 0
    try:
        if value.lower().startswith(("0x", "0o", "0b")):
            return int(value, 0)
        number = float(value)
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return int(number) if number.is_integer() else number


def parseMemoryFile(name: str, raw: str) -> Memory | None:
    match = _FRAME.fullmatch(raw.replace("\r\n", "\n"))
    if match is None:
        return None
    values: dict[str, str] = {}
    for line in match[1].split("\n"):
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    if not values.get("type") or not values.get("status"):
        return None
    importance = _number(values.get("importance"))
    return Memory(
        name=values.get("name") or name, title=values.get("title") or None,
        text=match[2].strip(), type=cast(MemoryType, values["type"]),
        created=values.get("created", ""), lastUsed=values.get("lastUsed", ""),
        importance=5 if importance is None else importance,
        confidence=_number(values.get("confidence")), uses=_number(values.get("uses")) or 0,
        source=values.get("source") or None, sourceHash=values.get("sourceHash") or None,
        status=cast(MemoryStatus, values["status"]), supersededBy=values.get("supersededBy") or None,
        validUntil=values.get("validUntil") or None, locked=values.get("locked") == "true",
        origin=values.get("origin") or None,
    )


def _formatNumber(number: int | float) -> str:
    if math.isinf(number):
        return "-Infinity" if number < 0 else "Infinity"
    return str(number)


def serializeMemory(memory: Memory) -> str:
    lines = [f"name: {memory.name}"]
    if memory.title:
        lines.append(f"title: {memory.title}")
    lines.extend((f"type: {memory.type}", f"importance: {_formatNumber(memory.importance)}",
                  f"uses: {_formatNumber(memory.uses)}"))
    if memory.confidence is not None:
        lines.append(f"confidence: {_formatNumber(memory.confidence)}")
    lines.extend((f"created: {memory.created}", f"lastUsed: {memory.lastUsed}"))
    for key, value in (("source", memory.source), ("sourceHash", memory.sourceHash)):
        if value:
            lines.append(f"{key}: {value}")
    lines.append(f"status: {memory.status}")
    for key, value in (("supersededBy", memory.supersededBy), ("validUntil", memory.validUntil),
                       ("origin", memory.origin)):
        if value:
            lines.append(f"{key}: {value}")
    lines.append("locked: true" if memory.locked else "locked: false")
    return "---\n" + "\n".join(lines) + "\n---\n" + memory.text.strip() + "\n"
