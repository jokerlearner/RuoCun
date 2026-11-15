"""将 ToolSearch 的查询交给当前上下文的搜索入口，按需透露匹配的工具定义。"""

import json
from importlib.resources import files
from typing import Any

from .types import Tool, ToolContext

_metadata = json.loads(files("ruocun.tools").joinpath("resources/tool-search.json").read_text("utf-8"))


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    return ctx.searchTools(args["query"]) if ctx.searchTools else "当前环境不支持工具搜索。"


toolSearchTool = Tool(
    "ToolSearch", _metadata["description"], {
        "type": "object", "properties": {"query": {"type": "string", "minLength": 1,
            "description": "搜索关键词(匹配工具名或描述,不分大小写)"}}, "required": ["query"],
        "additionalProperties": False,
    }, "read", "auto", _handler, descriptionEn=_metadata["descriptionEn"],
)
