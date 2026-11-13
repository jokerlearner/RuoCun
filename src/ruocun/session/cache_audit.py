"""冻结 ``src/session/cache_audit.ts`` 的旁路缓存诊断（MIT）。

仅记录调用方提供的诊断输入，不改变 Session/StoragePort；观测写入失败不影响任务。
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Literal, NotRequired, Protocol, TypedDict

from ..client.types import Usage
from ..config.compat import resolve_env


class CacheAuditInput(TypedDict):
    agent: Literal["main", "sub", "fork", "bg", "classifier", "summary", "distill", "fetch-extract"]
    subId: NotRequired[str]
    depth: int
    turn: int
    model: str
    usage: Usage
    sys: str
    tools: str
    tail: str
    msgs: NotRequired[str]


class CacheAuditDelta(TypedDict):
    fromLen: int
    toLen: int
    firstDiffAt: int
    sample: str


class CacheAuditEvent(TypedDict):
    agent: str
    subId: NotRequired[str]
    depth: int
    turn: int
    model: str
    prompt: int
    hit: int
    miss: int
    completion: int
    ratio: float
    fp: dict[str, str]
    changed: list[str]
    delta: NotRequired[dict[str, CacheAuditDelta]]
    ts: NotRequired[int]


class CacheAuditSink(Protocol):
    def record(self, inp: CacheAuditInput) -> None: ...


def _utf16(text: str) -> bytes:
    return text.encode("utf-16-le", errors="surrogatepass")


def _cheapHash(text: str) -> str:
    value = 5381
    raw = _utf16(text)
    for index in range(0, len(raw), 2):
        code = raw[index] | raw[index + 1] << 8
        value = (value * 33 + code) & 0xffffffff
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while value:
        value, remainder = divmod(value, 36)
        result = digits[remainder] + result
    return result or "0"


def cachePrefixFingerprint(model: str, system: str, tools: str) -> dict[str, str]:
    return {"model": model, "sys": _cheapHash(system), "tools": _cheapHash(tools), "tail": _cheapHash("")}


class Divergence(TypedDict):
    firstDiffAt: int
    sample: str


def divergence(a: str, b: str) -> Divergence:
    """首个 UTF-16 分歧位置及新串样本，偏移口径与 JS String 一致。"""
    left, right = _utf16(a), _utf16(b)
    index = 0
    while index < min(len(left), len(right)) and left[index:index + 2] == right[index:index + 2]:
        index += 2
    return {"firstDiffAt": index // 2,
            "sample": right[index:index + 240].decode("utf-16-le", errors="surrogatepass")}


class _Sink:
    def __init__(self, directory: Path) -> None:
        self.file = directory / "cache.jsonl"
        self.previous: dict[str, dict[str, str]] = {}
        self.lastMainMsgs = ""
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def record(self, inp: CacheAuditInput) -> None:
        key = f"{inp['agent']}:{inp.get('subId', '')}:{inp['depth']}"
        current = {"model": inp["model"], "sys": inp["sys"], "tools": inp["tools"], "tail": inp["tail"]}
        previous = self.previous.get(key)
        changed: list[str] = []
        delta: dict[str, CacheAuditDelta] = {}
        if previous is not None:
            for dimension in ("model", "sys", "tools", "tail"):
                if _cheapHash(current[dimension]) != _cheapHash(previous[dimension]):
                    changed.append(dimension)
                    if dimension != "model":
                        difference = divergence(previous[dimension], current[dimension])
                        delta[dimension] = {
                            "fromLen": len(_utf16(previous[dimension])) // 2,
                            "toLen": len(_utf16(current[dimension])) // 2,
                            "firstDiffAt": difference["firstDiffAt"], "sample": difference["sample"],
                        }
        self.previous[key] = current
        messages = inp.get("msgs", "")
        if inp["agent"] == "main" and messages:
            self.lastMainMsgs = messages
        if inp["agent"] == "distill" and messages and self.lastMainMsgs:
            difference = divergence(self.lastMainMsgs, messages)
            delta["vsMain"] = {
                "fromLen": len(_utf16(self.lastMainMsgs)) // 2, "toLen": len(_utf16(messages)) // 2,
                "firstDiffAt": difference["firstDiffAt"], "sample": difference["sample"],
            }
        usage = inp["usage"]
        prompt = usage.get("prompt_tokens", 0)
        hit = usage.get("prompt_cache_hit_tokens", 0)
        event: CacheAuditEvent = {
            "agent": inp["agent"], "depth": inp["depth"], "turn": inp["turn"], "model": inp["model"],
            "prompt": prompt, "hit": hit, "miss": usage.get("prompt_cache_miss_tokens", 0),
            "completion": usage.get("completion_tokens", 0), "ratio": hit / prompt if prompt > 0 else 0,
            "fp": {key: _cheapHash(value) for key, value in current.items()},
            "changed": changed, "ts": int(time.time() * 1000),
        }
        event["fp"]["msgs"] = _cheapHash(inp.get("msgs", ""))
        if inp.get("subId"):
            event["subId"] = inp["subId"]
        if delta:
            event["delta"] = delta
        try:
            with self.file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, separators=(",", ":")) + "\n")
        except OSError:
            pass


class _Noop:
    def record(self, inp: CacheAuditInput) -> None:
        pass


_NOOP = _Noop()


def createCacheAuditSink(
    sessionDir: str | Path, env: Mapping[str, str] | None = None,
) -> CacheAuditSink:
    values = os.environ if env is None else env
    specific = resolve_env("CACHE_AUDIT", values)
    if specific == "0" or (specific != "1" and resolve_env("AUDIT", values) == "0"):
        return _NOOP
    return _Sink(Path(sessionDir))


def _fixed(number: float, digits: int) -> str:
    amount = Decimal.from_float(float(number)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    return f"{amount:.{digits}f}"


def formatCacheReport(events: list[CacheAuditEvent], ttlMs: float = 5 * 60 * 1000) -> str:
    """逐轮命中率、前缀维变化及空闲 TTL 诊断；不保证供应商实际缓存命中。"""
    if not events:
        return "缓存审计为空。"
    rows: list[str] = []
    previous_ts = 0
    for event in events:
        sub_id = f"#{event['subId']}" if event.get("subId") else ""
        who = "main" if event["agent"] == "main" else f"{event['agent']}{sub_id}@{event['depth']}"
        percent = _fixed(event["ratio"] * 100, 0).rjust(3)
        changed = event.get("changed", [])
        timestamp = event.get("ts", 0)
        idle = timestamp - previous_ts if previous_ts else 0
        flag = ""
        if changed:
            flag = f"⚠ 破:{'/'.join(changed)}"
        elif event["ratio"] < .3 and event["prompt"] >= 4000 and idle > ttlMs:
            flag = f"· TTL过期(空闲{_fixed(idle / 60000, 1)}min)"
        rows.append(f"  t{event['turn']} {who.ljust(12)} {str(event['prompt']).rjust(7)}tok 命中{percent}% {flag}")
        previous_ts = timestamp
    return (f"缓存审计(记录 {len(events)}):\n" + "\n".join(rows)
            + "\n(⚠破=某前缀维变化;TTL过期=四维稳但空闲超时,非bug。详查 cache.jsonl 的 delta)")
