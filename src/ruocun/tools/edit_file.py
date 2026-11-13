"""冻结 edit_file.ts / edit_mismatch.ts / diff_hunk.ts 的文本 Edit（MIT）。"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
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

_GROUPS = ["-－—–−", '\"“”', "'‘’", ",，、", ".。", ":：", ";；", "(（", ")）", " \u00a0　"]
_LOOKALIKE = {char: f"[{re.escape(group)}]" for group in _GROUPS for char in group}


def _utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def _lookalike_match(raw: str, old: str) -> str | None:
    if not old or _utf16_length(old) > 5000:
        return None
    pattern = "".join(_LOOKALIKE.get(char, re.escape(char)) for char in old)
    match = re.search(pattern, raw)
    return match[0] if match else None


def findActualString(raw: str, old: str) -> str | None:
    if not old:
        return None
    return old if old in raw else _lookalike_match(raw, old)


def diagnoseMismatch(raw: str, old: str) -> str | None:
    actual = _lookalike_match(raw, old)
    if actual is None:
        return None
    for index, (wanted, found) in enumerate(zip(old, actual)):
        if wanted != found:
            position = _utf16_length(old[:index]) + 1
            return (f'old_string 第 {position} 个字符是"{wanted}"(U+{ord(wanted):04X}),'
                    f'文件里同一位置为"{found}"(U+{ord(found):04X})。'
                    "两处字符看起来相似。请用 Read 重新取得该段文字并保留原标点。")
    return None


def buildEditHunk(raw: str, old: str, new: str, ctx: int = 3) -> list[str]:
    index = raw.find(old)
    if index < 0:
        return []
    next_text = raw[:index] + new + raw[index + len(old):]
    before = raw.split("\n")
    after = next_text.split("\n")
    start = raw[:index].count("\n") + 1
    end_before = raw[:index + len(old)].count("\n") + 1
    end_after = next_text[:index + len(new)].count("\n") + 1
    rows: list[str] = []
    for number in range(max(1, start - ctx), start):
        rows.append(f" {number:4} {before[number - 1]}")
    for number in range(start, end_before + 1):
        rows.append(f"-{number:4} {before[number - 1]}")
    for number in range(start, end_after + 1):
        rows.append(f"+{number:4} {after[number - 1]}")
    for number in range(end_after + 1, min(len(after), end_after + ctx) + 1):
        rows.append(f" {number:4} {after[number - 1]}")
    return rows


async def _edit(args: dict[str, Any], ctx: ToolContext) -> str:
    absolute = await approvedPath(ctx, args["path"], write=True)
    result = await asyncio.to_thread(_edit_text, absolute, args, ctx)
    if ctx.onFileAccessed is not None:
        ctx.onFileAccessed(absolute)
    return result


def _edit_text(absolute: str, args: dict[str, Any], ctx: ToolContext) -> str:
    with fileLock(absolute):
        if ctx.signal.is_set():
            raise InterruptedError("工具调用已取消")
        if absolute not in ctx.readFiles:
            raise ToolRejected(f"编辑前请先用 Read 读过它:{args['path']}")
        checkReadBaseline(absolute, args["path"], ctx)
        try:
            raw = Path(absolute).read_bytes().decode("utf-8", errors="replace")
        except OSError as exc:
            raise ToolRejected(f"编辑前无法读取文件:{args['path']}。{exc}") from exc
        requested = args["old_string"]
        # 空串没有可核验的替换目标，首版准确拒绝。
        if not requested:
            raise ToolRejected("old_string 不能为空;请从 Read 原文复制需要替换的内容")
        old = findActualString(raw, requested)
        if old is None:
            raise ToolRejected(f"未找到 old_string:{args['path']}")
        count = raw.count(old)
        if count > 1 and not args.get("replace_all"):
            raise ToolRejected(f"old_string 在 {args['path']} 出现 {count} 次，不唯一。"
                               "只改一处时，把周围未改动的文字同时带入 old_string 和 new_string。"
                               "要替换所有匹配时请使用 replace_all。")
        next_text = raw.replace(old, args["new_string"])
        start_line = raw[:raw.index(old)].count("\n") + 1
        diff = "\n```diff\n" + "\n".join(buildEditHunk(raw, old, args["new_string"])) + "\n```"
        atomicWrite(absolute, next_text)
        refreshReadBaseline(absolute, ctx)
        if ctx.lang == "en":
            return f"Edited {args['path']} ({count} replacement(s), line {start_line}){diff}"
        return f"已编辑 {args['path']}(替换 {count} 处,行 {start_line}){diff}"


editFileTool = Tool(
    name="Edit",
    description=(
        "精确替换工作区文件中的文本。先用 Read 查看目标，然后把不带行号的原文本（含缩进和换行）放入 "
        "old_string。默认只允许匹配一处；有多处时补上下文，确实要全部修改才设 replace_all。new_string "
        "为空可删除匹配片段。保留文件现有风格，修改后核对实际差异。"
    ),
    descriptionEn=(
        "Change part of a workspace file by exact match. Read it first, then supply "
        "old_string with its original spacing and newlines, leaving out the displayed line "
        "numbers. A single match is required by default. Include surrounding text to "
        "disambiguate or set replace_all for an intentional bulk edit. An empty new_string "
        "removes the match. Review the resulting diff."
    ),
    schema=objectSchema({
        "path": {"type": "string", "description": "相对工作区根目录的文件路径"},
        "old_string": {"type": "string", "description": "要被替换的原文(需唯一)"},
        "new_string": {"type": "string", "description": "替换成的新文本"},
        "replace_all": {"type": "boolean", "description": "是否替换全部出现"},
    }, ["path", "old_string", "new_string"]), capability="write", approval="required", handler=_edit,
)
