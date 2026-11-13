"""冻结tools/execute的审批边界；首版只顺序执行，不启用自动写权限。"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from .types import Tool, ToolContext

Approval = Callable[[str, dict[str, Any]], Awaitable[bool]]


def looksFailed(content: str) -> bool:
    """来源exec失败屏障；兼容实际Bash的[exit N,运行…]结果格式。"""
    return content.startswith("Error") or bool(re.search(
        r"\[exit -?[1-9]\d*(?:\]|,)|\[超时|\[已中断(?:\]|,)", content,
    ))


class Registry(Protocol):
    def get(self, name: str) -> Tool | None: ...
    def validate(self, name: str, rawArgs: str) -> dict[str, Any]: ...
    def toApiTools(self) -> list[dict[str, Any]]: ...
    async def dispatch(self, name: str, rawArgs: str, ctx: ToolContext) -> str: ...


async def permitted(tool: Tool, args: dict[str, Any], approve: Approval) -> bool:
    # 普通文字审批覆盖来源复杂策略；写/exec即使来源auto也不能绕过。
    return tool.capability not in {"write", "exec"} or await approve(tool.name, args)
