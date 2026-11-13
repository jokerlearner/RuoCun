"""Frozen memory transcript.ts (MIT), exposing only messages used by scoring."""

import json
from pathlib import Path
from typing import Any

from ruocun.agent.deck_messages import utf16_length, utf16_slice
from ruocun.client.types import ChatMessage


def parseJsonl(raw: str) -> list[dict[str, Any]]:
    result = []
    for line in raw.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            result.append(row)
    return result


def toMessages(events: list[dict[str, Any]], tool_result_cap: int = 800) -> list[ChatMessage]:
    messages = []
    for row in events:
        kind = row.get("t")
        if kind == "user" and isinstance(row.get("text"), str):
            messages.append({"role": "user", "content": row["text"]})
        elif kind == "assistant":
            text = row.get("content")
            if not isinstance(text, str) or not text.strip():
                names = [str(call["name"]) for call in row.get("toolCalls") or [] if isinstance(call, dict) and call.get("name")]
                text = "[调用工具] " + ", ".join(names) if names else ""
            if text:
                messages.append({"role": "assistant", "content": text})
        elif kind == "tool_result" and isinstance(row.get("content"), str):
            text = row["content"]
            if utf16_length(text) > tool_result_cap:
                text = utf16_slice(text, tool_result_cap) + "…(截断)"
            messages.append({"role": "user", "content": f"[工具 {row.get('name', '?')} 结果] {text}"})
    return messages


def windowMessages(messages: list[ChatMessage], max_chars: int = 24000) -> list[ChatMessage]:
    size = 0
    start = len(messages)
    for message in reversed(messages):
        size += utf16_length(message["content"])
        if size > max_chars:
            break
        start -= 1
    return messages[start:]


def loadTranscript(path: Path) -> list[ChatMessage]:
    return windowMessages(toMessages(parseJsonl(path.read_text(encoding="utf-8"))))
