"""Turn-end reflection: model work outside tool locks, durable writes at paired boundaries.

Checkpoint metadata stages advisories; the existing scoped intent journal fences memory
side effects. A crash between files and acknowledgement is unknown, never replayed.
"""

from __future__ import annotations

import asyncio
import copy
import json
import math
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from typing import Any

from ..config.compat import resolve_env
from ..memory.memory_audit import ReflectAudit
from ..session.contract import RunRef, ToolRef
from ..session.conversation import Conversation
from ..session.session import Session
from .reflect_cadence import CadenceState, applyOutcome, initCadence, tickCadence

Analyze = Callable[[list[dict[str, Any]]], Coroutine[Any, Any, dict[str, Any]]]
Apply = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ReflectionRuntime:
    def __init__(self, conversation: Conversation, session: Session, *, enabled: bool,
                 analyze: Analyze, apply: Apply, audit: Callable[[ReflectAudit], None],
                 notice: Callable[[str], None], env: Mapping[str, str]) -> None:
        self.conversation, self.session = conversation, session
        self.enabled, self.analyze, self.apply = enabled, analyze, apply
        self.audit, self.notice, self.env = audit, notice, env
        self.task: asyncio.Task[dict[str, Any]] | None = None
        self.identity = ""
        self.stopped = False
        try:
            maximum = float(resolve_env("REFLECT_MAX_INTERVAL", env) or 3)
            self.maximum = max(1, int(maximum)) if math.isfinite(maximum) else 3
        except ValueError:
            self.maximum = 3
        if resolve_env("REFLECT_EVERY", env) == "1":
            self.maximum = 1

    def _state(self) -> dict[str, Any]:
        return copy.deepcopy(self.conversation.reflection_state or {"cadence": initCadence()})

    async def drain(self, *, apply_writes: bool = True) -> None:
        """Only called at a paired model/turn boundary (also during shutdown)."""
        if not self.enabled or self.stopped or self.conversation.blocked:
            return
        state = self._state()
        if self.task is not None and self.task.done():
            task, self.task = self.task, None
            try:
                result = task.result()
            except Exception as exc:
                state.update(phase="failed", error=type(exc).__name__)
                await self.conversation.set_reflection_state(self.session, state)
                self.notice(f"反思请求未完成（{type(exc).__name__}），原记忆保留。")
                return
            state.update(phase="ready", result=result)
            await self.conversation.set_reflection_state(self.session, state)
        if state.get("phase") not in {"ready", "applying"} or not apply_writes:
            return
        identity = state["id"]
        result = state["result"]
        ref = ToolRef("reflect", identity)
        args = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        async with self.conversation.agent_tool_batches:
            try:
                cached = await self.conversation.scoped_intent(
                    ref, "ReflectMemory", args, True, agent_run=RunRef("reflect", identity),
                    approval_ref="reflect-memory-enabled")
                if cached is None:
                    # Acknowledged intent precedes every memory-file mutation.
                    applied = await self.apply(result)
                    await self.conversation.scoped_result(ref, json.dumps(applied, ensure_ascii=False))
                else:
                    applied = json.loads(cached) if isinstance(cached, str) else cached
                quiet = bool(result.get("onTrack", True)) and not (applied.get("added") or applied.get("merged"))
                cadence = applyOutcome(state.get("cadence", initCadence()), quiet, self.maximum)
                advice = result.get("advisory")
                await self.conversation.set_reflection_state(
                    self.session, {"id": identity, "phase": "applied", "cadence": cadence},
                    advisories=[f"[反思]\n{advice}"] if advice else ())
            except BaseException:
                # Some preceding files may already be committed. Preserve the durable
                # intent and stop; neither a retry nor a fresh id may hide this scope.
                self.stopped = self.conversation.blocked = True
                raise
        self.audit({"ran": True, "onTrack": result.get("onTrack", True),
                    "advisoryInjected": bool(advice), "memAdded": applied.get("added", 0),
                    "memMerged": applied.get("merged", 0), "interval": cadence["interval"],
                    "note": result.get("note", ""), "corrected": len(applied.get("corrections", [])),
                    "confirmed": applied.get("confirmed", 0)})

    async def after_turn(self, identity: str, *, provider: str, compaction_imminent: bool = False) -> None:
        if not self.enabled or self.stopped or self.conversation.blocked:
            return
        await self.drain()
        if self.task is not None or self._state().get("id") == identity:
            return
        state = self._state()
        cadence: CadenceState = state.get("cadence", initCadence())
        tick = tickCadence(cadence, self.maximum)
        run = provider == "deepseek" or compaction_imminent or tick["run"]
        state = {"id": identity, "cadence": {**tick["next"], "counter": 0} if run else tick["next"],
                 "phase": "analyzing" if run else "skipped"}
        await self.conversation.set_reflection_state(self.session, state)
        if not run:
            self.audit({"ran": False, "onTrack": True, "advisoryInjected": False,
                        "memAdded": 0, "memMerged": 0, "interval": state["cadence"]["interval"]})
            return
        # Same tools and previously sent prefix belong to analyze's snapshot.
        length = self.session.lastSentLength
        fork = resolve_env("DISTILL_FORK", self.env) != "0"
        messages = copy.deepcopy(self.session.messages[:length] if fork and length > 0 else self.session.messages)
        self.identity = identity
        self.task = asyncio.create_task(self.analyze(messages), name="ruocun-reflection")
        if provider != "deepseek" and (compaction_imminent or resolve_env("REFLECT_SYNC", self.env) == "1"):
            await asyncio.wait({self.task})
            await self.drain()

    async def close(self) -> None:
        if self.task is not None:
            await asyncio.wait({self.task})
        # Save completed analysis for safe recovery; shutdown must not initiate new
        # memory writes after the shared cancellation signal has been raised.
        await self.drain(apply_writes=False)
