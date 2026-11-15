"""记录每次权限判断的来源和结果，并按工具汇总允许、拒绝和询问次数。"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Literal, Protocol, TypedDict, cast

from ..config.compat import resolve_env
from .secrets import redactSecrets

PermDecision = Literal["allow", "deny", "ask-approved", "ask-denied"]
PermSource = Literal["rule", "classifier", "human"]


class PermStat(TypedDict):
    tool: str
    allow: int
    deny: int
    askApproved: int
    askDenied: int
    total: int
    askRate: float


class PermAuditSink(Protocol):
    def decided(self, tool: str, cap: str, decision: PermDecision, source: PermSource) -> None: ...


class _Sink:
    def __init__(self, directory: Path | None, getMode: Callable[[], str]) -> None:
        self.directory, self.getMode = directory, getMode

    def decided(self, tool: str, cap: str, decision: PermDecision, source: PermSource) -> None:
        if self.directory is None:
            return
        event = {"kind": "decided", "ts": time.time_ns() // 1_000_000, "tool": redactSecrets(tool),
                 "cap": cap, "mode": self.getMode(), "decision": decision, "source": source}
        try:
            self.directory.mkdir(parents=True, exist_ok=True)
            with (self.directory / "perm-trace.jsonl").open("a", encoding="utf-8", errors="backslashreplace", newline="\n") as trace:
                trace.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        except OSError:
            pass


def createPermAuditSink(sessionDir: str | Path, getMode: Callable[[], str], env: Mapping[str, str] | None = None) -> PermAuditSink:
    values = os.environ if env is None else env
    specific = resolve_env("PERM_AUDIT", values)
    enabled = specific != "0" and (specific == "1" or resolve_env("AUDIT", values) != "0")
    return _Sink(Path(sessionDir) if enabled else None, getMode)


def summarizePermTrace(events: Iterable[Mapping[str, object]]) -> list[PermStat]:
    groups: dict[str, PermStat] = {}
    kinds = {"allow": "allow", "deny": "deny", "ask-approved": "askApproved", "ask-denied": "askDenied"}
    for event in events:
        tool = event.get("tool")
        if event.get("kind") != "decided" or not isinstance(tool, str):
            continue
        stat = groups.setdefault(tool, {"tool":tool,"allow":0,"deny":0,"askApproved":0,"askDenied":0,"total":0,"askRate":0.0})
        key = kinds.get(str(event.get("decision")))
        if key is not None:
            # 汇总行还包含名称，更新计数时须将该列与数字列区分开。
            counters = cast(dict[str, int], stat)
            counters[key] += 1
    for stat in groups.values():
        stat["total"] = stat["allow"] + stat["deny"] + stat["askApproved"] + stat["askDenied"]
        stat["askRate"] = (stat["askApproved"] + stat["askDenied"]) / stat["total"] if stat["total"] else 0.0
    return sorted(groups.values(), key=lambda row: (-row["askRate"], -row["total"]))


def readAllPermTraces(sessionsRoot: str | Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    try:
        directories = sorted(Path(sessionsRoot).iterdir())
    except OSError:
        return events
    for directory in directories:
        try:
            raw = (directory / "perm-trace.jsonl").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in raw.split("\n"):
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def formatPermReport(stats: list[PermStat]) -> str:
    if not stats:
        return "暂无权限裁决记录。"
    rows = [f"  {row['tool']:<18} 询问率 {row['askRate'] * 100:3.0f}% · allow {row['allow']} · deny {row['deny']} · 问准 {row['askApproved']} · 问驳 {row['askDenied']}" for row in stats]
    return "\n".join(["权限裁决审计(询问率高在前 → 可加 allow 白名单):", *rows])
