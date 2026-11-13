"""Independent real-file StoragePort probe. Reviewed before execution.

Only explicit synthetic roots and the fixed public SQLite archive are accepted.
No parent environment, credentials, source checkout imports, or remote service.
The script is also suitable for a repository-external product-wheel-only venv.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("root", type=Path)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    assert root.is_dir()
    assert args.archive.is_absolute()

    from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
    runtime = verify_controlled_runtime(verify_official_archive(args.archive, root / "dll"))
    assert runtime.version == "3.54.1"
    assert runtime.source_id == "2026-10-16 14:45:20 555e07ef33f69a0957d24d8e555b702464a131d6f1607f4c3c1e4551e8e6ca76"
    assert runtime.dll_sha256 == "4b59d3cded9dc1608544160f3b4b10ac974c6ac0d6ffc23064e5f4c8dbd05aea"
    assert runtime.compile_options and "win32" in runtime.vfs

    # Import SQLite only after the actual official library has been loaded.
    import sqlite3
    from ruocun.session.contract import (
        AcceptedInput, Checkpoint, Intent, OutboxEvent, OwnerConflictError,
        OwnerFencedError, RunRecord, RunRef, StoreError, ToolRef,
    )
    from ruocun.session.durable_store import DurableStore, read_durable_state
    from ruocun.session.process_identity import RealIdentityProvider

    directory = root / "private"
    cp = Checkpoint(
        "review-one", ({"role": "user", "content": "独立保存中文"},),
        "synthetic-model", "normal", "独立标题", 0,
        (AcceptedInput("input-1", 1, "已确认排队", (), "queued"),),
        (), {"promptTokens": 7, "completionTokens": 3}, "idle", 0,
    )

    if args.action == "runtime":
        print(json.dumps(asdict(runtime), ensure_ascii=False))
        return
    if args.action == "readonly":
        state = read_durable_state(directory, runtime)
        print(json.dumps(state, ensure_ascii=False))
        return
    if args.action.startswith("mutate-"):
        con = sqlite3.connect(directory / "session.db", isolation_level=None)
        try:
            if args.action == "mutate-future":
                con.execute("PRAGMA user_version=99")
            elif args.action == "mutate-dao":
                con.execute("PRAGMA user_version=2")
            elif args.action == "mutate-zero":
                con.execute("PRAGMA user_version=0")
            elif args.action == "mutate-missing-checkpoint":
                con.execute("DELETE FROM meta WHERE key='checkpoint'")
            elif args.action == "mutate-checkpoint-revision":
                data = json.loads(con.execute("SELECT json FROM meta WHERE key='checkpoint'").fetchone()[0])
                data["revision"] += 100
                con.execute("UPDATE meta SET json=? WHERE key='checkpoint'", (json.dumps(data),))
            else:
                raise AssertionError("unknown synthetic mutation")
        finally:
            con.close()
        print(json.dumps({"mutated": args.action}))
        return

    if args.action in ("worker-cancel", "worker-lost-ack"):
        import asyncio
        import threading
        from ruocun.session.sqlite_port import CommitUnconfirmedError
        from ruocun.session.storage_worker import StorageWorker

        release = threading.Event()
        lose_ack = False
        connection_factory = sqlite3.connect

        class LostAcknowledgement(sqlite3.Connection):
            def execute(self, sql, *parameters, **keywords):
                nonlocal lose_ack
                result = super().execute(sql, *parameters, **keywords)
                if sql == "COMMIT" and lose_ack:
                    lose_ack = False
                    raise sqlite3.OperationalError("synthetic acknowledgement lost after real disk COMMIT")
                return result

        if args.action == "worker-lost-ack":
            sqlite3.connect = lambda *a, **k: connection_factory(*a, factory=LostAcknowledgement, **k)

        def factory():
            if not release.wait(10):
                raise RuntimeError("synthetic factory scheduling deadline")
            provider = RealIdentityProvider()
            port = DurableStore(directory, "review-one", root, runtime, provider)
            owned, _ = port.open_or_claim(provider.current())
            return port, owned

        async def exercise():
            nonlocal lose_ack
            worker = StorageWorker(factory)
            try:
                if args.action == "worker-cancel":
                    handle = worker.enqueue_checkpoint(0, cp, (), operation_id="review-cancelled-wait")
                    cp.messages[0]["content"] = "must-not-change-accepted-input"
                    waiter = asyncio.create_task(handle.wait())
                    await asyncio.sleep(0)
                    waiter.cancel()
                    try:
                        await waiter
                    except asyncio.CancelledError:
                        pass
                    else:
                        raise AssertionError("cancelled wait reported success")
                    assert handle.status().state == "pending"
                    release.set()
                    assert await handle.wait() == 1
                    assert handle.status().state == "committed"
                    receipt = await worker.lookup_checkpoint_operation(handle.operation_id, request_digest=handle.request_digest)
                    assert receipt.revision == 1
                    view = await worker.load_recovery_view()
                    assert view.checkpoint.messages == ({"role": "user", "content": "独立保存中文"},)
                else:
                    release.set()
                    await worker.load_recovery_view()
                    lose_ack = True
                    handle = worker.enqueue_checkpoint(0, cp, (), operation_id="review-unknown-commit")
                    later = worker.enqueue_run_event(RunRecord(RunRef("later-task", "later-run"), "shell", "must-not-commit", False, {}), None)
                    try:
                        await handle.wait()
                    except CommitUnconfirmedError:
                        pass
                    else:
                        raise AssertionError("lost COMMIT acknowledgement reported success")
                    assert handle.status().state == "outcome_unknown"
                    try:
                        await later.wait()
                    except StoreError:
                        pass
                    else:
                        raise AssertionError("later write ran after unknown COMMIT")
                    receipt = await worker.lookup_checkpoint_operation(handle.operation_id, request_digest=handle.request_digest)
                    assert receipt.revision == 1
                    view = await worker.load_recovery_view()
                    assert view.checkpoint.revision == 1 and view.runs == ()
            finally:
                release.set()
                await worker.close()

        asyncio.run(exercise())
        for thread in threading.enumerate():
            if thread.name.startswith("ruocun-db"):
                thread.join(timeout=5)
                assert not thread.is_alive()
        # SQLite and the namespace pins must be closed before close() returns.
        directory.rename(root / "closed-session")
        assert read_durable_state(root / "closed-session", runtime)["revision"] == 1
        print(json.dumps({"scenario": args.action, "real_disk": True, "thread_joined": True, "namespace_released": True}))
        return

    identities = RealIdentityProvider()
    store = DurableStore(directory, "review-one", root, runtime, identities)
    try:
        owner, view = store.open_or_claim(identities.current())
    except OwnerConflictError:
        if args.action != "expect-live-owner":
            raise
        print(json.dumps({"live_owner_rejected": True}))
        return
    if args.action == "expect-live-owner":
        store.close(owner)
        raise AssertionError("live owner was displaced")

    try:
        assert store.config == {"journal_mode": "wal", "synchronous": 2, "busy_timeout": 3000, "foreign_keys": 1}
        if args.action == "save":
            assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id="review-checkpoint-1") == 1
            print(json.dumps({"saved_revision": 1, "owner_epoch": owner.owner_epoch}))
        elif args.action == "claim":
            assert view.checkpoint is not None
            print(json.dumps({"owner_epoch": owner.owner_epoch, "checkpoint": asdict(view.checkpoint)}, ensure_ascii=False))
        elif args.action == "hold":
            assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id="review-checkpoint-1") == 1
            print(json.dumps({"ready": True, "owner_epoch": owner.owner_epoch}), flush=True)
            command = sys.stdin.readline().strip()
            if command == "checkpoint":
                assert store.commit_checkpoint_ack(owner, 1, replace(cp, revision=1), (), operation_id="review-checkpoint-2") == 2
                print(json.dumps({"saved_revision": 2}), flush=True)
                sys.stdin.readline()
            elif command not in ("", "close"):
                raise AssertionError("unknown synthetic hold command")
        elif args.action.startswith("association-"):
            store.commit_checkpoint_ack(owner, 0, cp, ())
            intended = RunRef("task-1", "run-1")
            unrelated = RunRef("other-task", "other-run")
            run = RunRecord(intended, "shell", "completed", False, {"result": "synthetic"})
            event = OutboxEvent("event-1", "review-one", intended, "completed", {"result": "synthetic"}, owner.owner_epoch)
            ref = ToolRef("root", "tool-1")
            if args.action.startswith("association-result-"):
                store.commit_intent(owner, Intent(ref, intended, "synthetic", "{}", hashlib.sha256(b"{}").hexdigest(), True, "approval", "policy", owner.owner_epoch, "synthetic-time"))
            if args.action == "association-result-run":
                run, event = replace(run, run_ref=unrelated), None
            elif args.action.endswith("event-run"):
                event = replace(event, run_ref=unrelated)
            elif args.action.endswith("event-session"):
                event = replace(event, session_id="other-session")
            else:
                raise AssertionError("unknown association scenario")
            try:
                if args.action.startswith("association-result-"):
                    store.commit_result_and_event(owner, ref, "known-result", run, event)
                else:
                    store.commit_run_event(owner, run, event)
            except StoreError:
                view = store.load_recovery_view()
                assert view.runs == () and view.pending_events == ()
                if args.action.startswith("association-result-"):
                    assert view.tool_records[0].state == "started"
                print(json.dumps({"rejected_atomically": args.action}))
            else:
                view = store.load_recovery_view()
                raise AssertionError(json.dumps({
                    "accepted_conflict": args.action,
                    "tool_states": [item.state for item in view.tool_records],
                    "run_refs": [asdict(item.run_ref) for item in view.runs],
                    "event_sessions": [item.session_id for item in view.pending_events],
                    "event_run_refs": [asdict(item.run_ref) for item in view.pending_events],
                }))
        elif args.action in ("atomic", "disk-full"):
            assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id="review-checkpoint-1") == 1
            run = RunRecord(RunRef("task-1", "run-1"), "shell", "completed", False, {"output": "stable"})
            event = OutboxEvent("event-1", "review-one", run.run_ref, "completed", {"output": "stable"}, owner.owner_epoch)
            saved_event = store.commit_run_event(owner, run, event)
            assert saved_event is not None and saved_event.seq == 1
            if args.action == "atomic":
                try:
                    store.commit_run_event(owner, replace(run, status="different"), replace(event, snapshot={"output": "conflict"}))
                except StoreError:
                    pass
                else:
                    raise AssertionError("duplicate event ID with changed content was accepted")
                restored = store.load_recovery_view()
                assert restored.runs == (run,)
                assert len(restored.pending_events) == 1
                assert restored.pending_events[0].snapshot == {"output": "stable"}
                # Genuine current owner, malformed epoch: reject before modifying disk.
                try:
                    store.commit_checkpoint_ack(replace(owner, owner_epoch=owner.owner_epoch + 1), 1, replace(cp, revision=1), ("event-1",))
                except OwnerFencedError:
                    pass
                else:
                    raise AssertionError("mismatched owner epoch was allowed to commit")
                assert store.load_recovery_view().checkpoint.revision == 1
                assert len(store.read_pending_events()) == 1
                ref = ToolRef("root", "tool-1")
                digest = hashlib.sha256(b'{"value":1}').hexdigest()
                intent = Intent(ref, RunRef("task-2", "run-2"), "synthetic", '{"value":1}', digest, True, "approval", "policy-v1", owner.owner_epoch, "synthetic-time")
                assert store.commit_intent(owner, intent) is None
                store.commit_result_and_event(owner, ref, "known-result", None, None)
                assert store.commit_intent(owner, intent) == "known-result"
                try:
                    store.commit_intent(owner, replace(intent, args='{"value":2}'))
                except StoreError:
                    pass
                else:
                    raise AssertionError("ToolRef reused a known result after final args changed")
                print(json.dumps({"run_event_rollback": True, "epoch_fenced": True, "tool_identity_checked": True}))
            else:
                # SQLite's own page limit produces SQLITE_FULL without filling any host volume.
                con = store._require_con()
                pages = con.execute("PRAGMA page_count").fetchone()[0]
                assert con.execute(f"PRAGMA max_page_count={pages}").fetchone()[0] == pages
                try:
                    store.commit_checkpoint_ack(owner, 1, replace(cp, messages=({"role": "user", "content": "x" * 1048576},), revision=1), ("event-1",), operation_id="must-not-ack")
                except BaseException as error:
                    chain = []
                    current = error
                    while current is not None:
                        chain.append(getattr(current, "sqlite_errorcode", None))
                        current = current.__cause__
                    assert sqlite3.SQLITE_FULL in chain, chain
                else:
                    raise AssertionError("page-limited commit falsely succeeded")
                restored = store.load_recovery_view()
                assert restored.checkpoint.revision == 1
                assert restored.checkpoint.messages == cp.messages
                assert len(restored.pending_events) == 1
                assert store.lookup_checkpoint_operation(owner, "must-not-ack") is None
                print(json.dumps({"sqlite_full_observed": True, "checkpoint_and_delivery_rollback": True}))
        else:
            raise AssertionError("unknown probe action")
    finally:
        store.close(owner)


if __name__ == "__main__":
    main()
