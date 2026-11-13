"""冻结 read_file.ts 的文本/图片Read工具（MIT）。"""

from __future__ import annotations

import asyncio
import base64
import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from ..config.profiles import supportsVision
from .paths import approvedPath, detectImageFormat, isImagePath
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected


def _msg(ctx: ToolContext, zh: str, en: str) -> str:
    return en if ctx.lang == "en" else zh


async def _read(args: dict[str, Any], ctx: ToolContext) -> str:
    try:
        absolute = await approvedPath(ctx, args["path"])
    except ToolRejected:
        return _msg(
            ctx, f"Error: {args['path']} 在工作区之外，未获授权访问。可在权限提示中批准。",
            f"Error: {args['path']} is outside your workspace. Approve access in the permission prompt to open it.",
        )
    if ctx.signal.is_set():
        raise InterruptedError("工具调用已取消")
    # worker只填本次结果；真实共享读基线在业务loop应用，忙时/files不会遍历到线程写入。
    worker_ctx = replace(ctx, readFiles=set(), readMeta={}, currentImageData=None, onFileAccessed=None)
    text, accessed = await asyncio.to_thread(_read_text, absolute, args, worker_ctx)
    for path in worker_ctx.readFiles:
        ctx.readFiles.add(path)
    for path, meta in worker_ctx.readMeta.items():
        ctx.readMeta[path] = meta
    if worker_ctx.currentImageData is not None:
        ctx.currentImageData = worker_ctx.currentImageData
    if accessed and ctx.onFileAccessed is not None:
        ctx.onFileAccessed(absolute)
    return text


def _read_text(absolute: str, args: dict[str, Any], ctx: ToolContext) -> tuple[str, bool]:
    """返回展示结果和是否完成来源定义的文本访问。"""
    stat = os.stat(absolute)
    if stat.st_size > 5 * 1024 * 1024 and "offset" not in args and "limit" not in args:
        return _msg(
            ctx, f"Error: 文件过大({stat.st_size / 1024 / 1024:.1f}MB > 5MB)。请用 offset/limit 分段读,或用 Grep 精确定位。",
            f"Error: File too large ({stat.st_size / 1024 / 1024:.1f}MB > 5MB). Set offset and limit for a smaller read, or locate the text with Grep.",
        ), False
    if isImagePath(args["path"]):
        data = Path(absolute).read_bytes()
        if len(data) > 5 * 1024 * 1024:
            return _msg(ctx, f"Error: 图片过大({len(data) / 1024 / 1024:.1f}MB > 5MB)。",
                        f"Error: Image too large ({len(data) / 1024 / 1024:.1f}MB > 5MB)."), False
        mediaType = detectImageFormat(data)
        if mediaType is None:
            return _msg(ctx, "Error: 无法识别图片格式,支持 png/jpg/gif/webp。",
                        "Error: Could not identify the image. Read accepts PNG, JPG, GIF and WebP."), False
        if ctx.sessionModel and not supportsVision(ctx.sessionModel):
            return f"Error: 当前模型 {ctx.sessionModel} 不支持图片输入,无法读取图片文件。", False
        ctx.currentImageData = {"base64": base64.b64encode(data).decode("ascii"), "mediaType": mediaType}
        name = Path(args["path"]).name
        return _msg(ctx, f"[已读取图片: {name} ({len(data)} bytes, {mediaType})]",
                    f"[Image loaded: {name} ({len(data)} bytes, {mediaType})]"), False
    raw = Path(absolute).read_bytes().decode("utf-8", errors="replace")
    if "\0" in raw:
        return _msg(ctx, "Error: 看起来是二进制文件(含 NUL 字节),Read 只读文本。",
                    "Error: Found NUL bytes in this file. Read can display text or a supported image."), False
    # 元信息与实际读前 stat 绑定；不使用读后 stat 掩盖读取时的外部改动。
    ctx.readFiles.add(absolute)
    ctx.readMeta[absolute] = {"mtime": stat.st_mtime_ns / 1_000_000, "size": stat.st_size}
    lines = raw.split("\n")
    start = args.get("offset", 1) - 1
    if start >= len(lines):
        return _msg(ctx, f"(offset {args.get('offset')} 超过文件总行数 {len(lines)})",
                    f"(offset {args.get('offset')} exceeds total line count {len(lines)})"), False
    end = start + args.get("limit", 2000)
    bodyLines: list[str] = []
    for index, line in enumerate(lines[start:end]):
        encoded = line.encode("utf-16-le", errors="surrogatepass")
        length = len(encoded) // 2  # 来源JS String.length/slice按UTF-16 code unit。
        if length > 2000:
            line = encoded[:4000].decode("utf-16-le", errors="surrogatepass") + "…" + _msg(
                ctx, f"(本行共 {length} 字符,已截断)", f"(line has {length} chars, truncated)",
            )
        bodyLines.append(f"{start + index + 1}\t{line}")
    body = "\n".join(bodyLines)
    if "limit" not in args and end < len(lines):
        body += _msg(
            ctx, f"\n…(文件共 {len(lines)} 行,默认只显示前 2000 行;用 offset={end + 1} 续读,或用 Grep 精确定位)",
            f"\n…(File has {len(lines)} lines total; showing first 2000 by default; use offset={end + 1} to continue, or Grep for targeted search)",
        )
    if "limit" in args and len(lines) <= args["limit"] and start == 0:
        body += _msg(ctx, f"\n(文件共 {len(lines)} 行,已全部读取;下次读小文件可不传 limit,一次读完)",
                     f"\n(Read all {len(lines)} lines. You can leave limit out when opening small files.)")
    return body, True


readFileTool = Tool(
    name="Read",
    description=(
        "读取文本并标出行号，或为视觉模型打开 PNG、JPG、GIF、WebP。文本默认最多读 2000 行，单行最多 2000 字符；"
        "超过 5 MB 时先指定 offset 或 limit。offset 从 1 开始，长文件可先用 Grep 找到位置。"
        "成功读取会建立 Edit 和 Write 所需的文件基线，传给 Edit 的原文应去掉行号。访问工作区外文件需要授权。"
    ),
    descriptionEn=(
        "Read numbered text, or open a PNG, JPG, GIF, or WebP for a model with image support. "
        "Text is capped at 2,000 lines by default and 2,000 characters per line. "
        "For files over 5 MB, set a one-based offset or a limit. Use Grep to locate a section. "
        "A successful text read records the baseline for Edit and Write. Leave line numbers out of Edit input. "
        "Access outside the workspace requires permission."
    ),
    schema=objectSchema({
        "path": {"type": "string", "description": "相对工作区根目录的文件路径"},
        "offset": {"type": "integer", "minimum": 1, "description": "起始行号(1-based,含)"},
        "limit": {"type": "integer", "minimum": 1, "description": "最多读取的行数"},
    }, ["path"]), capability="read", approval="auto", handler=_read,
)
