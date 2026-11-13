"""Frozen managed_shell.test.ts real lifecycle assertions through D09 storage."""
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows独立runner/IPC实际产品确认")

_CODE = r"""
import asyncio, json, re, sys, threading, time
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.tools.managed_shell import ManagedShellManager
from ruocun.platform.shell_plan import buildShellPlan
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.session import Session

root=Path(sys.argv[1])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
role=[sys.executable,'-I','-X','utf8','-m','ruocun']
if Path(sys.argv[3]).name=='src':
    loader=Path(sys.argv[3]).parent/'tests/support/n15_role_loader.py'
    role=[sys.executable,'-I','-X','utf8',str(loader)]
async def open_store(resume=False):
    session=Session('SYS','synthetic',env={})
    store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=resume)
    return store,session
async def wait(manager,run_id,views=None):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        view=await manager.poll(run_id)
        if views is not None: views.append(view)
        if view['status'] in ('completed','failed','canceled','unknown'):
            return view
        await asyncio.sleep(.05)
    raise AssertionError('runner did not settle')
async def cleanup(manager,store):
    for run in await store.recover():
        if run.status not in ('completed','failed','canceled','failed-before-grant'):
            try:
                await manager.cancel(run.run_ref.run_id)
                await wait(manager,run.run_ref.run_id)
            except Exception:
                pass
    await manager.close()
    await store.close()
async def scenario():
    store,session=await open_store()
    manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
    try:
        script=root/'worker.py'
        script.write_text("from pathlib import Path\nimport time\np=Path('starts');p.write_text((p.read_text() if p.exists() else '')+'once')\nprint('before',flush=True)\ntime.sleep(1)\nprint('A'*25000+'TAIL',flush=True)\n",encoding='utf-8')
        command=f'"{sys.executable}" -I "{script}"'
        await store.intent('first','Bash',json.dumps({'command':command}),True)
        chunks=[]
        foreground_cancel=threading.Event()
        rpc=manager._rpc
        async def interrupt_at_detach_ack(entry, action):
            reply=await rpc(entry, action)
            if action=='detach':
                foreground_cancel.set()
                await asyncio.sleep(.22)
            return reply
        manager._rpc=interrupt_at_detach_ack
        executing=asyncio.create_task(manager.execute(buildShellPlan(command,str(root)),foreground_cancel,onOutput=lambda stream,text:chunks.append(text)))
        deadline=time.monotonic()+20
        while not any('before' in text for text in chunks):
            assert not executing.done(), 'foreground failed before live output'
            assert time.monotonic()<deadline
            await asyncio.sleep(.025)
        assert await manager.detach_foreground()
        ack=await executing
        assert isinstance(ack,str)
        run_id=re.search(r'id: ([0-9a-f-]{36})',ack)[1]
        await store.result('first',ack)
        # UI observation must not consume model-side BashOutput output.
        first=await manager.poll(run_id)
        assert 'before' in first['stdout']
        await store.save(session)
        await manager.close()
        await store.close()

        store,session=await open_store(resume=True)
        manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        records=await manager.restore()
        assert len(records)==1 and records[0].snapshot['tool_result']==ack
        assert not records[0].cancel_requested
        views=[]
        result=await wait(manager,run_id,views)
        assert result['status']=='completed',result
        # A single source poll observes the current end and keeps the latest tail.
        text=''.join(view['stdout'] for view in views)
        assert 'TAIL' in text and '已截断' in text
        empty=await manager.poll(run_id)
        assert empty['stdout']=='' and empty['stderr']==''
        assert (root/'starts').read_text()=='once'
        # Recovery is idempotent and never launches a second command.
        assert (await manager.restore())[0].status=='completed'
        assert (root/'starts').read_text()=='once'
        print('detach/reconnect/terminal/tail/UI cursor/source once passed')
    finally:
        await cleanup(manager,store)
asyncio.run(scenario())
"""


def test_real_detach_reconnect_logs_and_once(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _CODE, str(tmp_path), str(archive.resolve()), str(source)],
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_FAILURES = _CODE[:_CODE.index("async def scenario():")] + r"""
async def scenario():
    from ruocun.tools.types import ToolRejected
    store,session=await open_store()
    broken=ManagedShellManager(root/'session','one',store,
        runner_command=[sys.executable,'-I','-c',"print('synthetic bootstrap failure');raise SystemExit(23)"],
        helper_command=role+['--ruocun-ipc-helper'])
    try:
        command='echo never>never.txt'
        await store.intent('bad','Bash',json.dumps({'command':command}),True)
        try:
            await broken.execute(buildShellPlan(command,str(root)),threading.Event(),background=True)
        except ToolRejected:
            pass
        else:
            raise AssertionError('bootstrap failure was accepted')
        records=await store.recover()
        assert len(records)==1 and records[0].status=='failed-before-grant'
        directory=Path(records[0].snapshot['run_dir'])
        assert 'synthetic bootstrap failure' in (directory/'runner.log').read_text(encoding='utf-8')
        assert not (root/'never.txt').exists()
        assert not (directory/'grant.json').exists() and not (directory/'start.claim').exists()
        await broken.close()
        await store.close()
        store,session=await open_store(resume=True)
        restored=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        assert (await restored.restore())[0].status=='failed-before-grant'
        assert not (root/'never.txt').exists()
        await restored.close()
        manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        await store.intent('good','Bash','{"command":"echo allowed"}',True)
        result=await manager.execute(buildShellPlan('echo allowed',str(root)),threading.Event())
        assert result.code==0 and 'allowed' in result.stdout
        await store.result('good','allowed result')
        await manager.close()
        print('known failure before grant preserved and next command passed')
    finally:
        await broken.close()
        await store.close()
asyncio.run(scenario())
"""

