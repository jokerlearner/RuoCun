"""Necessary durable seam: hidden reflection identity survives restart without replay."""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun


@pytest.mark.skipif(sys.platform != "win32", reason="Windows controlled SQLite port")
def test_reflection_checkpoint_and_scoped_recovery_keep_one_identity(tmp_path):
    code = r'''
import asyncio,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.session.conversation import Conversation
from ruocun.session.contract import Checkpoint,RunRef,ToolRef,checkpoint_request_digest
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
legacy=Checkpoint('one',({'role':'system','content':'SYS'},),'synthetic','normal','title',0,(),(),{},'idle',0)
assert checkpoint_request_digest(0,legacy,())=='7b0fd391138465e444a986f53f92d201ea90b4bbb737e238b6a3ccfcc90c7a20'
async def scenario():
    session=Session('SYS','synthetic',env={})
    c=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
    ref=ToolRef('reflect','stable-one')
    try:
        await c.set_reflection_state(session,{'phase':'ready','id':'stable-one','advisories':['synthetic advice']})
        assert await c.scoped_intent(ref,'ReflectMemory','{}',True,agent_run=RunRef('reflect','stable-one'),approval_ref='reflect-memory-enabled') is None
        await c.scoped_result(ref,'confirmed once')
        await c.set_reflection_state(session,{'phase':'applied','id':'stable-one','advisories':['synthetic advice']})
    finally: await c.close()
    session=Session('SYS','synthetic',env={})
    c=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=True)
    try:
        assert c.reflection_state['id']=='stable-one'
        assert await c.scoped_intent(ref,'ReflectMemory','{}',True,agent_run=RunRef('reflect','stable-one'),approval_ref='reflect-memory-enabled')=='confirmed once'
        assert not any(m.get('role')=='tool' for m in session.messages)
        await c.set_reflection_state(session,None,advisories=['synthetic advice'])
        assert session.messages[-1]=={'role':'system','content':'synthetic advice'}
        await c.set_reflection_state(session,{'phase':'applying','id':'stable-two'})
        await c.scoped_intent(ToolRef('reflect','stable-two'),'ReflectMemory','{}',True,agent_run=RunRef('reflect','stable-two'),approval_ref='reflect-memory-enabled')
    finally: await c.close()
    c=await Conversation.open(root/'session','one',root,runtime,Session('SYS','synthetic',env={}),'synthetic-key',resume=True)
    try:
        assert c.blocked and c.reflection_state['id']=='stable-two'
        view=await c.worker.load_recovery_view()
        assert next(t for t in view.tool_records if t.tool_ref.tool_call_id=='stable-two').state=='outcome_unknown'
    finally: await c.close()
asyncio.run(scenario())
'''
    package=Path(ruocun.__file__).resolve().parent
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',code,str(tmp_path),
                           str(package/'resources/runtime/sqlite-dll-win-x64-3540100.zip'),str(package.parent)],
                          capture_output=True,text=True,encoding='utf-8',timeout=35)
    assert result.returncode==0,(result.stdout,result.stderr)
