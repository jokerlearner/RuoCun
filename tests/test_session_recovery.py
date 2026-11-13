"""Product storage's real-process commit and restart path (REC-01/03)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_committed_message_survives_process_restart(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    worker = """
import json, sys
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import Checkpoint
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
identity = RealIdentityProvider()
store = DurableStore(root / 'session', 'session-1', root, runtime, identity)
owner, view = store.open_or_claim(identity.current())
if sys.argv[3] == 'save':
    cp = Checkpoint('session-1', ({'role': 'user', 'content': 'hello'},), 'model',
        'normal', '', 0, (), (), {}, 'idle', 0)
    assert store.commit_checkpoint_ack(owner, 0, cp, ()) == 1
else:
    assert view.checkpoint is not None
    print(json.dumps({'messages': view.checkpoint.messages, 'revision': view.checkpoint.revision}))
store.close(owner)
"""
    outputs = []
    for action in ("save", "load"):
        result = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-c", worker, str(tmp_path), str(archive), action],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout)
    assert json.loads(outputs[-1]) == {
        "messages": [{"role": "user", "content": "hello"}],
        "revision": 1,
    }


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_live_owner_cannot_be_taken_over_by_another_process(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = """
import sys
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import Checkpoint, OwnerConflictError
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
root = Path(sys.argv[1]); archive = Path(sys.argv[2])
runtime = verify_controlled_runtime(verify_official_archive(archive, root / 'dll'))
identity = RealIdentityProvider()
store = DurableStore(root / 'session', 'one', root, runtime, identity)
if sys.argv[3] == 'owner':
    owner, _ = store.open_or_claim(identity.current())
    cp = Checkpoint('one', (), 'model', 'normal', '', 0, (), (), {}, 'idle', 0)
    store.commit_checkpoint_ack(owner, 0, cp, ())
    print('READY', flush=True)
    sys.stdin.read()
    store.close(owner)
else:
    try:
        store.open_or_claim(identity.current())
    except OwnerConflictError:
        print('CONFLICT')
    else:
        raise AssertionError('live owner was displaced')
"""
    argv = [sys.executable, "-I", "-X", "utf8", "-c", code, str(tmp_path), str(archive)]
    owner = subprocess.Popen(
        [*argv, "owner"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    try:
        assert owner.stdout is not None
        assert owner.stdout.readline().strip() == "READY"
        contender = subprocess.run(
            [*argv, "contender"], capture_output=True, text=True, timeout=30,
        )
        assert contender.returncode == 0, contender.stderr
        assert contender.stdout.strip() == "CONFLICT"
    finally:
        owner.communicate(timeout=30)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_checkpoint_operation_is_idempotent_and_survives_restart(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = """
import sys
from dataclasses import replace
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import Checkpoint, StoreError
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
root = Path(sys.argv[1]); archive = Path(sys.argv[2])
runtime = verify_controlled_runtime(verify_official_archive(archive, root / 'dll'))
identity = RealIdentityProvider()
store = DurableStore(root / 'session', 'one', root, runtime, identity)
owner, _ = store.open_or_claim(identity.current())
cp = Checkpoint('one', ({'role': 'user', 'content': 'one'},), 'model',
    'normal', '', 0, (), (), {}, 'idle', 0)
if sys.argv[3] == 'save':
    assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id='request-1') == 1
    assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id='request-1') == 1
    try:
        store.commit_checkpoint_ack(owner, 0, replace(cp, title='different'), (), operation_id='request-1')
    except StoreError:
        pass
    else:
        raise AssertionError('same operation ID accepted different content')
else:
    operation = store.lookup_checkpoint_operation(owner, 'request-1')
    assert operation is not None and operation.revision == 1
    assert store.commit_checkpoint_ack(owner, 0, cp, (), operation_id='request-1') == 1
store.close(owner)
"""
    for action in ("save", "lookup"):
        result = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-c", code, str(tmp_path), str(archive), action],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_cancelling_wait_does_not_cancel_accepted_checkpoint(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = """
import asyncio, threading, sys
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import Checkpoint
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
from ruocun.session.storage_worker import StorageWorker
root = Path(sys.argv[1]); archive = Path(sys.argv[2])
runtime = verify_controlled_runtime(verify_official_archive(archive, root / 'dll'))
ready = threading.Event()
def factory():
    if not ready.wait(10): raise RuntimeError('synthetic timeout')
    identity = RealIdentityProvider()
    store = DurableStore(root / 'session', 'one', root, runtime, identity)
    owner, _ = store.open_or_claim(identity.current())
    return store, owner
async def main():
    worker = StorageWorker(factory)
    cp = Checkpoint('one', ({'role': 'user', 'content': 'original'},), 'model', 'normal', '', 0, (), (), {}, 'idle', 0)
    handle = worker.enqueue_checkpoint(0, cp, (), operation_id='accepted-1')
    cp.messages[0]['content'] = 'modified after acceptance'
    waiter = asyncio.create_task(handle.wait())
    await asyncio.sleep(0)
    waiter.cancel()
    try: await waiter
    except asyncio.CancelledError: pass
    else: raise AssertionError('wait should be cancelled')
    assert handle.status().state == 'pending'
    ready.set()
    assert await handle.wait() == 1
    assert handle.status().state == 'committed'
    result = await worker.lookup_checkpoint_operation('accepted-1')
    assert result is not None and result.revision == 1
    assert result.request_digest == handle.request_digest
    await worker.close()
asyncio.run(main())
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(tmp_path), str(archive)],
        capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr
