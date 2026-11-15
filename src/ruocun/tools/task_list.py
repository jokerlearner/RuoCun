"""按请求列出全部或运行中的子代理任务，输出适合模型读取的状态列表。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .schema import objectSchema
from .types import Tool, ToolContext

if TYPE_CHECKING:
    from ..agent.tasks import BgTask


DESCRIPTION = (
    "列出当前会话的任务摘要。默认展示在跑的任务，打开 include_finished 可查历史。拿到 id 后用 TaskGet 看详情。"
)


DESCRIPTION_EN = (
    "List task summaries for this session. Running work is shown by default. Set "
    "include_finished to see history and use TaskGet for details about an ID."
)


_ICON = {
    "interrupted": "已中断", "unknown": "待核实", "canceling": "取消中", "running": "▶",
    "completed": "☑", "failed": "✗", "canceled": "☐",
}


def renderTaskList(tasks: Sequence[BgTask], *, include_finished: bool = False) -> str:
    if not tasks:
        return "(暂无任务)" if include_finished else "(暂无运行中的任务)"
    return "\n".join(f"{_ICON[task.status]} {task.id}  {task.description}" for task in tasks)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.taskManager is None:
        return "当前环境不支持任务追踪。"
    include_finished = args.get("include_finished", False)
    tasks = ctx.taskManager.all() if include_finished else ctx.taskManager.running()
    return renderTaskList(tasks, include_finished=include_finished)


taskListTool = Tool(
    name="TaskList", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="read", approval="auto",
    handler=_handler, schema=objectSchema({
        "include_finished": {"type": "boolean", "description": "是否连已结束(完成/失败/取消)的任务也列出,默认 false"},
    }, []),
)
