"""Frozen src/tools/schedule_tool.ts (MIT), W3 capability text and native paths."""
from __future__ import annotations

from typing import Any

from ..schedule import ScheduleService
from .schema import objectSchema
from .types import Tool, ToolContext

scheduleTool_DESCRIPTION = "管理系统定时任务。先查看当前平台是否可用。add 需要五字段 cron 和 prompt，list 列任务及序号，remove 用该序号删除。"
scheduleTool_DESCRIPTIONEN = (
    "Manage system scheduling where supported. add takes a five-field cron and a "
    "prompt, list shows the scheduled entries and their indexes, and remove deletes an "
    "entry by its index."
)

_SCHEMA = objectSchema({
    "action": {"type": "string", "enum": ["add", "list", "remove"], "description": "add 添加 / list 列出 / remove 删除"},
    "cron": {"type": "string", "description": "add:5 字段 cron,如 '0 9 * * *'(每天 9 点)"},
    "prompt": {"type": "string", "description": "add:到点要跑的 prompt"},
    "index": {"type": "integer", "minimum": 1, "description": "remove:ruocun schedule list 里的序号"},
}, ["action"])


def createScheduleTools(service: ScheduleService | None = None) -> tuple[Tool, Tool, Tool, Tool]:
    from .cron_tools import createCronTools

    current = service or ScheduleService()
    async def handler(args: dict[str, Any], ctx: ToolContext) -> str:
        output: list[str] = []
        if args["action"] == "add":
            if not args.get("cron") or not args.get("prompt"):
                return "add 需要 cron(5 字段)和 prompt。"
            await current.add(args["cron"], args["prompt"], ctx.workspaceRoot, output.append, ctx.signal)
        elif args["action"] == "list":
            await current.list(output.append, ctx.signal)
        else:
            if args.get("index") is None:
                return "remove 需要 index(先 list 看序号)。"
            await current.remove(args["index"], output.append, ctx.signal)
        return "".join(output).strip() or "(完成)"
    tool = Tool(name="Schedule", description=scheduleTool_DESCRIPTION, descriptionEn=scheduleTool_DESCRIPTIONEN,
                schema=_SCHEMA, capability="exec", approval="required", shouldDefer=True, handler=handler)
    return tool, *createCronTools(current)


scheduleTool = createScheduleTools()[0]
