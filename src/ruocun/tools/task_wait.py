"""Frozen task_wait.ts (MIT), control belongs to this turn's context scope."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, cast

from ..agent.background_runtime import currentWaitControl
from ..agent.background_types import WaitRequest
from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(
    files("ruocun.tools").joinpath("resources/task-wait.json").read_text("utf-8")
)


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    control = currentWaitControl()
    request = control.request if control is not None else ctx.requestTaskWait
    if request is None or ctx.subagentDepth > 0:
        return "Error: 当前环境不支持 TaskWait。"
    return request(
        cast(WaitRequest, {"ids": args["ids"], "mode": args.get("mode", "any")})
    )


taskWaitTool = Tool(
    name="TaskWait",
    description=_TEXT["description"],
    descriptionEn=_TEXT["descriptionEn"],
    capability="read",
    approval="auto",
    handler=_handler,
    schema=objectSchema(
        {
            "ids": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "minItems": 1,
            },
            "mode": {"type": "string", "enum": ["any", "all"], "default": "any"},
        },
        ["ids"],
    ),
)
