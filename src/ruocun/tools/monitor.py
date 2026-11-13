"""Frozen tools/monitor.ts (MIT)."""

from __future__ import annotations

import json
from typing import Any, Literal

from ..permissions.bash_safety import isDangerousCommand
from ..permissions.sanitize import hasSuspiciousUnicode
from ..platform.shell_plan import buildShellPlan
from .schema import objectSchema
from .types import Tool, ToolContext

DESCRIPTION = (
    "运行后台命令，主动把标准输出的每行作为通知送回；短时间内的多行会合并。一次性条件达成后应让命令自行退出。默认 5 分钟超时，可调整 timeout_ms；持续监控用 "
    "persistent，并通过 TaskStop 结束。"
)


DESCRIPTION_EN = (
    "Run a background command and deliver its stdout lines as notifications, grouping "
    "nearby lines. Have a one-time monitor exit when its condition is met. The default "
    "timeout is five minutes and can be set with timeout_ms. For a continuing monitor "
    "use persistent and stop it with TaskStop."
)


def _check(raw: str) -> Literal["ask"] | None:
    try:
        args = json.loads(raw)
        command = args.get("command") if isinstance(args, dict) else None
        if isinstance(command, str) and (isDangerousCommand(command) or hasSuspiciousUnicode(command)):
            return "ask"
    except ValueError:
        pass
    return None


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    manager = ctx.taskManager
    if manager is None:
        return "当前环境不支持任务追踪,monitor 需要它才能推送通知。"
    cwd, command = ctx.cwd or ctx.workspaceRoot, args["command"]
    plan = ctx.getShellPlan(command, cwd) if ctx.getShellPlan is not None else buildShellPlan(command, cwd, analyze=False)
    timeout = None if args.get("persistent", False) else args.get("timeout_ms", 300000)
    task = await manager.launch_monitor(plan, args["description"], timeout_ms=timeout,
                                        parent=manager.conversation.current_agent_parent(), parent_signal=ctx.signal)
    return (f"已在后台启动监控(task id={task.id}):{task.description}。命令输出会按行批量作为通知推送给你,不用轮询;"
            "想提前结束用 TaskStop。")


monitorTool = Tool(
    name="Monitor", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN, capability="exec", approval="required",
    shouldDefer=True, checkPermissions=_check, handler=_handler,
    schema=objectSchema({
        "command": {"type": "string", "minLength": 1, "description": "shell 命令/脚本;stdout 的每一行都是一个事件"},
        "description": {"type": "string", "minLength": 1, "description": "监控内容的简短描述(出现在每条通知里)"},
        "persistent": {"type": "boolean", "description": "true=跑满整个会话不设超时,靠 TaskStop 结束;默认 false"},
        "timeout_ms": {"type": "integer", "minimum": 1000, "maximum": 3600000,
                       "description": "超时后自动终止(毫秒),默认 300000;persistent:true 时忽略"},
    }, ["command", "description"]),
)
