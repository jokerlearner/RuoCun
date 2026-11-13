"""Frozen reflect_cadence.ts adaptive turn cadence (MIT)."""

import math
from typing import TypedDict


class CadenceState(TypedDict):
    interval: int
    counter: int


class CadenceTick(TypedDict):
    run: bool
    next: CadenceState


def initCadence() -> CadenceState:
    return {"interval": 1, "counter": 0}


def _clamp(value: float, maximum: float) -> int:
    return min(max(1, math.floor(value)), max(1, math.floor(maximum)))


def tickCadence(state: CadenceState, maxInterval: int = 3) -> CadenceTick:
    interval = _clamp(state["interval"], maxInterval)
    counter = state["counter"] + 1
    run = counter >= interval
    return {"run": run, "next": {"interval": interval, "counter": 0 if run else counter}}


def applyOutcome(state: CadenceState, quiet: bool, maxInterval: int = 3) -> CadenceState:
    return {**state, "interval": _clamp(state["interval"] + 1, maxInterval) if quiet else 1}
