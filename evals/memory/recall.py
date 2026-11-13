"""Frozen memory recall.ts (MIT), using product memory validation and injection."""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

from ruocun.memory.distill import ModelCall
from ruocun.memory.frontmatter import parseMemoryFile
from ruocun.memory.inject import ValidatedMemory, selectForInjection
from ruocun.memory.store import keepKnowledgeForProject, routeScope
from ruocun.memory.validate import validateMemory

from .lib.creds import EvalConfig, InvalidEvaluation
from .lib.judge import judgeBool, relevancePrompt
from .lib.metrics import precisionRecall, relevanceGap


async def loadRecallCase(directory: Path) -> tuple[dict[str, Any], list[ValidatedMemory], str]:
    gold = json.loads((directory / "context.json").read_text(encoding="utf-8"))
    if (not isinstance(gold, dict) or not isinstance(gold.get("task"), str)
            or any(not isinstance(gold.get(key), list) or any(not isinstance(item, str) for item in gold[key])
                   for key in ("valueGold", "relevanceGold"))):
        raise InvalidEvaluation("召回金标格式无效。")
    today = date.today().isoformat()
    project_id = gold.get("projectId")
    validated = []
    with tempfile.TemporaryDirectory(prefix="rc-recall-") as temporary:
        for file in sorted((directory / "store").iterdir()):
            if file.suffix != ".md" or file.is_symlink() or not file.is_file():
                continue
            memory = parseMemoryFile(file.stem, file.read_text(encoding="utf-8"))
            if memory is None:
                raise InvalidEvaluation("候选记忆文件格式无效。")
            if memory.status != "active":
                continue
            if project_id and routeScope(memory.type) == "knowledge" and not keepKnowledgeForProject(memory, project_id):
                continue
            validated.append(ValidatedMemory(memory, await validateMemory(memory, Path(temporary), today)))
    if not validated and (gold["valueGold"] or gold["relevanceGold"]):
        raise InvalidEvaluation("召回样本缺少候选记忆。")
    return gold, validated, today


async def gradeRecall(
    injected_names: list[str], stale_names: list[str], store: list[tuple[str, str]], gold: dict[str, Any],
    call: ModelCall, cfg: EvalConfig,
) -> dict[str, Any]:
    injected = set(injected_names)
    relevant = set()
    for name, text in store:
        vote, _ = await judgeBool(call, cfg, relevancePrompt(gold["task"], text), "relevant")
        if vote:
            relevant.add(name)
    reference = set(gold["relevanceGold"])
    return {"valuePR": precisionRecall(injected, set(gold["valueGold"])),
            "staleLeak": sum(name in injected for name in stale_names),
            "relevanceGapValue": relevanceGap(injected, reference),
            "judgeHumanAgreement": precisionRecall(relevant, reference)["f1"]}


async def runRecallCase(directory: Path, call: ModelCall, cfg: EvalConfig) -> dict[str, Any]:
    gold, candidates, today = await loadRecallCase(directory)
    injected = [item.mem.name for item in selectForInjection(candidates, today)]
    stale = [item.mem.name for item in candidates if item.verdict == "stale"]
    store = [(item.mem.name, item.mem.text) for item in candidates]
    return await gradeRecall(injected, stale, store, gold, call, cfg)
