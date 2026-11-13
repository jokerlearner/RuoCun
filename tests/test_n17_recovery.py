"""Frozen recovery.ts/durable_store.test.ts pair preservation and explicit decisions."""
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun
from ruocun.session.contract import ToolRecord, ToolRef
from ruocun.session.recovery import repairToolPairs


def test_repair_preserves_assistant_known_result_and_explicit_unknown_without_replay():
    assistant={"role":"assistant","content":"keep me","tool_calls":[{"id":name,"function":{"name":"Bash","arguments":"{}"}} for name in ['known','unknown','absent']]}
    record=ToolRecord(ToolRef('main','known'),'Bash','{}','result_committed','saved exact result',None,None)
    unknown=ToolRecord(ToolRef('main','unknown'),'Bash','{}','outcome_unknown',None,None,None)
    repaired=repairToolPairs([assistant],[record,unknown])
    assert repaired[0]==assistant and repaired[1]['content']=='saved exact result'
    assert '结果未知' in repaired[2]['content'] and '未执行' in repaired[3]['content']
    assert repairToolPairs(repaired,[record,unknown])==repaired
    assert '结果未知' in repairToolPairs([assistant],None)[-1]['content']


_CODE=r'''
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.session import Session
from ruocun.session.recovery import RecoveryController
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.session.contract import RunRecord,RunRef
from ruocun.session.recovery import attachmentToolRef
from dataclasses import replace
root=Path(sys.argv[1])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
async def opened(resume):
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=resume)
 return store,session
async def scenario():
 store,session=await opened(False)
 try:
  session.messages.append({'role':'assistant','content':'preserved','tool_calls':[{'id':'write','type':'function','function':{'name':'Write','arguments':'{"path":"synthetic.txt"}'}}]})
  await store.save(session)
  await store.intent('write','Write','{"path":"synthetic.txt"}',True)
  target=root/'synthetic.txt';target.write_text('already applied',encoding='utf-8')
  await store.close()
  store,session=await opened(True)
  background=BackgroundRuntime(store=store,workspaceRoot=root)
  controller=RecoveryController(store,session,background)
  await controller.recover()
  report=json.loads((await controller.command('/recovery')).split('\n核实未决工具',1)[0])
  assert report['unresolved'][0]['id']=='write' and store.blocked
  before=target.read_bytes()
  # Source atomicStore semantics: failure after journal mutation must roll back history and decision too.
  import ruocun.session.durable_store as durable
  original_put=durable._put_meta
  def fail_checkpoint(con,key,value):
   if key=='checkpoint':raise durable.StoreError('synthetic recovery checkpoint rollback')
   return original_put(con,key,value)
  durable._put_meta=fail_checkpoint
  try:
   try:await controller.command('/recovery resolve main write 已核实原写入已完成，不重放',decision_id='synthetic-resolution')
   except ValueError:pass
   else:raise AssertionError('checkpoint failure reported success')
  finally:durable._put_meta=original_put
  rolled=await store.background_view()
  assert rolled.tool_records[0].state=='outcome_unknown' and not rolled.decisions
  assert not any(str(m.get('content','')).startswith('[用户恢复决定]') for m in rolled.checkpoint.messages)
  result=await controller.command('/recovery resolve main write 已核实原写入已完成，不重放',decision_id='synthetic-resolution')
  assert '已记录' in result and not store.blocked
  view=await store.background_view()
  assert view.tool_records[0].state=='result_committed' and view.tool_records[0].decision_ref=='synthetic-resolution'
  assert view.checkpoint.messages[-1]['content'].startswith('[用户恢复决定]')
  count=len(view.checkpoint.messages)
  await controller.command('/recovery resolve main write 已核实原写入已完成，不重放',decision_id='synthetic-resolution')
  assert len((await store.background_view()).checkpoint.messages)==count and target.read_bytes()==before
  try:await controller.command('/recovery resolve main write 不同解释',decision_id='synthetic-resolution')
  except ValueError:pass
  else:raise AssertionError('same decision ID content conflict accepted')
  await store.close()
  store,session=await opened(True)
  controller=RecoveryController(store,session,BackgroundRuntime(store=store,workspaceRoot=root))
  await controller.recover()
  assert not store.blocked and target.read_bytes()==before
  assert any(message.get('content','').startswith('[用户恢复决定]') for message in session.messages)
  print('real unknown write preserved; explicit decision+message atomic; repeat/reopen no replay')
  # Unknown Shell result is a human attestation, not a synthetic runner receipt.
  run=RunRecord(RunRef('lost-shell','old-run'),'shell','unknown',False,{'background_execution':{
    'taskId':'lost-shell','runId':'old-run','kind':'shell','background':True,'description':'lost command','status':'unknown'}})
  await store.publish_background(run,None)
  await controller.command('/recovery decide lost-shell completed 已人工核对目标文件',decision_id='human-shell')
  saved=next(r for r in (await store.background_view()).runs if r.run_ref==run.run_ref)
  assert saved.status=='completed' and saved.snapshot['resolved_by_user'] and 'receipt_digest' not in saved.snapshot
  assert len([e for e in (await store.background_view()).pending_events if e.event_id=='old-run:user-decision'])==1
  await controller.command('/recovery decide lost-shell completed 已人工核对目标文件',decision_id='human-shell')
  assert len([e for e in (await store.background_view()).pending_events if e.event_id=='old-run:user-decision'])==1
  # Source missing-attachment marker stays unresolved until an explicit user disposition.
  file=root/'missing.txt';file.write_text('synthetic attachment',encoding='utf-8')
  import hashlib
  await store.register_background_attachment(str(file),hashlib.sha256(file.read_bytes()).hexdigest());file.unlink()
  await controller.recover()
  ref=attachmentToolRef(str(file))
  assert store.blocked and any(r.tool_ref==ref for r in (await store.background_view()).tool_records)
  await controller.command('/recovery resolve recovery '+ref.tool_call_id+' 接受此附件丢失，保留历史登记',decision_id='missing-disposition')
  assert not store.blocked and not file.exists() and not (await store.background_view()).missing_attachments
  # Interrupted agent requires all saved material and a real bound dispatcher.
  material={'model':'synthetic-model','agentType':'general','definitionVersion':'v1',
    'worktree':str(root),'messages':[{'role':'system','content':'S'}],'permissions':{},'budget':None}
  old=RunRecord(RunRef('agent-task','agent-old'),'agent','running',False,{'recovery_material':material,'background_execution':{'taskId':'agent-task','runId':'agent-old','kind':'agent','background':True,'description':'saved agent','status':'running'}})
  await store.publish_background(old,None)
  await controller.recover()
  assert next(r for r in (await store.background_view()).runs if r.run_ref==old.run_ref).status=='interrupted'
  assert any(e.event_id=='agent-old:recovery-interrupted' for e in (await store.background_view()).pending_events)
  try:await controller.command('/recovery continue agent-task 执行下一步',decision_id='continue-unbound')
  except ValueError as e:assert 'dispatcher' in str(e)
  else:raise AssertionError('unbound agent dispatcher pretended to run')
  assert not any(r.run_ref.run_id!='agent-old' and r.run_ref.task_id=='agent-task' for r in (await store.background_view()).runs)
  calls=[]
  async def dispatch(request):
   calls.append(request.new_run)
   (root/'agent-effect.txt').write_text('once',encoding='utf-8')
   return RunRecord(request.new_run,'agent','completed',False,{'recovery_material':request.material})
  controller.continue_agent=dispatch
  await controller.command('/recovery continue agent-task 执行下一步',decision_id='continue-once')
  await controller.command('/recovery continue agent-task 执行下一步',decision_id='continue-once')
  assert len(calls)==1 and (root/'agent-effect.txt').read_text()=='once'
  # Once authorization can reach execution, an exception never permits replay.
  other=replace(old,run_ref=RunRef('uncertain-task','uncertain-old'),snapshot={'recovery_material':material})
  await store.publish_background(other,None);await controller.recover()
  async def uncertain(request):
   calls.append(request.new_run);raise RuntimeError('synthetic executor lost acknowledgment')
  controller.continue_agent=uncertain
  try:await controller.command('/recovery continue uncertain-task 保留原信息',decision_id='uncertain-once')
  except RuntimeError:pass
  else:raise AssertionError('unknown dispatch should stop')
  for attempt in range(2):
   try:await controller.command('/recovery continue uncertain-task 保留原信息',decision_id='uncertain-once')
   except ValueError as e:assert '不会再次启动' in str(e)
   else:raise AssertionError('unknown continuation incorrectly claimed complete')
  assert len(calls)==2 and store.blocked
  print('human decide preserves provenance; missing attachment explicit; durable continue once/unknown no replay')
 finally:await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform!='win32',reason='controlled Windows SQLite')
def test_actual_unknown_tool_resolve_and_message_are_atomic_idempotent_no_replay(tmp_path):
    source=Path(ruocun.__file__).resolve().parent.parent
    archive=Path(__file__).parent/'fixtures/sqlite-dll-win-x64-3540100.zip'
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',_CODE,str(tmp_path),str(archive.resolve()),str(source)],capture_output=True,text=True,encoding='utf-8',timeout=30)
    assert result.returncode==0,result.stderr+result.stdout


_NATIVE = r'''
import asyncio,json,sys,threading
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.tools.managed_shell import ManagedShellManager
from ruocun.platform.shell_plan import buildShellPlan
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.conversation import Conversation
from ruocun.session.session import Session
from ruocun.session.recovery import RecoveryController
from ruocun.agent.background_runtime import BackgroundRuntime
root=Path(sys.argv[1]);source=Path(sys.argv[3])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
role=[sys.executable,'-I','-X','utf8','-m','ruocun']
if source.name=='src':role=[sys.executable,'-I','-X','utf8',str(source.parent/'tests/support/n15_role_loader.py')]
async def opened(resume):
 session=Session('SYS','synthetic',env={})
 store=await Conversation.open(root/'session','one',root,runtime,session,'synthetic-key',resume=resume)
 manager=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
 return store,session,manager
