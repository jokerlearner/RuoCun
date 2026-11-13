"""Existing unknown/missing-receipt recovery followed by the ordinary finally close."""
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows真实存储恢复接缝")

_CODE = r'''
import asyncio,json,sys,uuid
from dataclasses import asdict,replace
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.contract import RunRef
from ruocun.session.process_identity import process_identity
from ruocun.session.session import Session
from ruocun.tools.managed_shell import ManagedShellManager
root=Path(sys.argv[1])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
async def scenario():
    session=Session('SYS','synthetic',env={})
    store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
    try:
        run_id=str(uuid.uuid4())
        await store.intent('lost','Bash','{"command":"synthetic-unknown"}',True)
        directory=root/'session'/'runs'/run_id
        snapshot={'version':1,'phase':'grant-possible','launch_id':uuid.uuid4().hex,
                  'plan_digest':'a'*64,'run_dir':str(directory),'endpoint':None,'control_epoch':0,
                  'owner_identity':asdict(process_identity()),'detached':False}
        record=await store.prepare(RunRef('proc-synthetic',run_id),snapshot)
        await store.commit(replace(record,status='unknown'))
        if sys.argv[4]=='terminal':
            directory.mkdir(parents=True)
            (directory/'terminal.json').write_text('{"invalid":"synthetic"}',encoding='utf-8')
        manager=ManagedShellManager(root/'session','one',store)
        records=await manager.restore()
        assert records[0].status=='unknown'
        before=(await store.recover())[0]
        notices=await manager.close()
        after=(await store.recover())[0]
        assert after==before, 'finally close altered unknown evidence/cancellation intent'
        assert not after.cancel_requested and after.status=='unknown'
        assert notices and any(run_id in notice and '未确认' in notice for notice in notices)
        rejected=await manager.cancel(run_id)
        assert rejected['status']=='unknown' and 'reason' in rejected
        assert (await store.recover())[0]==before
        print(json.dumps({'unknown_preserved':True,'control_not_sent':True,'reported':True}))
    finally:
        await store.close()
asyncio.run(scenario())
'''


@pytest.mark.parametrize("material", ["missing", "terminal"])
def test_unknown_restore_finally_close_preserves_evidence_and_reports(tmp_path, material):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _CODE, str(tmp_path), str(archive.resolve()), str(source), material],
        capture_output=True, text=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr + result.stdout
