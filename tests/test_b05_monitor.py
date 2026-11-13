"""Frozen Monitor stdout, cancellation and timeout semantics with a real process."""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

_MONITOR = r'''
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.tasks import TaskManager
from ruocun.platform.shell_plan import buildShellPlan
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.monitor import monitorTool
from ruocun.tools.task_stop import taskStopTool
from ruocun.tools.types import ToolContext
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

async def scenario():
    session=Session('synthetic','synthetic',env={})
    store=await Conversation.open(root/'session','n46',root,runtime,session,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=store,workspaceRoot=root);await background.bind()
    manager=TaskManager(store,background)
    ctx=ToolContext(str(root),taskManager=manager,getShellPlan=lambda command,cwd:buildShellPlan(command,cwd,analyze=False))
    async def start(id,command,**extra):
        args={'command':command,'description':id,**extra}
        await store.intent(id,'Monitor',json.dumps(args),True)
        result=await monitorTool.handler(args,ctx)
        await store.result(id,result)
        task=next(task for task in manager.all() if task.description==id)
        assert 'task id='+task.id in result
        return task
    async def until(check):
        async with asyncio.timeout(10):
            while not check():await asyncio.sleep(.02)
    try:
        script=root/'lines.py';script.write_text('print("line1");print("line2");print("partial",end="")')
        command='"'+sys.executable+'" -I -u "'+str(script)+'"'
        task=await start('lines',command)
        await until(lambda:task.status=='completed')
        events=[event for event in background.events() if event.snapshot.taskId==task.id]
        assert [event.message for event in events if event.type=='message']==['line1\nline2\npartial']
        assert events[-1].type=='completed' and '监控结束' in task.result
        assert task.kind=='monitor'
        script=root/'long.py';heartbeat=root/'heartbeat'
        script.write_text('import time\nfrom pathlib import Path\np=Path('+repr(str(heartbeat))+')\n'
            'while True:\n p.write_text(str(time.monotonic()))\n print("tick",flush=True)\n time.sleep(.05)\n')
        command='"'+sys.executable+'" -I -u "'+str(script)+'"'
        task=await start('persistent',command,persistent=True,timeout_ms=1000)
        await until(heartbeat.exists)
        await asyncio.sleep(1.1)
        assert task.status=='running'
        await store.intent('stop','TaskStop',json.dumps({'id':task.id}),True)
        assert '已请求取消' in await taskStopTool.handler({'id':task.id},ctx)
        await store.result('stop','stop requested')
        await until(lambda:task.status=='canceled')
        stopped=heartbeat.read_text();await asyncio.sleep(.15)
        assert heartbeat.read_text()==stopped
        task=await start('timeout',command,timeout_ms=1000)
        await until(lambda:task.status=='completed')
        assert '监控超时(1000ms)已自动终止' in task.result
        view=await store.background_view()
        assert all(record.kind=='monitor' and record.status in {'completed','canceled'} for record in view.runs)
        assert monitorTool.checkPermissions(json.dumps({'command':'rm -rf /'}))=='ask'
        assert monitorTool.checkPermissions(json.dumps({'command':'tail -f app.log'})) is None
    finally:
        await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite and Job")
def test_source_monitor_batches_stdout_and_confirms_process_exit_before_terminal(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _MONITOR,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout


_CRASH = _MONITOR[:_MONITOR.index("async def scenario():")] + r'''
import os

async def scenario():
    session=Session('synthetic','synthetic',env={})
    store=await Conversation.open(root/'session','n46-crash',root,runtime,session,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=store,workspaceRoot=root);await background.bind()
    manager=TaskManager(store,background)
    ctx=ToolContext(str(root),taskManager=manager,getShellPlan=lambda command,cwd:buildShellPlan(command,cwd,analyze=False))
    script=root/'crash.py'
    script.write_text('import time\nfrom pathlib import Path\np=Path('+repr(str(root/'crash-heartbeat'))+')\n'
        'while True:\n p.write_text(str(time.monotonic()))\n print("crash tick",flush=True)\n time.sleep(.05)\n')
    args={'command':'"'+sys.executable+'" -I -u "'+str(script)+'"','description':'crash','persistent':True}
    await store.intent('crash','Monitor',json.dumps(args),True)
    result=await monitorTool.handler(args,ctx);await store.result('crash',result)
    async with asyncio.timeout(8):
        while not background.events():await asyncio.sleep(.02)
    os._exit(0)
asyncio.run(scenario())
'''

_RESTORE = _MONITOR[:_MONITOR.index("async def scenario():")] + r'''
from ruocun.session.recovery import RecoveryController
async def scenario():
    heartbeat=root/'crash-heartbeat'
    before=heartbeat.read_text();await asyncio.sleep(.2)
    assert heartbeat.read_text()==before
    session=Session('synthetic','synthetic',env={})
    store=await Conversation.open(root/'session','n46-crash',root,runtime,session,'synthetic-key',resume=True)
    background=BackgroundRuntime(store=store,workspaceRoot=root)
    try:
        await RecoveryController(store,session,background).recover()
        manager=TaskManager(store,background);await manager.bind()
        task=manager.all()[0]
        assert task.kind=='monitor' and task.status=='interrupted'
        assert any('crash tick' in event.message.splitlines() for event in background.events() if event.type=='message')
        await asyncio.sleep(.2)
        assert heartbeat.read_text()==before
        await manager.close()
    finally:await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite and Job")
def test_monitor_owner_loss_keeps_history_without_restarting_the_command(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    for script in (_CRASH, _RESTORE):
        result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", script,
                                 str(tmp_path), str(archive.resolve()), str(source)],
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        assert result.returncode == 0, result.stderr + result.stdout