async def scenario():
 store,session,manager=await opened(False)
 try:
  script=root/'worker.py';script.write_text("from pathlib import Path\np=Path('starts');p.write_text((p.read_text() if p.exists() else '')+'once')\nprint('synthetic output')\n",encoding='utf-8')
  command='"'+sys.executable+'" -I "'+str(script)+'"'
  await store.intent('bash','Bash',json.dumps({'command':command}),True)
  result=await manager.execute(buildShellPlan(command,str(root)),threading.Event())
  assert not isinstance(result,str)
  await store.result('bash','saved completed Shell result');await store.save(session)
  record=(await store.recover())[0]
  directory=Path(record.snapshot['run_dir']);(directory/'stdout.txt').unlink()
  await manager.close();await store.close()
  store,session,manager=await opened(True)
  await manager.restore(report_errors=True)
  assert manager.recovery_errors and (await store.recover())[0].status=='completed'
  controller=RecoveryController(store,session,BackgroundRuntime(store=store,workspaceRoot=root),manager)
  await controller.recover()
  view=await store.background_view()
  marker=next(r for r in view.tool_records if r.name=='RecoveryMaterial')
  assert store.blocked and marker.state=='outcome_unknown'
  await controller.command('/recovery resolve recovery '+marker.tool_ref.tool_call_id+' 接受完整日志缺失，保留原终态收据',decision_id='native-material')
  assert not store.blocked and (await store.recover())[0].status=='completed'
  assert (await store.recover())[0].snapshot['recovery_material_accepted']=='native-material'
  assert (root/'starts').read_text()=='once'
  await manager.restore(report_errors=True)
  assert not manager._runs and (root/'starts').read_text()=='once'
  print('real same-package runner: terminal stays terminal; corrupt log explicit disposition; no restart/control')
 finally:
  await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform!='win32',reason='actual Windows runner')
