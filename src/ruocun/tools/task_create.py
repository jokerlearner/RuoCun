"""通过当前任务管理器登记手工任务，返回供后续查询和更新使用的任务编号。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "为需要跨轮追踪的手工工作建一条任务记录，返回稳定 id。初始状态是 running，处理完要用 TaskUpdate 收尾。要运行子代理时调用 Agent。"
)


DESCRIPTION_EN = (
    "Create a tracked record for manual work spanning turns. The record starts as "
    "running and has a stable ID. Close it with TaskUpdate when the work ends. Use "
    "Agent to launch a child."
)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.taskManager is None:
        return "当前环境不支持任务追踪。"
    task_id = await ctx.taskManager.create(args["description"])
    task = ctx.taskManager.get(task_id)
    assert task is not None
    return f"已创建任务 {task_id}:{task.description}"


taskCreateTool = Tool(
    name="TaskCreate", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="plan", approval="auto",
    handler=_handler, schema=objectSchema({
        "description": {"type": "string", "minLength": 1, "description": "任务描述(简明扼要,会展示给用户)"},
    }, ["description"]), persistentEffect=True,
)
