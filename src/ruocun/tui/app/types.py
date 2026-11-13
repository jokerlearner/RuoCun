"""冻结tui/app/types.ts（MIT）的转录与动态展示状态。"""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from ...config.profiles import Provider


@dataclass(frozen=True)
class TranscriptItem:
    id: int
    kind: str
    data: dict[str, Any]


@dataclass
class LiveState:
    reasoning: str = ""
    content: str = ""
    tools: list[str] = field(default_factory=list)
    toolCount: int = 0


@dataclass
class AccountActions:
    listAccounts: Callable[[], Sequence[dict[str, Any]]]
    switchAccount: Callable[[str], Awaitable[bool]]
    removeAccount: Callable[[str], Awaitable[None]]
    addAccount: Callable[[str, str | None, Provider, str | None, str | None], Awaitable[dict[str, Any]]]
    fetchGatewayModels: Callable[[str, str], Awaitable[list[str]]] | None = None
