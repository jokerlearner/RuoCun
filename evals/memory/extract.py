"""Frozen memory extract.ts (MIT): grade persisted facts and quality independently."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from statistics import fmean
from typing import Any

from ruocun.memory.distill import ModelCall
from ruocun.memory.store import routeScope

from .lib.creds import EvalConfig, InvalidEvaluation
from .lib.judge import checkedReflect, factCoveredPrompt, judgeBool, judgeOnce, memoryQualityPrompt
from .lib.metrics import aggregate
from .lib.redact import redactText
from .lib.transcript import loadTranscript

_DIMS = ("durable", "typeScopeCorrect", "notCatalogDump", "actionable")
_SCOPES = ("project", "user", "knowledge")


async def gradeExtraction(
    extracted: list[Mapping[str, Any]], gold: dict[str, Any], call: ModelCall, cfg: EvalConfig,
) -> dict[str, Any]:
    facts, must_not = gold.get("mustExtract"), gold.get("mustNot")
    if (not isinstance(facts, list) or not isinstance(must_not, list)
            or any(not isinstance(item, str) for item in must_not)
            or any(not isinstance(fact, dict) or not isinstance(fact.get("text"), str)
                   or fact.get("scope") not in _SCOPES for fact in facts)):
        raise InvalidEvaluation("提取金标格式无效。")
    results: list[dict[str, Any]] = []
    for fact in facts:
        covered, agreement = await judgeBool(call, cfg, factCoveredPrompt(fact["text"], extracted), "covered")
        results.append({"fact": fact["text"], "covered": covered, "agreement": agreement})
    profiles = [row["covered"] for fact, row in zip(facts, results, strict=True) if fact.get("profile")]
    noise = 0
    quality = []
    for memory in extracted:
        for unwanted in must_not:
            found, _ = await judgeBool(call, cfg, factCoveredPrompt(unwanted, [memory]), "covered")
            if found:
                noise += 1
                break
        for _ in range(cfg.judgeK):
            sample = await judgeOnce(call, cfg, memoryQualityPrompt(memory))
            dimensions = [sample.get(key, 0) for key in _DIMS]
            if any(type(value) not in (int, float) or not 0 <= value <= 1 for value in dimensions):
                raise InvalidEvaluation("记忆质量评分超出维度范围。")
            quality.append(fmean(dimensions))
    stats = aggregate(quality) if quality else None
    scopes = {routeScope(item["type"]) for item in extracted}
    return {"factRecall": fmean(row["covered"] for row in results) if results else 1.0,
            "profileRecall": fmean(profiles) if profiles else None,
            "precision": 1 - noise / len(extracted) if extracted else None,
            "quality": stats["median"] if stats else None, "qualityStdev": stats["stdev"] if stats else None,
            "typeScopeMatch": fmean(fact["scope"] in scopes for fact in facts) if facts else 1.0,
            "perFact": results}


async def runExtractCase(directory: Path, call: ModelCall, cfg: EvalConfig) -> dict[str, Any]:
    gold = json.loads((directory / "gold.json").read_text(encoding="utf-8"))
    if not isinstance(gold, dict) or not isinstance(gold.get("existing"), list):
        raise InvalidEvaluation("缺少提取金标。")
    result = await checkedReflect(loadTranscript(directory / "conversation.jsonl"), call, cfg, gold["existing"])
    key = cfg.options.get("apiKey", "")
    items: list[Mapping[str, Any]] = [
        {**item, "title": redactText(item["title"], known_secret=key),
         "text": redactText(item["text"], known_secret=key)} for item in result["memories"]
    ]
    return await gradeExtraction(items, gold, call, cfg)
