"""Frozen tools/tool_audit.ts (MIT); redacted best-effort observational JSONL."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Literal, NotRequired, Protocol, TypedDict

from ..config.compat import resolve_env
from ..permissions.secrets import redactSecrets


class ToolTraceEvent(TypedDict):
    kind: Literal["call"]
    ts: int
    name: str
    cap: str
    ok: bool
    durationMs: int | float
    args: str
    sessionId: NotRequired[str]
    taskId: NotRequired[str]
    runId: NotRequired[str]
    toolCallId: NotRequired[str]


class ToolStat(TypedDict):
    name: str
    calls: int
    errors: int
    errorRate: float
    avgMs: float
    maxMs: int | float
    totalMs: int | float


class ToolAuditSink(Protocol):
    def call(self, name: str, cap: str, ok: bool, durationMs: int | float, args: str, *,
             metadata: Mapping[str, str] | None = None) -> None: ...


class _Sink:
    def __init__(self, directory: Path | None, redact: Callable[[str], str] | None) -> None:
        self.directory, self.redact = directory, redact
        if directory is not None:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

    def _safe(self, text: str) -> str:
        return redactSecrets(self.redact(text) if self.redact is not None else text)

    def call(self, name: str, cap: str, ok: bool, durationMs: int | float, args: str, *,
             metadata: Mapping[str, str] | None = None) -> None:
        if self.directory is None:
            return
        try:
            # JS slice counts UTF-16 units. Redact the complete arguments first,
            # so a key crossing the output boundary cannot leave its prefix.
            preview = self._safe(args).encode("utf-16-le", errors="surrogatepass")[:240].decode(
                "utf-16-le", errors="surrogatepass")
            event = {"kind": "call", "ts": time.time_ns() // 1_000_000, "name": self._safe(name),
                     "cap": self._safe(cap), "ok": ok, "durationMs": durationMs, "args": preview}
            if metadata is not None:
                for key in ("sessionId", "taskId", "runId", "toolCallId"):
                    if key in metadata:
                        event[key] = self._safe(metadata[key])
            with (self.directory / "tool-trace.jsonl").open(
                    "a", encoding="utf-8", errors="backslashreplace", newline="\n") as trace:
                trace.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
        except Exception:
            # Neither an unavailable trace path nor a failed redactor changes a
            # completed tool's result. No retry can re-execute its business call.
            pass


def createToolAuditSink(sessionDir: str | Path, env: Mapping[str, str] | None = None, *,
                        redact: Callable[[str], str] | None = None) -> ToolAuditSink:
    values = os.environ if env is None else env
    specific = resolve_env("TOOL_AUDIT", values)
    enabled = specific != "0" and (specific == "1" or resolve_env("AUDIT", values) != "0")
    return _Sink(Path(sessionDir) if enabled else None, redact)


def summarizeToolTrace(events: Iterable[Mapping[str, object]]) -> list[ToolStat]:
    groups: dict[str, ToolStat] = {}
    for event in events:
        name, duration = event.get("name"), event.get("durationMs")
        if (event.get("kind") != "call" or not isinstance(name, str)
                or type(duration) not in (int, float) or not isinstance(duration, (int, float))
                or not math.isfinite(duration)):
            continue
        stat = groups.setdefault(name, {"name": name, "calls": 0, "errors": 0, "errorRate": 0.,
                                        "avgMs": 0., "maxMs": 0, "totalMs": 0})
        stat["calls"] += 1
        stat["errors"] += not bool(event.get("ok"))
        stat["totalMs"] += duration
        stat["maxMs"] = max(stat["maxMs"], duration)
    for stat in groups.values():
        stat["errorRate"] = stat["errors"] / stat["calls"]
        stat["avgMs"] = stat["totalMs"] / stat["calls"]
    return sorted(groups.values(), key=lambda stat: (-stat["errorRate"], -stat["calls"]))


def readAllToolTraces(sessionsRoot: str | Path) -> list[dict[str, object]]:
    try:
        directories = sorted(Path(sessionsRoot).iterdir())
    except OSError:
        return []
    events: list[dict[str, object]] = []
    for directory in directories:
        try:
            raw = (directory / "tool-trace.jsonl").read_text(encoding="utf-8", errors="replace")
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


def formatToolReport(stats: Iterable[ToolStat]) -> str:
    rows = []
    for stat in stats:
        name = stat["name"]
        name += " " * max(0, 18 - len(name.encode("utf-16-le", errors="surrogatepass")) // 2)
        rate = str(math.floor(stat["errorRate"] * 100 + .5)).rjust(3)
        avg = math.floor(stat["avgMs"] + .5)
        peak = f"{stat['maxMs']:g}"
        rows.append(f"  {name} 调用 {stat['calls']:4} · 错误率 {rate}% · 均 {avg}ms · 峰 {peak}ms")
    return "\n".join(["工具调用审计(错误率高在前):", *rows]) if rows else "暂无工具调用记录。"
