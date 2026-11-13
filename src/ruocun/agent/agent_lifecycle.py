"""Known background agent terminal outcomes, following frozen agent_lifecycle.ts (MIT)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .background_types import ExecutionStatus

if TYPE_CHECKING:
    from ..session.session import Session
    from .loop import TurnResult


def settleAgentTurn(session: Session, outcome: TurnResult, *, output_start: int) -> tuple[ExecutionStatus, str]:
    last = next((message["content"] for message in reversed(session.messages[output_start:])
                 if message.get("role") == "assistant" and isinstance(message.get("content"), str)
                 and message["content"]), "")
    if outcome.status == "complete":
        return "completed", last or "(子代理无最终输出)"
    if outcome.status == "cancelled":
        return "canceled", last or outcome.error or "子代理已停止。"
    if outcome.status == "outcome_unknown":
        return "unknown", outcome.error or "子代理工具结果未确认，保留现场。"
    return "failed", (outcome.error or "子代理未完成。") + ("\n\n(部分输出)\n" + last if last else "")
