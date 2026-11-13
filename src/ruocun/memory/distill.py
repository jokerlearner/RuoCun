"""Extract persistent memories from recent conversation evidence."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import replace
from typing import cast

from ..client.types import ChatMessage, StreamChatOptions
from .secrets import findSecrets
from .store import slug
from .types import Memory, MemoryType, newMemory

ModelCall = Callable[[StreamChatOptions], Awaitable[str | None]]

_SYS = """为未来的若存会话提取值得持久保存的记录。每条必须独立读得懂，类型决定它的适用范围：

- user：适用于这个人的长期偏好、目标、环境或背景。推断的事实标低置信度，例如 0.4 到 0.6。
- feedback：可跨项目使用的工作方式，来自用户纠正或明确认可。text 写规则、为什么、怎么用。重要度通常在 7 到 9。
- procedural：换项目仍有效的工具、框架或平台经验，包含适用条件。
- semantic：只对当前项目成立的稳定事实，例如架构、数据流和经过确认的决策。
- episodic：当前项目可供接续的进展和下一步。写清项目名，重要度通常在 6 到 8。

如果换一个项目就不成立，优先选项目级类型。舍弃当前会话的临时操作、情绪、随手可读的实现细节、若存自带的工具与技能目录。不要记录凭据、秘密或没有长期用途的信息。

输出 JSON 数组。每个对象含 text、type、importance，可选 confidence（0 到 1）和 source。importance 可用 5 表示一般、7 表示重要、9 表示关键。只有实际证据来自文件时才填 source 为路径。没有合适的记录时返回 []。数组之外无需其他文字。"""

_CATALOG_PATTERNS = (
    re.compile(r"使用\s*[A-Za-z0-9_./-]+\s*(技能|工具)"),
    re.compile(r"[0-9]+\s*个技能"),
    re.compile(r"工具名.*改为"),
)
_VALID_TYPES = {"user", "feedback", "semantic", "procedural", "episodic"}


def isCatalogNoise(text: str) -> bool:
    return any(pattern.search(text) for pattern in _CATALOG_PATTERNS)


def _rejectConstant(value: str) -> None:
    raise ValueError("无效 JSON 数字")


def _number(value: object) -> float | int | None:
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    return None


def _extract(raw: str, today: str) -> list[Memory]:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    array = re.search(r"\[[\s\S]*\]", fence[1] if fence else raw)
    if not array:
        return []
    try:
        items = json.loads(array[0], parse_constant=_rejectConstant)
    except ValueError:
        return []
    if not isinstance(items, list):
        return []
    memories: list[Memory] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text, kind, source = item.get("text"), item.get("type"), item.get("source")
        if not isinstance(text, str) or not isinstance(kind, str) or kind not in _VALID_TYPES:
            continue
        importance = _number(item.get("importance"))
        importance = 5 if importance is None else importance
        if importance < 4 or isCatalogNoise(text) or findSecrets(text):
            continue
        if isinstance(source, str) and findSecrets(source):
            continue
        memory = newMemory(name=slug(text), text=text, type=cast(MemoryType, kind), today=today,
                           confidence=_number(item.get("confidence")), source=source if isinstance(source, str) else None)
        memories.append(replace(memory, importance=importance))
    return memories


def _transcript(messages: Sequence[ChatMessage]) -> str:
    lines = []
    for message in messages:
        role = message.get("role", "undefined")
        if role == "system":
            continue
        content = message.get("content")
        if isinstance(content, list):
            # JS String() renders content-part objects without including their image payload.
            content = ",".join("[object Object]" for _ in content)
        lines.append(f"{role}: {content if content is not None else ''}")
    return "\n".join(lines).encode("utf-16-le", errors="surrogatepass")[-48000:].decode(
        "utf-16-le", errors="surrogatepass",
    )


async def distill(
    messages: Sequence[ChatMessage], *, today: str, options: StreamChatOptions, call: ModelCall,
    fork: bool = False, incremental: bool = False, reasoningEffort: str = "max",
) -> list[Memory]:
    request = options.copy()
    request.pop("parallelToolCalls", None)
    if fork:
        task = ("只处理上次记录之后的新信息，跳过早期已经保存的内容。返回 JSON 数组。"
                if incremental else "在以上完整对话中挑选可长期使用的信息，返回 JSON 数组。")
        request["messages"] = [*messages, {"role": "user", "content": f"{_SYS}\n\n{task}"}]
        request["extra"] = {"reasoning_effort": reasoningEffort}
        if request.get("tools"):
            request["parallelToolCalls"] = True
        else:
            request.pop("tools", None)
    else:
        request.pop("tools", None)
        request["messages"] = [{"role": "system", "content": _SYS},
                               {"role": "user", "content": _transcript(messages)}]
        request["extra"] = {"thinking": {"type": "disabled"}, "temperature": 0}
    return _extract(await call(request) or "", today)
