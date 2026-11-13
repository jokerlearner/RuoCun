"""Storage worker failure reporting at the storage-port boundary."""

from __future__ import annotations

import asyncio
import threading

import pytest

from ruocun.session.contract import Checkpoint
from ruocun.session.storage_worker import StorageWorker


def test_unclassified_storage_failure_does_not_claim_rollback() -> None:
    class UnknownPort:
        def commit_checkpoint_ack(self, *_args: object, **_kwargs: object) -> int:
            raise RuntimeError("synthetic unknown failure")

        def close(self, _owner: object) -> None:
            pass

    async def run() -> None:
        worker = StorageWorker(lambda: (UnknownPort(), object()))  # type: ignore[arg-type]
        cp = Checkpoint("one", (), "model", "normal", "", 0, (), (), {}, "idle", 0)
        handle = worker.enqueue_checkpoint(0, cp, ())
        with pytest.raises(RuntimeError):
            await handle.wait()
        assert handle.status().state == "outcome_unknown"
        await worker.close()

    asyncio.run(run())


def test_cancelled_close_can_be_awaited_again() -> None:
    ready = threading.Event()
    closed = threading.Event()

    class Port:
        def close(self, _owner: object) -> None:
            closed.set()

    def factory() -> tuple[object, object]:
        assert ready.wait(10)
        return Port(), object()

    async def run() -> None:
        worker = StorageWorker(factory)  # type: ignore[arg-type]
        first = asyncio.create_task(worker.close())
        await asyncio.sleep(0)
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        second = asyncio.create_task(worker.close())
        await asyncio.sleep(0)
        assert not second.done(), "the DB has not closed yet"
        ready.set()
        await second
        assert closed.is_set()

    asyncio.run(run())
