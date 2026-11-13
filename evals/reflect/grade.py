"""Frozen reflect grade.ts (MIT), separate classification and semantic advisory scores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ruocun.memory.distill import ModelCall

from ..memory.lib.creds import EvalConfig, InvalidEvaluation
from ..memory.lib.judge import checkedReflect, judgeBool
from ..memory.lib.redact import redactText
from ..memory.lib.transcript import loadTranscript


async def gradeReflect(
    on_track: bool, advisory: str | None, gold: dict[str, Any], call: ModelCall, cfg: EvalConfig,
) -> dict[str, Any]:
    expected = gold.get("expectOnTrack")
    if type(expected) is not bool:
        raise InvalidEvaluation("反思金标缺少布尔 expectOnTrack。")
    flag = gold.get("expectFlag")
    points = None
    if not expected and isinstance(flag, str) and flag:
        points = 0
        if advisory:
            prompt = (f"判断反思提醒是否语义指出期望问题，表述不同也算命中。\n期望问题:{flag}\n反思提醒:{advisory}\n"
                      '只输出 JSON:{"onPoint":true/false,"why":"一句话理由"}')
            decision, _ = await judgeBool(call, cfg, prompt, "onPoint")
            points = int(decision)
    return {"gotOnTrack": on_track, "onTrackMatch": on_track == expected,
            "advisory": advisory, "advisoryOnPoint": points}


async def runReflectCase(directory: Path, call: ModelCall, cfg: EvalConfig) -> dict[str, Any]:
    gold = json.loads((directory / "gold.json").read_text(encoding="utf-8"))
    if not isinstance(gold, dict) or type(gold.get("expectOnTrack")) is not bool:
        raise InvalidEvaluation("反思金标无效。")
    flag = gold.get("expectFlag")
    if not gold["expectOnTrack"] and (not isinstance(flag, str) or not flag.strip()):
        raise InvalidEvaluation("报警金标缺少独立语义目标。")
    result = await checkedReflect(loadTranscript(directory / "conversation.jsonl"), call, cfg)
    advisory = result["advisory"]
    if advisory is not None:
        advisory = redactText(advisory, known_secret=cfg.options.get("apiKey", ""))
    score = await gradeReflect(result["onTrack"], advisory, gold, call, cfg)
    return {"expectedOnTrack": gold["expectOnTrack"], **score}
