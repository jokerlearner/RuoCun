"""对现有记忆计算留存评分、识别噪声，并为 /memory 构造只读审计结果。"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from .store import MemoryStore
from .types import Memory

AuditFlag = Literal["superseded", "noise", "lowvalue", "stale", "ok"]
_ORDER: tuple[AuditFlag, ...] = ("noise", "lowvalue", "superseded", "stale", "ok")
_LABELS: dict[AuditFlag, str] = {
    "superseded": "🔵 已取代",
    "noise": "🔴 噪音污染",
    "lowvalue": "🔴 低价值",
    "stale": "🟡 陈旧(久未命中)",
    "ok": "🟢 健康",
}
_CATALOG = re.compile(r"使用\s*[A-Za-z0-9_./-]+\s*(技能|工具)|[0-9]+\s*个技能|工具名[^\r\n]*改为")


@dataclass(frozen=True)
class Assessment:
    flag: AuditFlag
    reason: str


@dataclass(frozen=True)
class AuditRow:
    tier: str
    memory: Memory
    flag: AuditFlag
    reason: str
    fileName: str | None = None
    editable: bool = True


def daysBetween(first: str, second: str) -> int:
    try:
        return abs((date.fromisoformat(second) - date.fromisoformat(first)).days)
    except ValueError:
        return 0


def retention(memory: Memory, today: str) -> float:
    age = daysBetween(memory.lastUsed, today)
    scale = 45 * (1 + memory.uses)
    if scale == 0:
        return 0.0 if age else math.nan
    try:
        return math.exp(-age / scale)
    except OverflowError:
        return math.inf


def isCatalogNoise(text: str) -> bool:
    return _CATALOG.search(text) is not None


def assessMemory(memory: Memory, today: str) -> Assessment:
    if memory.status == "superseded":
        return Assessment("superseded", f"已被 {memory.supersededBy or '新记忆'} 取代")
    if isCatalogNoise(memory.text):
        return Assessment("noise", "像产品/技能/工具目录清单,不是关于用户的事实")
    if (memory.type == "user" and memory.confidence is not None and memory.confidence < 0.5
            and memory.uses == 0 and memory.importance < 6):
        return Assessment("lowvalue", f"低置信({memory.confidence})、从未被召回、低重要度的推断")
    if retention(memory, today) < 0.3:
        return Assessment("stale", f"{daysBetween(memory.lastUsed, today)} 天未被命中,留存已衰减")
    return Assessment("ok", "")


def _snippet(text: str) -> str:
    units = text.encode("utf-16-le", errors="surrogatepass")
    if len(units) <= 128:
        return text
    return units[:128].decode("utf-16-le", errors="ignore") + "…"


def formatAudit(rows: Sequence[AuditRow], today: str) -> str:
    if not rows:
        return "记忆为空。"
    groups: dict[AuditFlag, list[AuditRow]] = {flag: [] for flag in _ORDER}
    for row in rows:
        groups[row.flag].append(row)
    summary = " · ".join(f"{_LABELS[flag]} {len(group)}" for flag, group in groups.items() if group)
    lines = [f"记忆审核(共 {len(rows)} 条):{summary}", ""]
    for flag, group in groups.items():
        if not group:
            continue
        lines.append(_LABELS[flag])
        for row in group:
            memory = row.memory
            confidence = f"·信{memory.confidence}" if memory.confidence is not None else ""
            age = daysBetween(memory.created, today)
            meta = f"[{row.tier}·{memory.type}·重{memory.importance}{confidence}·命中{memory.uses}·{age}天]"
            reason = f"  ← {row.reason}" if row.reason else ""
            lines.append(f"  · {row.fileName or memory.name}  {meta}")
            lines.append(f"      {_snippet(memory.text)}{reason}")
        lines.append("")
    flagged = sum(row.editable and row.flag in ("noise", "lowvalue") for row in rows)
    if flagged:
        lines.append(f"建议清理 {flagged} 条(🔴)。删除:/memory delete <名>(多个空格分隔)。")
    elif any(row.flag in ("noise", "lowvalue") for row in rows):
        lines.append("发现噪音或低价值记忆，锁定或只读来源已保留。")
    else:
        lines.append("未发现明显噪音。删除某条:/memory delete <名>。")
    return "\n".join(lines)


async def gatherAudit(store: MemoryStore, today: str) -> list[AuditRow]:
    labels = {"user": "用户", "knowledge": "知识", "project": "项目"}
    rows = []
    for entry in await store.load(("user", "knowledge", "project"), includeSuperseded=True):
        if entry.path.name == "MEMORY.md":
            continue
        tier = labels[entry.scope]
        if entry.source is not None:
            tier += f"·只读兼容 {entry.source.id}"
        if entry.memory.locked:
            tier += "·锁定"
        assessment = assessMemory(entry.memory, today)
        rows.append(AuditRow(tier, entry.memory, assessment.flag, assessment.reason,
                             entry.path.stem, entry.source is None and not entry.memory.locked))
    return rows
