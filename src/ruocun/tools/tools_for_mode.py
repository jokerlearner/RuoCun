"""按权限模式生成模型可见的工具清单，仅暴露当前可用的 MCP 工具和已启用的延迟工具。"""
from typing import Literal

from ..client.types import ApiTool
from .registry import ToolRegistry

Mode = Literal["normal", "plan"]


def apiToolsForMode(registry: ToolRegistry, mode: Mode, lang: str | None = None) -> list[ApiTool]:
    if mode == "normal":
        return registry.toApiTools(lambda tool: registry.isMcpVisible(tool.name), lang, hideUnactivatedDeferred=True)
    return registry.toApiTools(lambda tool: not tool.name.startswith("mcp__") and tool.capability not in ("write", "exec"), lang, hideUnactivatedDeferred=True)
