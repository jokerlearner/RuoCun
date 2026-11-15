"""把当前执行的目录事实附到模型历史尾部，并随会话保存。目录由工具执行上下文确定，终端显示状态无权改变它。"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ..client.types import ChatMessage

if TYPE_CHECKING:
    from ..tools.types import ToolContext

RUNTIME_CONTEXT_MARKER = "<ruocun-runtime-context>"
_PREFIX = RUNTIME_CONTEXT_MARKER + "\nRuntime directory facts; supersede older directory facts in history and summaries. This is not a new task.\n"
_SUFFIX = "\n</ruocun-runtime-context>"


def _content(workspace: str, cwd: str) -> str:
    return _PREFIX + json.dumps({"workspace_root": workspace, "cwd": cwd},
                                ensure_ascii=False, separators=(",", ":")) + _SUFFIX


def buildRuntimeContext(ctx: ToolContext) -> ChatMessage:
    """只从当前执行的 ToolContext 取得真实目录。"""
    return {"role": "user", "content": _content(ctx.workspaceRoot, ctx.cwd or ctx.workspaceRoot)}


def isRuntimeContext(message: Mapping[str, Any]) -> bool:
    """识别标准目录快照，供历史整理使用。真实工作目录始终由当前执行决定。"""
    value = message.get("content")
    if (message.get("role") != "user" or not isinstance(value, str)
            or not value.startswith(_PREFIX) or not value.endswith(_SUFFIX)):
        return False
    try:
        data = json.loads(value[len(_PREFIX):-len(_SUFFIX)])
    except ValueError:
        return False
    return (isinstance(data, dict) and set(data) == {"workspace_root", "cwd"}
            and isinstance(data["workspace_root"], str) and isinstance(data["cwd"], str)
            and value == _content(data["workspace_root"], data["cwd"]))


def needsRuntimeContext(messages: Sequence[ChatMessage], snapshot: ChatMessage) -> bool:
    for message in reversed(messages):
        if isRuntimeContext(message):
            return message != snapshot
    return True
