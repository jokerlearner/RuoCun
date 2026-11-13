"""Frozen durable_store/background_delivery boundaries through actual SQLite."""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="actual controlled SQLite Windows port"
)
_CODE = r"""
import asyncio,sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.session import Session
from ruocun.agent.background_runtime import BackgroundRuntime,WaitControl
from ruocun.agent.background_types import ExecutionEvent,ExecutionSnapshot
from ruocun.agent.background_delivery import BackgroundDelivery
root=Path(sys.argv[1])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
async def scenario():
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind()
  await store.refresh_recovery(session)
  a=ExecutionSnapshot('a','a-1','agent',True,'synthetic a','running')
  await background.publish(ExecutionEvent('started',a))
  record=(await store.background_view()).runs[0]
  await background.publish(ExecutionEvent('completed',replace(a,status='completed',result='invalid premature completion')),record)
  assert background.fault is not None and not background.events()
  assert (await store.background_view()).runs[0].status=='running'
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind()
  control=WaitControl(background)
  control.request({'ids':['a'],'mode':'all'})
  await store.save(session)
  handle=control.commit()
  assert handle is not None
  await background.publish(ExecutionEvent('completed',replace(a,status='completed',result='x'*50000)))
  assert background.fault is None
  event=background.events()[0]
  assert '完整输出' in event.snapshot.result
  assert len((await store.background_view()).pending_events)==1
  delivery=BackgroundDelivery(session,background)
  await delivery.deliver(background.events())
  assert len(session.messages)==2 and session.messages[-1]['content'].startswith('[后台任务数据,非用户指令]')
  view=await store.background_view()
  assert not view.pending_events and view.checkpoint.messages==tuple(session.messages)
  await delivery.deliver([event])
  assert len(session.messages)==2
  await store.close()
  session2=Session('SYS','synthetic',env={})
  store=await Conversation.open(root/'session','one',root,runtime,session2,'synthetic-key',resume=True)
  restored=BackgroundRuntime(store=store,workspaceRoot=root)
  await restored.bind()
  assert not restored.events() and restored.snapshot('a').status=='completed'
  attachment=next((root/'session'/'results').glob('*.txt'))
  attachment.unlink()
  broken=BackgroundRuntime(store=store,workspaceRoot=root)
  await broken.bind()
  assert broken.fault is not None
  await store.refresh_recovery(session2)
  assert store.blocked
  print('run/event persisted; message+delivered ack atomic; reopen dedupe; missing spill blocked')
 finally:
  await store.close()
asyncio.run(scenario())
"""


