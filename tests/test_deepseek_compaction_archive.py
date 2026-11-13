"""B archive contract through the real StorageWorker and controlled SQLite."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="controlled Windows SQLite")

_SETUP = r'''
import asyncio, sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.contract import Checkpoint, StoreError
from ruocun.session.storage_worker import StorageWorker
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root/'dll'))
def opened(name='one'):
    return StorageWorker.open(root/name, name, root, runtime)
def checkpoint(messages, name='one'):
    return Checkpoint(name, tuple(messages), 'synthetic', 'normal', '', 0, (), (), {}, 'idle', 0)
'''


def _run(tmp_path, scenario):
    package = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    allowed = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "HOME", "USERPROFILE",
               "APPDATA", "LOCALAPPDATA", "ProgramData", "TEMP", "TMP")
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8", "-c", _SETUP + scenario,
         str(tmp_path), str(archive.resolve()), str(package)],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8", timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_saved_transcript_keeps_repeated_messages_and_metadata_versions_after_restart(tmp_path):
    _run(tmp_path, r'''
async def scenario():
    worker = opened()
    messages = [{'role':'system','content':'SYS'}, {'role':'user','content':'repeat'},
                {'role':'user','content':'repeat'}, {'role':'assistant','content':'answer'}]
    await worker.enqueue_checkpoint(0, checkpoint(messages), ()).wait()
    messages[-1]['reasoning_content'] = 'saved protocol metadata'
    await worker.enqueue_checkpoint(1, checkpoint(messages), ()).wait()
    await worker.close()
    worker = opened()
    try:
        page = await worker.archive_export()
        assert [m['content'] for m in page['messages']] == ['SYS','repeat','repeat','answer']
        assert page['messages'][-1]['reasoning_content'] == 'saved protocol metadata'
        assert len(page['records']) == 5
        listing = await worker.archive_list(limit=2)
        assert len(listing['items']) == 2 and listing['next_offset'] == 2
        identity = listing['items'][1]['id']
        text = await worker.archive_read(identity, limit=3)
        assert text['total'] > 3 and text['next_offset'] == 3
        try:
            await worker.archive_read(identity, scope='other')
        except StoreError:
            pass
        else:
            raise AssertionError('cross-scope read accepted')
    finally:
        await worker.close()
asyncio.run(scenario())
''')


def test_rewrite_preserves_sources_boundaries_and_branch_closure(tmp_path):
    _run(tmp_path, r'''
from ruocun.session.contract import ArchiveDerivation, ArchiveRewrite
async def scenario():
    worker = opened()
    original = [{'role':'system','content':'SYS'},
                {'role':'system','content':'[[ruocun:session-start-hook]]\nSAVED HOOK'},
                {'role':'user','content':'early'},
                {'role':'assistant','content':'old answer'}, {'role':'user','content':'recent'}]
    await worker.enqueue_checkpoint(0, checkpoint(original), ()).wait()
    expected = original + [{'role':'assistant','content':'latest'}]
    compacted = [*original[:2], {'role':'system','content':'summary archive:d-one'}, *expected[4:]]
    rewrite = ArchiveRewrite('compact', tuple(expected), (0,1,None,4,5),
                            (ArchiveDerivation('d-one','summary',2,(0,1,2,3),'pressure'),))
    await worker.enqueue_checkpoint(1, checkpoint(compacted), (), operation_id='compact-one', archive_rewrite=rewrite).wait()
    await worker.enqueue_checkpoint(1, checkpoint(compacted), (), operation_id='compact-one', archive_rewrite=rewrite).wait()
    assert (await worker.archive_export())['messages'] == expected
    exported = await worker.archive_export(versions=True)
    assert exported['derived'][0]['message']['content'] == 'summary archive:d-one'
    assert len(exported['derived'][0]['sources']) == 4
    projection = await worker.archive_projection()
    assert projection['lineage'][2] == 'd-one'
    original_page = await worker.archive_read('d-one')
    assert 'early' in original_page['text'] and 'old answer' in original_page['text']
    import json
    offset, fragments = 0, []
    while offset is not None:
        part = await worker.archive_read('d-one',offset=offset,limit=7)
        assert len(part['text']) <= 7
        fragments.append(part['text'])
        offset = part['next_offset']
    assert json.loads(''.join(fragments)) == original[:4]
    imported = await worker.archive_branch()
    branch = opened('branch')
    await branch.enqueue_checkpoint(0, checkpoint(compacted,'branch'), (), archive_import=imported).wait()
    await branch.close()
    await worker.enqueue_checkpoint(2, checkpoint([original[0]]), (),
        archive_rewrite=ArchiveRewrite('clear',tuple(compacted),(0,),reason='user clear')).wait()
    await worker.enqueue_checkpoint(3, checkpoint([original[0],original[2]]), ()).wait()
    export = await worker.archive_export()
    assert export['messages'] == [*expected, original[2]]
    assert export['boundaries'][0]['boundary'] == 'clear'
    try:
        await worker.enqueue_checkpoint(4, checkpoint([original[0],{'role':'user','content':'changed history'}]), ()).wait()
    except StoreError:
        pass
    else:
        raise AssertionError('implicit history rewrite accepted')
    await worker.close()
    branch = opened('branch')
    try:
        assert (await branch.archive_export())['messages'] == expected
        assert json.loads((await branch.archive_read('d-one'))['text']) == original[:4]
    finally:
        await branch.close()
asyncio.run(scenario())
''')


def test_child_archive_save_has_persistent_operation_receipt_and_scope_isolation(tmp_path):
    _run(tmp_path, r'''
from ruocun.session.contract import ArchiveDerivation, ArchiveRewrite, RunRecord, RunRef
async def scenario():
    worker = opened()
    await worker.enqueue_checkpoint(0, checkpoint([{'role':'system','content':'parent'}]), ()).wait()
    messages = [{'role':'system','content':'child'}, {'role':'user','content':'child task'},
                {'role':'assistant','content':'child result'}]
    run = RunRecord(RunRef('task','child-run'),'agent','running',False,{'messages':messages})
    handle = worker.enqueue_run_event(run,None,operation_id='child-save')
    await handle.wait()
    assert await worker.archive_scopes() == ['main','child-run']
    assert handle.request_digest
    receipt = await worker.lookup_archive_operation('child-save',request_digest=handle.request_digest)
    assert receipt is not None and receipt.scope == 'child-run'
    await worker.close()
    worker = opened()
    try:
        receipt = await worker.lookup_archive_operation('child-save',request_digest=handle.request_digest)
        assert receipt is not None and receipt.revision == 1
        await worker.enqueue_run_event(run,None,operation_id='child-save').wait()
        assert [m['content'] for m in (await worker.archive_export('child-run'))['messages']] == ['child','child task','child result']
        assert [m['content'] for m in (await worker.archive_export())['messages']] == ['parent']
        changed = replace(run,snapshot={'messages':messages+[{'role':'assistant','content':'different'}]})
        try:
            await worker.enqueue_run_event(changed,None,operation_id='child-save').wait()
        except StoreError:
            pass
        else:
            raise AssertionError('same child operation accepted different payload')
    finally:
        await worker.close()
asyncio.run(scenario())
''')


def test_explicit_offline_upgrade_keeps_backup_and_legacy_coverage_gap(tmp_path):
    _run(tmp_path, r'''
import hashlib, json
from ruocun.session.sqlite_port import connect_database
from ruocun.session.upgrade import upgrade_session
from ruocun.session.contract import VersionRejectError
async def scenario():
    worker = opened()
    messages = [{'role':'system','content':'SYS'}, {'role':'system','content':'[早期对话摘要] missing originals'},
                {'role':'user','content':'still available'}]
    await worker.enqueue_checkpoint(0,checkpoint(messages),()).wait()
    await worker.close()
    # Seed a known old-format fixture, not an observation channel for assertions.
    con = connect_database(root/'one'/'session.db')
    old_identity = json.loads(con.execute("SELECT json FROM meta WHERE key='identity'").fetchone()[0])
    old_identity['storage_version'] = 1
    con.execute("UPDATE meta SET json=? WHERE key='identity'",(json.dumps(old_identity),))
    con.execute("DELETE FROM meta WHERE key LIKE 'archive:%'")
    con.close()
    rejected = opened()
    try:
        await rejected.load_recovery_view()
    except VersionRejectError:
        pass
    else:
        raise AssertionError('old session silently upgraded')
    try:
        await rejected.close()
    except VersionRejectError:
        pass
    report = upgrade_session(root/'one',runtime,expected_session_id='one',cwd=root)
    backup = Path(report['backup_path'])
    assert backup.is_file() and hashlib.sha256(backup.read_bytes()).hexdigest() == report['backup_sha256']
    assert report['storage_version'] == 3
    assert Path(report['attachment_manifest']).is_file()
    worker = opened()
    try:
        view = await worker.load_recovery_view()
        assert list(view.checkpoint.messages) == messages and view.checkpoint.revision == 1
        exported = await worker.archive_export()
        assert exported['legacy_gap'] and exported['messages'] == messages
    finally:
        await worker.close()
asyncio.run(scenario())
''')


def test_archive_and_checkpoint_rollback_together_and_unknown_receipt_reconciles(tmp_path):
    _run(tmp_path, r'''
import ruocun.session.durable_store as durable
from ruocun.session.contract import ArchiveDerivation, ArchiveRewrite
from ruocun.session.sqlite_port import CommitUnconfirmedError
async def scenario():
    worker = opened()
    original = [{'role':'system','content':'SYS'}, {'role':'user','content':'saved original'}]
    await worker.enqueue_checkpoint(0,checkpoint(original),()).wait()
    expected = original + [{'role':'assistant','content':'not saved until compaction'}]
    changed = [original[0],{'role':'system','content':'summary'}]
    rewrite = ArchiveRewrite('compact',tuple(expected),(0,None),(ArchiveDerivation('atomic-d','summary',1,(1,2)),))
    saved_put = durable._put_meta
    def rejected_checkpoint(con,key,value):
        if key == 'checkpoint':
            raise StoreError('synthetic confirmed rollback')
        return saved_put(con,key,value)
    durable._put_meta = rejected_checkpoint
    try:
        try:
            await worker.enqueue_checkpoint(1,checkpoint(changed),(),operation_id='atomic',archive_rewrite=rewrite).wait()
        except StoreError:
            pass
        else:
            raise AssertionError('confirmed failure hidden')
    finally:
        durable._put_meta = saved_put
    assert (await worker.archive_export())['messages'] == original
    assert list((await worker.load_recovery_view()).checkpoint.messages) == original
    assert await worker.lookup_checkpoint_operation('atomic') is None
    saved_atomic = durable.DurableStore._atomic
    def lose_ack(self,owner,body):
        answer = saved_atomic(self,owner,body)
        if type(answer) is int:
            raise CommitUnconfirmedError('synthetic committed archive ack lost')
        return answer
    durable.DurableStore._atomic = lose_ack
    try:
        handle = worker.enqueue_checkpoint(1,checkpoint(changed),(),operation_id='atomic',archive_rewrite=rewrite)
        try:
            await handle.wait()
        except CommitUnconfirmedError:
            pass
        else:
            raise AssertionError('unknown confirmation hidden')
        assert handle.status().state == 'outcome_unknown'
        assert (await worker.lookup_checkpoint_operation('atomic',request_digest=handle.request_digest)).revision == 2
    finally:
        durable.DurableStore._atomic = saved_atomic
        await worker.close()
    worker = opened()
    try:
        await worker.enqueue_checkpoint(1,checkpoint(changed),(),operation_id='atomic',archive_rewrite=rewrite).wait()
        assert (await worker.archive_export())['messages'] == expected
        assert len([item for item in (await worker.archive_list())['items'] if item['kind']=='summary']) == 1
    finally:
        await worker.close()
asyncio.run(scenario())
''')


def test_cancelling_archive_wait_keeps_accepted_material_and_commits_once(tmp_path):
    _run(tmp_path, r'''
import threading
from ruocun.session.durable_store import DurableStore
from ruocun.session.process_identity import RealIdentityProvider
async def scenario():
    ready = threading.Event()
    def factory():
        assert ready.wait(10)
        ids = RealIdentityProvider()
        store = DurableStore(root/'one','one',root,runtime,ids)
        owner,_ = store.open_or_claim(ids.current())
        return store,owner
    worker = StorageWorker(factory)
    material = [{'role':'user','content':'accepted original'}]
    handle = worker.enqueue_checkpoint(0,checkpoint(material),(),operation_id='cancel-archive')
    material[0]['content'] = 'mutated caller memory'
    waiter = asyncio.create_task(handle.wait())
    await asyncio.sleep(0)
    waiter.cancel()
    try:
        await waiter
    except asyncio.CancelledError:
        pass
    else:
        raise AssertionError('wait was not cancelled')
    ready.set()
    assert await handle.wait() == 1
    assert (await worker.archive_export())['messages'] == [{'role':'user','content':'accepted original'}]
    await worker.close()
asyncio.run(scenario())
''')


def test_upgrade_failure_rolls_back_and_retains_backup_for_explicit_retry(tmp_path):
    _run(tmp_path, r'''
import json
import ruocun.session.upgrade as upgrade
from ruocun.session.sqlite_port import connect_database
async def scenario():
    worker = opened()
    messages = [{'role':'user','content':'old surviving material'}]
    await worker.enqueue_checkpoint(0,checkpoint(messages),()).wait()
    await worker.close()
    con = connect_database(root/'one'/'session.db')
    identity = json.loads(con.execute("SELECT json FROM meta WHERE key='identity'").fetchone()[0])
    identity['storage_version'] = 1
    con.execute("UPDATE meta SET json=? WHERE key='identity'",(json.dumps(identity),))
    con.execute("DELETE FROM meta WHERE key LIKE 'archive:%'")
    con.close()
    original = upgrade._put_meta
    def fail_after_archive(con,key,value):
        if key == 'identity':
            raise StoreError('synthetic upgrade rollback')
        return original(con,key,value)
    upgrade._put_meta = fail_after_archive
    try:
        try:
            upgrade.upgrade_session(root/'one',runtime)
        except StoreError as error:
            assert 'synthetic upgrade rollback' in str(error)
        else:
            raise AssertionError('failed upgrade was hidden')
    finally:
        upgrade._put_meta = original
    assert len(list(root.glob('one-upgrade-backup-*/session.db'))) == 1
    report = upgrade.upgrade_session(root/'one',runtime)
    assert Path(report['backup_path']).is_file()
    worker = opened()
    try:
        assert (await worker.archive_export())['messages'] == messages
        assert len((await worker.archive_list())['items']) == 1
    finally:
        await worker.close()
asyncio.run(scenario())
''')


def test_cleanup_preserves_archived_spill_and_branch_owns_material_after_source_retirement(tmp_path):
    _run(tmp_path, r'''
import hashlib, os, time
from ruocun.agent.cleanup import cleanup
from ruocun.session.contract import ArchiveDerivation, ArchiveRewrite
from ruocun.tools.spill import spillOutput
async def scenario():
    sessions = root/'sessions'
    sessions.mkdir()
    worker = StorageWorker.open(sessions/'source','source',root,runtime)
    rendered = spillOutput('saved full output '*5000,str(root),40)
    spill = next((root/'.ruocun/spill').glob('*.txt'))
    os.utime(spill,(1,1))
    originals = [{'role':'system','content':'SYS'},
        {'role':'assistant','content':None,'tool_calls':[{'id':'read','type':'function','function':{'name':'Read','arguments':'{}'}}]},
        {'role':'tool','tool_call_id':'read','content':rendered}]
    await worker.enqueue_checkpoint(0,checkpoint(originals,'source'),()).wait()
    compressed = [originals[0],{'role':'system','content':'archived result'}]
    rewrite = ArchiveRewrite('compact',tuple(originals),(0,None),(ArchiveDerivation('spill-d','summary',1,(1,2)),))
    await worker.enqueue_checkpoint(1,checkpoint(compressed,'source'),(),archive_rewrite=rewrite).wait()
    await worker.close()
    cleanup(root,1,int(time.time()*1000),sessions_dir=sessions,runtime=runtime,environ={})
    assert spill.is_file(), 'compressed transcript lost its spill dependency'
    worker = StorageWorker.open(sessions/'source','source',root,runtime)
    imported = await worker.archive_branch()
    branch = StorageWorker.open(sessions/'branch','branch',root,runtime)
    await branch.enqueue_checkpoint(0,checkpoint(compressed,'branch'),(),archive_import=imported).wait()
    await branch.close()
    await worker.enqueue_checkpoint(2,replace(checkpoint(compressed,'source'),background_state='closed'),()).wait()
    await worker.close()
    result = cleanup(root,1,int(time.time()*1000)+3*86400000,sessions_dir=sessions,runtime=runtime,environ={})
    assert result.sessions == 1 and not (sessions/'source').exists()
    branch = StorageWorker.open(sessions/'branch','branch',root,runtime)
    try:
        page = await branch.archive_read('spill-d')
        assert page['attachments']
        physical = Path(page['attachments'][0]['path'])
        assert physical.is_relative_to(sessions/'branch') and physical.is_file()
        assert hashlib.sha256(physical.read_bytes()).hexdigest() == page['attachments'][0]['sha256']
        assert physical.read_text('utf-8') == 'saved full output '*5000
    finally:
        await branch.close()
asyncio.run(scenario())
''')


def test_scope_import_only_selected_inherited_prefix_then_appends_new_task(tmp_path):
    _run(tmp_path, r'''
async def scenario():
    worker = opened()
    parent = [{'role':'system','content':'SYS'},{'role':'user','content':'not inherited'},
              {'role':'user','content':'visible source'}]
    await worker.enqueue_checkpoint(0,checkpoint(parent),()).wait()
    inherited = await worker.archive_branch(indices=(0,2))
    child = opened('child')
    desired = [parent[0],parent[2],{'role':'user','content':'new dispatched task'}]
    await child.enqueue_checkpoint(0,checkpoint(desired,'child'),(),archive_import=inherited).wait()
    try:
        history = await child.archive_export()
        assert [m['content'] for m in history['messages']] == ['SYS','visible source','new dispatched task']
        assert 'not inherited' not in str(history)
    finally:
        await child.close()
        await worker.close()
asyncio.run(scenario())
''')
