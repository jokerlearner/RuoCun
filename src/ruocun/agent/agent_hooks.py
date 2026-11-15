"""在单个代理通过准入后运行其生命周期钩子，并维护本次执行的钩子状态。"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Protocol

from ..hooks.hooks import HookRuntime, HookSpec, RunCtx
from ..hooks.journal import HookJournal, HookOutcomeUnknown, runJournaledHooks
from ..session.contract import RunRef
from ..session.session import Session
from .agent_defs import AgentDefinition


class AgentHookJournal(HookJournal, Protocol):
    async def save(self, session: Session) -> None: ...


def createAgentHookRuntime(
    definition: AgentDefinition, env: Mapping[str, str], *,
    audit_dir: Path | None = None, redact: Callable[[str], str] | None = None,
) -> HookRuntime | None:
    specs = [HookSpec(event, command=command) for event in ("SubagentStart", "SubagentStop")
             for command in definition.hooks.get(event, ())]
    return HookRuntime(specs, env, audit_dir=audit_dir, redact=redact) if specs else None


def _context(event: str, cwd: str, agent_id: str, agent_type: str) -> RunCtx:
    return RunCtx(cwd, payload={"hook_event_name": event, "agent_id": agent_id, "agent_type": agent_type})


async def startAgentHooks(
    runtime: HookRuntime, session: Session, run: RunRef, agent_type: str, cwd: str,
    signal: threading.Event, journal: AgentHookJournal,
) -> None:
    if signal.is_set():
        return
    context = _context("SubagentStart", cwd, run.task_id, agent_type)
    outcome = await runJournaledHooks(runtime, "SubagentStart", run.run_id, context, signal, journal)
    if outcome.additional_context and not signal.is_set():
        message = {"role": "system", "content": "[hook 注入的上下文]\n" + runtime.redacted(outcome.additional_context)}
        session.messages.append(message)
        try:
            await journal.save(session)
        except Exception as error:
            session.messages.pop()
            raise HookOutcomeUnknown("SubagentStart 的上下文保存未确认，未派发子代理模型。") from error


async def stopAgentHooks(
    runtime: HookRuntime, run: RunRef, agent_type: str, cwd: str, journal: HookJournal, *,
    agent_id: str | None = None,
) -> None:
    context = _context("SubagentStop", cwd, agent_id if agent_id is not None else run.task_id, agent_type)
    await runJournaledHooks(runtime, "SubagentStop", run.run_id, context, threading.Event(), journal)
