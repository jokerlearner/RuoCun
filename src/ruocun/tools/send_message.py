"""把模型消息交给用户通知入口，可附带指定文件的有界文本预览。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext


async def _handle(args: dict[str, Any], ctx: ToolContext) -> str:
    parts = [args["message"]]
    for path in args.get("attachments", []):
        absolute = Path(path)
        if not absolute.is_absolute():
            absolute = Path(ctx.cwd or ctx.workspaceRoot) / absolute
        try:
            content = (await asyncio.to_thread(absolute.read_bytes)).decode("utf-8", errors="replace")
            encoded = content.encode("utf-16-le", errors="surrogatepass")
            excerpt = encoded[:8000].decode("utf-16-le", errors="surrogatepass")
            suffix = "\n…(已截断)" if len(encoded) > 8000 else ""
            parts.append(f"\n---\n附件:{Path(path).name}\n```\n{excerpt}{suffix}\n```")
        except (OSError, ValueError):
            parts.append(f"\n(附件 {path} 读取失败)")
    if args["status"] == "proactive" and ctx.notifyUser is not None:
        preview = args["message"].encode("utf-16-le", errors="surrogatepass")[:200]
        ctx.notifyUser(preview.decode("utf-16-le", errors="surrogatepass"))
    return "\n".join(parts)
DESCRIPTION = (
    "发送用户可见的 Markdown 消息，可附工作区文件路径。回复当前问题用 status=normal；主动汇报进展或阻塞用 status=proactive。"
)
DESCRIPTION_EN = (
    "Send a user-visible Markdown message with optional workspace file attachments. Set "
    "status to normal for a reply or proactive for an update about progress or a "
    "blocker."
)


sendMessageTool = Tool(
    name="SendUserMessage", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
    capability="plan", approval="auto", handler=_handle,
    schema=objectSchema({
        "message": {"type": "string", "description": "要发给用户的消息(支持 markdown)"},
        "attachments": {"type": "array", "items": {"type": "string"},
                        "description": "要附带的文件路径(绝对或相对工作区根)"},
        "status": {"type": "string", "enum": ["normal", "proactive"],
                   "description": "'normal'=回复;'proactive'=主动推送"},
    }, ["message", "status"]),
)
