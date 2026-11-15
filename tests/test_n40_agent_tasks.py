"""Frozen TaskOutput/TaskStop and lifecycle semantics on the durable event path."""

import asyncio
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import ruocun


def test_source_task_output_cursor_and_task_stop_channel():
    from ruocun.agent.runtime_context import buildRuntimeContext
    from ruocun.agent.tasks import BgTask
    from ruocun.tools.task_output import taskOutputTool
    from ruocun.tools.task_stop import taskStopTool
    from ruocun.tools.types import ToolContext

    async def scenario():
        task = BgTask("agent-1", "run-1", "agent", "synthetic", "running")
        tasks = {task.id: task}

        async def cancel(task_id):
            entry = tasks.get(task_id)
            if entry is None or entry.status != "running":
                return None
            entry.status = "canceled" if entry.kind == "manual" else "canceling"
            return entry.status

        ctx = SimpleNamespace(workspaceRoot="/synthetic", taskManager=SimpleNamespace(get=tasks.get, cancel=cancel))
        task.messages.extend([
            buildRuntimeContext(ToolContext("synthetic-runtime")),
            {"role": "assistant", "content": "开始探索代码库"},
            {"role": "assistant", "tool_calls": [{"function": {"name": "Grep", "arguments": '{"pattern":"foo"}'}}]},
        ])
        args = {"id": task.id}
        first = await taskOutputTool.handler(args, ctx)
        assert "开始探索" in first and "Grep" in first
        assert "<ruocun-runtime-context>" not in first
        assert "没有新消息" in await taskOutputTool.handler(args, ctx)
        task.messages.append({"role": "tool", "content": "match: foo.ts:12"})
        third = await taskOutputTool.handler(args, ctx)
        assert "foo.ts:12" in third and "Grep" not in third
        assert "已请求取消" in await taskStopTool.handler(args, ctx)
        assert "未生效" in await taskStopTool.handler(args, ctx)
        tasks[task.id] = BgTask(task.id, "run-2", "agent", "next run", "completed", messages=[{"role": "assistant", "content": "new identity"}])
        assert "new identity" in await taskOutputTool.handler(args, ctx)
        manual = BgTask("manual", "run-3", "manual", "manual", "running")
        tasks[manual.id] = manual
        assert "TaskGet" in await taskOutputTool.handler({"id": manual.id}, ctx)
        assert "已取消" in await taskStopTool.handler({"id": manual.id}, ctx)
        assert "未找到" in await taskOutputTool.handler({"id": "missing"}, ctx)

    asyncio.run(scenario())


