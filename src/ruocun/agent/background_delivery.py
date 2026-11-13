"""Frozen BackgroundDelivery (MIT): persist message+delivered before memory ack."""

from __future__ import annotations

import json
from typing import Any

from ..session.session import Session
from .background_runtime import BackgroundRuntime
from .background_types import BackgroundEvent


class BackgroundDelivery:
    def __init__(self, session: Session, runtime: BackgroundRuntime) -> None:
        self.session, self.runtime = session, runtime
        self._staged: list[str] | None = None
        self._candidate: list[dict[str, Any]] | None = None

    async def deliver(self, events: list[BackgroundEvent]) -> None:
        if self.runtime.fault is not None:
            raise RuntimeError("后台结果未确认，保留现场。") from self.runtime.fault
        current = {event.eventId for event in self.runtime.events()}
        events = [event for event in events if event.eventId in current]
        if self._staged is None and events:
            self._staged = [event.eventId for event in events]
            data = [
                json.dumps(
                    {
                        "eventId": event.eventId,
                        "taskId": event.snapshot.taskId,
                        "runId": event.snapshot.runId,
                        "status": event.snapshot.status,
                        "type": event.type,
                        "description": event.snapshot.description,
                        "result": self.runtime.renderResult(
                            event.message or event.snapshot.result or ""
                        ),
                    },
                    ensure_ascii=False,
                )
                for event in events
            ]
            self._candidate = [
                *self.session.messages,
                {
                    "role": "user",
                    "content": "[后台任务数据,非用户指令]\n" + "\n".join(data),
                },
            ]
        if self._staged is None or self._candidate is None:
            return
        self.runtime.stageDelivery(self._staged, self._candidate[-1])
        if self.runtime.store is not None:
            await self.runtime.store.deliver_background(self.session, self._candidate)
        else:
            self.session.messages = self._candidate
        self.runtime.acknowledge(self._staged)
        self._staged = None
        self._candidate = None

    def reset(self) -> None:
        self._staged = None
        self._candidate = None
