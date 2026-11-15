"""编排轮末反思。工具锁外等待模型分析，到助手调用和工具结果已经配对时，再处理持久写入。

建议暂存在检查点。写记忆前提交对应的执行意图，写入与确认之间若发生中断，恢复时保留未决状态。
"""

from __future__ import annotations

import asyncio
import copy
import json
import math
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from threading import Event
from typing import Any

from ..config.compat import resolve_env
from ..memory.memory_audit import ReflectAudit
from ..session.contract import RunRef, ToolRef
from ..session.conversation import Conversation
from ..session.session import Session
from .controlled_learning import hasLearningEvidence
from .reflect_cadence import CadenceState, applyOutcome, initCadence, tickCadence

Analyze = Callable[[list[dict[str, Any]]], Coroutine[Any, Any, dict[str, Any]]]
Apply = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class ControlledLearningSignal(Event):
    """综合退出信号、原回合信号和调度代次，判断受控学习是否仍可继续。"""
    def __init__(self, shutdown: Event, turn: Event, is_current: Callable[[], bool]) -> None:
        super().__init__()
        self.shutdown, self.turn, self.is_current = shutdown, turn, is_current

    def is_set(self) -> bool:
        return super().is_set() or self.shutdown.is_set() or self.turn.is_set() or not self.is_current()


class ReflectionRuntime:
    def __init__(self, conversation: Conversation, session: Session, *, enabled: bool,
                 analyze: Analyze, apply: Apply, audit: Callable[[ReflectAudit], None],
                 notice: Callable[[str], None], env: Mapping[str, str],
                 controlled: bool = False, controlled_budget: dict[str, int] | None = None) -> None:
        self.conversation, self.session = conversation, session
        self.enabled, self.analyze, self.apply = enabled, analyze, apply
        self.audit, self.notice, self.env = audit, notice, env
        self.controlled = controlled
        self.controlled_budget = controlled_budget if controlled_budget is not None else {"analyses": 0}
        self.limit_noticed = False
        self.analysis_cancelled: Callable[[], bool] = lambda: False
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
        """只在消息已经配对的模型或回合边界处理已完成的反思，退出时也沿用这个边界。"""
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
                if self.controlled:
                    self.controlled_budget["halted"] = 1
                    self.notice("本次受控自动积累已暂停，不自动重试；可以继续正常任务。")
                return
            if self.controlled and self.analysis_cancelled():
                state.pop("result", None)
                state.update(phase="skipped", reason="cancelled_controlled_learning")
                await self.conversation.set_reflection_state(self.session, state)
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
            if self.controlled and self.analysis_cancelled():
                state.pop("result", None)
                state.update(phase="skipped", reason="cancelled_controlled_learning")
                await self.conversation.set_reflection_state(self.session, state)
                return
            try:
                cached = await self.conversation.scoped_intent(
                    ref, "ReflectMemory", args, True, agent_run=RunRef("reflect", identity),
                    approval_ref="controlled-memory-learning-enabled" if self.controlled else "reflect-memory-enabled")
                if cached is None:
                    # 修改任何记忆文件前，先取得执行意图的持久化确认。
                    applied = await self.apply(result)
                    await self.conversation.scoped_result(ref, json.dumps(applied, ensure_ascii=False))
                else:
                    applied = json.loads(cached) if isinstance(cached, str) else cached
                quiet = (self.controlled or bool(result.get("onTrack", True))) and not (applied.get("added") or applied.get("merged"))
                cadence = applyOutcome(state.get("cadence", initCadence()), quiet, self.maximum)
                advice = None if self.controlled else result.get("advisory")
                await self.conversation.set_reflection_state(
                    self.session, {"id": identity, "phase": "applied", "cadence": cadence},
                    advisories=[f"[反思]\n{advice}"] if advice else ())
            except BaseException:
                # 前面的部分文件可能已经提交，保留这次执行的意图记录。
                # 停止写入，避免用重试或新 ID 覆盖未确认的结果。
                self.stopped = self.conversation.blocked = True
                raise
        if self.controlled and (applied.get("added") or applied.get("merged")):
            self.notice(f"受控记忆：新增{applied.get('added', 0)}条、更新{applied.get('merged', 0)}条项目经验。")
        self.audit({"ran": True, "onTrack": True if self.controlled else result.get("onTrack", True),
                    "advisoryInjected": bool(advice), "memAdded": applied.get("added", 0),
                    "memMerged": applied.get("merged", 0), "interval": cadence["interval"],
                    "note": result.get("note", ""), "corrected": len(applied.get("corrections", [])),
                    "confirmed": applied.get("confirmed", 0)})

    async def after_turn(self, identity: str, *, provider: str, compaction_imminent: bool = False,
                         cancelled: Callable[[], bool] | None = None) -> None:
        if not self.enabled or self.stopped or self.conversation.blocked:
            return
        await self.drain()
        if self.task is not None or self._state().get("id") == identity:
            return
        state = self._state()
        if self.controlled:
            messages = copy.deepcopy(self.session.messages)
            reason = ("analysis_failed" if self.controlled_budget.get("halted") else
                      "analysis_limit" if self.controlled_budget.get("analyses", 0) >= 6 else
                      "no_learning_evidence" if not hasLearningEvidence(messages) else None)
            if reason is not None:
                state.update(id=identity, phase="skipped", controlled=True, reason=reason)
                await self.conversation.set_reflection_state(self.session, state)
                if reason == "analysis_limit" and not self.limit_noticed:
                    self.notice("本次启动已达到6次自动学习分析上限；已有记忆仍可读取，手动记忆工具仍可使用。")
                    self.limit_noticed = True
                return
            state.update(id=identity, phase="analyzing", controlled=True)
            await self.conversation.set_reflection_state(self.session, state)
            self.controlled_budget["analyses"] = self.controlled_budget.get("analyses", 0) + 1
            self.analysis_cancelled = cancelled if cancelled is not None else lambda: False
            self.identity = identity
            self.task = asyncio.create_task(self.analyze(messages), name="ruocun-controlled-learning")
            # 普通 /exit 会触发退出取消，先在当前配对边界收尾，
            # 让已完成的经验有机会保存。
            await asyncio.wait({self.task})
            await self.drain()
            return
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
        # 分析快照须沿用当时的工具集合和已发送前缀。
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
        # 保存已完成的分析供恢复。
        # 公共取消信号置位后，退出流程停止发起新的记忆写入。
        await self.drain(apply_writes=False)
