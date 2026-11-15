"""向任务管理器请求取消该任务当前正在进行的执行，是否已经停止由任务管理器确认。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema import objectSchema
from .types import Tool, ToolContext

if TYPE_CHECKING:
    from ..agent.tasks import TaskManager


DESCRIPTION = (
    "请求停止运行中的任务。代理任务在执行器确认结束前显示 canceling；手工任务记录直接进入 canceled。已有文件变更需要另外检查。要重跑请创建新任务。"
)

DESCRIPTION_EN = (
    "Request that a running task stop. An agent task remains canceling until its runner "
    "confirms exit. A manual record moves directly to canceled. Review any existing "
    "file changes separately. Start a new task to rerun the work."
)

async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    manager: TaskManager | None = getattr(ctx, "taskManager", None)
    if manager is None:
        return "当前环境不支持任务追踪。"
    task_id = args["id"]
    status = await manager.cancel(task_id)
    if status == "canceling":
        return f"已请求取消任务 {task_id},等待执行器确认停止。"
    if status == "canceled":
        return f"已取消任务 {task_id}。"
    return f"任务 {task_id} 不存在、已结束、正在取消或无法中止,未生效。"


taskStopTool = Tool(
    name="TaskStop", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="exec", approval="auto",
    handler=_handler, schema=objectSchema({"id": {"type": "string", "minLength": 1, "description": "任务 id"}}, ["id"]),
)
