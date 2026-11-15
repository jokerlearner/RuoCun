"""检查写入权限与读取基线，再通过原子替换写入文本。覆写已有文件时先校验读过的版本，以免覆盖后来修改。"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from .paths import (
    approvedPath,
    atomicWrite,
    checkReadBaseline,
    fileLock,
    refreshReadBaseline,
)
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected


async def _write(args: dict[str, Any], ctx: ToolContext) -> str:
    absolute = await approvedPath(ctx, args["path"], write=True)
    result = await asyncio.to_thread(_write_text, absolute, args, ctx)
    if ctx.onFileAccessed is not None:
        ctx.onFileAccessed(absolute)
    return result


def _write_text(absolute: str, args: dict[str, Any], ctx: ToolContext) -> str:
    with fileLock(absolute):
        if ctx.signal.is_set():
            raise InterruptedError("工具调用已取消")
        if os.path.exists(absolute):
            if absolute not in ctx.readFiles:
                raise ToolRejected(f"覆盖已存在文件前请先用 Read 读过它:{args['path']}")
            # 已有改动等待命令验证时，先拦截整篇覆写，保留模型做局部 Edit 的路径。
            if absolute in ctx.pendingUnverifiedWrites:
                raise ToolRejected(
                    f"拒绝写入：{args['path']} 的现有改动还未经命令验证。"
                    "请先运行与该文件有关的检查，再根据反馈决定是否整篇覆盖。已经定位到局部问题时可直接用 Edit。"
                )
            checkReadBaseline(absolute, args["path"], ctx)
        atomicWrite(absolute, args["content"])
        refreshReadBaseline(absolute, ctx)
        ctx.pendingUnverifiedWrites.add(absolute)
        count = len(args["content"].split("\n"))
        if ctx.lang == "en":
            return f"Wrote {args['path']} ({count} lines)"
        return f"已写入 {args['path']}({count} 行)"


writeFileTool = Tool(
    name="Write",
    description=(
        "创建文件或替换整个文件，content 应是写完后要保留的完整内容。覆盖已有文件前先用 Read 查看。局部改动用 "
        "Edit；新文件放在工作区允许的路径。写入后检查文件内容和变更范围。"
    ),
    descriptionEn=(
        "Create a file or replace its entire contents. Supply the complete desired file in "
        "content and read an existing file first. Use Edit for local changes. Keep the path "
        "within the workspace and verify the resulting contents and diff."
    ),
    schema=objectSchema({
        "path": {"type": "string", "description": "相对工作区根目录的文件路径"},
        "content": {"type": "string", "description": "文件的完整内容"},
    }, ["path", "content"]), capability="write", approval="required", handler=_write,
)
