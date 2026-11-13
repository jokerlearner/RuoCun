"""Fork context construction from the frozen reference fork_agent.ts and resume_agent.ts (MIT)."""
from __future__ import annotations

import copy
from collections.abc import Sequence

from ..client.types import ChatMessage
from .agent_defs import AgentDefinition

FORK_AGENT = AgentDefinition(
    agent_type="fork", system_prompt="", model="inherit",
    when_to_use="以 fork=true 在父代理上下文中启动子任务。agent_type 不能指定此角色。",
)
_PLACEHOLDER = "Fork 已启动 - 后台处理中"
_BOILERPLATE = """<fork-boilerplate>
本次调用由父代理分派。继承的历史用于理解上下文，其中交给父代理的工作不得重复。仅执行下面的子任务，不再派发子代理，也不更改主任务进度。

所需操作用 Bash、Read、Write 等可用工具完成。过程中保持静默，不发问题、进度旁白或进一步建议。发现范围外的事项只留一句提示。若修改文件，先提交本次改动，再将提交哈希写入结果。

结束时给父代理一份纯文本记录，通常不超过 500 字。第一行从“范围:”开始。用“结果:”写已核实的结论。调查任务附“关键文件:”，修改过文件时附“改动文件:”和提交哈希，存在阻塞时写“问题:”。省略与本次任务无关的字段，报告后结束。
</fork-boilerplate>

分派事项："""


def buildForkContextMessages(parent_messages: Sequence[ChatMessage], directive: str) -> list[ChatMessage]:
    messages = copy.deepcopy(list(parent_messages))
    body = _BOILERPLATE + directive
    tail = messages[-1] if messages else None
    if tail is not None and tail.get("role") == "assistant" and tail.get("tool_calls"):
        parts = [{"type": "text", "text": _PLACEHOLDER} for _ in tail["tool_calls"]]
        parts.append({"type": "text", "text": body})
        messages.append({"role": "user", "content": parts})
    else:
        messages.append({"role": "user", "content": body})
    return messages


def forkRequestMessages(parent_messages: Sequence[ChatMessage], task: str) -> list[ChatMessage]:
    directive = "[fork 任务] " + task
    messages = buildForkContextMessages(parent_messages, directive)
    # The placeholder remains user text. Only actual tool messages can pair an assistant call.
    paired_ids = {message.get("tool_call_id") for message in messages if message.get("role") == "tool"}
    return [message for message in messages if message.get("role") != "assistant"
            or all(call.get("id") in paired_ids for call in message.get("tool_calls") or ())]
