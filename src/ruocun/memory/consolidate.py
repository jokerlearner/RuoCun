"""按阈值选出需要归并的来源，通过模型生成合并计划，再确认计划写入。新记录可靠发布之后才标记来源被替代。"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from threading import Event
from typing import Literal, NotRequired, TypedDict, cast

from ..client.types import StreamChatOptions
from ..tools.types import ToolRejected
from .distill import ModelCall
from .memory_audit import ConsolidationAudit
from .secrets import findSecrets
from .store import MemoryEntry, MemoryStore, dedupKey, slug
from .types import Memory, MemoryType, Scope, newMemory


class CanonicalMemory(TypedDict):
    title: str
    text: str
    type: NotRequired[str]
    importance: NotRequired[int | float]
    confidence: NotRequired[int | float]
    source: NotRequired[str]


class ConsolidationGroup(TypedDict):
    canonical: CanonicalMemory
    supersede: list[str]
    reason: str


class ConsolidationPlan(TypedDict):
    groups: list[ConsolidationGroup]


def _rejectConstant(value: str) -> None:
    raise ValueError("无效 JSON 数字")


def _parseGroup(raw: object) -> ConsolidationGroup | None:
    if not isinstance(raw, dict):
        return None
    candidate, supersede = raw.get("canonical"), raw.get("supersede")
    if not isinstance(candidate, dict) or not isinstance(supersede, list):
        return None
    title, text = candidate.get("title"), candidate.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    canonical: CanonicalMemory = {"title": title.strip() if isinstance(title, str) else "", "text": text.strip()}
    kind, source = candidate.get("type"), candidate.get("source")
    importance, confidence = candidate.get("importance"), candidate.get("confidence")
    if isinstance(kind, str):
        canonical["type"] = kind
    if isinstance(source, str) and source.strip():
        canonical["source"] = source.strip()
    if type(importance) is int or type(importance) is float:
        canonical["importance"] = importance
    if type(confidence) is int or type(confidence) is float:
        canonical["confidence"] = confidence
    reason = raw.get("reason")
    return {"canonical": canonical, "supersede": [name for name in supersede if isinstance(name, str) and name.strip()],
            "reason": reason.strip() if isinstance(reason, str) else ""}


def parseConsolidationPlan(raw: str) -> ConsolidationPlan:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    body = re.search(r"\{[\s\S]*\}", fence[1] if fence else raw)
    if body:
        try:
            data = json.loads(body[0], parse_constant=_rejectConstant)
        except ValueError:
            return {"groups": []}
        if isinstance(data, dict) and isinstance(data.get("groups"), list):
            return {"groups": [group for item in data["groups"] if (group := _parseGroup(item)) is not None]}
    return {"groups": []}


Force = Literal["aggressive", "medium", "conservative"]


@dataclass(frozen=True, slots=True)
class ConsolCfg:
    days: int
    min: int
    force: Force


_CONFIGS: dict[Scope, ConsolCfg] = {
    "user": ConsolCfg(3, 12, "aggressive"),
    "knowledge": ConsolCfg(3, 15, "medium"),
    "project": ConsolCfg(3, 20, "conservative"),
}
_FORCE_LINES: dict[Force, str] = {
    "aggressive": "积极处理：同一用户偏好维度可合成一条。",
    "medium": "按技术事实归并重复记录。",
    "conservative": "保守处理：只处理明确冗余或相互冲突的同一事实。主题不同或关系不清时保留原记录。",
}
_DAY_MS = 86_400_000


def consolidationCfg(scope: Scope) -> ConsolCfg:
    return _CONFIGS[scope]


def shouldConsolidate(lastMs: int, liveCount: int, now: int, cfg: ConsolCfg) -> bool:
    return liveCount >= cfg.min and now - lastMs >= cfg.days * _DAY_MS


def buildConsolidatePrompt(scope: Scope, mems: Sequence[Memory]) -> str:
    lines = "\n".join(f"- name={m.name} | type={m.type}{' | source=' + m.source if m.source else ''} | "
                      f"{m.title or ''}: {m.text}" for m in mems)
    return f"""为若存的 {scope} 记忆提出合并计划。当前策略为：{_FORCE_LINES[consolidationCfg(scope).force]}

从以下已生效条目找出表达同一事实的记录：
{lines}

每个合并组需要一条完整的 canonical，以及它替换的条目 name 列表 supersede 和简短 reason。canonical 包含 title、text、type、importance、confidence 和原 source。只合并同一 source 的条目。明确陈述与推断的证据各自保留。组内取最高置信度。遇到直接冲突时优先选择用户陈述和较新的证据。

