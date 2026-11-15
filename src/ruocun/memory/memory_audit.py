"""记录记忆维护和反思的审计事件，供使用者追查选取和写入过程。审计按尽力而为执行。"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

from ..config.compat import resolve_env
from .secrets import redactSecrets
from .types import Scope


class ConsolidationAudit(TypedDict):
    scope: Scope
    groups: int
    superseded: int
    reasons: list[str]


class DistillCounts(TypedDict):
    extracted: int
    added: int
    updated: int


class _Distilled(DistillCounts):
    kind: Literal["distilled"]
    ts: int


class _Consolidated(ConsolidationAudit):
    kind: Literal["consolidated"]
    ts: int


class ReflectAudit(TypedDict):
    ran: bool
    onTrack: bool
    advisoryInjected: bool
    memAdded: int
    memMerged: int
    interval: int
    note: NotRequired[str]
    corrected: NotRequired[int]
    confirmed: NotRequired[int]


class CorrectionAudit(TypedDict):
    target: str
    action: Literal["supersede", "revise"]
    reason: str


class _Reflected(ReflectAudit):
    kind: Literal["reflected"]
    ts: int


class _Corrected(CorrectionAudit):
    kind: Literal["corrected"]
    ts: int


class RecallCounts(TypedDict):
    injected: int
    stale: int
    changed: int
    types: dict[str, int]
    foreign: NotRequired[int]


class _Recalled(RecallCounts):
    kind: Literal["recalled"]
    ts: int


class _TaskRecalled(TypedDict):
    kind: Literal["task_recalled"]
    ts: int
    ids: list[str]
    statistics: dict[str, int]


class _Wrote(TypedDict):
    kind: Literal["wrote"]
    ts: int
    type: str
    merged: bool


MemoryTraceEvent = _Distilled | _Consolidated | _Reflected | _Corrected | _Recalled | _TaskRecalled | _Wrote


class MemoryAuditSink:
    def __init__(self, file: Path | None, redact: Callable[[str], str] | None = None) -> None:
        self._file = file
        self._redact = redact

    def _write(self, event: Mapping[str, Any]) -> None:
        if self._file is None:
            return
        try:
            text = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            redact = self._redact
            if redact:
                # 先对字符串值脱敏，再编码 JSON，避免引号等内容破坏输出格式。
                def safe(value: Any) -> Any:
                    if isinstance(value, str):
                        return redactSecrets(redact(value))
                    if isinstance(value, dict):
                        return {k: safe(v) for k, v in value.items()}
                    if isinstance(value, list):
                        return [safe(v) for v in value]
                    return value
                text = json.dumps(safe(dict(event)), ensure_ascii=False, separators=(",", ":"))
            with self._file.open("a", encoding="utf-8", errors="backslashreplace", newline="\n") as stream:
                stream.write(text + "\n")
        except Exception:
            pass

    def recalled(self, injected: int, stale: int, changed: int, types: dict[str, int],
                  foreign: int | None = None) -> None:
        event: _Recalled = {"kind": "recalled", "ts": time.time_ns() // 1_000_000,
                           "injected": injected, "stale": stale, "changed": changed, "types": types}
        if foreign:
            event["foreign"] = foreign
        self._write(event)

    def wrote(self, type: str, merged: bool) -> None:
        self._write({"kind": "wrote", "ts": time.time_ns() // 1_000_000, "type": type, "merged": merged})

    def task_recalled(self, ids: Sequence[str], statistics: dict[str, int]) -> None:
        self._write({"kind": "task_recalled", "ts": time.time_ns() // 1_000_000,
                     "ids": list(ids), "statistics": statistics})

    def distilled(self, extracted: int, added: int, updated: int) -> None:
        self._write({"kind": "distilled", "ts": time.time_ns() // 1_000_000,
                     "extracted": extracted, "added": added, "updated": updated})

    def consolidated(self, audit: ConsolidationAudit) -> None:
        self._write({"kind": "consolidated", "ts": time.time_ns() // 1_000_000,
                     "scope": audit["scope"], "groups": audit["groups"], "superseded": audit["superseded"],
                     "reasons": [redactSecrets(reason) for reason in audit["reasons"]]})

    def reflected(self, audit: ReflectAudit) -> None:
        event: _Reflected = {"kind": "reflected", "ts": time.time_ns() // 1_000_000, **audit}
        if "note" in event:
            event["note"] = redactSecrets(event["note"])
        self._write(event)

    def corrected(self, audit: CorrectionAudit) -> None:
        self._write({"kind": "corrected", "ts": time.time_ns() // 1_000_000,
                     "target": redactSecrets(audit["target"]), "action": audit["action"],
                     "reason": redactSecrets(audit["reason"])})


def createMemoryAuditSink(sessionDir: str | Path, env: Mapping[str, str] | None = None, *,
                         redact: Callable[[str], str] | None = None) -> MemoryAuditSink:
    values = os.environ if env is None else env
    specific = resolve_env("MEMORY_AUDIT", values)
    if specific == "0" or (specific != "1" and resolve_env("AUDIT", values) == "0"):
        return MemoryAuditSink(None, redact)
    directory = Path(sessionDir)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return MemoryAuditSink(directory / "memory-trace.jsonl", redact)


class ConsolidationCounts(TypedDict):
    runs: int
    groups: int
    superseded: int
    reasons: list[str]


class MemorySummary(TypedDict, total=False):
    recall: RecallCounts
    writes: int
    writesMerged: int
    byType: dict[str, dict[str, int]]
    distill: DistillCounts
    consolidation: ConsolidationCounts


def summarizeMemoryTrace(events: Sequence[MemoryTraceEvent]) -> MemorySummary:
    summary: MemorySummary = {"writes": 0, "writesMerged": 0, "byType": {}}
    for event in events:
        if event["kind"] == "recalled":
            recall: RecallCounts = {"injected": event["injected"], "stale": event["stale"],
                                   "changed": event["changed"], "types": event["types"]}
            if event.get("foreign"):
                recall["foreign"] = event["foreign"]
            summary["recall"] = recall
        elif event["kind"] == "wrote":
            summary["writes"] += 1
            summary["writesMerged"] += int(event["merged"])
            counts_type = summary["byType"].setdefault(event["type"], {"total": 0, "merged": 0})
            counts_type["total"] += 1
            counts_type["merged"] += int(event["merged"])
        elif event["kind"] == "distilled":
            summary["distill"] = {"extracted": event["extracted"], "added": event["added"], "updated": event["updated"]}
        elif event["kind"] == "consolidated":
            counts = summary.setdefault("consolidation", {"runs": 0, "groups": 0, "superseded": 0, "reasons": []})
            counts["runs"] += 1
            counts["groups"] += event["groups"]
            counts["superseded"] += event["superseded"]
            counts["reasons"].extend(event["reasons"])
    return summary


def formatMemoryReport(summary: MemorySummary) -> str:
    rows = ["记忆审计:"]
    if recall := summary.get("recall"):
        extra = f" · 挡掉跨项目 knowledge {recall['foreign']}" if recall.get("foreign") else ""
        rows.append(f"  召回:注入 {recall['injected']} · 剔除 stale {recall['stale']} · "
                    f"标记 changed {recall['changed']}{extra}")
    writes = summary.get("writes", 0)
    merged = summary.get("writesMerged", 0)
    rate = int(merged / writes * 100 + 0.5) if writes else 0
    rows.append(f"  写入:{writes} 次(合并 {merged},合并率 {rate}%)")
    rows.extend(f"    {kind}: {counts['total']} 写 / {counts['merged']} 合并"
                for kind, counts in summary.get("byType", {}).items())
    if distilled := summary.get("distill"):
        rows.append(f"  蒸馏:抽取 {distilled['extracted']} · 新建 {distilled['added']} · 合并 {distilled['updated']}")
    if consolidated := summary.get("consolidation"):
        rows.append(f"  合并 pass:{consolidated['runs']} 轮 · 合并组 {consolidated['groups']} · "
                    f"取代旧条目 {consolidated['superseded']}")
        rows.extend(f"    · {reason}" for reason in consolidated["reasons"][:3])
    return "\n".join(rows)


def readAllMemoryTraces(sessionsRoot: str | Path) -> list[MemoryTraceEvent]:
    events: list[MemoryTraceEvent] = []
    try:
        directories = list(Path(sessionsRoot).iterdir())
    except OSError:
        return events
    for directory in directories:
        try:
            for line in (directory / "memory-trace.jsonl").read_text("utf-8").splitlines():
                try:
                    event = json.loads(line)
                    if isinstance(event, dict):
                        events.append(cast(MemoryTraceEvent, event))
                except (ValueError, TypeError):
                    pass
        except OSError:
            pass
    return events


class ReflectSummary(TypedDict):
    rounds: int
    ran: int
    advisories: int
    memAdded: int
    memMerged: int
    lastInterval: int
    notes: list[str]
    corrected: int
    confirmed: int
    correctedDetails: list[CorrectionAudit]


def summarizeReflectTrace(events: Sequence[MemoryTraceEvent]) -> ReflectSummary:
    summary: ReflectSummary = {"rounds": 0, "ran": 0, "advisories": 0, "memAdded": 0,
        "memMerged": 0, "lastInterval": 1, "notes": [], "corrected": 0, "confirmed": 0,
        "correctedDetails": []}
    for event in events:
        if event["kind"] == "corrected":
            summary["correctedDetails"].append({"target": event["target"],
                "action": event["action"], "reason": event["reason"]})
        elif event["kind"] == "reflected":
            summary["rounds"] += 1
            summary["ran"] += int(event["ran"])
            summary["advisories"] += int(event["advisoryInjected"])
            summary["memAdded"] += event["memAdded"]
            summary["memMerged"] += event["memMerged"]
            summary["lastInterval"] = event["interval"]
            summary["corrected"] += event.get("corrected", 0)
            summary["confirmed"] += event.get("confirmed", 0)
            if note := event.get("note"):
                summary["notes"].append(note)
    return summary


def formatReflectReport(summary: ReflectSummary) -> str:
    rows = ["统一反思器:",
        f"  回合:{summary['rounds']}(实跑 {summary['ran']} · 节奏跳过 {summary['rounds'] - summary['ran']})",
        f"  advisory:{summary['advisories']} 次(有问题才注入)",
        f"  记忆:新增 {summary['memAdded']} · 合并 {summary['memMerged']}",
        f"  纠错:supersede/revise {summary['corrected']} · 确认续命 {summary['confirmed']}",
        f"  当前节奏:每 {summary['lastInterval']} 回合反思一次"]
    details = summary["correctedDetails"]
    if details:
        rows.append(f"  纠错明细(最近 {min(3, len(details))}/{len(details)} 条):")
        rows.extend(f"    · {detail['action']} 「{detail['target']}」:{detail['reason']}" for detail in details[-3:])
    notes = summary["notes"]
    if notes:
        rows.append(f"  复述(最近 {min(3, len(notes))}/{len(notes)} 条):")
        rows.extend(f"    · {note}" for note in notes[-3:])
    return "\n".join(rows)
