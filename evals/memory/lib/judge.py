"""Source judge.ts (MIT): structured votes on independent rubrics."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ruocun.agent.reflect_result import ReflectResult
from ruocun.agent.unified_reflect import reflect
from ruocun.client.types import ChatMessage, StreamChatOptions
from ruocun.memory.distill import ModelCall

from .creds import EvalConfig, InvalidEvaluation
from .metrics import majorityVote


def _reject_constant(value: str) -> None:
    raise ValueError("JSON 不接受非有限常量。")


def parseJudgeJson(raw: str) -> dict[str, Any] | None:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(raw[start:end + 1], parse_constant=_reject_constant)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


async def judgeOnce(call: ModelCall, cfg: EvalConfig, prompt: str) -> dict[str, Any]:
    options: StreamChatOptions = {**cfg.options, "messages": [{"role": "user", "content": prompt}],
                                  "extra": {"thinking": {"type": "disabled"}, "temperature": 0}}
    result = parseJudgeJson(await call(options) or "")
    if result is None:
        raise InvalidEvaluation("judge 未返回可解析的 JSON。")
    return result


async def judgeBool(call: ModelCall, cfg: EvalConfig, prompt: str, key: str) -> tuple[bool, float]:
    votes = []
    for _ in range(cfg.judgeK):
        value = (await judgeOnce(call, cfg, prompt)).get(key)
        if type(value) is not bool:
            raise InvalidEvaluation("judge 缺少明确布尔投票。")
        votes.append(value)
    return majorityVote(votes)


async def checkedReflect(
    messages: list[ChatMessage], call: ModelCall, cfg: EvalConfig,
    existing: Sequence[Mapping[str, str]] = (), *, fork: bool = True,
) -> ReflectResult:
    if not messages:
        raise InvalidEvaluation("缺少有效的对话消息。")

    async def verify(options: StreamChatOptions) -> str:
        raw = await call(options) or ""
        fence = re.search(r"\x60{3}(?:json)?\s*([\s\S]*?)\x60{3}", raw)
        parsed = parseJudgeJson(fence[1] if fence else raw)
        if parsed is None or type(parsed.get("onTrack")) is not bool:
            raise InvalidEvaluation("反思响应缺少明确的 onTrack 判定。")
        return raw

    return await reflect(messages, options=cfg.options, call=verify, existing=existing, fork=fork, reasoningEffort="high")


def factCoveredPrompt(fact: str, extracted: list[Mapping[str, Any]]) -> str:
    items = "\n".join(f"{i}. 标题:{m.get('title', '(无)')} | 正文:{m['text']}" for i, m in enumerate(extracted, 1))
    return ("判断【金标事实】是否被任一【抽出记忆】语义覆盖，表述不同但同一事实也算覆盖。\n"
            f"金标事实:{fact}\n\n抽出记忆:\n{items or '(无)'}\n"
            '只输出 JSON:{"covered": true/false, "byTitle": "标题或null", "why": "一句话理由"}')


def memoryQualityPrompt(memory: Mapping[str, Any]) -> str:
    return (f"评价这条记忆: 标题={memory.get('title')} 类型={memory.get('type')} 正文={memory['text']}\n"
            "每维按 0–1 打分: 耐久、type/scope 合理、非目录倾倒、可执行。\n"
            '只输出 JSON:{"durable":0,"typeScopeCorrect":0,"notCatalogDump":0,"actionable":0,"why":"一句话"}')


def relevancePrompt(task: str, memory: str) -> str:
    return f"判断记忆对当前任务是否真正相关。\n任务:{task}\n记忆:{memory}\n" + '只输出 JSON:{"relevant":true/false}'


def pullWorthyPrompt(task: str, title: str) -> str:
    return (f"你仅看到记忆标题索引。面对当前任务会主动调用 memory_read 读取这条全文吗？\n任务:{task}\n记忆标题:{title}\n"
            '只输出 JSON:{"wouldRead":true/false}')
