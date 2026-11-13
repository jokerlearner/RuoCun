"""Frozen obs/attrs.ts: Laminar token attributes and cache signals."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from typing import Any, Literal

from ..client.resilient import _jsNumber
from ..config.compat import resolve_env

TAGS_KEY = "lmnr.association.properties.tags"


def llmAttributes(model: str, usage: Mapping[str, Any] | None = None) -> dict[str, Any]:
    attrs: dict[str, Any] = {"gen_ai.request.model": model}
    if usage:
        for target, source in (("gen_ai.usage.input_tokens", "prompt_tokens"),
                               ("gen_ai.usage.output_tokens", "completion_tokens"),
                               ("llm.usage.total_tokens", "total_tokens")):
            if source in usage:
                attrs[target] = usage[source]
    return attrs


def cacheTag(usage: Mapping[str, Any] | None = None) -> Literal["cache_hit", "cache_miss"] | None:
    if usage:
        if (usage.get("prompt_cache_hit_tokens") or 0) > 0:
            return "cache_hit"
        if (usage.get("prompt_cache_miss_tokens") or 0) > 0:
            return "cache_miss"
    return None


def _number(value: str | None, fallback: float) -> float:
    number = _jsNumber(value or "")
    return fallback if not number or math.isnan(number) else number


def cacheLow(usage: Mapping[str, Any] | None = None, floor: float | None = None,
             rate: float | None = None, *, environ: Mapping[str, str] | None = None) -> dict[str, Any] | None:
    env = os.environ if environ is None else environ
    floor = _number(resolve_env("OBS_CACHE_LOW_FLOOR", env), 10000) if floor is None else floor
    rate = _number(resolve_env("OBS_CACHE_LOW_RATE", env), 0.5) if rate is None else rate
    prompt = usage.get("prompt_tokens", 0) if usage else 0
    if not prompt or prompt < floor:
        return None
    hit_rate = (usage.get("prompt_cache_hit_tokens", 0) or 0) / prompt if usage else 0
    if hit_rate >= rate:
        return None
    return {"hit_rate": math.floor(hit_rate * 1000 + 0.5) / 1000, "prompt_tokens": prompt}
