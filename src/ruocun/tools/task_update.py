"""通过任务管理器修改当前任务的描述或状态，保留管理器负责的状态约束。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "按 id 修改任务描述。手工任务还可以用 completed、failed、canceled 结束并附结果。执行任务由运行器结算。"
)


DESCRIPTION_EN = (
    "Edit a task description by ID. Manual records can also be closed as completed, failed, "
    "or canceled with a result. The runner settles tasks that execute work."
)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    manager = ctx.taskManager
    if manager is None:
        return "当前环境不支持任务追踪。"
    task_id, status = args["id"], args.get("status")
    task = manager.get(task_id)
    if task is None:
        return f"未找到任务 {task_id}。"
    if status and task.kind != "manual":
        return "执行任务由运行时结算,请用 TaskStop 请求取消。"
    if not await manager.update(task_id, description=args.get("description"), status=status, result=args.get("result")):
        return f"任务 {task_id} 已结束,状态不可再改(若本次同时改了 description,那部分已生效)。"
    return f"已更新任务 {task_id}。"


taskUpdateTool = Tool(
    name="TaskUpdate", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="plan", approval="auto",
    handler=_handler, schema=objectSchema({
        "id": {"type": "string", "minLength": 1, "description": "任务 id"},
        "description": {"type": "string", "description": "新描述(可选)"},
        "status": {"type": "string", "enum": ["completed", "failed", "canceled"],
                   "description": "要转到的结束状态(可选;已结束的任务无法再改)"},
        "result": {"type": "string", "description": "结论(status=completed 时)或原因(status=failed 时)"},
    }, ["id"]), persistentEffect=True,
)