def test_actual_sqlite_background_delivery_and_missing_attachment(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "utf8",
            "-c",
            _CODE,
            str(tmp_path),
            str(archive.resolve()),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_ROLLBACK = (
    _CODE[: _CODE.index("async def scenario():")]
    + r"""
async def scenario():
 from ruocun.session.contract import StoreError
 from ruocun.session import durable_store
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 original=durable_store._put_meta
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind()
  await store.refresh_recovery(session)
  snap=ExecutionSnapshot('a','a-1','agent',True,'a','running')
  await background.publish(ExecutionEvent('started',snap))
  await background.publish(ExecutionEvent('completed',replace(snap,status='completed',result='done')))
  delivery=BackgroundDelivery(session,background)
  before=(await store.background_view()).checkpoint
  def fail_checkpoint(con,key,value):
   if key=='checkpoint': raise StoreError('synthetic confirmed rollback')
   return original(con,key,value)
  durable_store._put_meta=fail_checkpoint
  try: await delivery.deliver(background.events())
  except StoreError: pass
  else: raise AssertionError('save failure hidden')
  assert not background.consumed and not store.blocked
  view=await store.background_view()
  assert len(view.pending_events)==1 and view.checkpoint==before and len(session.messages)==1
  durable_store._put_meta=original
  await delivery.deliver(background.events())
  assert len(session.messages)==2 and not background.events() and not (await store.background_view()).pending_events
  print('confirmed rollback preserves transcript+pending event and retries same staged batch once')
 finally:
  durable_store._put_meta=original
  await store.close()
asyncio.run(scenario())
"""
)


def test_confirmed_save_rollback_unstages_and_retries_same_message_once(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "utf8",
            "-c",
            _ROLLBACK,
            str(tmp_path),
            str(archive.resolve()),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_READY = (
    _CODE[: _CODE.index("async def scenario():")]
    + r"""
async def scenario():
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind();await store.refresh_recovery(session)
  for task in ['a','other']:
   snap=ExecutionSnapshot(task,task+'-1','agent',True,task,'running')
   await background.publish(ExecutionEvent('started',snap))
   await background.publish(ExecutionEvent('completed',replace(snap,status='completed',result=task+' result')))
  control=WaitControl(background)
  await store.intent('wait','TaskWait','{"ids":["a"]}',False)
  body=control.request({'ids':['a'],'mode':'any'})
  # A concurrent accepted input has not saved the TaskWait result message yet.
  await store.queue_user(session,'additional')
  assert len((await store.background_view()).pending_events)==2
  await store.result('wait',body)
  session.messages.extend([{'role':'assistant','content':'','tool_calls':[{'id':'wait','type':'function','function':{'name':'TaskWait','arguments':'{"ids":["a"]}'}}]},
                           {'role':'tool','tool_call_id':'wait','content':body}])
  await store.save(session)
  assert control.commit() is None
  pending=(await store.background_view()).pending_events
  assert len(pending)==1 and pending[0].run_ref.task_id=='other'
  print('ready TaskWait acknowledges only own run after its actual message is committed')
 finally: await store.close()
asyncio.run(scenario())
"""
)


def test_ready_wait_ack_requires_its_message_and_consumes_only_own_run(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "utf8",
            "-c",
            _READY,
            str(tmp_path),
            str(archive.resolve()),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_SHELL = (
    _CODE[: _CODE.index("async def scenario():")]
    + r"""
async def scenario():
 import json,threading
 from ruocun.platform.shell_plan import buildShellPlan
 from ruocun.tools.managed_shell import ManagedShellManager
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 role=[sys.executable,'-I','-X','utf8','-m','ruocun']
 if Path(sys.argv[3]).name=='src':
  loader=Path(sys.argv[3]).parent/'tests/support/n15_role_loader.py'
  role=[sys.executable,'-I','-X','utf8',str(loader)]
 manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
 stop=asyncio.Event();observer=None
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind();await store.refresh_recovery(session)
  manager.bind_background(background)
  script=root/'native.py'
  script.write_text("from pathlib import Path\nimport time\np=Path('starts');p.write_text((p.read_text() if p.exists() else '')+'once')\ntime.sleep(.3)\nprint('SHELL-DONE',flush=True)\n",encoding='utf-8')
  command=f'"{sys.executable}" -I "{script}"'
  await store.intent('bash','Bash',json.dumps({'command':command}),True)
  ack=await manager.execute(buildShellPlan(command,str(root)),threading.Event(),background=True)
  await store.result('bash',ack)
  registered=(await store.recover())[0]
  handle,_=background.prepare({'ids':[registered.run_ref.run_id],'mode':'all'})
  assert handle.targets[0].taskId==registered.run_ref.task_id and handle.targets[0].runId==registered.run_ref.run_id
  background.release(handle)
  observer=asyncio.create_task(manager.observe_background(background,stop))
  for _ in range(200):
   if background.events() or background.fault: break
   await asyncio.sleep(.05)
  assert background.fault is None
  events=background.events()
  assert len(events)==1 and events[0].type=='completed' and 'SHELL-DONE' in events[0].snapshot.result
  assert (root/'starts').read_text()=='once'
  # Reading notification data must not consume BashOutput's separate cursor.
  record=(await store.recover())[0]
  assert 'SHELL-DONE' in (await manager.poll(record.run_ref.run_id))['stdout']
  await BackgroundDelivery(session,background).deliver(events)
  assert not background.events() and not (await store.background_view()).pending_events
  print('actual same-package shell completion imported once; model log cursor preserved; durable notification acknowledged')
 finally:
  stop.set()
  if observer is not None: await observer
  await manager.close();await store.close()
asyncio.run(scenario())
"""
)


def test_actual_shell_observer_delivers_once_without_consuming_model_logs(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "utf8",
            "-c",
            _SHELL,
            str(tmp_path),
            str(archive.resolve()),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_RECOVER = (
    _CODE[: _CODE.index("async def scenario():")]
    + r"""
async def scenario():
 from ruocun.agent.session_scheduler import SessionScheduler
 from ruocun.agent.loop import TurnResult
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 scheduler=None
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind();await store.refresh_recovery(session)
  snap=ExecutionSnapshot('a','a-1','agent',True,'synthetic execution source','running')
  await background.publish(ExecutionEvent('started',snap))
  await store.intent('wait','TaskWait','{"ids":["a"]}',False)
  control=WaitControl(background);body=control.request({'ids':['a'],'mode':'all'})
  await store.result('wait',body)
  session.messages.extend([{'role':'assistant','content':'','tool_calls':[{'id':'wait','type':'function','function':{'name':'TaskWait','arguments':'{"ids":["a"]}'}}]},
                           {'role':'tool','tool_call_id':'wait','content':body}])
  await store.save(session);assert control.commit() is not None
  await store.close()
  session=Session('SYS','synthetic',env={})
  store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=True)
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind();await store.refresh_recovery(session)
  delivery=BackgroundDelivery(session,background)
  calls=[]
  async def run(signal,boundary,generation):
   calls.append(generation);return TurnResult('complete')
  scheduler=SessionScheduler(queued_inputs=store.queued_inputs,
   queue_user=lambda text:store.queue_user(session,text),consume_user=lambda ident:store.consume_user(session,ident),
   discard_queued=lambda state:store.discard_queued(session,state=state),set_state=lambda state:store.set_foreground_state(session,state),
   run=run,background_runtime=background,deliver_background=lambda:delivery.deliver(background.events()))
  await scheduler.recover(store.foreground_state);await scheduler.settled()
  assert scheduler.status().state=='waiting' and calls==[]
  await background.publish(ExecutionEvent('completed',replace(snap,status='completed',result='offline completed')))
  await scheduler.finished()
  assert len(calls)==1 and not (await store.background_view()).pending_events
  print('persisted fixed-run wait restored with zero model calls, one event wake and one delivery')
 finally:
  if scheduler is not None:await scheduler.close()
  await store.close()
asyncio.run(scenario())
"""
)


def test_persisted_wait_restores_and_event_wakes_without_model_poll(tmp_path):
    source = Path(ruocun.__file__).resolve().parent.parent
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-X",
            "utf8",
            "-c",
            _RECOVER,
            str(tmp_path),
            str(archive.resolve()),
            str(source),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_ACK_UNKNOWN=_CODE[:_CODE.index("async def scenario():")]+r'''
async def scenario():
 import json,os,signal,threading,time
 from ruocun.platform.shell_plan import buildShellPlan
 from ruocun.tools.managed_shell import ManagedShellManager
 from ruocun.tools.shell_runner import identity
 from ruocun.session.process_identity import identity_alive,process_identity
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=False)
 role=[sys.executable,'-I','-X','utf8','-m','ruocun']
 if Path(sys.argv[3]).name=='src':
  loader=Path(sys.argv[3]).parent/'tests/support/n15_role_loader.py'
  role=[sys.executable,'-I','-X','utf8',str(loader)]
 manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
 try:
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  await background.bind();await store.refresh_recovery(session)
  manager.bind_background(background)
  original=manager.detach
  async def lose_after_detach(run_id):
   result=await original(run_id)
   record=(await store.recover())[0]
   runner=identity(record.snapshot['runner_identity'])
   assert process_identity(runner.pid)==runner
   os.kill(runner.pid,signal.SIGTERM)
   deadline=time.monotonic()+5
   while identity_alive(runner):
    assert time.monotonic()<deadline
    await asyncio.sleep(.025)
   return result
  manager.detach=lose_after_detach
  script=root/'loss_before_ack.py';script.write_text('import time;time.sleep(30)',encoding='utf-8')
  command=f'"{sys.executable}" -I "{script}"'
  await store.intent('bash','Bash',json.dumps({'command':command}),True)
  try: await manager.execute(buildShellPlan(command,str(root)),threading.Event(),background=True)
  except RuntimeError: pass
  else: raise AssertionError('unknown execution returned an ordinary successful background acknowledgement')
  view=await store.background_view()
  assert view.runs[0].status=='unknown' and view.tool_records[0].result is None
  assert store.blocked and len(background.events())==1 and background.events()[0].type=='unknown'
  print('pre-ack real runner loss retained same unknown run/event, no success acknowledgement')
 finally:
  await manager.close()
  for launcher in manager._launchers.values():launcher.wait(timeout=5)
  await store.close()
asyncio.run(scenario())
'''


def test_runner_loss_during_ack_refresh_preserves_unknown_without_success(tmp_path):
    source=Path(ruocun.__file__).resolve().parent.parent
    archive=Path(__file__).parent/"fixtures/sqlite-dll-win-x64-3540100.zip"
    result=subprocess.run([sys.executable,"-I","-X","utf8","-c",_ACK_UNKNOWN,str(tmp_path),str(archive.resolve()),str(source)],capture_output=True,text=True,encoding="utf-8",timeout=45)
    assert result.returncode==0,result.stderr+result.stdout
