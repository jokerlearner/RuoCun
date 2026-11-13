"""冻结参考 deck_messages.ts（MIT）：对外消息投影、窗口和修订号。"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import Any

from ..client.types import ChatMessage


def utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def utf16_slice(text: str, end: int) -> str:
    return text.encode("utf-16-le", errors="surrogatepass")[:end * 2].decode(
        "utf-16-le", errors="surrogatepass",
    )


def utf16_tail(text: str, size: int) -> str:
    return text.encode("utf-16-le", errors="surrogatepass")[-size * 2:].decode(
        "utf-16-le", errors="surrogatepass",
    )


def json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8", errors="backslashreplace",
    )


def contentText(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return "" if value.strip() == "[图片或多模态消息]" else value
    if not isinstance(value, list):
        return "[暂不支持的消息内容]"
    parts = []
    for part in value:
        if not isinstance(part, dict):
            continue
        kind = part.get("type")
        if isinstance(part.get("text"), str):
            text = part["text"]
        elif kind in ("image", "image_url", "input_image"):
            text = "[图片附件 · 请在原终端查看]"
        else:
            text = f"[附件：{kind if isinstance(kind, str) else '未知类型'}]"
        if text:
            parts.append(text)
    return "\n".join(parts)


def _tool_calls(message: ChatMessage) -> list[dict[str, Any]] | None:
    calls = message.get("toolCalls")
    if isinstance(calls, list):
        return calls
    raw = message.get("tool_calls")
    if not isinstance(raw, list):
        return None
    return [
        {"id": call.get("id"), "name": call["function"]["name"], "args": call["function"]["arguments"]}
        for call in raw
    ]


def normalizeMessage(
    message: ChatMessage, index: int | None = None, *, redact: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    text = contentText(message.get("content"))
    if redact is not None:
        text = redact(text)
    size = utf16_length(text)
    calls = _tool_calls(message)
    projected = {
        "content": utf16_slice(text, 24000),
        "contentTruncated": bool(message.get("contentTruncated")) or size > 24000,
        "contentLength": message.get("contentLength") or size,
        "toolCallsTruncated": bool(message.get("toolCallsTruncated")) or (calls is not None and len(calls) > 16),
    }
    if "role" in message:
        projected["role"] = message["role"]
    if index is not None or "index" in message:
        projected["index"] = index if index is not None else message["index"]
    tool_id = message.get("toolCallId") or message.get("tool_call_id")
    if tool_id is not None:
        projected["toolCallId"] = tool_id
    if calls is not None:
        call_page = []
        for call in calls[:16]:
            args = str(call.get("args") or "")
            if redact is not None:
                args = redact(args)
            call_page.append({
                **call, "args": utf16_slice(args, 12000),
                "argsTruncated": bool(call.get("argsTruncated")) or utf16_length(args) > 12000,
            })
        projected["toolCalls"] = call_page
    return projected


def messageRevision(messages: Sequence[ChatMessage], *, redact: Callable[[str], str] | None = None) -> str:
    prefix = []
    for message in [row for row in messages if row.get("role") != "system"][:3]:
        text = contentText(message.get("content"))
        calls = _tool_calls(message)
        call_ids = [[call.get("id"), call.get("name")] for call in calls] if calls is not None else None
        prefix.append([message.get("role"), utf16_slice(redact(text) if redact is not None else text, 512), call_ids])
    fingerprint = 2166136261
    for char in json_bytes(prefix).decode("utf-8"):
        code = ord(char)
        if code > 0xFFFF:
            code = 0xD800 + ((code - 0x10000) >> 10)
        fingerprint = ((fingerprint ^ code) * 16777619) & 0xFFFFFFFF
    return str(fingerprint if fingerprint < 0x80000000 else fingerprint - 0x100000000)


def messagePage(
    all_messages: Sequence[ChatMessage], before: int | None = None, limit: int = 100,
    *, redact: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    messages = [message for message in all_messages if message.get("role") != "system"]
    total = len(messages)
    end = total if before is None else min(total, max(0, before))
    start = end
    size = 0
    page: list[dict[str, Any]] = []
    while start > 0 and len(page) < min(100, max(1, limit)):
        message = normalizeMessage(messages[start - 1], start - 1, redact=redact)
        message_size = len(json_bytes(message))
        if page and size + message_size > 1_200_000:
            break
        size += message_size
        page.append(message)
        start -= 1
    return {"messages": list(reversed(page)), "pagination": {
        "total": total, "start": start, "end": end, "hasMore": start > 0, "nextBefore": start,
        "revision": messageRevision(messages, redact=redact),
    }}
