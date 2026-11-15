"""处理终端编辑缓冲区的粘贴占位和 Unicode 光标移动。长文本、图片用占位符留在编辑区，提交时展开为实际内容。"""

from __future__ import annotations

import re
from copy import deepcopy

from wcwidth import grapheme_boundary_before, iter_graphemes

from ..client.types import ImageData
from ..session.inputs import Content

_SURROGATES = re.compile("[\ud800-\udbff][\udc00-\udfff]|[\ud800-\udfff]")


def normalizeSurrogates(text: str) -> str:
    """把 Windows 输入和旧转录中的 UTF-16 代理对还原成 Unicode 字符。"""
    return _SURROGATES.sub(lambda match: match[0].encode("utf-16-le", "surrogatepass").decode("utf-16-le", "replace"),
                           text)


class PasteStore:
    def __init__(self) -> None:
        self._sequence = 0
        self._parts: dict[str, Content] = {}

    def insert(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        trimmed = text.rstrip("\n")
        lines = len(trimmed.split("\n")) if trimmed else 0
        if len(text.encode("utf-16-le", errors="surrogatepass")) // 2 <= 280 and lines <= 6:
            return text
        self._sequence += 1
        placeholder = f"[粘贴#{self._sequence} +{lines}行]"
        self._parts[placeholder] = text
        return placeholder

    def insert_image(self, image: ImageData) -> str:
        self._sequence += 1
        placeholder = f"[图片#{self._sequence}]"
        self._parts[placeholder] = [{"type": "image_url", "image_url": {
            "url": f"data:{image['mediaType']};base64,{image['base64']}"}}]
        return placeholder

    def restore_content(self, content: Content) -> str:
        if isinstance(content, str):
            return content
        result = []
        for part in content:
            if part.get("type") == "text":
                result.append(str(part.get("text", "")))
            elif part.get("type") == "image_url":
                self._sequence += 1
                placeholder = f"[图片#{self._sequence}]"
                self._parts[placeholder] = [deepcopy(part)]
                result.append(placeholder)
        return "".join(result)

    def expand(self, text: str) -> Content:
        if not self._parts:
            return text
        pattern = "|".join(re.escape(key) for key in self._parts if key in text)
        if not pattern:
            return text
        parts = []
        pending, previous, has_image = "", 0, False
        for match in re.finditer(pattern, text):
            pending += text[previous:match.start()]
            value = self._parts[match[0]]
            if isinstance(value, str):
                pending += value
            else:
                has_image = True
                if pending:
                    parts.append({"type": "text", "text": pending})
                    pending = ""
                parts.extend(deepcopy(value))
            previous = match.end()
        pending += text[previous:]
        if not has_image:
            return pending
        if pending:
            parts.append({"type": "text", "text": pending})
        return parts

    def retain(self, text: str) -> None:
        self._parts = {key: value for key, value in self._parts.items() if key in text}


def previous_grapheme(text: str, cursor: int) -> int:
    return grapheme_boundary_before(text, cursor) if cursor else 0


def next_grapheme(text: str, cursor: int) -> int:
    if cursor >= len(text):
        return len(text)
    start = previous_grapheme(text, cursor + 1)
    cluster = next(iter_graphemes(text, start))
    return start + len(cluster)
