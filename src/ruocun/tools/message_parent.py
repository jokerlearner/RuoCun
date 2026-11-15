"""将子代理的进展通过当前执行提供的报告入口发给父代理。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "后台子代理可向父代理汇报进展、发现或问题。progress 记录动态；attention（默认）让父代理在安全接缝处处理。发送后可以继续手头可做的工作；父代理用 "
    "TaskSend 回传。"
)


DESCRIPTION_EN = (
    "A background child can report progress, a finding, or a question to its parent. "
    "Use progress for an update or attention (the default) when the parent should act "
    "at a safe boundary. Continue available work after sending. The parent can reply "
    "with TaskSend."
)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    report = ctx.messageParent
    if report is None:
        return "你不是后台子代理(无父任务通道):你的结论会在完成时直接返回父代理,无需中途发送。"
    kind = args.get("kind", "attention")
    english = ctx.lang == "en"
    if not await report(args["message"], kind):
        return ("The original background run is no longer active; message not sent." if english else
                "原后台运行已不再活动，消息未发送。")
    if kind == "progress":
        return "Progress updated without waking the parent." if english else "进度已更新,不触发父代理续跑。"
    return "Sent to parent for handling at a safe boundary." if english else "已发送给父代理(它在安全边界处理)。"


messageParentTool = Tool(
    name="MessageParent", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="plan", approval="auto",
    handler=_handler, schema=objectSchema({
        "kind": {"type": "string", "enum": ["progress", "attention"],
                 "description": "普通进展用 progress;需要父代理处理用 attention(默认)"},
        "message": {"type": "string", "minLength": 1, "description": "发给父代理的中途消息(进度/发现/问题)"},
    }, ["message"]), shouldDefer=True, persistentEffect=True,
)
