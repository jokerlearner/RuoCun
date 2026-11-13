"""Synthetic in-memory StoragePort tests; no product directory I/O."""

from __future__ import annotations

import asyncio
import sqlite3
import threading

import pytest

from ruocun.session.contract import (
    DbOwner,
    Intent,
    ProcessIdentity,
    RecoveryView,
    RunRecord,
    RunRef,
    StoreError,
    ToolRef,
    UnknownOutcomeBlockedError,
)
from ruocun.session.sqlite_port import CommitUnconfirmedError
from ruocun.session.storage_worker import StorageWorker


def test_storage_operations_share_one_database_thread() -> None:
    ids: list[int] = []
    owner = DbOwner("one", "synthetic", "a", 1, ProcessIdentity("h", "b", 1, "s"))

    class MemoryPort:
        def __init__(self) -> None:
            ids.append(threading.get_ident())
            self.con = sqlite3.connect(":memory:")
            self.con.execute("create table events (value text)")

        def commit_intent(self, _owner: DbOwner, intent: Intent) -> None:
            ids.append(threading.get_ident())
            self.con.execute("insert into events values (?)", (intent.name,))

        def commit_run_event(self, _owner: DbOwner, run: RunRecord, _event: object) -> None:
            ids.append(threading.get_ident())
            self.con.execute("insert into events values (?)", (run.status,))

        def commit_result_and_event(
            self, _owner: DbOwner, _ref: ToolRef, result: str, _run: object, _event: object,
        ) -> None:
            ids.append(threading.get_ident())
            self.con.execute("insert into events values (?)", (result,))

        def record_recovery_decision(
            self, _owner: DbOwner, decision_id: str, _target: str, _decision: str, _explanation: str,
        ) -> None:
            ids.append(threading.get_ident())
            self.con.execute("insert into events values (?)", (decision_id,))

        def load_recovery_view(self) -> RecoveryView:
            ids.append(threading.get_ident())
            return RecoveryView(owner, None, (), (), (), ())

        def read_pending_events(self) -> tuple[str, ...]:
            ids.append(threading.get_ident())
            return tuple(row[0] for row in self.con.execute("select value from events order by rowid"))

        def close(self, _owner: DbOwner) -> None:
            ids.append(threading.get_ident())
            self.con.close()

    async def run() -> None:
        worker = StorageWorker(lambda: (MemoryPort(), owner))  # type: ignore[arg-type]
        intent = Intent(ToolRef("root", "t1"), RunRef("task", "run"), "intent", "{}", "h", True, "a", "p", 1, "now")
        record = RunRecord(RunRef("task", "run"), "shell", "finished", False, {})
        first = worker.enqueue_intent(intent)
        result = worker.enqueue_result_and_event(intent.tool_ref, "result", None, None)
        second = worker.enqueue_run_event(record, None)
        decision = worker.enqueue_recovery_decision("decision", "target", "resolve", "checked")
        await first.wait()
        await result.wait()
        await second.wait()
        await decision.wait()
        assert await worker.read_pending_events() == ("intent", "result", "finished", "decision")
        assert (await worker.load_recovery_view()).owner == owner
        await worker.close()

    asyncio.run(run())
    assert len(set(ids)) == 1


@pytest.mark.parametrize("error_type", [CommitUnconfirmedError, OSError, RuntimeError])
def test_unknown_commit_blocks_later_writes_but_allows_readback(
    error_type: type[Exception],
) -> None:
    owner = DbOwner("one", "synthetic", "a", 1, ProcessIdentity("h", "b", 1, "s"))

    class MemoryPort:
        def __init__(self) -> None:
            self.con = sqlite3.connect(":memory:")
            self.con.execute("create table events (value text)")

        def commit_intent(self, _owner: DbOwner, intent: Intent) -> None:
            self.con.execute("insert into events values (?)", (intent.name,))
            raise error_type("synthetic unknown commit")

        def commit_run_event(self, _owner: DbOwner, run: RunRecord, _event: object) -> None:
            self.con.execute("insert into events values (?)", (run.status,))

        def read_pending_events(self) -> tuple[str, ...]:
            return tuple(row[0] for row in self.con.execute("select value from events"))

        def close(self, _owner: DbOwner) -> None:
            self.con.close()

    async def run() -> None:
        worker = StorageWorker(lambda: (MemoryPort(), owner))  # type: ignore[arg-type]
        intent = Intent(ToolRef("root", "t1"), RunRef("task", "run"), "first", "{}", "h", True, "a", "p", 1, "now")
        record = RunRecord(RunRef("task", "run"), "shell", "second", False, {})
        first = worker.enqueue_intent(intent)
        second = worker.enqueue_run_event(record, None)
        with pytest.raises(error_type):
            await first.wait()
        assert first.status().state == "outcome_unknown"
        with pytest.raises(StoreError):
            await second.wait()
        assert await worker.read_pending_events() == ("first",)
        await worker.close()

    asyncio.run(run())


