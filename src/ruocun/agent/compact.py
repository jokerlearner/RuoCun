"""生成更短的模型上下文候选，并记录候选所引用的原消息位置。这里负责准备候选，由调用方发布原文归档并确认替换。

近期尾部保留策略改编自 DeepSeek Harness（MIT）。
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal, NotRequired, TypedDict

from ..client.types import ChatMessage, ContentPart
from .compaction_policy import estimateRequestTokens


def _jsLength(text: str) -> int:
    """按 UTF-16 代码单元计数，与 JavaScript 的 String.length 一致。"""
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def estimateTokens(messages: list[ChatMessage]) -> int:
    """按字符数除以三粗估 token，图片按固定一百字符计入。"""
    chars = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            chars += _jsLength(content)
        elif isinstance(content, list):
            for part in content:
                chars += _jsLength(part["text"]) if part["type"] == "text" else 100
        if message["role"] == "assistant" and message.get("tool_calls"):
            for call in message["tool_calls"]:
                chars += _jsLength(call["function"]["name"])
                chars += _jsLength(call["function"]["arguments"])
    return math.ceil(chars / 3)


def shouldCompact(messages: list[ChatMessage], maxTokens: float, ratio: float = .85) -> bool:
    return estimateTokens(messages) >= maxTokens * ratio


class CompactOptions(TypedDict):
    summarize: Callable[[list[ChatMessage]], Awaitable[str]]
    retainTokens: NotRequired[int]
    thresholdTokens: NotRequired[int]
    tools: NotRequired[list[dict[str, Any]]]
    protectedIndices: NotRequired[set[int]]
    archiveIdForRange: NotRequired[Callable[[tuple[int, ...], str], str]]
    measureMessages: NotRequired[Callable[[list[ChatMessage]], int]]


class CompactionError(RuntimeError):
    """当前模型上下文无法安全压缩，或候选达不到有效缩减。"""


@dataclass(frozen=True)
class CompactionReplacement:
    kind: Literal["summary", "prune"]
    new_index: int
    old_indices: tuple[int, ...]
    archive_id: str


@dataclass(frozen=True)
class CompactionCandidate:
    messages: list[ChatMessage]
    origins: tuple[int | None, ...]
    replacements: tuple[CompactionReplacement, ...]
    before_tokens: int
    after_tokens: int
    status: Literal["unchanged", "pruned", "summarized"]


def _isSummary(message: ChatMessage) -> bool:
    content = message.get("content")
    return (message.get("role") == "system" and isinstance(content, str)
            and content.startswith(("[早期对话摘要", "<compacted-summary>")))


def _isTodo(message: ChatMessage) -> bool:
    content = message.get("content")
    return message.get("role") == "system" and isinstance(content, str) and content.startswith("[当前任务清单]")


def _isHook(message: ChatMessage) -> bool:
    content = message.get("content")
    return (message.get("role") == "system" and isinstance(content, str)
            and content.startswith(("[[ruocun:session-start-hook]]\n", "[[dao:session-start-hook]]\n")))


def _balancedCuts(messages: list[ChatMessage]) -> list[bool]:
    pending: set[str] = set()
    seen: set[str] = set()
    balanced = [True]
    for message in messages:
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or ():
                call_id = call.get("id")
                if not isinstance(call_id, str) or not call_id or call_id in seen:
                    raise CompactionError("工具调用身份重复或无效，原上下文保留。")
                pending.add(call_id)
                seen.add(call_id)
        elif message.get("role") == "tool":
            call_id = message.get("tool_call_id")
            if call_id not in pending:
                raise CompactionError("工具结果缺少匹配调用，原上下文保留。")
            pending.remove(call_id)
        balanced.append(not pending)
    if pending:
        raise CompactionError("工具结果尚未配对，原上下文保留。")
    return balanced


def _archiveId(messages: list[ChatMessage], indices: tuple[int, ...], kind: str, opts: CompactOptions) -> str:
    callback = opts.get("archiveIdForRange")
    if callback is not None:
        return callback(indices, kind)
    raw = json.dumps({"kind": kind, "indices": indices, "messages": [messages[i] for i in indices]},
                     ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8", errors="backslashreplace")).hexdigest()[:16]


def _pruneContent(content: Any, archive_id: str) -> str | list[ContentPart] | None:
    blocks = ([{"type": "text", "text": content}] if isinstance(content, str)
              else content if isinstance(content, list) else [])
    total = sum(len(part.get("text", "")) for part in blocks if part.get("type") == "text")
    if total <= 8192:
        return None
    result: list[ContentPart] = []
    position, marked = 0, False
    for part in blocks:
        if part.get("type") != "text":
            result.append(part)
            continue
        text = part.get("text", "")
        stop = position + len(text)
        first = text[:max(0, min(len(text), 4096 - position))]
        last = text[max(0, total - 1024 - position):] if stop > total - 1024 else ""
        omitted = len(text) - len(first) - len(last)
        middle = "\n[…工具结果中间已省略…]\n" if omitted > 0 and not marked else ""
        marked = marked or omitted > 0
        if first or middle or last:
            result.append({**part, "text": first + middle + last})
        position = stop
    pointer = f"\n[原文归档:{archive_id}；用 ArchiveRead 读取完整结果。]"
    if result and result[-1].get("type") == "text":
        result[-1] = {**result[-1], "text": result[-1]["text"] + pointer}
    else:
        result.append({"type": "text", "text": pointer})
    return result[0]["text"] if isinstance(content, str) else result


def _pruneTools(
    messages: list[ChatMessage], opts: CompactOptions,
) -> tuple[list[ChatMessage], dict[int, str]]:
    candidate = list(messages)
    replacements: dict[int, str] = {}
    names = {call["id"]: call.get("function", {}).get("name")
             for message in messages for call in message.get("tool_calls") or ()}
    protected = opts.get("protectedIndices", set())
    for index, message in enumerate(messages):
        content = message.get("content")
        if (message.get("role") != "tool" or index in protected
                or names.get(message.get("tool_call_id")) == "TaskWait"):
            continue
        archive_id = _archiveId(messages, (index,), "prune", opts)
        pruned = _pruneContent(content, archive_id)
        if pruned is None:
            continue
        candidate[index] = {**message, "content": pruned}
        replacements[index] = archive_id
    return candidate, replacements


async def buildCompaction(
    messages: list[ChatMessage], opts: CompactOptions, pinned: str | None = None,
) -> CompactionCandidate:
    """生成精简后的模型上下文和精确的原消息索引映射，由调用方负责持久化。"""
    tools = opts.get("tools", [])
    measure = opts.get("measureMessages")

    def price(items: list[ChatMessage]) -> int:
        return measure(items) if measure is not None else estimateRequestTokens({"messages": items, "tools": tools})

    before = price(messages)
    framing = price([])

    def unchanged() -> CompactionCandidate:
        if "thresholdTokens" in opts and before >= opts["thresholdTokens"]:
            raise CompactionError("没有可安全压缩的旧区段，原上下文保留。")
        return CompactionCandidate(messages, tuple(range(len(messages))), (), before, before, "unchanged")

    if len(messages) <= 1:
        return unchanged()
    balanced = _balancedCuts(messages)
    threshold = opts.get("thresholdTokens")
    working, pruned = _pruneTools(messages, opts) if threshold is None or before >= threshold else (messages, {})

    def pruned_candidate() -> CompactionCandidate:
        kept = [index for index, message in enumerate(working) if not _isTodo(message)]
        result = [working[index] for index in kept]
        origins: list[int | None] = [None if index in pruned else index for index in kept]
        replacements = tuple(CompactionReplacement("prune", new_index, (old_index,), pruned[old_index])
                             for new_index, old_index in enumerate(kept) if old_index in pruned)
        if pinned and pinned.strip():
            result.append({"role": "system", "content": f"[当前任务清单]\n{pinned}"})
            origins.append(None)
        after = price(result)
        if after >= before:
            raise CompactionError("工具裁剪未降低请求压力，原上下文保留。")
        return CompactionCandidate(result, tuple(origins), replacements, before, after, "pruned")

    if pruned and (threshold is None or price(working) < threshold):
        return pruned_candidate()
    anchors = [0, *(i for i, item in enumerate(messages[1:], 1) if _isHook(item))]
    history = [i for i, item in enumerate(messages) if i not in anchors and not _isTodo(item)]
    if not history or len(history) == 1 and _isSummary(messages[history[0]]):
        return unchanged()
    retain = opts.get("retainTokens", max(1, math.floor(before * .16)))
    if type(retain) is not int or retain < 0:
        raise ValueError("retainTokens must be a nonnegative integer")
    accumulated, cut = 0, len(messages)
    for index in reversed(history):
        accumulated += price([working[index]]) - framing
        cut = index
        if accumulated >= retain:
            break
    for index in opts.get("protectedIndices", set()):
        if not 0 <= index < len(messages):
            raise ValueError("protected message index is outside the current projection")
        if index not in anchors:
            cut = min(cut, index)
    while cut > 0 and not balanced[cut]:
        cut -= 1
    selected = tuple(index for index in history if index < cut)
    if not selected:
        if pruned:
            return pruned_candidate()
        if "thresholdTokens" in opts and before >= opts["thresholdTokens"]:
            raise CompactionError("没有可安全压缩的旧区段，原上下文保留。")
        return unchanged()
    # 摘要请求沿用原始的连续前缀，让模型服务有机会命中缓存。
    # 裁剪旧消息和移动控制锚点只应用到压缩后的模型上下文。
    summary_sources = tuple(range(cut))
    summary = (await opts["summarize"](copy.deepcopy(messages[:cut]))).strip()
    if not summary:
        raise CompactionError("摘要为空，原上下文保留。")
    archive_id = _archiveId(messages, summary_sources, "summary", opts)
    checkpoint: ChatMessage = {"role": "system", "content":
        f"[早期对话摘要]\n{summary}\n[原文归档:{archive_id}；需要细节时用 ArchiveRead。]"}
    if price([checkpoint]) >= price([messages[index] for index in selected]):
        raise CompactionError("摘要未严格缩小被替换区段，原上下文保留。")
    tail = [index for index in history if index >= cut]
    result = [*[working[index] for index in anchors], checkpoint, *[working[index] for index in tail]]
    origins: list[int | None] = [*anchors, None, *[None if index in pruned else index for index in tail]]
    if pinned and pinned.strip():
        result.append({"role": "system", "content": f"[当前任务清单]\n{pinned}"})
        origins.append(None)
    after = price(result)
    if after >= before:
        raise CompactionError("压缩候选未降低请求压力，原上下文保留。")
    replacements = [CompactionReplacement("summary", len(anchors), summary_sources, archive_id)]
    replacements.extend(CompactionReplacement("prune", len(anchors) + 1 + tail_index, (index,), pruned[index])
                        for tail_index, index in enumerate(tail) if index in pruned)
    return CompactionCandidate(result, tuple(origins), tuple(replacements), before, after, "summarized")


async def compactMessages(
    messages: list[ChatMessage], opts: CompactOptions, pinned: str | None = None,
) -> list[ChatMessage]:
    """兼容入口只准备压缩候选。归档和上下文替换由调用方确认。"""
    return (await buildCompaction(messages, opts, pinned)).messages


def stripImagesFromMessages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """摘要请求把图片替换为 [image]，纯文本沿用原对象，保留完整原消息供归档。"""
    result: list[ChatMessage] = []
    for message in messages:
        content = message.get("content")
        if not isinstance(content, list):
            result.append(message)
            continue
        changed = False
        stripped: list[ContentPart] = []
        for part in content:
            if part["type"] == "image_url":
                changed = True
                if not (stripped and stripped[-1].get("type") == "text"
                        and stripped[-1].get("text") == "[image]"):
                    stripped.append({"type": "text", "text": "[image]"})
            else:
                stripped.append(part)
        result.append({**message, "content": stripped} if changed else message)
    return result
