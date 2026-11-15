"""定义 Bash 语法节点和安全分析结果。节点位置采用 UTF-8 字节偏移。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Literal, TypedDict


@dataclass
class Node:
    type: str
    text: str
    startIndex: int
    endIndex: int
    children: list[Node] = field(default_factory=list)


class SimpleResult(TypedDict):
    kind: Literal["simple"]
    subcommands: list[str]


class ComplexResult(TypedDict):
    kind: Literal["too-complex"]
    reason: str


class FallbackResult(TypedDict):
    kind: Literal["fallback"]


BashParseResult = SimpleResult | ComplexResult | FallbackResult
BashParser = Callable[[str], Awaitable[BashParseResult]]
