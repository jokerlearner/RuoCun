"""冻结session_scheduler.test.ts前台断言及R2必要队列适配。"""

import asyncio
import copy
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ruocun.agent.session_scheduler import SessionScheduler
from ruocun.session.contract import AcceptedInput


class QueueStore:
    """已审Conversation队列接口的系统边界替身，不实现第二份产品存储。"""

    def __init__(self):
        self.records = []
        self.messages = []
        self.state = "idle"

    def queued_inputs(self):
        return tuple(item for item in self.records if item.state == "queued")

    async def queue_user(self, content):
        seq = len(self.records) + 1
        item = AcceptedInput(str(seq), seq, json.dumps(copy.deepcopy(content)), (), "queued")
        self.records.append(item)
        return item

    async def consume_user(self, input_id):
        for index, item in enumerate(self.records):
            if item.input_id == input_id and item.state == "queued":
                self.records[index] = replace(item, state="consumed")
                self.messages.append(json.loads(item.payload))
                return True
        return False

    async def discard_queued(self, state):
        self.records = [replace(item, state="discarded") if item.state == "queued" else item
                        for item in self.records]
        self.state = state

    async def set_state(self, state):
        self.state = state

    def scheduler(self, run, **kwargs):
        return SessionScheduler(queued_inputs=self.queued_inputs, queue_user=self.queue_user,
                                consume_user=self.consume_user, discard_queued=self.discard_queued,
                                set_state=self.set_state, run=run, **kwargs)


def test_clear_pending_keeps_the_active_turn_running():
    # WT-04 Esc先清已确认队列，复用现有调度器公开接缝和合成存储。
    async def scenario():
        store = QueueStore()
        started, release = asyncio.Event(), asyncio.Event()
        signals = []

        async def run(signal, boundary, generation):
            signals.append(signal)
            started.set()
            await release.wait()
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await started.wait()
        await scheduler.submit("queued")
        assert await scheduler.clear_pending() == 1
        assert scheduler.status().state == "running"
        assert scheduler.status().queued == 0
        assert not signals[0].is_set()
        release.set()
        await scheduler.finished()
        assert store.messages == ["start"]
    asyncio.run(scenario())

def complete():
    return SimpleNamespace(status="complete", error="")


def test_session_loop_deduplicates_pending_input_and_stops_without_canceling_active_turn():
    # Frozen App.tsx /loop: enqueue through the scheduler, keep one pending
    # copy, and clear the interval without interrupting the current request.
    async def scenario():
        store = QueueStore()
        started, release = asyncio.Event(), asyncio.Event()
        signals = []

        async def run(signal, boundary, generation):
            signals.append(signal)
            started.set()
            await release.wait()
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await started.wait()
        await scheduler.start_loop(.01, "periodic")
        await asyncio.sleep(.05)
        assert [json.loads(item.payload) for item in store.queued_inputs()] == ["periodic"]
        assert await scheduler.stop_loop()
        assert not signals[0].is_set()
        await scheduler.clear_pending()
        release.set()
        await scheduler.finished()
        await scheduler.start_loop(.01, "after close")
        await scheduler.close()
        await asyncio.sleep(.03)
        assert [json.loads(item.payload) for item in store.records] == ["start", "periodic"]

    asyncio.run(scenario())


def test_busy_submissions_are_consumed_in_fifo_at_boundary_without_concurrent_run():
    # 来源 user input ... late results never start concurrent model turns 的前台子路径。
    async def scenario():
        store = QueueStore()
        started = asyncio.Event()
        gate = asyncio.Event()
        consume_boundary = None
        calls = 0

        async def run(signal, boundary, generation):
            nonlocal calls, consume_boundary
            calls += 1
            consume_boundary = boundary
            started.set()
            await gate.wait()
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await started.wait()
        await scheduler.submit("change plan")
        await scheduler.submit("more")
        assert calls == 1 and store.messages == ["start"]
        assert scheduler.hasQueued("more")
        await consume_boundary()
        assert store.messages == ["start", "change plan", "more"]
        gate.set()
        await scheduler.finished()
        assert calls == 1 and scheduler.status().state == "idle"
    asyncio.run(scenario())


def test_close_resolves_existing_waiters_only_after_active_run_settles():
    # 冻结source同名close用例。
    async def scenario():
        store = QueueStore()
        started, done = asyncio.Event(), asyncio.Event()

        async def run(signal, boundary, generation):
            started.set()
            await done.wait()
            assert signal.is_set()
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await started.wait()
        settled = asyncio.create_task(scheduler.settled())
        finished = asyncio.create_task(scheduler.finished())
        closing = asyncio.create_task(scheduler.close())
        await asyncio.sleep(0)
        assert scheduler.status().state == "closed"
        assert not closing.done() and not settled.done() and not finished.done()
        done.set()
        await asyncio.gather(closing, settled, finished)
        assert await scheduler.submit("ignored") is None
        assert len(store.records) == 1
    asyncio.run(scenario())


def test_submit_during_interrupted_run_waits_and_uses_fresh_event_and_generation():
    # 冻结submit during interrupted run ... starts one new run，附D08旧delta过滤。
    async def scenario():
        store = QueueStore()
        started, done = asyncio.Event(), asyncio.Event()
        leases, signals = [], []
        calls = 0

        async def run(signal, boundary, generation):
            nonlocal calls
            calls += 1
            leases.append(generation)
            signals.append(signal)
            if calls == 1:
                started.set()
                await done.wait()
                return SimpleNamespace(status="cancelled", error="")
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await started.wait()
        assert scheduler.is_current(leases[0])
        await scheduler.pause()
        assert signals[0].is_set() and not scheduler.is_current(leases[0])
        await scheduler.submit("continue")
        assert calls == 1
        done.set()
        await scheduler.finished()
        assert calls == 2 and store.messages == ["start", "continue"]
        assert signals[0] is not signals[1] and not signals[1].is_set()
        assert leases[0] != leases[1] and scheduler.status().state == "idle"
        await scheduler.close()
    asyncio.run(scenario())


