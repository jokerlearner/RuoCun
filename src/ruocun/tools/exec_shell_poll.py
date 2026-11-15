"""从受管 Shell 控制器读取新增输出或最近的日志。同一后台命令没有新输出时节流。"""
from __future__ import annotations

import json
import time
from importlib.resources import files
from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(files("ruocun.tools").joinpath("resources/exec-shell-poll.json").read_text("utf-8"))

_lastPollAt: dict[str, float] = {}


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.managedShell is None:
        return "A recoverable Shell backend is not bound to this session." if ctx.lang == "en" else "当前会话未绑定可恢复Shell后端。"
    run_id = args["id"]
    result = await ctx.managedShell.poll(run_id)
    status, stdout, stderr = result["status"], result["stdout"], result["stderr"]
    if status == "running" and not stdout.strip() and not stderr.strip():
        now = time.monotonic()
        previous = _lastPollAt.get(run_id, float("-inf"))
        _lastPollAt[run_id] = now
        if now - previous < 30:
            return ("No output since the recent check. Wait for the completion notification."
                    if ctx.lang == "en" else "刚才的查询之后没有新输出，请等待完成通知。")
        return ("The command is still running. The session will report completion."
                if ctx.lang == "en" else "命令还在运行，会话会报告最终结果。")
    _lastPollAt.pop(run_id, None)
    displayed = "exited" if status in {"completed", "failed", "canceled"} else status
    parts = [f"Status: {displayed}" if ctx.lang == "en" else f"状态:{displayed}"]
    if stdout.strip():
        parts.append(stdout.rstrip())
    if stderr.strip():
        parts.append("[stderr]\n" + stderr.rstrip())
    if displayed == "exited":
        parts.append(f"[exit {result.get('exitCode', '')}]")
    if status == "unknown":
        parts.append("Execution outcome is unconfirmed; the original run is retained and will not be restarted automatically." if ctx.lang == "en" else "执行结果未确认；原run保留，不自动重新启动。")
    if result.get("runnerDir"):
        parts.append(f"[logs] {result['runnerDir']}")
    return "\n".join(parts)


execShellPollTool = Tool(
    name="BashOutput", description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
    schema=objectSchema({"id": {"type": "string", "description": _TEXT["parameters"]["id"]}}, ["id"]),
    capability="read", approval="auto", handler=_handler,
)