_SQLITE = r'''
import asyncio,json,sys,threading,time
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.bundled_agents import bundledAgentDefinitions
from ruocun.agent.run_agent import prepareAgentRun
from ruocun.agent.tasks import TaskManager
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.contract import RunRef,ToolRef
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import AgentRequest
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.task_output import taskOutputTool
from ruocun.tools.task_stop import taskStopTool
from ruocun.tools.types import Tool,ToolContext
from ruocun.tools.write_file import writeFileTool
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

def call(id,name,args):
    return {'id':id,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}

def reply(text='',*calls,cancelled=False):
    return ResilientResult('complete',[],{'role':'assistant','content':text,'tool_calls':list(calls)},None,'stop',[],{},cancelled=cancelled)

async def scenario():
    session=Session('parent system','synthetic',env={})
    store=await Conversation.open(root/'session','n40',root,runtime,session,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=store,workspaceRoot=root)
    await background.bind()
    manager=TaskManager(store,background)
    ctx=ToolContext(str(root));ctx.taskManager=manager
    async def ask(_):raise AssertionError('local rule already authorizes Write')
    rules=emptyPermissions();rules['allow']=['Write']
    permission=await createPermissionRuntime(root,root/'config',Compatibility(1,()),session,rules,ask,
        interactive=False,env={'ProgramData':str(root/'policy')})
    registry=ToolRegistry();registry.register(writeFileTool)
    options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':'synthetic'}
    definitions=bundledAgentDefinitions({})
    async def wait_for(check):
        async with asyncio.timeout(8):
            while not check():await asyncio.sleep(.01)
    async def launch(id,task,request,*,agent_type='general-purpose',explicit=True):
        args={'task':task,'agent_type':agent_type,**({'background':True} if explicit else {})}
        request_message=call(id,'Agent',args)
        session.messages.append({'role':'assistant','content':None,'tool_calls':[request_message]})
        await store.save(session)
        await store.intent(id,'Agent',request_message['function']['arguments'],True)
        prepared=prepareAgentRun(session,ctx,registry,permission,options,AgentRequest(task,agent_type),
            definitions[agent_type],env={},signal=threading.Event(),is_async=True)
        entry=await manager.launch(prepared,description=task,parent=store.current_agent_parent(),request=request)
        await store.result(id,'started '+entry.id)
        session.messages.append({'role':'tool','tool_call_id':id,'content':'started '+entry.id})
        await store.save(session)
        return entry
    start=threading.Event();after_write=threading.Event();stopping=threading.Event();stop_ack=threading.Event()
    count=0
    def work(options,context):
        nonlocal count
        count+=1
        if count==1:
            if not start.wait(8):raise RuntimeError('synthetic barrier timed out')
            return reply('',call('write1','Write',{'path':'once.txt','content':'only once'}))
        if not after_write.wait(8):raise RuntimeError('synthetic barrier timed out')
        return reply('DONE FROM SAME RUN')
    def delayed_stop(options,context):
        deadline=time.monotonic()+8
        stopping.set()
        while not context.cancel() and time.monotonic()<deadline:time.sleep(.01)
        if not context.cancel() or not stop_ack.wait(8):raise RuntimeError('missing abort acknowledgement')
        return reply(cancelled=True)
    try:
        first=await launch('bg-parent','synthetic write',work)
        handle,ready=background.prepare({'ids':[first.id],'mode':'all'});assert not ready
        start.set()
        await wait_for(lambda: (root/'once.txt').exists() and any(m.get('role')=='tool' for m in first.messages))
        text=await taskOutputTool.handler({'id':first.id},ctx)
        assert 'Write' in text and '没有新消息' in await taskOutputTool.handler({'id':first.id},ctx)
        assert await manager.emitFromTask(RunRef(first.id,first.runId),'attention')
        assert background.ready(handle)
        after_write.set()
        await wait_for(lambda:first.status=='completed')
        view=await store.background_view()
        by_scope={r.tool_ref.scope:r for r in view.tool_records}
        assert by_scope[first.runId].state=='result_committed' and by_scope[first.runId].intent.parent_tool_ref==ToolRef('main','bg-parent')
        assert count==2 and (root/'once.txt').read_text()=='only once'
        assert [event.type for event in background.events() if event.snapshot.runId==first.runId]==['message','completed']
        second=await launch('stop-parent','synthetic stop',delayed_stop,agent_type='verify',explicit=False)
        await wait_for(stopping.is_set)
        msg=await taskStopTool.handler({'id':second.id},ctx)
        assert '已请求取消' in msg and second.status=='canceling'
        db=next(run for run in (await store.background_view()).runs if run.run_ref.run_id==second.runId)
        assert db.status=='canceling' and db.cancel_requested and db.snapshot['background_by_definition']
        stop_ack.set()
        await wait_for(lambda:second.status=='canceled')
        assert [event.type for event in background.events() if event.snapshot.runId==second.runId]==['canceled']
        assert '未生效' in await taskStopTool.handler({'id':second.id},ctx)
        assert not store.blocked
        entered,release=asyncio.Event(),asyncio.Event()
        async def lost_write(args,_ctx):
            (root/'unknown.txt').write_text('applied once')
            entered.set()
            await release.wait()
            raise RuntimeError('synthetic write receipt lost')
        registry.register(Tool('Write','synthetic write receipt failure',writeFileTool.schema,'write','auto',lost_write))
        third=await launch('unknown-parent','synthetic unknown write',
            lambda _o,_c:reply('',call('unknown-write','Write',{'path':'unknown.txt','content':'applied once'})))
        try:
            await asyncio.wait_for(entered.wait(),8)
            stop=call('stop-unknown','TaskStop',{'id':third.id})
            session.messages.append({'role':'assistant','content':None,'tool_calls':[stop]})
            await store.save(session)
            await store.intent('stop-unknown','TaskStop',stop['function']['arguments'],True)
            stop_result=await taskStopTool.handler({'id':third.id},ctx)
            assert '已请求取消' in stop_result and third.status=='canceling'
            await store.result('stop-unknown',stop_result)
        finally:
            release.set()
        await wait_for(lambda:third.status=='unknown')
        assert [event.type for event in background.events() if event.snapshot.runId==third.runId]==['unknown']
        assert store.blocked and (root/'unknown.txt').read_text()=='applied once'
        unknown=next(record for record in (await store.background_view()).tool_records if record.tool_ref.scope==third.runId)
        assert unknown.state=='started' and unknown.name=='Write'
        print('authenticated launch / child receipt after parent ack / TaskWait attention / confirmed cancel')
    finally:
        start.set();after_write.set();stop_ack.set()
        await manager.close()
        await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
def test_source_background_writes_after_parent_receipt_and_waits_for_stop_ack(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _SQLITE,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout


_RECOVERY = _SQLITE[:_SQLITE.index("async def scenario():")] + r'''
from dataclasses import asdict
from ruocun.agent.background_types import ExecutionSnapshot
from ruocun.agent.resume_agent import agentRecoveryMaterial,continuationMessages,validatePreparedContinuation
from ruocun.session.contract import RunRecord
from ruocun.session.recovery import RecoveryController
from ruocun.agent.runtime_context import isRuntimeContext

async def scenario():
    session=Session('parent system','synthetic',env={})
    store=await Conversation.open(root/'session','n40-resume',root,runtime,session,'synthetic-key',resume=False)
    rules=emptyPermissions();rules['allow']=['Write']
    async def ask(_):raise AssertionError('local rule already authorizes Write')
    async def permission():
        return await createPermissionRuntime(root,root/'config',Compatibility(1,()),session,rules,ask,
            interactive=False,env={'ProgramData':str(root/'policy')})
    registry=ToolRegistry();registry.register(writeFileTool)
    options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':'synthetic'}
    definition=bundledAgentDefinitions({})['general-purpose']
    ctx=ToolContext(str(root));permit=await permission()
    parent_call=call('old-parent','Agent',{'task':'original','background':True})
    session.messages.append({'role':'assistant','content':None,'tool_calls':[parent_call]})
    await store.save(session)
    await store.intent('old-parent','Agent',parent_call['function']['arguments'],True)
    child=prepareAgentRun(session,ctx,registry,permit,options,AgentRequest('original'),definition,
                         env={},signal=threading.Event(),is_async=True)
    old=RunRef('agent-old','old-run')
    old_call=call('old-write','Write',{'path':'old.txt','content':'preserved'})
    child.session.messages.extend([{'role':'assistant','content':None,'tool_calls':[old_call]},
                                  {'role':'tool','tool_call_id':'old-write','content':'known old result'}])
    material=agentRecoveryMaterial(child);material['turnsRemaining']=3
    material.pop('toolPolicy')  # The original format-1 background checkpoint did not include this field.
    snap=ExecutionSnapshot(old.task_id,old.run_id,'agent',True,'original','running')
    await store.publish_background(RunRecord(old,'agent','running',False,{'parent_tool_ref':asdict(ToolRef('main','old-parent')),
        'background_agent_epoch':store.owner_epoch,'background_by_definition':False,'description':'original','agentType':'general-purpose',
        'messages':child.session.messages,'output_start':2,'recovery_material':material,'background_execution':asdict(snap)}),None)
    await store.result('old-parent','started agent-old')
    session.messages.append({'role':'tool','tool_call_id':'old-parent','content':'started agent-old'})
    await store.save(session)
    (root/'old.txt').write_text('preserved')
    old_epoch=store.owner_epoch
    await store.close()

    session=Session('parent system','synthetic',env={})
    store=await Conversation.open(root/'session','n40-resume',root,runtime,session,'synthetic-key',resume=True)
    background=BackgroundRuntime(store=store,workspaceRoot=root);manager=TaskManager(store,background)
    controller=RecoveryController(store,session,background,activate_continuation=manager.activate_continuation)
    staged={};requests=[]
    def request(opts,_context):
        requests.append(opts['messages'])
        if len(requests)==1:
            return reply('',call('new-write','Write',{'path':'new.txt','content':'new once'}))
        return reply('resumed completion')
    async def validate(candidate):
        messages=await continuationMessages(store,candidate)
        prepared=prepareAgentRun(session,ctx,registry,await permission(),options,AgentRequest(candidate.instruction),definition,
            env={},signal=threading.Event(),initial_messages=messages,is_async=True)
        validatePreparedContinuation(prepared,candidate)
        staged[candidate.new_run]=prepared
    async def proceed(candidate):
        return await manager.continue_run(staged.pop(candidate.new_run),candidate,request=request)
    controller.validate_continuation=validate;controller.continue_agent=proceed
    try:
        await controller.recover();await manager.bind()
        assert manager.get(old.task_id).status=='interrupted' and not requests and store.owner_epoch>old_epoch
        assert '新run' in await controller.command('/recovery continue agent-old continue explicitly')
        async with asyncio.timeout(8):
            while manager.get(old.task_id).status!='completed':await asyncio.sleep(.01)
        task=manager.get(old.task_id)
        assert task.runId!=old.run_id and len(requests)==2
        assert any(m.get('content')=='known old result' for m in requests[0])
        assert [m for m in requests[0] if not isRuntimeContext(m)][-1]=={'role':'user','content':'continue explicitly'}
        assert isRuntimeContext(requests[0][-1])
        assert (root/'new.txt').read_text()=='new once' and (root/'old.txt').read_text()=='preserved'
        await controller.command('/recovery continue agent-old continue explicitly')
        assert len(requests)==2
        view=await store.background_view()
        assert next(r for r in view.runs if r.run_ref==old).status=='interrupted'
        new=next(r for r in view.runs if r.run_ref.run_id==task.runId)
        assert new.snapshot['recovery_material']['turnsRemaining']==1 and new.status=='completed'
        assert new.snapshot['recovery_material']['toolPolicy']=='background'
        assert any(record.tool_ref.scope==task.runId and record.name=='Write' for record in view.tool_records)
        print('old checkpoint imported / explicit new owner and run / original tool pair preserved / duplicate decision not dispatched')
    finally:
        await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
def test_source_explicit_agent_continuation_uses_new_run_and_saved_tool_pairs(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _RECOVERY,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout
