"""冻结 src/tools/notify_user.ts (MIT)，按 ADR-0010/W6 改为终端渠道。"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from ..tui.notifier import notify
from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(files("ruocun.tools").joinpath("resources/notify-user.json").read_text("utf-8"))


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.notifyUser is None:
        return "当前环境不支持终端提示；未发送桌面通知。"
    if notify("", args["message"], write=ctx.notifyUser, env=ctx.notificationEnv):
        return "终端提示已请求（best-effort，不保证用户当下看到）；未发送桌面通知。"
    return "终端提示未发送（通知已关闭或提示渠道不可用）；未发送桌面通知。"


notifyUserTool = Tool(
    name="NotifyUser", description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
    capability="plan", approval="auto", shouldDefer=True, handler=_handler,
    schema=objectSchema({"message": {"type": "string", "minLength": 1,
                                    "description": "要提示的内容(简明，仅显示在终端内，不发送桌面通知)"}}, ["message"]),
)
