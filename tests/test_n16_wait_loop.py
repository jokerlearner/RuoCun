"""Frozen TaskWait single-call/yield and event-driven scheduler source assertions."""

import asyncio
import copy
from dataclasses import replace

import pytest
from test_mvp_loop import Model, call, reply
from test_n1_session_scheduler import QueueStore, complete

from ruocun.agent.background_runtime import BackgroundRuntime, wait_scope
from ruocun.agent.background_types import ExecutionEvent, ExecutionSnapshot
from ruocun.agent.loop import run_turn
from ruocun.session.session import Session
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.task_wait import taskWaitTool
from ruocun.tools.types import Tool, ToolContext


class Journal:
    def __init__(self):
        self.saved = []

    async def save(self, session):
        self.saved.append(copy.deepcopy(session.messages))

    async def intent(self, *args):
        return None

    async def result(self, *args):
        pass


async def approve(*args):
    return True


async def start(runtime):
    snapshot = ExecutionSnapshot("a", "a-1", "shell", True, "a", "running")
    await runtime.publish(ExecutionEvent("started", snapshot))
    return snapshot


def test_real_loop_yields_after_saved_taskwait_and_mixed_batch_only_rejects_wait():
    async def scenario():
        runtime = BackgroundRuntime()
        await start(runtime)
        registry = ToolRegistry()
        registry.register(taskWaitTool)

        async def read(args, ctx):
            return "read result"

        registry.register(
            Tool("Read", "read", {"type": "object"}, "read", "auto", read)
        )
        session = Session("SYS", "synthetic", env={})
        model = Model([reply(calls=[call('{"ids":["a"]}', "TaskWait")])])
        journal = Journal()
        with wait_scope(runtime) as control:
            result = await run_turn(
                session,
                {"model": "synthetic"},
                registry,
                ToolContext("synthetic"),
                approve=approve,
                request=model,
                journal=journal,
                wait_control=control,
            )
        assert result.status == "waiting" and result.wait.targets[0].runId == "a-1"
        assert len(model.requests) == 1 and journal.saved[-1][-1]["role"] == "tool"
        runtime.release(result.wait)
        model = Model(
            [
                reply(
                    calls=[
                        call('{"ids":["a"]}', "TaskWait", "wait"),
                        call("{}", "Read", "read"),
                    ]
                ),
                reply("done"),
            ]
        )
        with wait_scope(runtime) as control:
            result = await run_turn(
                session,
                {"model": "synthetic"},
                registry,
                ToolContext("synthetic"),
                approve=approve,
                request=model,
                journal=journal,
                wait_control=control,
            )
        assert result.status == "complete" and runtime.activeWaits == 0
        messages = {
            message.get("tool_call_id"): message
            for message in session.messages
            if message.get("role") == "tool"
        }
        assert (
            "必须单独调用" in messages["wait"]["content"]
            and messages["read"]["content"] == "read result"
        )

    asyncio.run(scenario())


def test_scheduler_waits_for_event_without_model_poll_and_user_can_interrupt():
    async def scenario():
        runtime = BackgroundRuntime()
        snapshot = await start(runtime)
        store = QueueStore()
        calls = []

        async def deliver():
            runtime.acknowledge([event.eventId for event in runtime.events()])

        async def run(signal, boundary, generation):
            calls.append(generation)
            if len(calls) == 1:
                handle, _ = runtime.prepare({"ids": ["a"], "mode": "any"})
                from ruocun.agent.loop import TurnResult

                return TurnResult("waiting", wait=handle)
            return complete()

        scheduler = store.scheduler(
            run, background_runtime=runtime, deliver_background=deliver
        )
        await scheduler.submit("start")
        await scheduler.settled()
        assert scheduler.status().state == "waiting" and len(calls) == 1
        await asyncio.sleep(0.01)
        assert len(calls) == 1
        with pytest.raises(RuntimeError, match="synthetic summary failure"):
            async with scheduler.preserve_wait() as waiting:
                assert waiting and runtime.activeWaits == 1
                await runtime.publish(
                    ExecutionEvent(
                        "completed", replace(snapshot, status="completed", result="done")
                    )
                )
                await asyncio.sleep(0)
                assert scheduler.status().state == "waiting" and len(calls) == 1
                raise RuntimeError("synthetic summary failure")
        await scheduler.settled()
        assert store.state == "paused" and len(calls) == 1 and runtime.activeWaits == 1
        assert runtime.events()
        async with scheduler.preserve_wait() as waiting:
            assert waiting and scheduler.status().state == "paused"
            assert runtime.activeWaits == 1 and runtime.events()
        await scheduler.finished()
        assert (
            len(calls) == 2
            and not runtime.events()
            and scheduler.status().state == "idle"
        )
        await scheduler.close()
        # User input releases an otherwise unready wait, preserving the same runner identity.
        runtime = BackgroundRuntime()
        await start(runtime)
        store = QueueStore()
        calls = []
        scheduler = store.scheduler(
            run, background_runtime=runtime, deliver_background=deliver
        )
        await scheduler.submit("start")
        await scheduler.settled()
        assert scheduler.status().state == "waiting"
        await scheduler.submit("additional")
        await scheduler.finished()
        assert (
            store.messages == ["start", "additional"]
            and runtime.activeWaits == 0
            and len(calls) == 2
        )
        await scheduler.close()

    asyncio.run(scenario())
