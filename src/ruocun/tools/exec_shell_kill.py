"""Frozen exec_shell_kill.ts (MIT): cancellation request is not process closure."""
from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(files("ruocun.tools").joinpath("resources/exec-shell-kill.json").read_text("utf-8"))


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.managedShell is None:
        return "A recoverable Shell backend is not bound to this session." if ctx.lang == "en" else "当前会话未绑定可恢复Shell后端。"
    run_id = args["id"]
    result = await ctx.managedShell.cancel(run_id)
    if result.get("reason"):
        return "Execution or control credentials are unconfirmed; the original run is retained and no termination request was sent." if ctx.lang == "en" else "原执行或控制材料未确认；保留现场，未发出终止请求。"
    if result["status"] == "not-found":
        return (f"No active run with ID {run_id} was found."
                if ctx.lang == "en" else f"未找到可停止的任务 {run_id}。")
    return f"Requested termination of {run_id}; canceled is confirmed only after executor exit." if ctx.lang == "en" else f"已向 {run_id} 请求终止;执行器退出后才确认 canceled。"


execShellKillTool = Tool(
    name="KillShell", description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
    schema=objectSchema({"id": {"type": "string", "description": _TEXT["parameters"]["id"]}}, ["id"]),
    capability="exec", approval="auto", handler=_handler,
)
