"""Check a child agent’s tool calls before accepting its result."""
from __future__ import annotations

import re
from collections.abc import Awaitable, Callable

from ..client.types import ChatMessage, StreamChatOptions
from ..permissions.classifier import buildClassifierTranscript
from ..permissions.classifier_model import ModelContext, createClassifierRunner

Handoff = Callable[[list[ChatMessage], str], Awaitable[str | None]]
_UNAVAILABLE = "子代理操作未能自动复核，请先手动检查，再使用它的结果。"
_SYSTEM = (
    "检查已结束的子代理调用，确认是否需要人工复核。逐条比较调用与任务范围。遇到不可恢复的破坏、"
    "凭据访问（包括 .ssh、.aws 和 .env）、写到工作区之外、与任务无关的危险行为，"
    "或向外部传输敏感信息时选择 block。任务范围内的普通读取和可恢复编辑可选择 allow。"
    "若证据不足以排除影响，选择 block。"
    "仅返回 <decision>allow</decision> 或 <decision>block</decision><reason>简述操作及其风险</reason>。"
)


def createAgentHandoff(
    get_context: Callable[[], ModelContext], request: Callable[[StreamChatOptions], Awaitable[str | None]],
    notice: Callable[[str], None],
) -> Handoff:
    choose_model = createClassifierRunner(notice)

    async def handoff(messages: list[ChatMessage], agent_type: str) -> str | None:
        transcript = buildClassifierTranscript(messages)
        if not transcript:
            return None
        context = get_context()

        async def ask(model: str) -> str | None:
            return await request({
                "baseUrl": context["baseUrl"], "apiKey": context["apiKey"], "provider": context["provider"],
                "model": model, "extra": {"thinking": {"type": "disabled"}, "temperature": 0},
                "messages": [{"role": "system", "content": _SYSTEM},
                             {"role": "user", "content": f"角色：{agent_type}\n调用记录：\n{transcript}\n\n根据以上记录给出判定。"}],
            })

        try:
            answer = await choose_model(context, ask)
        except Exception:
            return _UNAVAILABLE
        decision = re.search(r"<decision>\s*(allow|block)\s*</decision>", answer or "", re.IGNORECASE)
        if decision is None:
            return _UNAVAILABLE
        if decision[1].lower() == "allow":
            return None
        reason = re.search(r"<reason>\s*([\s\S]*?)\s*</reason>", answer or "", re.IGNORECASE)
        detail = reason[1].strip() if reason is not None else "未知"
        return f"安全警告:子代理执行了可能违反安全策略的操作。原因:{detail or '未知'}。请仔细审查子代理的操作后再信任其输出。"

    return handoff
