"""Real Windows product port tests; every child loads the controlled DLL first."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows product storage")

_BOOT = """
import sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import *
from ruocun.session.durable_store import DurableStore, read_durable_state
from ruocun.session.process_identity import RealIdentityProvider, SyntheticIdentityProvider
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
identities = RealIdentityProvider()
identity = identities.current()
def checkpoint():
    return Checkpoint('one', ({'role': 'user', 'content': 'saved'},), 'model',
        'normal', '', 0, (), (), {}, 'idle', 0)

def shell_run(store, owner, task_id, run_id, **extra):
    # Synthetic already-verified manager metadata at the public storage seam.
    # This fixture does not claim that an OS runner or receipt was exercised.
    ref = RunRef(task_id, run_id)
    tool = ToolRef('root', 'shell:' + run_id)
    store.commit_intent(owner, Intent(tool, ref, 'Bash', '{}', 'synthetic:' + run_id,
        True, 'approval', 'policy', owner.owner_epoch, 'synthetic'))
    registered = store.prepare_shell(owner, tool, ref, dict(version=1, control_epoch=1,
        launch_id='synthetic:' + run_id, plan_digest='b' * 64,
        run_dir=str(root / 'synthetic-runs' / run_id), endpoint='synthetic-pipe:' + run_id))
    return replace(registered, status='completed', snapshot={**registered.snapshot,
        'receipt_digest':'a' * 64, 'tool_result':'synthetic completed Shell ' + run_id, **extra})

def execution_snapshot(run):
    return {'taskId':run.run_ref.task_id, 'runId':run.run_ref.run_id,
        'kind':run.kind, 'background':True, 'description':'synthetic storage execution',
        'status':run.status}
"""


def _run(tmp_path: Path, code: str) -> str:
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    source = Path(ruocun.__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _BOOT + code, str(tmp_path), str(archive.resolve()), str(source)],
        capture_output=True, text=True, encoding="utf-8", timeout=45,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_open_store_pins_directory_until_sqlite_is_closed(tmp_path: Path) -> None:
    _run(tmp_path, """
