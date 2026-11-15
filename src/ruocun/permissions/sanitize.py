"""识别隐藏控制字符和 Unicode 规范化差异，为权限检查提供可疑标记与清理后的文本。"""
from __future__ import annotations

import unicodedata
from typing import TypedDict


class SanitizedText(TypedDict):
    clean: str
    suspicious: bool


def hasSuspiciousUnicode(text: str) -> bool:
    return (any(unicodedata.category(char) in {"Cf", "Co", "Cn", "Cc"} for char in text if char not in "\t\n\r")
            or unicodedata.normalize("NFKC", text) != text)


def hasNullByte(text: str) -> bool:
    return "\0" in text


def sanitizeText(text: str) -> SanitizedText:
    clean = "".join(char for char in unicodedata.normalize("NFKC", text)
                    if char != "\0" and unicodedata.category(char) not in {"Cf", "Co", "Cn"})
    return {"clean": clean, "suspicious": clean != text}
