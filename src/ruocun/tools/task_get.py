"""从当前子代理任务管理器读取指定任务的状态和描述，并将时间转换为可显示的格式。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "按任务 id 查看状态、起止时间和最终结果或失败原因。可从 TaskList 或创建任务的响应查到 id。仍在运行时可能还没有结果。"
)


DESCRIPTION_EN = (
    "Get a task’s state, timestamps, and final result or failure by ID. Obtain the ID "
    "from TaskList or the call that created the task. A running task may have no final "
    "result yet."
)


def _iso(timestamp: int | None) -> str:
    if timestamp is None:
        return "未记录"
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.taskManager is None:
        return "当前环境不支持任务追踪。"
    task_id = args["id"]
    task = ctx.taskManager.get(task_id)
    if task is None:
        return f"未找到任务 {task_id}。"
    lines = [f"id: {task.id}", f"描述: {task.description}", f"状态: {task.status}", f"开始: {_iso(task.startedAt)}"]
    if task.endedAt is not None:
        lines.append(f"结束: {_iso(task.endedAt)}")
    if task.result:
        lines.append(f"结果:\n{task.result}")
    if task.error:
        lines.append(f"报错:\n{task.error}")
    return "\n".join(lines)


taskGetTool = Tool(
    name="TaskGet", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="read", approval="auto",
    handler=_handler, schema=objectSchema({"id": {"type": "string", "minLength": 1, "description": "任务 id"}}, ["id"]),
)