directory = root / 'session'
store = DurableStore(directory, 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
try:
    try:
        directory.rename(root / 'retired')
    except PermissionError:
        pass
    else:
        raise AssertionError('open database allowed its namespace to be replaced')
    store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
finally:
    store.close(owner)
directory.rename(root / 'retired')
assert not list((root / 'retired').glob('.ruocun-guard-*'))
""")


def test_sqlite_open_cannot_follow_a_directory_swapped_after_validation(tmp_path: Path) -> None:
    _run(tmp_path, r"""
import os, sqlite3, subprocess
from ruocun.platform.windows.durable_file import ensure_private_dir
directory, alternate, retired = (root / x for x in ('session', 'alternate', 'retired'))
ensure_private_dir(alternate)
connect = sqlite3.connect
redirected = False
def raced_connect(path, *args, **kwargs):
    global redirected
    if Path(path) == directory / 'session.db':
        try: directory.rename(retired)
        except PermissionError: pass
        else:
            result = subprocess.run([r'C:\Windows\System32\cmd.exe', '/c', 'mklink', '/J',
                str(directory), str(alternate)], capture_output=True, timeout=10)
            assert result.returncode == 0
            redirected = True
    return connect(path, *args, **kwargs)
sqlite3.connect = raced_connect
store = DurableStore(directory, 'one', root, runtime)
try:
    owner, _ = store.open_or_claim(identity)
    store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
    store.close(owner)
    assert not (alternate / 'session.db').exists(), 'SQLite followed replacement junction'
finally:
    if redirected: os.rmdir(directory)
""")


def test_tool_identity_conflict_never_reuses_another_operations_result(tmp_path: Path) -> None:
    _run(tmp_path, """
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
intent = Intent(ToolRef('root', 'call'), RunRef('task', 'run'), 'Write',
    '{"value":1}', 'digest-one', True, 'approval', 'policy', owner.owner_epoch, 'synthetic')
try:
    store.commit_intent(owner, intent)
    store.commit_result_and_event(owner, intent.tool_ref, 'result-one', None, None)
    assert store.commit_intent(owner, intent) == 'result-one'
    try:
        store.commit_intent(owner, replace(intent, args='{"value":2}', args_digest='digest-two'))
    except StoreError: pass
    else: raise AssertionError('same call ID reused result for changed final arguments')
finally: store.close(owner)
""")


def test_existing_database_hardlink_is_rejected_before_writing(tmp_path: Path) -> None:
    _run(tmp_path, """
import os
from ruocun.platform.file_contract import AtomicFileError
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
store.close(owner)
database = root / 'session/session.db'
alias = root / 'external-alias.db'
os.link(database, alias)
before = alias.read_bytes()
candidate = DurableStore(root / 'session', 'one', root, runtime)
try:
    candidate.open_or_claim(identity)
except AtomicFileError: pass
else: raise AssertionError('database with external hardlink was accepted')
assert alias.read_bytes() == before
""")


def test_real_dead_owner_can_be_recovered_without_losing_checkpoint(tmp_path: Path) -> None:
    _run(tmp_path, """
import json, subprocess, os
child_code = '''
import sys, os, json
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import Checkpoint
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
ids = RealIdentityProvider()
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(ids.current())
store.commit_checkpoint_ack(owner, 0, Checkpoint('one', ({'role':'user','content':'survives crash'},),
    'model', 'normal', '', 0, (), (), {}, 'idle', 0), ())
print(owner.owner_epoch, flush=True)
sys.stdin.read()
os._exit(0)
'''
child = subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-c', child_code,
    str(root), sys.argv[2], sys.argv[3]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
try:
    assert child.stdout.readline().strip() == '1'
    contender = DurableStore(root / 'session', 'one', root, runtime)
    try: contender.open_or_claim(identity)
    except OwnerConflictError: pass
    else: raise AssertionError('live owner displaced')
    child.communicate(timeout=15)
    assert child.returncode == 0
    # Keep child (and its Windows handle) alive as a Python object here.
    recovered = DurableStore(root / 'session', 'one', root, runtime)
    owner, view = recovered.open_or_claim(identity)
    assert owner.owner_epoch == 2
    assert view.checkpoint.messages == ({'role':'user','content':'survives crash'},)
    assert view.checkpoint.revision == 1
    recovered.close(owner)
finally:
    if child.poll() is None: child.communicate(timeout=15)
""")


def test_stale_writer_cannot_write_or_clear_new_owner(tmp_path: Path) -> None:
    _run(tmp_path, """
ids = SyntheticIdentityProvider(identity)
first = DurableStore(root / 'session', 'one', root, runtime, ids)
old, _ = first.open_or_claim(identity)
first.commit_checkpoint_ack(old, 0, checkpoint(), ())
second = DurableStore(root / 'session', 'one', root, runtime, ids)
new, _ = second.open_or_claim(identity)
assert new.owner_epoch == old.owner_epoch + 1
try:
    try: first.commit_checkpoint_ack(old, 1, checkpoint(), ())
    except OwnerFencedError: pass
    else: raise AssertionError('stale writer committed')
    try: first.close(old)
    except OwnerFencedError: pass
    else: raise AssertionError('stale close cleared new ownership')
    assert second.commit_checkpoint_ack(new, 1, checkpoint(), ()) == 2
finally: second.close(new)
""")


@pytest.mark.parametrize("kind", ["future", "dao", "nonempty-zero", "wrong-product", "missing-checkpoint", "corrupt", "missing-table", "invalid-checkpoint", "invalid-json"])
def test_bad_database_is_rejected_without_empty_fallback(tmp_path: Path, kind: str) -> None:
    _run(tmp_path, """
import sqlite3, hashlib
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
store.close(owner)
database = root / 'session/session.db'
kind = """ + repr(kind) + """
if kind == 'corrupt': database.write_bytes(b'not a SQLite database')
else:
    con = sqlite3.connect(database, isolation_level=None)
    if kind == 'future': con.execute('PRAGMA user_version=99')
    elif kind == 'dao': con.execute('PRAGMA user_version=2')
    elif kind == 'nonempty-zero': con.execute('PRAGMA user_version=0')
    elif kind == 'wrong-product': con.execute('UPDATE meta SET json=? WHERE key=?', ('{"product":"dao"}', 'identity'))
    elif kind == 'missing-checkpoint': con.execute('DELETE FROM meta WHERE key=?', ('checkpoint',))
    elif kind == 'missing-table': con.execute('DROP TABLE tools')
    elif kind == 'invalid-checkpoint': con.execute('UPDATE meta SET json=? WHERE key=?', ('{}', 'checkpoint'))
    else: con.execute('UPDATE meta SET json=? WHERE key=?', ('{bad json', 'identity'))
    con.close()
before = hashlib.sha256(database.read_bytes()).hexdigest()
candidate = DurableStore(root / 'session', 'one', root, runtime)
for action in [lambda: candidate.open_or_claim(identity), lambda: read_durable_state(root / 'session', runtime)]:
    try: action()
    except StoreError: pass
    else: raise AssertionError('invalid state silently became an empty session')
assert hashlib.sha256(database.read_bytes()).hexdigest() == before
(root / 'session').rename(root / 'rejected-no-handles')
""")


def test_failed_schema_initialization_can_be_retried_without_partial_state(tmp_path: Path) -> None:
    _run(tmp_path, """
import sqlite3
connect = sqlite3.connect
class FaultConnection(sqlite3.Connection):
    def execute(self, sql, *args, **kwargs):
        if sql == 'PRAGMA user_version=1':
            raise sqlite3.OperationalError('synthetic initialization disk failure')
        return super().execute(sql, *args, **kwargs)
def failed_connect(*args, **kwargs):
    return connect(*args, factory=FaultConnection, **kwargs)
sqlite3.connect = failed_connect
failed = DurableStore(root / 'session', 'one', root, runtime)
try: failed.open_or_claim(identity)
except CorruptDatabaseError: pass
else: raise AssertionError('initialization failure was swallowed')
sqlite3.connect = connect
retry = DurableStore(root / 'session', 'one', root, runtime)
owner, view = retry.open_or_claim(identity)
assert owner.owner_epoch == 1 and view.checkpoint is None
retry.commit_checkpoint_ack(owner, 0, checkpoint(), ())
retry.close(owner)
""")


def test_checkpoint_delivery_and_run_event_failures_rollback_atomically(tmp_path: Path) -> None:
    _run(tmp_path, """
import sqlite3
connect = sqlite3.connect
fail_checkpoint = False
class FaultConnection(sqlite3.Connection):
    def execute(self, sql, *args, **kwargs):
        if fail_checkpoint and sql.startswith('INSERT INTO checkpoint_operations'):
            raise sqlite3.OperationalError('synthetic checkpoint disk failure')
        return super().execute(sql, *args, **kwargs)
sqlite3.connect = lambda *a, **k: connect(*a, factory=FaultConnection, **k)
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
try:
    assert store.config == {'journal_mode':'wal','synchronous':2,'busy_timeout':3000,'foreign_keys':1}
    store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
    run = shell_run(store, owner, 'task', 'run', result='one')
    event = OutboxEvent('event-1', 'one', run.run_ref, 'completed', {'result':'one', 'execution':execution_snapshot(run)}, owner.owner_epoch)
    saved = store.commit_run_event(owner, run, event)
    assert saved.seq == 1
    try: store.commit_run_event(owner, replace(run, snapshot={**run.snapshot, 'result':'conflict'}),
        replace(event, snapshot={'result':'conflict', 'execution':execution_snapshot(run)}))
    except StoreError: pass
    else: raise AssertionError('event content conflict overwritten')
    assert store.load_recovery_view().runs == (run,)
    fail_checkpoint = True
    try: store.commit_checkpoint_ack(owner, 1, replace(checkpoint(), background_state='waiting'), ('event-1',))
    except sqlite3.OperationalError: pass
    else: raise AssertionError('checkpoint fault swallowed')
    view = store.load_recovery_view()
    assert view.checkpoint.revision == 1 and view.checkpoint.background_state == 'idle'
    assert len(view.pending_events) == 1 and view.pending_events[0].delivered_revision is None
    fail_checkpoint = False
    assert store.commit_checkpoint_ack(owner, 1, replace(checkpoint(), background_state='waiting'), ('event-1',)) == 2
    assert store.read_pending_events() == ()
finally: store.close(owner)
assert read_durable_state(root / 'session', runtime)['revision'] == 2
""")


def test_real_worker_lost_commit_ack_poison_blocks_later_write_and_allows_receipt(tmp_path: Path) -> None:
    _run(tmp_path, """
import asyncio, sqlite3
from ruocun.session.storage_worker import StorageWorker
from ruocun.session.sqlite_port import CommitUnconfirmedError
connect = sqlite3.connect
lose_next_ack = False
class LostAcknowledgement(sqlite3.Connection):
    def execute(self, sql, *args, **kwargs):
        global lose_next_ack
        result = super().execute(sql, *args, **kwargs)
        if sql == 'COMMIT' and lose_next_ack:
            lose_next_ack = False
            raise sqlite3.OperationalError('synthetic COMMIT response lost after real disk transaction')
        return result
sqlite3.connect = lambda *a, **k: connect(*a, factory=LostAcknowledgement, **k)
def factory():
    store = DurableStore(root / 'session', 'one', root, runtime)
    owner, _ = store.open_or_claim(identity)
    return store, owner
async def exercise():
    global lose_next_ack
    worker = StorageWorker(factory)
    await worker.load_recovery_view()
    lose_next_ack = True
    accepted = worker.enqueue_checkpoint(0, checkpoint(), (), operation_id='accepted-commit')
    later = worker.enqueue_run_event(RunRecord(RunRef('task','run'), 'shell', 'must-not-write', False, {}), None)
    try: await accepted.wait()
    except CommitUnconfirmedError: pass
    else: raise AssertionError('lost acknowledgement was called committed')
    assert accepted.status().state == 'outcome_unknown'
    try: await later.wait()
    except StoreError: pass
    else: raise AssertionError('write after uncertain commit was accepted')
    receipt = await worker.lookup_checkpoint_operation('accepted-commit', request_digest=accepted.request_digest)
    assert receipt.revision == 1
    view = await worker.load_recovery_view()
    assert view.checkpoint.revision == 1 and view.runs == ()
    await worker.close()
asyncio.run(exercise())
""")


def test_reopened_started_intent_is_unknown_and_blocks_changed_call_id(tmp_path: Path) -> None:
    _run(tmp_path, """
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
intent = Intent(ToolRef('root','old-call'), RunRef('task','run'), 'Write', '{}',
    'digest', True, 'approval', 'policy', owner.owner_epoch, 'synthetic')
store.commit_intent(owner, intent)
store.close(owner)
restored = DurableStore(root / 'session', 'one', root, runtime)
owner, view = restored.open_or_claim(identity)
try:
    assert view.tool_records[0].state == 'outcome_unknown'
    try: restored.commit_intent(owner, replace(intent, tool_ref=ToolRef('root','new-call'), owner_epoch=owner.owner_epoch))
    except UnknownOutcomeBlockedError: pass
    else: raise AssertionError('new call ID replayed an unresolved side effect')
    restored.record_recovery_decision(owner, 'decision', 'root:old-call', 'resolve', 'synthetic verified not executed')
    restored.commit_intent(owner, replace(intent, tool_ref=ToolRef('root','new-call'), owner_epoch=owner.owner_epoch))
finally: restored.close(owner)
""")


def test_readonly_recovery_preserves_database_bytes_and_observes_sidecars(tmp_path: Path) -> None:
    output = _run(tmp_path, r"""
import hashlib, json, os, subprocess
directory = root / 'session'
store = DurableStore(directory, 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
def snapshot():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
        if not p.name.startswith('.ruocun-guard-')}
active_before = snapshot()
view = read_durable_state(directory, runtime)
active_after = snapshot()
assert view['revision'] == 1
assert active_before['session.db'] == active_after['session.db']
assert active_before['session.db-wal'] == active_after['session.db-wal']
assert store.load_recovery_view().owner == owner
store.close(owner)
closed_before = snapshot()
assert set(closed_before) == {'session.db'}
assert read_durable_state(directory, runtime)['messages'] == [{'role':'user','content':'saved'}]
closed_after = snapshot()
assert closed_after['session.db'] == closed_before['session.db']
assert not list(directory.glob('.ruocun-guard-*'))
for name in closed_after:
    acl = subprocess.run([r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        '-NoProfile', '-NonInteractive', '-Command',
        '[Console]::Write((Get-Acl -LiteralPath $env:RUOCUN_TEST_ACL_PATH).Sddl + "`n" + [Security.Principal.WindowsIdentity]::GetCurrent().User.Value)'],
        env={**os.environ, 'RUOCUN_TEST_ACL_PATH':str(directory / name)}, capture_output=True, text=True, timeout=10, check=True)
    sddl, sid = acl.stdout.strip().splitlines()
    assert sddl.count('(A;') == 1 and '(A;ID;FA;;;' + sid + ')' in sddl
report = {'active_changed':[k for k in active_before if active_before[k] != active_after.get(k)],
    'closed_created':sorted(set(closed_after)-set(closed_before))}
# A WAL read may create or update coordination files. It must never change
# the authoritative main DB, WAL frames, checkpoint, owner or epoch.
print(json.dumps(report, sort_keys=True))
""")
    print(output.strip())


def test_owner_identity_query_failure_and_cross_host_do_not_take_over(tmp_path: Path) -> None:
    _run(tmp_path, """
first = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = first.open_or_claim(identity)
first.commit_checkpoint_ack(owner, 0, checkpoint(), ())
denied_ids = SyntheticIdentityProvider(identity, alive_query_error=True)
denied = DurableStore(root / 'session', 'one', root, runtime, denied_ids)
try:
    try: denied.open_or_claim(identity)
    except IdentityQueryError: pass
    else: raise AssertionError('query failure was treated as dead')
    assert first.commit_checkpoint_ack(owner, 1, checkpoint(), ()) == 2
finally: first.close(owner)
foreign = replace(identity, host=identity.host + '-synthetic-other-host')
foreign_store = DurableStore(root / 'foreign', 'one', root, runtime, SyntheticIdentityProvider(foreign))
foreign_owner, _ = foreign_store.open_or_claim(foreign)
foreign_store.commit_checkpoint_ack(foreign_owner, 0, checkpoint(), ())
candidate = DurableStore(root / 'foreign', 'one', root, runtime)
try:
    try: candidate.open_or_claim(identity)
    except CrossHostError: pass
    else: raise AssertionError('cross-host owner was automatically replaced')
    assert foreign_store.commit_checkpoint_ack(foreign_owner, 1, checkpoint(), ()) == 2
finally: foreign_store.close(foreign_owner)
""")


def test_public_worker_factory_serializes_all_real_storage_methods(tmp_path: Path) -> None:
    _run(tmp_path, """
import asyncio
from ruocun.session.storage_worker import StorageWorker
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
old = Intent(ToolRef('root','old'), RunRef('task','old-run'), 'Write', '{}',
    'old-digest', True, 'approval', 'policy', owner.owner_epoch, 'synthetic')
store.commit_intent(owner, old)
store.close(owner)
async def exercise():
    worker = StorageWorker.open(root / 'session', 'one', root, runtime)
    view = await worker.load_recovery_view()
    assert view.tool_records[0].state == 'outcome_unknown'
    await worker.enqueue_recovery_decision('decision', 'root:old', 'resolve', 'synthetic verified').wait()
    owner = view.owner
    intent = replace(old, tool_ref=ToolRef('root','new'), run_ref=RunRef('task','new-run'),
        name='Bash', owner_epoch=owner.owner_epoch)
    await worker.enqueue_intent(intent).wait()
    registered = await worker.enqueue_prepare_shell(intent.tool_ref, intent.run_ref, dict(version=1,
        control_epoch=1, launch_id='synthetic-worker-launch', plan_digest='b' * 64,
        run_dir=str(root / 'synthetic-worker-run'), endpoint='synthetic-worker-pipe')).wait()
    run = replace(registered, status='running')
    await worker.enqueue_run_event(run, None).wait()
    completed = replace(run, status='completed', snapshot={**run.snapshot, 'receipt_digest':'a' * 64})
    event = OutboxEvent('event-new', 'one', run.run_ref, 'completed',
        {'result':'done', 'execution':execution_snapshot(completed)}, owner.owner_epoch)
    await worker.enqueue_result_and_event(intent.tool_ref, 'done', completed, event).wait()
    pending = await worker.read_pending_events()
    assert len(pending) == 1 and pending[0].seq == 1
    saved = worker.enqueue_checkpoint(1, checkpoint(), ('event-new',), operation_id='all-methods')
    assert await saved.wait() == 2
    assert (await worker.lookup_checkpoint_operation('all-methods')).revision == 2
    final = await worker.load_recovery_view()
    assert final.runs[0].status == 'completed' and final.pending_events == ()
    assert next(record for record in final.tool_records if record.tool_ref.tool_call_id == 'new').result == 'done'
    await worker.close()
    try: worker.enqueue_checkpoint(2, checkpoint(), ())
    except StoreError: pass
    else: raise AssertionError('closed worker accepted write')
asyncio.run(exercise())
assert read_durable_state(root / 'session', runtime)['revision'] == 2
""")


def test_reopened_events_deduplicate_and_acknowledge_only_consumed_event(tmp_path: Path) -> None:
    _run(tmp_path, """
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
run = shell_run(store, owner, 'task-1', 'run-1', value='one')
event = OutboxEvent('event-1', 'one', run.run_ref, 'completed', {'value':'one', 'execution':execution_snapshot(run)}, owner.owner_epoch)
first = store.commit_run_event(owner, run, event)
other_run = shell_run(store, owner, 'task-2', 'run-2', value='one')
store.commit_run_event(owner, other_run, replace(event, event_id='event-2', run_ref=other_run.run_ref,
    snapshot={'value':'one', 'execution':execution_snapshot(other_run)}))
store.close(owner)
restored = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = restored.open_or_claim(identity)
try:
    duplicate = restored.commit_run_event(owner, run, event)
    assert duplicate.seq == first.seq == 1
    assert [item.event_id for item in restored.read_pending_events()] == ['event-1','event-2']
    assert restored.commit_checkpoint_ack(owner, 1, checkpoint(), ('event-1',)) == 2
    assert [item.event_id for item in restored.read_pending_events()] == ['event-2']
finally: restored.close(owner)
(root / 'session/state.json').write_text('{"revision":999,"messages":[]}', encoding='utf-8')
(root / 'session/events.jsonl').write_text('not a database', encoding='utf-8')
authoritative = read_durable_state(root / 'session', runtime)
assert authoritative['revision'] == 2
assert authoritative['messages'] == [{'role':'user','content':'saved'}]
""")


def test_recovery_view_is_one_sqlite_snapshot_during_concurrent_commit(tmp_path: Path) -> None:
    _run(tmp_path, """
import json, sqlite3
from dataclasses import asdict
connect = sqlite3.connect
armed = False
writer = None
class Cursor:
    def __init__(self, cursor): self.cursor = cursor
    def fetchone(self):
        global armed
        row = self.cursor.fetchone()
        armed = False
        writer.execute('BEGIN IMMEDIATE')
        writer.execute('UPDATE meta SET json=? WHERE key=?',
            (json.dumps(asdict(replace(checkpoint(), revision=2, delivered_revision=2))), 'checkpoint'))
        writer.execute('UPDATE meta SET json=? WHERE key=?', ('2','revision'))
        writer.execute('UPDATE runs SET json=? WHERE id=?',
            (json.dumps(asdict(replace(run, status='after'))), 'run'))
        writer.execute('COMMIT')
        return row
class ConcurrentConnection(sqlite3.Connection):
    def execute(self, sql, *args, **kwargs):
        cursor = super().execute(sql, *args, **kwargs)
        if armed and sql == 'SELECT json FROM meta WHERE key=?' and args[0] == ('checkpoint',):
            return Cursor(cursor)
        return cursor
sqlite3.connect = lambda *a, **k: connect(*a, factory=ConcurrentConnection, **k)
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
store.commit_checkpoint_ack(owner, 0, checkpoint(), ())
run = RunRecord(RunRef('task','run'), 'shell', 'before', False, {})
store.commit_run_event(owner, run, None)
writer = connect(root / 'session/session.db', isolation_level=None)
try:
    armed = True
    view = store.load_recovery_view()
    assert view.checkpoint.revision == 1 and view.runs[0].status == 'before', 'mixed SQLite snapshots'
    next_view = store.load_recovery_view()
    assert next_view.checkpoint.revision == 2 and next_view.runs[0].status == 'after'
finally:
    writer.close()
    store.close(owner)
""")


@pytest.mark.parametrize("mismatch", ["result-run", "result-event-ref", "result-session", "run-event-ref", "run-session"])
def test_conflicting_result_run_and_event_associations_are_rejected_atomically(
    tmp_path: Path, mismatch: str,
) -> None:
    _run(tmp_path, """
store = DurableStore(root / 'session', 'one', root, runtime)
owner, _ = store.open_or_claim(identity)
intent = Intent(ToolRef('root','call'), RunRef('task','run'), 'Write', '{}',
    'digest', True, 'approval', 'policy', owner.owner_epoch, 'synthetic')
store.commit_intent(owner, intent)
run = RunRecord(intent.run_ref, 'shell', 'completed', False, {})
event = OutboxEvent('event', 'one', intent.run_ref, 'completed', {}, owner.owner_epoch)
mismatch = """ + repr(mismatch) + """
if mismatch == 'result-run': run = replace(run, run_ref=RunRef('other-task','other-run'))
elif mismatch.endswith('event-ref'): event = replace(event, run_ref=RunRef('other-task','other-run'))
else: event = replace(event, session_id='another-session')
try:
    try:
        if mismatch.startswith('result'):
            store.commit_result_and_event(owner, intent.tool_ref, 'result', run, event)
        else: store.commit_run_event(owner, run, event)
    except StoreError: pass
    else: raise AssertionError('conflicting result/run/event association was committed')
    view = store.load_recovery_view()
    assert view.tool_records[0].state == 'started' and view.runs == () and view.pending_events == ()
finally: store.close(owner)
""")