_CANCEL = _CODE[:_CODE.index("async def scenario():")] + r"""
async def scenario():
    store,session=await open_store()
    manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
    try:
        script=root/'write_loop.py'
        script.write_text("from pathlib import Path\nimport time\np=Path('ticks');i=0\nwhile True:\n p.write_text(str(i));print(i,flush=True);i+=1;time.sleep(.02)\n",encoding='utf-8')
        command=f'"{sys.executable}" -I "{script}"'
        await store.intent('cancel','Bash',json.dumps({'command':command}),True)
        ack=await manager.execute(buildShellPlan(command,str(root)),threading.Event(),background=True)
        run_id=re.search(r'id: ([0-9a-f-]{36})',ack)[1]
        await store.result('cancel',ack)
        deadline=time.monotonic()+10
        while not (root/'ticks').exists():
            assert time.monotonic()<deadline
            await asyncio.sleep(.025)
        requested=await manager.cancel(run_id)
        assert requested['status'] in ('canceling','canceled')
        stopped=await wait(manager,run_id)
        assert stopped['status']=='canceled',stopped
        saved=(root/'ticks').read_bytes()
        await asyncio.sleep(.15)
        assert (root/'ticks').read_bytes()==saved
        records=await store.recover()
        record=records[0]
        assert record.cancel_requested and len(record.snapshot['receipt_digest'])==64
        logs=Path(record.snapshot['run_dir'])
        assert (logs/'stdout.log').read_bytes()==(logs/'stdout.txt').read_bytes()
        # The frozen identity mismatch is checked before accepting a signed receipt.
        from ruocun.tools.shell_runner import read_signed,write_signed
        capability=(logs/'capability').read_bytes()
        receipt=read_signed(logs/'terminal.json',capability)
        write_signed(logs/'terminal.json',{**receipt,'run_id':'other'},capability)
        rejected=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        try:
            await rejected.restore()
        except RuntimeError:
            pass
        else:
            raise AssertionError('mismatched signed run accepted')
        assert any('附件未确认' in notice for notice in await rejected.close())
        assert (await store.recover())[0].status=='canceled'
        write_signed(logs/'terminal.json',receipt,capability)
        # A missing attachment is retained as a recovery error, never a second launch.
        (Path(record.snapshot['run_dir'])/'stdout.log').unlink()
        other=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        try:
            await other.restore()
        except RuntimeError:
            pass
        else:
            raise AssertionError('missing attachment accepted')
        assert any('附件未确认' in notice for notice in await other.close())
        assert (await store.recover())[0].status=='canceled'
        assert (root/'ticks').read_bytes()==saved
        print('actual cancellation receipt/stop-write and missing attachment rejection passed')
    finally:
        await cleanup(manager,store)
asyncio.run(scenario())
"""


def _run_case(code, tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(tmp_path), str(archive.resolve()), str(source)],
        capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_before_grant_failure_retains_diagnostics_and_unblocks_next(tmp_path):
    _run_case(_FAILURES, tmp_path)


def test_real_cancel_receipt_and_missing_attachment_no_relaunch(tmp_path):
    _run_case(_CANCEL, tmp_path)


_LOSS = _CODE[:_CODE.index("async def scenario():")] + r"""
async def scenario():
    import os,signal
    from ruocun.session.process_identity import identity_alive,process_identity
    from ruocun.tools.shell_runner import identity
    store,session=await open_store()
    manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
    try:
        script=root/'loss_worker.py'
        script.write_text("from pathlib import Path\nimport time\np=Path('starts');p.write_text((p.read_text() if p.exists() else '')+'once')\ni=0\nwhile True:\n Path('ticks').write_text(str(i));i+=1;time.sleep(.02)\n",encoding='utf-8')
        command=f'"{sys.executable}" -I "{script}"'
        await store.intent('lost','Bash',json.dumps({'command':command}),True)
        ack=await manager.execute(buildShellPlan(command,str(root)),threading.Event(),background=True)
        run_id=re.search(r'id: ([0-9a-f-]{36})',ack)[1]
        await store.result('lost',ack)
        deadline=time.monotonic()+10
        while not (root/'ticks').exists():
            assert time.monotonic()<deadline
            await asyncio.sleep(.025)
        record=(await store.recover())[0]
        original=identity(record.snapshot['runner_identity'])
        assert process_identity(original.pid)==original
        os.kill(original.pid,signal.SIGTERM)
        while identity_alive(original):
            assert time.monotonic()<deadline
            await asyncio.sleep(.025)
        result=await wait(manager,run_id)
        assert result['status']=='unknown',result
        assert (await manager.poll(run_id))['status']=='unknown'
        restored=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        assert (await restored.restore())[0].status=='unknown'
        assert (root/'starts').read_text()=='once'
        saved=(root/'ticks').read_bytes()
        await asyncio.sleep(.15)
        assert (root/'ticks').read_bytes()==saved
        # The OS-confirmed runner loss cannot produce a fabricated close receipt.
        assert not (Path(record.snapshot['run_dir'])/'terminal.json').exists()
        print('actual runner loss stays unknown, native Job stops writes, no relaunch passed')
    finally:
        for launcher in manager._launchers.values():
            launcher.wait(timeout=5)
        await store.close()
asyncio.run(scenario())
"""


def test_real_runner_loss_stays_unknown_and_does_not_restart(tmp_path):
    _run_case(_LOSS, tmp_path)
