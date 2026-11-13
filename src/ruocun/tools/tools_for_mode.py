"""Reference tools_for_mode.ts (MIT); production catalog omits inactive deferred tools."""
from typing import Literal

from ..client.types import ApiTool
from .registry import ToolRegistry

Mode = Literal["normal", "plan"]


def apiToolsForMode(registry: ToolRegistry, mode: Mode, lang: str | None = None) -> list[ApiTool]:
    if mode == "normal":
        return registry.toApiTools(lambda tool: registry.isMcpVisible(tool.name), lang, hideUnactivatedDeferred=True)
    return registry.toApiTools(lambda tool: not tool.name.startswith("mcp__") and tool.capability not in ("write", "exec"), lang, hideUnactivatedDeferred=True)
