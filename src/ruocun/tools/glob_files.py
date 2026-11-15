"""将 Glob 请求定位到已批准访问的目录，匹配相对路径并整理搜索结果。"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from .glob import globToRegExp, walkFiles
from .paths import approvedPath
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected


async def _glob(args: dict[str, Any], ctx: ToolContext) -> str:
    try:
        root = await approvedPath(ctx, args.get("path", "."))
    except ToolRejected:
        path = args.get("path", "undefined")
        return (f"Error: {path} is outside your workspace. Approve access in the permission prompt to search it."
                if ctx.lang == "en" else f"Error: {path} 在工作区之外，未获授权访问。可在权限提示中批准。")
    return await asyncio.to_thread(_search, root, args, ctx)


def _search(root: str, args: dict[str, Any], ctx: ToolContext) -> str:
    regex = globToRegExp(args["glob"])
    hits: list[tuple[str, float]] = []
    for count, (absolute, relative) in enumerate(walkFiles(root), 1):
        if ctx.signal.is_set() or count > 50000:
            break
        if regex.search(relative):
            try:
                hits.append((relative, os.stat(absolute).st_mtime_ns / 1_000_000))
            except OSError:
                continue
    hits.sort(key=lambda hit: -hit[1])
    return "\n".join(relative for relative, _ in hits[:100]) if hits else "(无匹配)"


globFilesTool = Tool(
    name="Glob", description=(
        "按名称或相对路径查找工作区文件。可用 path 缩小范围。最多返回 100 项，最近修改的排在前面。查文件内容用 Grep。"
    ),
    descriptionEn=(
        "Find workspace files by name or relative path pattern. Set path to narrow the search. "
        "Up to 100 results are returned, most recently modified first. Use Grep for file contents."
    ),
    schema=objectSchema({
        "glob": {"type": "string", "description": "文件名/路径 glob"},
        "path": {"type": "string", "description": "搜索子目录或具体某个文件,默认工作区根"},
    }, ["glob"]), capability="read", approval="auto", handler=_glob,
)

# 为调用方保留文件搜索工具的原有名称。
fileSearchTool = globFilesTool
