"""Frozen reflect_result.ts: independent, non-throwing result sections (MIT)."""

from __future__ import annotations

import json
import re
from typing import Any, Literal, NotRequired, TypedDict, cast

from ..memory.types import MemoryType


class ReflectMem(TypedDict):
    title: str
    text: str
    type: MemoryType
    importance: NotRequired[float]
    confidence: NotRequired[float]
    source: NotRequired[str]
    mergeInto: NotRequired[str]


class Correction(TypedDict):
    target: str
    action: Literal["supersede", "revise"]
    reason: str
    newText: NotRequired[str]


class ReflectResult(TypedDict):
    onTrack: bool
    advisory: str | None
    memories: list[ReflectMem]
    note: NotRequired[str]
    corrections: list[Correction]
    confirmed: list[str]


def _safe() -> ReflectResult:
    return {"onTrack": True, "advisory": None, "memories": [], "corrections": [], "confirmed": []}


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _memory(value: Any) -> ReflectMem | None:
    if not isinstance(value, dict):
        return None
    title, text, kind = _string(value.get("title")), _string(value.get("text")), value.get("type")
    if not title or not text or kind not in ("user", "feedback", "procedural", "semantic", "episodic"):
        return None
    result: ReflectMem = {"title": title, "text": text, "type": cast(MemoryType, kind)}
    if type(value.get("importance")) in (int, float):
        result["importance"] = value["importance"]
    if type(value.get("confidence")) in (int, float):
        result["confidence"] = value["confidence"]
    if content := _string(value.get("source")):
        result["source"] = content
    if content := _string(value.get("mergeInto")):
        result["mergeInto"] = content
    return result


def _correction(value: Any) -> Correction | None:
    if not isinstance(value, dict):
        return None
    target, action = _string(value.get("target")), value.get("action")
    if not target or action not in ("supersede", "revise"):
        return None
    result: Correction = {"target": target, "action": action, "reason": _string(value.get("reason"))}
    if action == "revise":
        text = _string(value.get("newText"))
        if not text:
            return None
        result["newText"] = text
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("JSON不接受非标准数值")


def parseReflectResult(raw: str) -> ReflectResult:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    body = fence[1] if fence else raw
    match = re.search(r"\{[\s\S]*\}", body)
    if match is None:
        return _safe()
    try:
        value = json.loads(match[0], parse_constant=_reject_constant)
    except (ValueError, TypeError):
        return _safe()
    if not isinstance(value, dict):
        return _safe()
    advisory = _string(value.get("advisory")) or None
    on_track = value["onTrack"] if type(value.get("onTrack")) is bool else advisory is None
    memories = value.get("memories", [])
    corrections = value.get("corrections", [])
    confirmed = value.get("confirmed", [])
    result: ReflectResult = {
        "onTrack": on_track, "advisory": None if on_track else advisory,
        "memories": [memory for item in memories if (memory := _memory(item)) is not None] if isinstance(memories, list) else [],
        "corrections": [correction for item in corrections if (correction := _correction(item)) is not None] if isinstance(corrections, list) else [],
        "confirmed": [item.strip() for item in confirmed if isinstance(item, str) and item.strip()] if isinstance(confirmed, list) else [],
    }
    if note := _string(value.get("note")):
        result["note"] = note
    return result
