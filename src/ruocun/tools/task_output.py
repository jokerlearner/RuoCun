"""Frozen tools/task_output.ts (MIT), incremental output per task object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary

from .schema import objectSchema
from .types import Tool, ToolContext

if TYPE_CHECKING:
    from ..agent.tasks import BgTask, TaskManager

DESCRIPTION = (
    "按 id 查看后台子代理新增的活动，每次读取推进游标。最终结果用 TaskGet 查看，需要等待且手头没有独立工作时用 TaskWait。手工任务没有中间输出。"
)

DESCRIPTION_EN = (
    "Read newly recorded activity from a background child by ID. The read advances a "
    "cursor. Use TaskGet for the final result, or TaskWait when no independent work "
    "remains. Manual records have no intermediate activity."
)

_cursors: WeakKeyDictionary[BgTask, int] = WeakKeyDictionary()


def _trunc(value: str) -> str:
    units = value.encode("utf-16-le", errors="surrogatepass")
    return value if len(units) <= 1000 else units[:1000].decode("utf-16-le", errors="replace") + "…(截断)"


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(item["text"] for item in value if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str))
    return ""


def _render(message: dict[str, Any]) -> str:
    role = message.get("role")
    content = _text(message.get("content")).strip()
    if role == "assistant":
        parts = [_trunc(content)] if content else []
        for call in message.get("tool_calls") or ():
            function = call["function"]
            parts.append(f"[调用 {function['name']}] {_trunc(function['arguments'])}")
        return "\n".join(parts)
    if role in {"tool", "user"} and content:
        return ("[结果] " if role == "tool" else "[追加消息] ") + _trunc(content)
    return ""


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    manager: TaskManager | None = getattr(ctx, "taskManager", None)
    if manager is None:
        return "当前环境不支持任务追踪。"
    task = manager.get(args["id"])
    if task is None:
        return f"未找到任务 {args['id']}。"
    if not task.messages:
        if task.status == "running":
            return "当前没有新活动。后台代理完成时会通知；手工任务的状态和详情请用 TaskGet 查询。"
        return "没有已记录的任务活动。用 TaskGet 查看结论。"
    fresh = task.messages[_cursors.get(task, 0):]
    _cursors[task] = len(task.messages)
    lines = [line for message in fresh if (line := _render(message))]
    if not lines:
        return f"状态: {task.status}(自上次查询以来没有新消息)。完成后会自动通知,不要连续查询。"
    return "\n".join([f"状态: {task.status}", *lines])


taskOutputTool = Tool(
    name="TaskOutput", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="read", approval="auto",
    handler=_handler, schema=objectSchema({"id": {"type": "string", "minLength": 1,
                                                "description": "任务 id(来自 TaskList/agent(background:true) 的返回)"}}, ["id"]),
)
