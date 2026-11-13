"""Incremental output decoding for explicit UTF-8 or observed Windows output.

Auto mode distinguishes BOM/valid UTF-8 from the inherited OEM encoding per
line. Arbitrary mixed encodings remain ambiguous; raw bytes and diagnostics
are retained by the foreground result.
"""

from __future__ import annotations

import codecs
import re
import xml.etree.ElementTree as ET


class ShellOutputDecoder:
    def __init__(self, policy: str, *, clixml: bool = False, clixmlLimit: int | None = None) -> None:
        self.auto = policy.startswith("auto:")
        self.fallback = policy.partition(":")[2] if self.auto else policy
        codecs.lookup(
            self.fallback
        )  # Reject an invalid policy before a business process starts.
        self.diagnostics: list[str] = []
        self._decoder: codecs.IncrementalDecoder | None = None
        self._codec = ""
        self._prefix = b""
        self._fixed = not self.auto
        self._atStart = True
        self._header = ""
        self._xml: bool | None = None if clixml else False
        self._xmlparts: list[str] = []
        self._xmlsize = 0
        self._xmlLimit = clixmlLimit
        if self._fixed:
            self._select(self.fallback)

    def _note(self, message: str) -> None:
        if message not in self.diagnostics:
            self.diagnostics.append(message)

    def _select(self, codec: str) -> None:
        self._codec = codec
        self._decoder = codecs.getincrementaldecoder(codec)(errors="strict")

    def _decode(self, data: bytes) -> str:
        if self._decoder is None:
            data = self._prefix + data
            self._prefix = b""
            if self._atStart:
                for bom, codec in [
                    (codecs.BOM_UTF8, "utf-8-sig"),
                    (codecs.BOM_UTF16_LE, "utf-16"),
                    (codecs.BOM_UTF16_BE, "utf-16"),
                ]:
                    if data.startswith(bom):
                        self._select(codec)
                        self._fixed = True
                        self._note(f"按BOM选择{codec}")
                        break
                    if bom.startswith(data):
                        self._prefix = data
                        return ""
            if self._decoder is None:
                self._atStart = False
                if data.isascii():
                    if b"\0" in data:
                        self._note(
                            "输出含空字节，可能为无BOM的未知编码；原始字节已保留"
                        )
                    return data.decode("ascii")
                self._select("utf-8")
        assert self._decoder is not None
        pending = self._decoder.getstate()[0]
        try:
            text = self._decoder.decode(data)
            if self.auto and self._codec == "utf-8":
                self._note("按有效UTF-8字节解码；自动判定无法保证任意混合编码")
            return text
        except UnicodeError:
            raw = pending + data
            if self.auto and self._codec == "utf-8":
                self._select(self.fallback)
                self._note(f"UTF-8不匹配，当前行使用{self.fallback}；原始字节已保留")
                assert self._decoder is not None
                try:
                    return self._decoder.decode(raw)
                except UnicodeError:
                    pass
            self._note(f"{self._codec}存在不可解码字节，使用反斜杠转义保留")
            text = raw.decode(self._codec, errors="backslashreplace")
            self._select(self._codec)
            return text

    def _endLine(self) -> str:
        tail = ""
        if self._decoder is not None:
            pending = self._decoder.getstate()[0]
            try:
                tail = self._decoder.decode(b"", final=True)
            except UnicodeError:
                self._note(f"{self._codec}尾部字节不完整，使用转义保留")
                tail = pending.decode(self._codec, errors="backslashreplace")
        if self._prefix:
            self._note("输出前缀不完整，使用转义保留")
            tail += self._prefix.decode(self.fallback, errors="backslashreplace")
        self._decoder, self._prefix, self._atStart = None, b"", True
        return tail

    def _feedBytes(self, data: bytes) -> str:
        if not self.auto or self._fixed:
            return self._decode(data)
        output: list[str] = []
        pieces = data.splitlines(keepends=True)
        for piece in pieces:
            output.append(self._decode(piece))
            if not self._fixed and piece.endswith(b"\n"):
                output.append(self._endLine())
        return "".join(output)

    def _text(self, text: str) -> str:
        marker = "#< CLIXML"
        if self._xml is None:
            self._header += text
            if marker.startswith(self._header):
                return ""
            self._xml = self._header.startswith(marker)
            text, self._header = self._header, ""
        if self._xml:
            self._xmlparts.append(text)
            self._xmlsize += len(text)
            if self._xmlLimit is not None and self._xmlsize > self._xmlLimit:
                self._note("PowerShell CLIXML超过缓存上限，按原文持续输出；原始字节已保留")
                self._xml = False
                raw = "".join(self._xmlparts)
                self._xmlparts.clear()
                return raw
            return ""
        return text

    def feed(self, data: bytes) -> str:
        return self._text(self._feedBytes(data))

    def finish(self) -> str:
        tail = self._text(self._endLine())
        if not self._xml:
            return tail + self._header
        raw = "".join(self._xmlparts)
        try:
            root = ET.fromstring(raw.partition("\n")[2])
        except ET.ParseError:
            self._note("PowerShell CLIXML未能解析，保留原文与原始字节")
            return raw
        messages = [
            element.text or ""
            for element in root.iter()
            if element.tag.rpartition("}")[2] == "S" and element.get("S")
        ]
        text = "".join(messages)
        text = re.sub(
            r"_x([0-9a-fA-F]{4})_", lambda match: chr(int(match[1], 16)), text
        )
        text = text.encode("utf-16-le", errors="surrogatepass").decode(
            "utf-16-le", errors="backslashreplace"
        )
        self._note("已解析PowerShell CLIXML文本；原始结构字节保留")
        return text
