"""退出当前工作树，按用户选择保留或移除工作树，并恢复会话的工作目录。"""

from __future__ import annotations

import asyncio
from typing import Any

from ..agent.worktree import ActiveWorktree, GitBoundaryError, WorktreeChanges
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected

DESCRIPTION = (
    "返回进入前的工作目录。keep 保留独立目录和分支；remove 请求清理两者。若有未提交改动或独有提交，清理需要明确确认丢弃并传 "
    "discard_changes。没有进入工作树时无需处理。"
)

DESCRIPTION_EN = (
    "Restore the original working directory. Choose keep to retain the checkout and its "
    "branch, or remove to clean them up. If changes or unique commits would be lost, "
    "obtain explicit confirmation before setting discard_changes. There is nothing to "
    "clean up if no worktree is active."
)

async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    active: ActiveWorktree | None = getattr(ctx, "activeWorktree", None)
    if active is None:
        return "当前不在 worktree 会话里,无需退出。"
    tree = active.worktree
    action = args["action"]
    if action == "remove":
        try:
            await asyncio.to_thread(tree.cleanup, discard_changes=args.get("discard_changes") is True)
        except WorktreeChanges as exc:
            return str(exc)
        except GitBoundaryError as exc:
            raise ToolRejected(str(exc)) from exc
    ctx.cwd = active.previousCwd
    setattr(ctx, "activeWorktree", None)
    if action == "remove":
        return f"已移除 worktree({tree.root})并删除分支 {tree.branch},回到原目录。"
    return f"worktree 保留在磁盘上(分支 {tree.branch},目录 {tree.root}),已退出会话回到原目录。"


exitWorktreeTool = Tool(
    name="ExitWorktree", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
    capability="write", approval="suggest", shouldDefer=True, persistentEffect=True, handler=_handler,
    schema=objectSchema({"action": {"type": "string", "enum": ["keep", "remove"],
                                    "description": "keep=保留目录和分支;remove=删除目录和分支"},
                         "discard_changes": {"type": "boolean",
                                             "description": "action=remove 且有未提交改动时,传 true 才会真正丢弃并删除"}}, ["action"]),
)