def test_cancelled_wait_does_not_cancel_accepted_intent() -> None:
    entered, release = threading.Event(), threading.Event()
    owner = DbOwner("one", "synthetic", "a", 1, ProcessIdentity("h", "b", 1, "s"))

    class MemoryPort:
        def __init__(self) -> None:
            self.con = sqlite3.connect(":memory:")
            self.con.execute("create table events (value text)")

        def commit_intent(self, _owner: DbOwner, intent: Intent) -> None:
            entered.set()
            if not release.wait(10):
                raise RuntimeError("synthetic timeout")
            self.con.execute("insert into events values (?)", (intent.name,))

        def read_pending_events(self) -> tuple[str, ...]:
            return tuple(row[0] for row in self.con.execute("select value from events"))

        def close(self, _owner: DbOwner) -> None:
            self.con.close()

    async def run() -> None:
        worker = StorageWorker(lambda: (MemoryPort(), owner))  # type: ignore[arg-type]
        intent = Intent(ToolRef("root", "t1"), RunRef("task", "run"), "intent", "{}", "h", True, "a", "p", 1, "now")
        handle = worker.enqueue_intent(intent)
        while not entered.is_set():
            await asyncio.sleep(0.01)
        waiter = asyncio.create_task(handle.wait())
        await asyncio.sleep(0)
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        assert handle.status().state == "pending"
        release.set()
        await handle.wait()
        assert handle.status().state == "committed"
        assert await worker.read_pending_events() == ("intent",)
        await worker.close()

    asyncio.run(run())


def test_expected_unknown_outcome_rejection_still_allows_recovery_decision() -> None:
    owner = DbOwner("one", "synthetic", "a", 1, ProcessIdentity("h", "b", 1, "s"))
    decisions: list[str] = []

    class MemoryPort:
        def commit_intent(self, _owner: DbOwner, _intent: Intent) -> None:
            raise UnknownOutcomeBlockedError("synthetic unresolved operation")

        def record_recovery_decision(
            self, _owner: DbOwner, decision_id: str, _target: str, _decision: str, _explanation: str,
        ) -> None:
            decisions.append(decision_id)

        def close(self, _owner: DbOwner) -> None:
            pass

    async def run() -> None:
        worker = StorageWorker(lambda: (MemoryPort(), owner))  # type: ignore[arg-type]
        intent = Intent(ToolRef("root", "t1"), RunRef("task", "run"), "intent", "{}", "h", True, "a", "p", 1, "now")
        blocked = worker.enqueue_intent(intent)
        recovery = worker.enqueue_recovery_decision("d1", "target", "resolve", "checked")
        with pytest.raises(UnknownOutcomeBlockedError):
            await blocked.wait()
        await recovery.wait()
        await worker.close()

    asyncio.run(run())
    assert decisions == ["d1"]


def test_accepted_run_snapshot_cannot_be_mutated_by_caller() -> None:
    owner = DbOwner("one", "synthetic", "a", 1, ProcessIdentity("h", "b", 1, "s"))
    release = threading.Event()
    observed: list[str] = []

    class MemoryPort:
        def commit_run_event(self, _owner: DbOwner, run: RunRecord, _event: object) -> None:
            if not release.wait(10):
                raise RuntimeError("synthetic timeout")
            observed.append(run.snapshot["message"])

        def close(self, _owner: DbOwner) -> None:
            pass

    async def run() -> None:
        worker = StorageWorker(lambda: (MemoryPort(), owner))  # type: ignore[arg-type]
        record = RunRecord(RunRef("task", "run"), "shell", "running", False, {"message": "before"})
        handle = worker.enqueue_run_event(record, None)
        record.snapshot["message"] = "after"
        release.set()
        await handle.wait()
        await worker.close()

    asyncio.run(run())
    assert observed == ["before"]
