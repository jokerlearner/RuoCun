"""列出已批准访问目录的直接条目，并在真正的子目录名后加斜杠。"""

from __future__ import annotations

import asyncio
import os
import stat
from typing import Any

from .paths import approvedPath
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected


async def _list_dir(args: dict[str, Any], ctx: ToolContext) -> str:
    try:
        absolute = await approvedPath(ctx, args.get("path", "."))
    except ToolRejected:
        path = args.get("path", "undefined")
        return (f"Error: {path} is outside your workspace. Approve access in the permission prompt to list it."
                if ctx.lang == "en" else f"Error: {path} 在工作区之外，未获授权访问。可在权限提示中批准。")
    return await asyncio.to_thread(_entries, absolute, ctx.lang)


def _entries(absolute: str, lang: str) -> str:
    with os.scandir(absolute) as scan:
        entries = sorted(scan, key=lambda entry: entry.name.encode("utf-16-be", errors="surrogatepass"))
    if not entries:
        return "(empty directory)" if lang == "en" else "(空目录)"
    names: list[str] = []
    for entry in entries:
        directory = entry.is_dir(follow_symlinks=False)
        if directory and os.name == "nt":
            # Windows 目录联接显示为链接，末尾斜杠留给可作为真实子目录的条目。
            directory = not bool(entry.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
        names.append(entry.name + "/" if directory else entry.name)
    result = "\n".join(names[:500])
    if len(names) > 500:
        result += f"\n…(共 {len(names)} 项,已截断前 500;用 Grep/Glob 精确定位)"
    return result


listDirTool = Tool(
    name="ListDir",
    description=(
        "按名称列出目录的直接子项，末尾的 / 表示子目录。path 省略时查看工作区根。列表最多显示 500 项，按路径搜索时用 Glob。"
    ),
    descriptionEn=(
        "List up to 500 immediate directory entries in name order. A trailing / marks a directory. "
        "Omit path to inspect the workspace root. Use Glob to find paths by pattern."
    ),
    capability="read", approval="auto",
    schema=objectSchema({
        "path": {"type": "string", "description": "相对工作区根目录的目录路径,默认根目录"},
    }, []),
    apiParameters={"type": "object", "properties": {
        "path": {"type": "string", "description": "相对工作区根目录的目录路径,默认根目录"},
    }, "additionalProperties": False}, handler=_list_dir,
)
