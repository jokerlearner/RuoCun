"""Frozen memory injection_ab.ts (MIT), comparing names for both axes."""

from pathlib import Path
from typing import Any

from ruocun.memory.distill import ModelCall
from ruocun.memory.inject import selectForInjection

from .lib.creds import EvalConfig
from .lib.judge import judgeBool, pullWorthyPrompt
from .lib.metrics import precisionRecall
from .recall import loadRecallCase


async def gradeInjectionAB(
    push_names: list[str], pull_names: list[str], gold: dict[str, Any], call: ModelCall, cfg: EvalConfig,
) -> dict[str, Any]:
    reference = set(gold["valueGold"])
    selected = set()
    for name in pull_names:
        vote, _ = await judgeBool(call, cfg, pullWorthyPrompt(gold["task"], name), "wouldRead")
        if vote:
            selected.add(name)
    push = precisionRecall(set(push_names), reference)
    pull = precisionRecall(selected, reference)
    return {"push": push, "pull": pull, "delta": push["r"] - pull["r"]}


async def runInjectionABCase(directory: Path, call: ModelCall, cfg: EvalConfig) -> dict[str, Any]:
    gold, candidates, today = await loadRecallCase(directory)
    push = [item.mem.name for item in selectForInjection(candidates, today)]
    pull = [item.mem.name for item in candidates if item.verdict != "stale"]
    return await gradeInjectionAB(push, pull, gold, call, cfg)