def test_real_runner_bad_material_requires_explicit_disposition_without_restart(tmp_path):
    source=Path(ruocun.__file__).resolve().parent.parent
    archive=Path(__file__).parent/'fixtures/sqlite-dll-win-x64-3540100.zip'
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',_NATIVE,str(tmp_path),str(archive.resolve()),str(source)],capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert result.returncode==0,result.stderr+result.stdout


@pytest.mark.skipif(sys.platform!='win32',reason='actual Windows runner loss')
def test_real_lost_runner_user_decision_does_not_create_receipt_or_relaunch(tmp_path):
    fixture=Path(__file__).with_name('test_n15_managed_shell.py').read_text(encoding='utf-8')
    namespace={}
    exec(compile(fixture,str(Path(__file__).with_name('test_n15_managed_shell.py')),'exec'),namespace)
    code=namespace['_LOSS'].replace("        print('actual runner loss stays unknown, native Job stops writes, no relaunch passed')",r"""
        from ruocun.session.recovery import RecoveryController
        from ruocun.agent.background_runtime import BackgroundRuntime
        bg=BackgroundRuntime(store=store,workspaceRoot=root)
        controller=RecoveryController(store,session,bg,manager)
        await controller.recover()
        await controller.command('/recovery decide '+record.run_ref.task_id+' failed 已确认原runner退出且目标停止写入',decision_id='native-loss')
        after=(await store.recover())[0]
        assert after.status=='failed' and after.snapshot['resolved_by_user'] and 'receipt_digest' not in after.snapshot
        assert (await manager.poll(run_id))['status']=='resolved-by-user'
        assert (await manager.cancel(run_id))['status']=='resolved-by-user'
        assert '未重新控制' in ' '.join(await manager.close())
        another=ManagedShellManager(root/'session','one',store,runner_command=role+['--ruocun-shell-runner'],helper_command=role+['--ruocun-ipc-helper'])
        assert not await another.restore(report_errors=True)
        assert (root/'starts').read_text()=='once' and (root/'ticks').read_bytes()==saved
        assert not (Path(record.snapshot['run_dir'])/'terminal.json').exists()
        await another.close()
        print('actual runner loss + human decide preserves provenance, no fabricated receipt or replay')
""")
    source=Path(ruocun.__file__).resolve().parent.parent
    archive=Path(__file__).parent/'fixtures/sqlite-dll-win-x64-3540100.zip'
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',code,str(tmp_path),str(archive.resolve()),str(source)],capture_output=True,text=True,encoding='utf-8',timeout=90)
    assert result.returncode==0,result.stderr+result.stdout


