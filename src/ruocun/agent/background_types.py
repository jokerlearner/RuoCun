"""定义后台执行、等待和结果交付共用的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

ExecutionStatus = Literal[
    "running", "canceling", "completed", "failed", "canceled", "interrupted", "unknown"
]
EventType = Literal[
    "started",
    "progress",
    "completed",
    "failed",
    "canceled",
    "message",
    "interrupted",
    "unknown",
]


@dataclass(frozen=True)
class ExecutionSnapshot:
    taskId: str
    runId: str
    kind: Literal["agent", "fork", "shell", "monitor"]
    background: bool
    description: str
    status: ExecutionStatus
    result: str | None = None
    recovery: str | None = None
    runnerDir: str | None = None
    progress: str | None = None


@dataclass(frozen=True)
class ExecutionEvent:
    type: EventType
    snapshot: ExecutionSnapshot
    message: str | None = None
    requiresAttention: bool = False
    eventId: str | None = None


@dataclass(frozen=True)
class BackgroundEvent:
    sessionId: str
    eventId: str
    seq: int
    type: EventType
    snapshot: ExecutionSnapshot
    message: str | None = None
    requiresAttention: bool = False


class WaitRequest(TypedDict):
    ids: list[str]
    mode: Literal["any", "all"]


@dataclass(frozen=True)
class WaitTarget:
    taskId: str
    runId: str


@dataclass(frozen=True)
class WaitHandle:
    waitId: str
    sessionId: str
    targets: tuple[WaitTarget, ...]
    mode: Literal["any", "all"]
    observedSeq: int


def isTerminal(status: str) -> bool:
    return status in {"completed", "failed", "canceled", "interrupted"}
