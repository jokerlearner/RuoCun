"""定义回合事件的展示接口，把流式文本转成展示事件，并提供纯文本的终端实现。"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any, Protocol

from .markdown import renderMarkdown


class TurnEvents(Protocol):
    def reasoning(self, chunk: str) -> None: ...
    def content(self, chunk: str) -> None: ...
    def assistantDone(self, message: dict[str, Any]) -> None: ...
    def toolStart(self, call: dict[str, Any]) -> None: ...
    def toolResult(self, call: dict[str, Any], message: dict[str, Any]) -> None: ...
    def notice(self, text: str) -> None: ...
    def userMessage(self, text: str) -> None: ...


class PlainEvents:
    def __init__(self, write: Callable[[str], None]) -> None:
        self._write = write
        self._reasoning = False
        self._content = ""

    def _flush(self) -> None:
        if self._content:
            self._write(renderMarkdown(self._content))
            self._content = ""

    def reasoning(self, chunk: str) -> None:
        if not self._reasoning:
            self._write("\x1b[90m")
            self._reasoning = True
        self._write(chunk)

    def content(self, chunk: str) -> None:
        if self._reasoning:
            self._write("\x1b[0m\n\n")
            self._reasoning = False
        self._content += chunk

    def toolStart(self, call: dict[str, Any]) -> None:
        if self._reasoning:
            self._write("\x1b[0m\n")
            self._reasoning = False
        self._flush()
        self._write(f"\x1b[36m→ {call['name']}\x1b[0m\n")

    def assistantDone(self, message: dict[str, Any]) -> None:
        if self._reasoning:
            self._write("\x1b[0m")
            self._reasoning = False
        self._flush()
        self._write("\n")

    def toolResult(self, call: dict[str, Any], message: dict[str, Any]) -> None:
        pass  # 纯文本入口省略工具结果的单独展示。

    def notice(self, text: str) -> None:
        self._write(text)

    def userMessage(self, text: str) -> None:
        self._write(f"\n> {text}\n")


def plainEvents(write: Callable[[str], None]) -> PlainEvents:
    return PlainEvents(write)


async def consumeStream(gen: AsyncIterator[dict[str, Any]], events: TurnEvents, message: dict[str, Any]) -> dict[str, Any]:
    # 异步生成器只传递增量。调用方另传最终消息，用于完成展示和返回。
    async for delta in gen:
        if delta["kind"] == "reasoning":
            events.reasoning(delta["text"])
        elif delta["kind"] == "content":
            events.content(delta["text"])
        else:
            events.toolStart({"index": delta["index"], "name": delta["name"]})
    events.assistantDone(message)
    return message


async def renderStream(gen: AsyncIterator[dict[str, Any]], write: Callable[[str], None], message: dict[str, Any]) -> dict[str, Any]:
    return await consumeStream(gen, plainEvents(write), message)
