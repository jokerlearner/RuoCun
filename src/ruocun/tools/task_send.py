"""向运行中的子代理发送消息，或通过当前回合的恢复入口把消息交给可续接的任务。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "给子代理追加任务要求。仍在运行时，子代理会在安全边界取消息。符合恢复条件的已结束子代理可从存档接续。回执只确认提交。"
)


DESCRIPTION_EN = (
    "Send a child additional instructions. A running child picks them up at a safe "
    "boundary. An eligible finished child can resume from its saved transcript. A "
    "receipt confirms submission."
)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    send = ctx.sendToTask
    if send is None:
        return "当前环境不支持后台任务消息。"
    task_id, message = args["id"], args["message"]
    english = ctx.lang == "en"

    def task_status() -> str | None:
        task = ctx.taskManager.get(task_id) if ctx.taskManager is not None else None
        return task.status if task is not None else None

    canceling = (f"{task_id} is canceling; wait for executor exit before resuming." if english else
                 f"{task_id} 正在取消,请等待执行器退出后再恢复。")
    if task_status() == "canceling":
        return canceling
    if await send(task_id, message):
        return (f"Sent to {task_id} (effective at next turn boundary)." if english else
                f"已发送给 {task_id}(下一回合边界生效)。")
    status = task_status()
    if status == "canceling":
        return canceling
    if status not in (None, "running") and ctx.resumeAgent is not None:
        try:
            await ctx.resumeAgent(task_id, message)
        except ValueError as error:
            return (f"{task_id} has ended and could not be resumed: {error}" if english else
                    f"{task_id} 已结束且无法恢复:{error}")
        return (f"{task_id} had ended; resumed and appended the message." if english else
                f"{task_id} 已结束,已恢复并追加该消息继续执行。")
    return (f"{task_id} does not exist or has ended; cannot send." if english else
            f"{task_id} 不存在或已结束,无法发送。")


taskSendTool = Tool(
    name="TaskSend", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="plan", approval="auto",
    handler=_handler, schema=objectSchema({
        "id": {"type": "string", "description": "后台任务 id(如 task-3)"},
        "message": {"type": "string", "minLength": 1, "description": "要追加给该任务的指令"},
    }, ["id", "message"]), persistentEffect=True,
)
