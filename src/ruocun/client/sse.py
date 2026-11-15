"""对 SSE 字节流先做严格 UTF-8 增量解码，再按空行分隔事件。跨数据块的字符和未结束事件留到后续块补齐。

CRLF 归一后提取 data 行。流结束还未闭合的字节序列以错误报告，避免乱码继续进入消息。
"""

from __future__ import annotations

import codecs
from dataclasses import dataclass


@dataclass(frozen=True)
class SSEParseResult:
    payloads: list[str]
    rest: str


def parseSSEChunk(buffer: str) -> SSEParseResult:
    normalized = buffer.replace("\r\n", "\n")
    parts = normalized.split("\n\n")
    rest = parts.pop() if parts else ""
    payloads: list[str] = []
    for event in parts:
        for line in event.split("\n"):
            if line.startswith("data:"):
                payloads.append(line[len("data:"):].strip())
    return SSEParseResult(payloads=payloads, rest=rest)


class SSEByteDecoder:
    """缓存尚未收齐的 UTF-8 字节。流关闭时仍无法完成解码则报告错误。"""

    def __init__(self) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")("strict")

    def feed(self, chunk: bytes) -> str:
        return self._decoder.decode(chunk, final=False)

    def flush(self) -> str:
        return self._decoder.decode(b"", final=True)


class SSEStreamParser:
    """串联增量解码、换行归一和分帧，产出各事件中的数据。"""

    def __init__(self) -> None:
        self._decoder = SSEByteDecoder()
        self._buffer = ""

    def feed(self, chunk: bytes) -> list[str]:
        self._buffer += self._decoder.feed(chunk)
        result = parseSSEChunk(self._buffer)
        self._buffer = result.rest
        return result.payloads

    def flush(self) -> list[str]:
        self._buffer += self._decoder.flush()
        if not self._buffer.strip():
            return []
        # 流结束时仍解析最后一个未以空行收尾的事件。
        buf = self._buffer if self._buffer.endswith("\n\n") else self._buffer + "\n\n"
        return parseSSEChunk(buf).payloads
