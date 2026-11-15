"""组装轮末反思所需的模型输入，并过滤返回内容。写入记忆与展示提醒由外层运行时负责。"""

from __future__ import annotations

import copy
import json
import threading
from collections.abc import Mapping, Sequence

from ..client.types import ChatMessage, StreamChatOptions
from ..memory.distill import ModelCall, isCatalogNoise
from ..memory.secrets import findSecrets
from .experience_memory import EXPERIENCE_TAIL
from .reflect_result import ReflectResult, parseReflectResult
from .reflect_tail import REFLECT_TAIL


def buildTail(existing: Sequence[Mapping[str, str]] = ()) -> str:
    if not existing:
        return REFLECT_TAIL.replace("{existing}", "(无)", 1)
    titles = "\n".join("- " + item["title"] for item in existing)
    with_text = "\n".join(f"· {item['title']}:{item['text']}" for item in existing[:30])
    block = f"〈全部已记标题〉(mergeInto 可指向其中任一):\n{titles}\n\n〈高价值条目正文〉(判微妙重复用):\n{with_text}"
    return REFLECT_TAIL.replace("{existing}", block, 1)


def _transcript(messages: Sequence[ChatMessage]) -> str:
    lines = []
    for message in messages:
        if message.get("role") == "system":
            continue
        value = message.get("content")
        content = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, separators=(",", ":")) if value else ""
        lines.append(str(message.get("role", "undefined")) + ": " + content)
    return "\n".join(lines).encode("utf-16-le", errors="surrogatepass")[-48000:].decode("utf-16-le", errors="surrogatepass")


async def reflect(
    messages: Sequence[ChatMessage], *, options: StreamChatOptions, call: ModelCall,
    existing: Sequence[Mapping[str, str]] = (), fork: bool = False, reasoningEffort: str = "max",
    signal: threading.Event | None = None,
    taskAware: bool = False,
) -> ReflectResult:
    if signal is not None and signal.is_set():
        raise InterruptedError("反思已取消。")
    request = options.copy()
    request.pop("parallelToolCalls", None)
    tail = buildTail(existing) + (EXPERIENCE_TAIL if taskAware else "")
    if fork:
        request["messages"] = [*copy.deepcopy(messages), {"role": "user", "content": tail}]
        request["extra"] = {"reasoning_effort": reasoningEffort}
        if request.get("tools"):
            request["parallelToolCalls"] = True
        else:
            request.pop("tools", None)
    else:
        request.pop("tools", None)
        request["messages"] = [{"role": "system", "content": tail}, {"role": "user", "content": _transcript(messages)}]
        request["extra"] = {"thinking": {"type": "disabled"}, "temperature": 0}
    parsed = parseReflectResult(await call(request) or "", taskAware=taskAware)
    if signal is not None and signal.is_set():
        raise InterruptedError("反思已取消，结果未应用。")
    parsed["memories"] = [memory for memory in parsed["memories"]
        if memory.get("importance", 5) >= 4
        and not isCatalogNoise(memory["text"]) and not isCatalogNoise(memory["title"])
        and not findSecrets(memory["text"]) and not findSecrets(memory["title"])
        and (memory["type"] != "feedback" or "为什么" in memory["text"] and "怎么用" in memory["text"])]
    return parsed
