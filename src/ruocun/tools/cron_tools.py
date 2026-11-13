"""Frozen src/tools/cron_tools.ts (MIT), W3 capability text and native paths."""
from __future__ import annotations

from typing import Any

from ..schedule import ScheduleService
from .schema import objectSchema
from .types import Tool, ToolContext

cronCreateTool_DESCRIPTION = (
    "创建定时任务。用本地时区的五字段 cron 表达式和要运行的 prompt 注册系统任务，机器运行时触发。"
    "任务使用无界面的若存进程，日志写入 ~/.ruocun/schedule.log。"
    "recurring=false 为一次性标记，完成后仍需删除。durable=false 与 Windows 均不支持。"
)
cronCreateTool_DESCRIPTIONEN = (
    "Register a prompt with the system scheduler using a five-field cron expression in local time. "
    "The machine must be running. The headless run logs to ~/.ruocun/schedule.log. "
    "With recurring=false, remove the entry after it runs. Session-only entries and Windows are unsupported."
)
cronDeleteTool_DESCRIPTION = "从系统定时器移除一项任务。jobId 取 CronList 显示的序号。Windows 不支持。"
cronDeleteTool_DESCRIPTIONEN = "Remove a system schedule using the jobId from CronList. Unavailable on Windows."
cronListTool_DESCRIPTION = "查看系统定时任务的序号、时间表达式和执行内容概要。Windows 不支持。"
cronListTool_DESCRIPTIONEN = "Show the system schedule, with job IDs, timing expressions, and prompt previews. Unavailable on Windows."

_CREATE = objectSchema({
    "cron": {"type": "string", "description": "5 字段 cron,如 '0 9 * * *'(每天 9 点)"},
    "prompt": {"type": "string", "description": "到点要跑的 prompt"},
    "recurring": {"type": "boolean", "description": "true=循环(默认);false=一次性标记(需手动删除)"},
    "durable": {"type": "boolean", "description": "显式 false 的会话内调度暂不支持;省略或 true 写 OS crontab"},
}, ["cron", "prompt"])
_DELETE = objectSchema({"jobId": {"type": "integer", "minimum": 1, "description": "CronList 里的序号"}}, ["jobId"])


def createCronTools(service: ScheduleService | None = None) -> tuple[Tool, Tool, Tool]:
    current = service or ScheduleService()
    async def create(args: dict[str, Any], ctx: ToolContext) -> str:
        if not args.get("cron") or not args.get("prompt"):
            return "需要 cron(5 字段)和 prompt。"
        if args.get("durable") is False:
            return "session-only 定时任务(durable=false)暂不支持，本工具不创建会话内调度。"
        prompt = (f"[一次性任务] {args['prompt']}\n(完成后请运行 ruocun schedule remove 删除此定时任务)"
                  if args.get("recurring") is False else args["prompt"])
        output: list[str] = []
        added = await current.add(args["cron"], prompt, ctx.workspaceRoot, output.append, ctx.signal)
        if added and args.get("recurring") is False:
            output.append("注意:一次性任务执行后需手动删除(用 CronDelete 或 ruocun schedule remove)。\n")
        return "".join(output).strip() or "(完成)"

    async def delete(args: dict[str, Any], ctx: ToolContext) -> str:
        output: list[str] = []
        await current.remove(args["jobId"], output.append, ctx.signal)
        return "".join(output).strip() or "(完成)"

    async def listed(args: dict[str, Any], ctx: ToolContext) -> str:
        output: list[str] = []
        await current.list(output.append, ctx.signal)
        return "".join(output).strip() or "(暂无定时任务)"

    return (Tool(name="CronCreate", description=cronCreateTool_DESCRIPTION, descriptionEn=cronCreateTool_DESCRIPTIONEN,
                 schema=_CREATE, capability="exec", approval="required", shouldDefer=True, handler=create),
            Tool(name="CronDelete", description=cronDeleteTool_DESCRIPTION, descriptionEn=cronDeleteTool_DESCRIPTIONEN,
                 schema=_DELETE, capability="exec", approval="required", shouldDefer=True, handler=delete),
            Tool(name="CronList", description=cronListTool_DESCRIPTION, descriptionEn=cronListTool_DESCRIPTIONEN,
                 schema=objectSchema({}, []), capability="read", approval="auto", shouldDefer=True, handler=listed))


cronCreateTool, cronDeleteTool, cronListTool = createCronTools()
