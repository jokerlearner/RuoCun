"""Frozen background_runtime.test.ts assertions; no models or process matrix."""

import asyncio
import json
from dataclasses import replace

import pytest

from ruocun.agent.background_runtime import BackgroundRuntime, WaitControl
from ruocun.agent.background_types import ExecutionEvent, ExecutionSnapshot


async def execution(runtime, task="a", run=None, kind="agent"):
    snapshot = ExecutionSnapshot(task, run or task + "-1", kind, True, task, "running")
    await runtime.publish(ExecutionEvent("started", snapshot))
    return snapshot


async def finish(runtime, snapshot, status="completed"):
    await runtime.publish(
        ExecutionEvent(
            status, replace(snapshot, status=status, result=snapshot.runId + " result")
        )
    )


@pytest.mark.parametrize("mode", ["any", "all"])
def test_mixed_wait_and_unrelated_completion(mode):
    async def scenario():
        runtime = BackgroundRuntime()
        a = await execution(runtime)
        b = await execution(runtime, "b", kind="shell")
        c = await execution(runtime, "c")
        handle, ready = runtime.prepare({"ids": ["a", "b", "a"], "mode": mode})
        assert len(handle.targets) == 2 and not ready
        await finish(runtime, c)
        await runtime.publish(ExecutionEvent("progress", a))
        assert not runtime.ready(handle)
        await finish(runtime, a)
        assert runtime.ready(handle) == (mode == "any")
        await finish(runtime, b)
        assert runtime.ready(handle)
        runtime.release(handle)
        assert runtime.activeWaits == 0

    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["failed", "canceled", "attention"])
def test_unrelated_failure_cancel_attention_wakes_all(kind):
    async def scenario():
        runtime = BackgroundRuntime()
        await execution(runtime)
        b = await execution(runtime, "b")
        handle, _ = runtime.prepare({"ids": ["a"], "mode": "all"})
        if kind == "attention":
            await runtime.publish(
                ExecutionEvent(
                    "message", b, message="needs decision", requiresAttention=True
                )
            )
        else:
            await finish(runtime, b, kind)
        assert runtime.ready(handle)

    asyncio.run(scenario())


def test_validate_targets_atomically_and_distinct_limit():
    async def scenario():
        runtime = BackgroundRuntime()
        await execution(runtime)
        await runtime.publish(
            ExecutionEvent(
                "started",
                ExecutionSnapshot("foreground", "f-1", "agent", False, "fg", "running"),
            )
        )
        for target in ["missing", "manual", "foreground"]:
            with pytest.raises(ValueError):
                runtime.prepare({"ids": ["a", target], "mode": "any"})
        assert runtime.activeWaits == 0
        for ids in [[], [str(n) for n in range(33)]]:
            with pytest.raises(ValueError):
                runtime.prepare({"ids": ids, "mode": "any"})
        handle, _ = runtime.prepare({"ids": ["a"] * 50, "mode": "any"})
        assert len(handle.targets) == 1
        runtime.dispose()

    asyncio.run(scenario())


def test_completion_before_prepare_and_during_save():
    async def scenario():
        runtime = BackgroundRuntime()
        a = await execution(runtime)
        control = WaitControl(runtime)
        assert (
            json.loads(control.request({"ids": ["a"], "mode": "any"}))["status"]
            == "waiting"
        )
        await finish(runtime, a)
        handle = control.commit()
        assert runtime.ready(handle) and len(runtime.events()) == 1
        runtime.release(handle)
        ready = WaitControl(runtime)
        assert (
            json.loads(ready.request({"ids": ["a"], "mode": "any"}))["status"]
            == "ready"
        )
        assert len(runtime.events()) == 1
        assert ready.commit() is None and not runtime.events()

    asyncio.run(scenario())


def test_fixed_run_late_terminal_and_gc_pinning():
    async def scenario():
        runtime = BackgroundRuntime()
        old = await execution(runtime, "same", "old")
        pinned, _ = runtime.prepare({"ids": ["same"], "mode": "all"})
        await finish(runtime, old)
        current = await execution(runtime, "same", "new")
        await finish(runtime, old, "failed")
        assert runtime.result(pinned)[0].result == "old result"
        assert runtime.snapshot("same").runId == current.runId
        await finish(runtime, current)
        runtime.acknowledge([event.eventId for event in runtime.events()])
        for n in range(1000):
            snap = await execution(runtime, str(n))
            await finish(runtime, snap)
            handle, _ = runtime.prepare({"ids": [str(n)], "mode": "any"})
            runtime.acknowledge([event.eventId for event in runtime.events()])
            runtime.release(handle)
        assert (
            runtime.result(pinned)[0].result == "old result"
            and runtime.activeWaits == 1
        )
        runtime.release(pinned)
        assert runtime.activeWaits == 0 and len(runtime.snapshots()) <= 200

    asyncio.run(scenario())


def test_progress_reset_and_dispose_reject_previous_events():
    async def scenario():
        runtime = BackgroundRuntime()
        old = await execution(runtime)
        await runtime.publish(ExecutionEvent("progress", old))
        assert runtime.events() == []
        runtime.reset()
        await finish(runtime, old)
        assert runtime.events() == []
        runtime.dispose()
        await finish(runtime, await execution(runtime, "b"))
        assert runtime.events() == []

    asyncio.run(scenario())
