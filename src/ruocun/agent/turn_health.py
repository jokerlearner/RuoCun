"""根据本轮结果更新健康状态，判断重复失败或目标偏移是否值得插入提示。"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from typing import NotRequired, TypedDict

from ..client.resilient import _jsNumber
from ..config.compat import resolve_env


class TurnOutcome(TypedDict):
    progressed: bool
    toolFailures: int
    errSig: NotRequired[str]
    verifyPassed: NotRequired[bool]


class HealthState(TypedDict):
    failureStreak: int
    repeatedErr: int
    turnsSinceRefocus: int
    lastErrSig: NotRequired[str]


class HealthConfig(TypedDict):
    failureStreakTrip: float
    repeatedErrTrip: float
    refocusEvery: float


class HealthDecision(TypedDict):
    next: HealthState
    challenger: bool
    refocuser: bool
    reason: str


def initHealth() -> HealthState:
    return {"failureStreak": 0, "repeatedErr": 0, "turnsSinceRefocus": 0}


def _number(value: str | None, fallback: float) -> float:
    number = _jsNumber(value or "")
    return fallback if not number or math.isnan(number) else number


def defaultHealthConfig(environ: Mapping[str, str] | None = None) -> HealthConfig:
    env = os.environ if environ is None else environ
    refocus = resolve_env("REFOCUS_EVERY", env)
    return {"failureStreakTrip": _number(resolve_env("FAIL_STREAK", env), 3),
            "repeatedErrTrip": _number(resolve_env("REPEAT_ERR", env), 2),
            "refocusEvery": 3 if refocus is None else max(0, _number(refocus, 0))}


def assessTurn(state: HealthState, outcome: TurnOutcome, cfg: HealthConfig, opts: Mapping[str, bool]) -> HealthDecision:
    streak = state["failureStreak"] + 1 if outcome["toolFailures"] > 0 else 0
    signature = outcome.get("errSig")
    repeated = (state["repeatedErr"] + 1 if signature == state.get("lastErrSig") else 1) if signature else 0
    challenger = streak >= cfg["failureStreakTrip"] or repeated >= cfg["repeatedErrTrip"]
    turns = state["turnsSinceRefocus"] + 1
    refocuser = opts.get("longTask", False) and cfg["refocusEvery"] > 0 and turns >= cfg["refocusEvery"]
    next_state: HealthState = {"failureStreak": 0 if challenger else streak,
                               "repeatedErr": 0 if challenger else repeated,
                               "turnsSinceRefocus": 0 if refocuser else turns}
    if signature is not None or "lastErrSig" in state:
        next_state["lastErrSig"] = signature if signature is not None else state["lastErrSig"]
    reason = ("failure-streak" if streak >= cfg["failureStreakTrip"] else "repeated-error") if challenger else "refocus-cadence" if refocuser else "ok"
    return {"next": next_state, "challenger": challenger, "refocuser": refocuser, "reason": reason}


def errSignature(content: str) -> str:
    normalized = re.sub(r"\s+", " ", re.sub(r"[0-9]+", "", re.sub(r"/[^\s]+", "", re.sub(
        r"0x[0-9a-f]+", "", content.lower())))).strip()
    encoded = normalized.encode("utf-16-le", errors="surrogatepass")[:400]
    result = 5381
    for offset in range(0, len(encoded), 2):
        result = (result * 33 + int.from_bytes(encoded[offset:offset + 2], "little")) & 0xFFFFFFFF
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    text = ""
    while result:
        result, remainder = divmod(result, 36)
        text = digits[remainder] + text
    return text or "0"
