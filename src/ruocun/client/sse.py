"""SSE 分帧与增量 UTF-8 严格解码。

- ``parseSSEChunk`` 忠实迁移冻结 ``src/client/sse.ts``：事件以空行 ``\\n\\n``
  分隔，CRLF 归一，取 ``data:`` 行，残留不完整尾事件留 ``rest``。
- ``SSEStreamParser`` 是本票产品修复：用标准库增量 UTF-8 **strict** 解码器
  按字节喂入，正确处理中文/emoji 跨字节分片、CR/LF、多帧、空行与 ``[DONE]``；
  非法/不完整字节序列明确抛错，不静默替换、不伪报成功。
  （冻结 client.ts 用 TextDecoder stream 模式；这里显式用 strict 增量解码器，
  不复制来源 ``data.toString()`` 按 chunk 解码的 Unicode/65536 缓冲瑕疵。）
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
    """按增量字节严格解码 UTF-8；未闭合的多字节序列在块间缓冲，末尾仍不完整则报错。"""

    def __init__(self) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")("strict")

    def feed(self, chunk: bytes) -> str:
        return self._decoder.decode(chunk, final=False)

    def flush(self) -> str:
        return self._decoder.decode(b"", final=True)


class SSEStreamParser:
    """组合：字节流 → 严格增量解码 → CR/LF 归一 → SSE 分帧 → payload 列表。"""

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
        # 冻结 client.ts:330-335：处理未以 \n\n 收尾的最后一个事件。
        buf = self._buffer if self._buffer.endswith("\n\n") else self._buffer + "\n\n"
        return parseSSEChunk(buf).payloads
