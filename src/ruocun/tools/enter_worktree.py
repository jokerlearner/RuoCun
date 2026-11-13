"""Frozen tools/enter_worktree.ts (MIT)."""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Callable
from typing import Any

from ..agent.worktree import (
    NAME_PATTERN,
    ActiveWorktree,
    GitBoundaryError,
    Worktree,
    validateWorktreeName,
)
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected

DESCRIPTION = (
    "仅在用户要求时从当前 Git HEAD 创建独立工作树。文件工具与 Shell "
    "随后从新路径运行；项目级配置、记忆及服务仍按原项目加载。同一会话只能进入一个工作树，完成后调用 ExitWorktree。"
)

DESCRIPTION_EN = (
    "Create a separate checkout from the current Git HEAD when requested by the user. "
    "File tools and the shell resolve paths there, while project configuration, memory, "
    "and services still use the original project identity. Only one worktree can be "
    "active. Use ExitWorktree when finished."
)

async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    active: ActiveWorktree | None = getattr(ctx, "activeWorktree", None)
    if active is not None:
        return f"已经在 worktree 会话里({active.worktree.root}),先用 ExitWorktree 退出当前的,再进新的。"
    create: Callable[[str], Worktree | None] | None = getattr(ctx, "createWorktree", None)
    if create is None:
        return "当前环境不支持 worktree。"
    name = args.get("name")
    if name is None:
        name = secrets.token_hex(4)
    try:
        validateWorktreeName(name)
        worktree = await asyncio.to_thread(create, name)
    except GitBoundaryError as exc:
        raise ToolRejected(str(exc)) from exc
    if worktree is None:
        return "创建 worktree 失败(当前目录不是 git 仓库、没有可检出的 HEAD 或 Git 不可用)。"
    setattr(ctx, "activeWorktree", ActiveWorktree(worktree, ctx.cwd))
    ctx.cwd = worktree.root
    return (f"已进入 worktree：{worktree.root}（分支 {worktree.branch}）。此处用于文件操作和运行命令。"
            "记忆、MCP、LSP 和技能继续采用原项目的配置。结束时调用 ExitWorktree。")


enterWorktreeTool = Tool(
    name="EnterWorktree", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
    capability="write", approval="suggest", shouldDefer=True, persistentEffect=True, handler=_handler,
    schema=objectSchema({"name": {"type": "string", "pattern": NAME_PATTERN,
                                  "description": "worktree 名字(用作目录名和分支后缀);省略则随机生成"}}, []),
)