def test_hook_rejected_input_does_not_run_model_and_reset_discards_queued_input():
    # 冻结Hook拒绝/重置用例的前台分支；不冒充后台事件恢复通过。
    async def scenario():
        store = QueueStore()
        calls = 0

        async def run(signal, boundary, generation):
            nonlocal calls
            calls += 1
            return complete()

        async def rejected(input_id):
            store.records = [replace(item, state="discarded") if item.input_id == input_id else item
                             for item in store.records]
            return False

        scheduler = SessionScheduler(queued_inputs=store.queued_inputs, queue_user=store.queue_user,
                                     consume_user=rejected, discard_queued=store.discard_queued,
                                     set_state=store.set_state, run=run)
        await scheduler.submit("blocked")
        await scheduler.finished()
        assert calls == 0 and store.messages == [] and store.records[0].state == "discarded"
        await scheduler.submit("not yet consumed")
        await scheduler.reset()
        await scheduler.settled()
        assert store.records[1].state == "discarded" and scheduler.status().state == "idle"
        assert calls == 0
        await scheduler.close()
    asyncio.run(scenario())


def test_recover_preserves_queued_inputs_until_resume_and_pause_records_discarded():
    # R2必要确认：不把冻结TS内存队列当作保存承诺的完整实现。
    async def scenario():
        store = QueueStore()
        await store.queue_user("older acknowledged input")
        calls = 0

        async def run(signal, boundary, generation):
            nonlocal calls
            calls += 1
            return complete()

        scheduler = store.scheduler(run)
        await scheduler.recover("running")
        assert scheduler.status().state == "paused"
        assert store.records[0].state == "queued" and calls == 0
        await scheduler.submit("continue")
        await scheduler.finished()
        assert store.messages == ["older acknowledged input", "continue"] and calls == 1
        await store.queue_user("explicitly discarded")
        await scheduler.pause()
        assert store.records[-1].state == "discarded" and store.state == "paused"
        await scheduler.close()
        reopened = store.scheduler(run)
        await reopened.recover("closed")
        assert reopened.status().state == "idle"
        await reopened.close()
    asyncio.run(scenario())


def test_queue_save_failure_pauses_without_ack_or_model_call():
    # 来源保存失败暂停语义的R2队列适配；真实blocked由root的Conversation掌握。
    async def scenario():
        store = QueueStore()
        failure = OSError("synthetic queue save failure")

        async def queue_user(content):
            raise failure

        async def run(signal, boundary, generation):
            raise AssertionError("must not call model")

        scheduler = SessionScheduler(queued_inputs=store.queued_inputs, queue_user=queue_user,
                                     consume_user=store.consume_user, discard_queued=store.discard_queued,
                                     set_state=store.set_state, run=run)
        with pytest.raises(OSError):
            await scheduler.submit("not acknowledged")
        assert scheduler.lastError is failure and scheduler.status().state == "paused"
        assert store.records == [] and scheduler.counters["runCalls"] == 0
        await scheduler.close()

        entered, release = asyncio.Event(), asyncio.Event()

        async def late_failure(content):
            entered.set()
            await release.wait()
            raise failure

        closing_scheduler = SessionScheduler(
            queued_inputs=store.queued_inputs, queue_user=late_failure,
            consume_user=store.consume_user, discard_queued=store.discard_queued,
            set_state=store.set_state, run=run,
        )
        submitting = asyncio.create_task(closing_scheduler.submit("not acknowledged"))
        await entered.wait()
        closing = asyncio.create_task(closing_scheduler.close())
        await asyncio.sleep(0)
        assert closing_scheduler.status().state == "closed"
        release.set()
        with pytest.raises(OSError):
            await submitting
        await closing
        assert closing_scheduler.status().state == "closed"
        assert closing_scheduler.lastError is failure
        assert await closing_scheduler.submit("ignored") is None
    asyncio.run(scenario())


def test_cooperative_cancelled_run_reaches_paused_without_counting_failure():
    # 源interrupted终态映射；直接Event取消也不能遗留空的running状态。
    async def scenario():
        store = QueueStore()

        async def run(signal, boundary, generation):
            signal.set()
            return SimpleNamespace(status="cancelled", error="")

        scheduler = store.scheduler(run)
        await scheduler.submit("start")
        await scheduler.finished()
        assert scheduler.status().state == "paused"
        assert scheduler.lastError is None and scheduler.counters["failures"] == 0
        await scheduler.close()
    asyncio.run(scenario())


def test_session_loop_does_not_restart_after_manual_recovery():
    async def scenario():
        store = QueueStore()

        async def run(signal, boundary, generation):
            if store.messages[-1] == "failed turn":
                return SimpleNamespace(status="failed", error="synthetic session failure")
            return complete()

        scheduler = store.scheduler(run)
        try:
            await scheduler.start_loop(.15, "old periodic input")
            await scheduler.submit("failed turn")
            await scheduler.finished()
            assert scheduler.status().state == "paused"
            await scheduler.submit("manual recovery")
            await scheduler.finished()
            assert scheduler.lastError is None
            await asyncio.sleep(.2)
            assert store.messages == ["failed turn", "manual recovery"]
            assert not scheduler.hasQueued("old periodic input")
        finally:
            await scheduler.close()

    asyncio.run(scenario())