_UNKNOWN = _CODE[:_CODE.index('async def scenario():')] + r'''
async def scenario():
 import ruocun.session.durable_store as durable
 from ruocun.session.contract import RecoveryReceipt
 from ruocun.session.sqlite_port import CommitUnconfirmedError
 store,session=await opened(False)
 try:
  await store.save(session);await store.intent('uncertain-write','Write','{}',True)
  await store.close();store,session=await opened(True)
  controller=RecoveryController(store,session,BackgroundRuntime(store=store,workspaceRoot=root))
  await controller.recover()
  original=durable.DurableStore._atomic
  def committed_but_unconfirmed(self,owner,body):
   result=original(self,owner,body)
   if isinstance(result,RecoveryReceipt):raise CommitUnconfirmedError('synthetic committed recovery ack lost')
   return result
  durable.DurableStore._atomic=committed_but_unconfirmed
  try:
   try:await controller.command('/recovery resolve main uncertain-write 已核实，勿自动重复',decision_id='uncertain-decision')
   except CommitUnconfirmedError:pass
   else:raise AssertionError('unknown commit incorrectly classified as ordinary rejection')
  finally:durable.DurableStore._atomic=original
  assert store.blocked
  view=await store.background_view()
  assert view.tool_records[0].state=='result_committed'
  assert len(view.decisions)==1 and len([m for m in view.checkpoint.messages if str(m.get('content','')).startswith('[用户恢复决定]')])==1
  await store.close();store,session=await opened(True)
  controller=RecoveryController(store,session,BackgroundRuntime(store=store,workspaceRoot=root))
  await controller.recover()
  await controller.command('/recovery resolve main uncertain-write 已核实，勿自动重复',decision_id='uncertain-decision')
  view=await store.background_view()
  assert len(view.decisions)==1 and len([m for m in view.checkpoint.messages if str(m.get('content','')).startswith('[用户恢复决定]')])==1
  print('real committed decision with lost ack stays unknown in-process; reopen reconciles once without replay')
 finally:await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform!='win32',reason='actual controlled SQLite')
def test_recovery_commit_ack_unknown_remains_distinct_and_reconciles_once(tmp_path):
    source=Path(ruocun.__file__).resolve().parent.parent
    archive=Path(__file__).parent/'fixtures/sqlite-dll-win-x64-3540100.zip'
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',_UNKNOWN,str(tmp_path),str(archive.resolve()),str(source)],capture_output=True,text=True,encoding='utf-8',timeout=30)
    assert result.returncode==0,result.stderr+result.stdout
