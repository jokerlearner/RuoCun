"""Shared parser tree and security result; offsets are UTF-8 byte offsets."""
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