只返回一个 JSON 对象，顶层键为 groups，数组的每项含 canonical、supersede 和 reason。没有可靠的合并对象时返回 {{"groups":[]}}。"""


async def consolidate(
    scope: Scope, mems: Sequence[Memory], *, options: StreamChatOptions, call: ModelCall,
) -> ConsolidationPlan:
    request = options.copy()
    request.pop("tools", None)
    request.pop("parallelToolCalls", None)
    request["messages"] = [{"role": "user", "content": buildConsolidatePrompt(scope, mems)}]
    request["extra"] = {"thinking": {"type": "disabled"}, "temperature": 0}
    try:
        return parseConsolidationPlan(await call(request) or "")
    except Exception:
        return {"groups": []}


@dataclass(frozen=True, slots=True)
class AppliedConsolidation:
    merged: int
    superseded: int
    reasons: list[str]


def _origin(memory: Memory) -> tuple[str | None, str | None, str | None]:
    return memory.source, memory.sourceHash, memory.origin


def _canonical(
    proposal: CanonicalMemory, name: str, base: Memory, today: str, *, existing: bool,
) -> Memory:
    importance = proposal.get("importance", 5)
    if isinstance(importance, float) and not math.isfinite(importance):
        importance = 5
    confidence = proposal.get("confidence", base.confidence) if not existing else base.confidence
    if confidence is not None and not 0 <= confidence <= 1:
        confidence = base.confidence
    return replace(base, name=name, title=proposal["title"] or base.title, text=proposal["text"],
                   created=base.created if existing else today, lastUsed=today,
                   importance=max(base.importance, importance) if existing else importance,
                   confidence=confidence, uses=base.uses + 1 if existing else 0)


def _cancelled(signal: Event | None) -> bool:
    return signal is not None and signal.is_set()


def _nativeActive(entries: Sequence[MemoryEntry], scope: Scope) -> dict[str, MemoryEntry]:
    return {entry.memory.name: entry for entry in entries
            if entry.source is None and entry.scope == scope and entry.memory.status == "active"}


async def applyConsolidationPlan(
    store: MemoryStore, scope: Scope, plan: ConsolidationPlan, existing: Sequence[MemoryEntry], today: str, *,
    signal: Event | None = None,
) -> AppliedConsolidation:
    """先确认合并后的正式记录已经发布，再将来源记录标记为已替代。"""
    original = _nativeActive(existing, scope)
    current = _nativeActive(await store.loadNative(scope), scope) if plan["groups"] else {}
    used: set[str] = set()
    reasons: list[str] = []
    superseded = 0
    for group in plan["groups"]:
        if _cancelled(signal):
            break
        names = tuple(dict.fromkeys(group["supersede"]))
        targets = [original[name] for name in names if name in original]
        proposal = group["canonical"]
        name = slug(proposal["title"] or proposal["text"])
        expected = next((entry for entry in original.values()
                         if entry.memory.name == name or dedupKey(entry.memory) == name), None)
        if targets:
            if len(targets) != len(names):
                continue
            base = expected.memory if expected is not None else targets[0].memory
        else:
            # 计划中的旧记录均未解析到时，仍可按计划独立新增一条。
            if expected is not None or name in used or any(
                entry.memory.name == name or dedupKey(entry.memory) == name for entry in current.values()
            ):
                continue
            kind = proposal.get("type", "user")
            if kind not in ("user", "feedback", "semantic", "procedural", "episodic"):
                kind = "user"
            base = newMemory(name=name, text=proposal["text"], type=cast(MemoryType, kind), today=today)
        anchors = targets + ([expected] if expected is not None else [])
        identity = _origin(base)
        if any(entry.memory.locked or _origin(entry.memory) != identity or entry.memory.name in used
               or current.get(entry.memory.name) != entry for entry in anchors):
            continue
        canonical = _canonical(proposal, expected.memory.name if expected is not None else name, base, today,
                               existing=expected is not None)
        fields = (canonical.title, canonical.text, *identity)
        if any(value and findSecrets(value) for value in fields):
            continue
        if not await store.publishExpected(
            scope, canonical, expected, preserveOriginal=expected is not None, signal=signal,
        ):
            continue
        used.update(entry.memory.name for entry in anchors)
        used.add(canonical.name)
        reasons.append(group["reason"])
        for entry in targets:
            if _cancelled(signal) or entry.memory.name == canonical.name:
                continue
            old = replace(entry.memory, status="superseded", supersededBy=canonical.name, validUntil=today)
            if await store.publishExpected(scope, old, entry, signal=signal):
                superseded += 1
    return AppliedConsolidation(len(reasons), superseded, reasons)


async def maybeConsolidate(
    store: MemoryStore, scope: Scope, *, today: str, now: int, options: StreamChatOptions, call: ModelCall,
    signal: Event | None = None, onAudit: Callable[[ConsolidationAudit], None] | None = None,
) -> None:
    """按来源条件执行一次合并。遇到结果不明的写入时停止当前作用域，保留待确认状态。"""
    if _cancelled(signal):
        return
    cfg = consolidationCfg(scope)
    try:
        existing = await store.loadNative(scope)
        if len(existing) < cfg.min or _cancelled(signal):
            return
        last = await store.readConsolidationMarker(scope)
        if not shouldConsolidate(last, len(existing), now, cfg) or _cancelled(signal):
            return
        plan = await consolidate(scope, [entry.memory for entry in existing], options=options, call=call)
        if _cancelled(signal) or await store.readConsolidationMarker(scope) != last:
            return
        result = await applyConsolidationPlan(store, scope, plan, existing, today, signal=signal)
        if _cancelled(signal):
            return
        await store.writeConsolidationMarker(scope, now, signal=signal)
        if onAudit is not None:
            onAudit({"scope": scope, "groups": result.merged, "superseded": result.superseded, "reasons": result.reasons})
    except ToolRejected:
        return
