"""15新增DB/runner原子关联的必要公开存储接缝确认。"""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows产品存储端口")


def test_shell_run_links_one_intent_and_preserves_committed_result(tmp_path):
    code = r'''
import asyncio, sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.contract import RunRecord, RunRef, StoreError
from ruocun.session.session import Session
root = Path(sys.argv[1])
runtime = verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]), root / 'dll'))
async def scenario():
    session = Session('SYS', 'synthetic', env={})
    c = await Conversation.open(root / 'session', 'one', root, runtime, session, 'synthetic-key', resume=False)
    try:
        assert await c.intent('call', 'Bash', '{"command":"echo approved"}', True) is None
        snapshot = dict(version=1, control_epoch=0, launch_id='launch-one',
                        plan_digest='b' * 64, run_dir='synthetic-run', endpoint='pipe-one')
        run = await c.prepare(RunRef('task-one', 'run-one'), snapshot)
        assert (await c.prepare(run.run_ref, snapshot)) == run
        try:
            await c.prepare(RunRef('task-two', 'run-two'), snapshot)
        except StoreError:
            pass
        else:
            raise AssertionError('same tool launched a second run')
        running = replace(run, status='running', snapshot={**run.snapshot, 'control_epoch': 1})
        await c.commit(running)
        try:
            await c.commit(run)
        except StoreError:
            pass
        else:
            raise AssertionError('stale control epoch accepted')
        await c.result('call', 'original result')
        completed = replace(running, status='completed', snapshot={**running.snapshot,
                            'receipt_digest': 'a' * 64, 'tool_result': 'recovery acknowledgement'})
        await c.commit(completed)
        saved, = await c.recover()
        assert saved.snapshot['tool_result'] == 'original result'
        assert saved.status == 'completed'
        assert await c.intent('call', 'Bash', '{"command":"echo approved"}', True) == 'original result'
        view = await c.worker.load_recovery_view()
        assert view.tool_records[0].intent.run_ref == saved.run_ref
        assert len(view.runs) == 1
        legacy = RunRecord(RunRef('legacy-task', 'legacy-run'), 'shell', 'completed', False,
                           {'tool_ref': {'legacy_field': 'preserved'}})
        await c.worker.enqueue_run_event(legacy, None).wait()
        assert len(await c.recover()) == 1
    finally:
        await c.close()
asyncio.run(scenario())
'''
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    source = Path(ruocun.__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(tmp_path), str(archive.resolve()), str(source)],
        capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr
