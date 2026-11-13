"""Freeze DAO's synchronous Agent result, context and tool isolation at the turn boundary."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

_CODE = r'''
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[3])
from ruocun.agent.run_agent import createAgentRunner
from ruocun.agent.agent_handoff import createAgentHandoff
from ruocun.agent.loop import run_turn
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.conversation import Conversation
from ruocun.session.contract import Intent, StoreError, ToolRef
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import agentTool
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext
from ruocun.tools.write_file import writeFileTool
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

def call(identity, name, args):
    return {'id':identity, 'type':'function','function':{'name':name,'arguments':json.dumps(args)}}

def reply(text='', *calls):
    return ResilientResult('complete', [], {'role':'assistant','content':text,'tool_calls':list(calls)}, None, 'stop', [], {})

async def scenario():
    parent=Session('parent system private text','parent/gateway-MODEL',env={})
    conversation=await Conversation.open(root/'session','agent-one',root,runtime,parent,'synthetic-key',resume=False)
    try:
        await conversation.accept_user(parent,'parent private history')
        rules=emptyPermissions();rules['allow']=['Read','Write']
        async def ask(_prompt):raise AssertionError('synthetic permission config handles approvals')
        permissions=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,
            interactive=False,env={'ProgramData':str(root/'policy')})
        registry=ToolRegistry()
        for tool in (agentTool,readFileTool,writeFileTool):registry.register(tool)
        ctx=ToolContext(str(root));captured=[];handoffs=[];loop=asyncio.get_running_loop()
        async def forged_child():
            view=await conversation.background_view();running,=view.runs
            # Even with a genuine current parent, an unrelated scope is not authorized.
            forged=Intent(ToolRef('other-scope','bad'),running.run_ref,'Write','{}','bad',True,
                'approval','policy',view.owner.owner_epoch,'synthetic',parent_tool_ref=ToolRef('main','same-id'))
            try:await conversation.worker.enqueue_intent(forged).wait()
            except StoreError as error:assert '父Agent执行授权' in str(error)
            else:raise AssertionError('cross-scope child write escaped guard')
        options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','model':parent.model}
        def child_request(opts,context):
            captured.append(opts)
            if len(captured)==1:
                asyncio.run_coroutine_threadsafe(forged_child(),loop).result(timeout=5)
                return reply('',call('same-id','Write',{'path':'made.txt','content':'child write'}))
            if len(captured)==2:return reply('SYNTHETIC-CHILD-FINAL')
            if len(captured)==3:
                return reply('',call('same-id','Write',{'path':'blocked.txt','content':'must not write'}))
            return reply('SYNTHETIC-EXPLORE-FINAL')
        async def handoff_request(opts):
            handoffs.append(opts)
            return '<decision>block</decision><reason>synthetic warning</reason>' if len(handoffs)==1 else '<decision>allow</decision>'
        handoff=createAgentHandoff(lambda:{'model':parent.model,'provider':'openai','baseUrl':options['baseUrl'],
            'apiKey':options['apiKey']},handoff_request,lambda _message:None)
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,conversation,options,
            env={'RUOCUN_EXPLORE_MODEL':'inherit'},project_instructions='SYNTHETIC PROJECT RULE',
            request=child_request,handoff=handoff)
        replies=iter([reply('',call('same-id','Agent',{'task':'independent task','model':'Vendor/Exact-Case'})),
            reply('',call('second','Agent',{'task':'explore separately','agent_type':'explore'})),reply('SYNTHETIC-PARENT-FINAL')])
        result=await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:next(replies),
            authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,permission_mode=permissions.getMode)
        assert result.status=='complete',result
        assert (root/'made.txt').read_text()=='child write' and not (root/'blocked.txt').exists()
        assert [o['model'] for o in captured]==['Vendor/Exact-Case']*2+['parent/gateway-MODEL']*2
        assert 'SYNTHETIC PROJECT RULE' in captured[0]['messages'][0]['content']
        assert 'SYNTHETIC PROJECT RULE' not in captured[2]['messages'][0]['content']
        assert all('parent private history' not in json.dumps(o['messages']) for o in captured)
        assert all('Agent' not in [t['function']['name'] for t in o['tools']] for o in captured)
        assert 'Write' not in [t['function']['name'] for t in captured[2]['tools']]
        assert parent.messages[-1]['content']=='SYNTHETIC-PARENT-FINAL'
        first,second=[m['content'] for m in parent.messages if m['role']=='tool']
        assert first.startswith('安全警告:') and 'synthetic warning' in first and first.endswith('SYNTHETIC-CHILD-FINAL')
        assert second=='SYNTHETIC-EXPLORE-FINAL'
        assert len(handoffs)==2 and handoffs[0]['model']==parent.model
        for opts in handoffs:
            text=opts['messages'][1]['content']
            assert 'parent private history' not in text and 'SYNTHETIC-CHILD-FINAL' not in text
        assert 'independent task' in handoffs[0]['messages'][1]['content']
        assert parent.model=='parent/gateway-MODEL' and not ctx.readFiles
        view=await conversation.background_view()
        same=[r for r in view.tool_records if r.tool_ref.tool_call_id=='same-id']
        assert len(same)==2 and {r.name for r in same}=={'Agent','Write'}
        assert all(r.state=='result_committed' for r in same)
    finally:await conversation.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite parent and child journals")
def test_synchronous_agent_returns_only_result_and_enforces_child_tool_scope(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _CODE, str(tmp_path), str(archive.resolve()), str(package)],
        text=True, encoding="utf-8", capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_PARALLEL = _CODE[:_CODE.index("async def scenario():")] + r'''
import threading
from dataclasses import replace

async def scenario():
    parent=Session('parent system','gateway/synthetic')
    conversation=await Conversation.open(root/'session','agent-one',root,runtime,parent,'synthetic-key',resume=False)
    try:
        await conversation.accept_user(parent,'private parent input')
        async def ask(_prompt):raise AssertionError('unexpected permission prompt')
        rules=emptyPermissions();rules['allow']=['Read','Write'];rules['defaultMode']='default'
        permissions=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,
            interactive=False,env={'ProgramData':str(root/'policy')})
        registry=ToolRegistry()
        for tool in (agentTool,readFileTool,writeFileTool):registry.register(tool)
        ctx=ToolContext(str(root));barrier=threading.Barrier(2);counts={}
        options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','model':parent.model}
        (root/'read.txt').write_text('fixture',encoding='utf-8')
        def child_request(opts,context):
            task=opts['messages'][1]['content'];counts[task]=counts.get(task,0)+1
            if task in ('fails','succeeds'):
                barrier.wait(timeout=5)
                if task=='fails':return replace(reply(),status='failed',error='synthetic child failure')
                return reply('parallel result')
            if task=='bounded':return reply('',call('read','Read',{'path':'read.txt'}))
            if task=='cancel':
                ctx.signal.set()
                assert context.cancel()
                return reply('partial',call('cancelled-write','Write',{'path':'cancelled.txt','content':'forbidden'}))
            raise AssertionError(task)
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,conversation,options,
            env={'DAO_MAX_TURNS':'99','RUOCUN_SUBAGENT_MAX_TURNS':'1','RUOCUN_MAX_PARALLEL_AGENTS':'2'},request=child_request)
        async def turn(*responses):
            replies=iter(responses)
            return await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:next(replies),
                authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,permission_mode=permissions.getMode)
        result=await turn(reply('',call('batch','Agent',{'tasks':['fails','succeeds','bounded']})),reply('parent final'))
        assert result.status=='complete'
        body=next(m['content'] for m in parent.messages if m.get('tool_call_id')=='batch')
        assert body.index('synthetic child failure')<body.index('parallel result')<body.index('已达最大轮数')
        assert counts=={'fails':1,'succeeds':1,'bounded':1} and not ctx.readFiles
        result=await turn(reply('',call('cancel','Agent',{'task':'cancel'})))
        assert result.status=='cancelled' and not (root/'cancelled.txt').exists()
        assert counts['cancel']==1
        view=await conversation.background_view()
        assert sorted(r.status for r in view.runs)==['canceled','completed','failed','failed']
        assert all(r.state=='result_committed' for r in view.tool_records)
    finally:await conversation.close()
asyncio.run(scenario())
'''


_UNKNOWN = _CODE[:_CODE.index("async def scenario():")] + r'''
from dataclasses import replace
from ruocun.session.contract import Intent, RunRef, StoreError, ToolRef

async def scenario():
    parent=Session('parent system','gateway/synthetic')
    conversation=await Conversation.open(root/'session','agent-one',root,runtime,parent,'synthetic-key',resume=False)
    try:
        await conversation.accept_user(parent,'root request')
        async def ask(_prompt):raise AssertionError('unexpected permission prompt')
        rules=emptyPermissions();rules['allow']=['Write'];rules['defaultMode']='default'
        permissions=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,
            interactive=False,env={'ProgramData':str(root/'policy')})
        registry=ToolRegistry()
        async def lost_result(args,ctx):
            await writeFileTool.handler(args,ctx)
            raise OSError('synthetic write result lost after filesystem mutation')
        registry.register(agentTool);registry.register(replace(writeFileTool,handler=lost_result))
        ctx=ToolContext(str(root));options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','model':parent.model}
        def request_child(_opts,_context):return reply('',call('write','Write',{'path':'once.txt','content':'actual effect'}))
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,conversation,options,env={},request=request_child)
        reply_parent=reply('',call('agent','Agent',{'task':'run one write'}))
        result=await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:reply_parent,
            authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,permission_mode=permissions.getMode)
        assert result.status=='outcome_unknown' and conversation.blocked
        assert (root/'once.txt').read_text()=='actual effect'
        view=await conversation.background_view();run,=view.runs
        assert run.status=='unknown'
        assert [(record.name,record.state) for record in view.tool_records]==[('Agent','started'),('Write','started')]
        assert not [m for m in parent.messages if m.get('tool_call_id')=='agent']
        # Directly attempt a forged child delegation against the real store.
        forged=Intent(ToolRef('unrelated-scope','bad'),RunRef(run.run_ref.task_id,run.run_ref.run_id),'Write','{}','bad',True,
            'approval','policy',view.owner.owner_epoch,'synthetic',parent_tool_ref=ToolRef('main','agent'))
        try:await conversation.worker.enqueue_intent(forged).wait()
        except StoreError:pass
        else:raise AssertionError('unrelated scope escaped unknown guard')
    finally:await conversation.close()
    resumed=Session('parent system','gateway/synthetic')
    reopened=await Conversation.open(root/'session','agent-one',root,runtime,resumed,'synthetic-key',resume=True)
    try:
        assert reopened.blocked and (root/'once.txt').read_text()=='actual effect'
        assert {r.state for r in (await reopened.background_view()).tool_records}=={'outcome_unknown'}
    finally:await reopened.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite child journal")
@pytest.mark.parametrize("scenario", [_PARALLEL, _UNKNOWN], ids=["parallel-cancel-budget", "unknown-effect"])
def test_synchronous_agent_parallel_failure_cancellation_and_unknown_effect(tmp_path, scenario):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", scenario, str(tmp_path), str(archive.resolve()), str(package)],
        text=True, encoding="utf-8", capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_RESULT_ACK_LOST = (
    _UNKNOWN[:_UNKNOWN.index("        async def lost_result(args,ctx):")]
    + r'''
        from ruocun.session.durable_store import DurableStore
        from ruocun.session.sqlite_port import CommitUnconfirmedError
        original = DurableStore.commit_result_and_event
        effects = []
        attempts = []
        async def count_actual_write(args, ctx):
            result = await writeFileTool.handler(args, ctx)
            effects.append(result)
            return result
        def lose_result_receipt(port, owner, ref, result, run_update, event, **kwargs):
            if ref.scope != 'main' and ref.tool_call_id == 'write':
                attempts.append(result)
                if sys.argv[4] == 'committed':
                    original(port, owner, ref, result, run_update, event, **kwargs)
                raise CommitUnconfirmedError('synthetic lost SQLite result receipt')
            return original(port, owner, ref, result, run_update, event, **kwargs)
        DurableStore.commit_result_and_event = lose_result_receipt
        registry.register(agentTool);registry.register(replace(writeFileTool,handler=count_actual_write))
'''
    + _UNKNOWN[_UNKNOWN.index("        ctx=ToolContext"):]
).replace(
    "        assert run.status=='unknown'\n"
    "        assert [(record.name,record.state) for record in view.tool_records]==[('Agent','started'),('Write','started')]",
    """        child_state = 'result_committed' if sys.argv[4] == 'committed' else 'started'
        assert run.status=='running' and attempts==effects and len(effects)==1
        assert [(record.name,record.state) for record in view.tool_records]==[('Agent','started'),('Write',child_state)]
        if child_state=='result_committed':assert view.tool_records[1].result==effects[0]""",
).replace(
    "        assert {r.state for r in (await reopened.background_view()).tool_records}=={'outcome_unknown'}",
    """        await reopened.worker.enqueue_prepare_recovery().wait()
        await reopened.refresh_recovery(resumed)
        view = await reopened.background_view()
        recovered, = view.runs
        assert recovered.run_ref==run.run_ref
        committed = sys.argv[4] == 'committed'
        assert recovered.status==('interrupted' if committed else 'unknown')
        assert [(record.name,record.state) for record in view.tool_records]==[
            ('Agent','outcome_unknown'),('Write','result_committed' if committed else 'outcome_unknown')]
        if committed:assert view.tool_records[1].result==effects[0]
        assert attempts==effects and len(effects)==1 and reopened.blocked""",
)


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite result acknowledgement")
@pytest.mark.parametrize("receipt", ["unconfirmed", "committed"])
def test_synchronous_agent_preserves_exact_child_result_when_receipt_is_lost(tmp_path, receipt):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _RESULT_ACK_LOST,
         str(tmp_path), str(archive.resolve()), str(package), receipt],
        text=True, encoding="utf-8", capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_INTERRUPTED_SYNC = _CODE[:_CODE.index("async def scenario():")] + r'''
import os, threading
from dataclasses import replace
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.bundled_agents import bundledAgentDefinitions
from ruocun.agent.resume_agent import continuationMessages, restorePreparedContinuation
from ruocun.agent.run_agent import prepareAgentRun
from ruocun.agent.tasks import TaskManager
from ruocun.session.recovery import RecoveryController
from ruocun.tools.agent import AgentRequest
from ruocun.tools.plan_mode import enterPlanModeTool, exitPlanModeTool
from ruocun.tools.tool_search import toolSearchTool

async def scenario():
    resume=sys.argv[4]=='resume'
    parent=Session('parent prompt','gateway/synthetic',env={})
    store=await Conversation.open(root/'session','sync-recovery',root,runtime,parent,'synthetic-key',resume=resume)
    registry=ToolRegistry()
    for tool in (agentTool,writeFileTool,toolSearchTool,enterPlanModeTool,exitPlanModeTool,
                 replace(readFileTool,name='PlanScopedRead',shouldDefer=True),
                 replace(readFileTool,name='UntouchedDeferred',shouldDefer=True)):registry.register(tool)
    rules=emptyPermissions();rules['allow']=['Write','ToolSearch','EnterPlanMode','PlanScopedRead'];rules['defaultMode']='default'
    async def ask(_):raise AssertionError('expected local policy')
    permissions=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,
        interactive=False,env={'ProgramData':str(root/'policy')})
    options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':parent.model}
    ctx=ToolContext(str(root));env={'RUOCUN_SUBAGENT_MAX_TURNS':'6'};requests=[]
    if not resume:
        await store.accept_user(parent,'run sync Agent')
        def request(opts,_):
            requests.append(opts)
            if len(requests)==1:return reply('',call('old-write','Write',{'path':'old.txt','content':'original effect'}))
            if len(requests)==2:return reply('',call('activate','ToolSearch',{'query':'plan'}))
            if len(requests)==3:return reply('',call('enter-plan','EnterPlanMode',{}))
            assert len(requests)==4 and any(m.get('tool_call_id')=='old-write' for m in opts['messages'])
            assert any(m.get('tool_call_id')=='enter-plan' and '已进入规划模式' in m['content'] for m in opts['messages'])
            assert [t['function']['name'] for t in opts['tools']]==['ToolSearch','EnterPlanMode','ExitPlanMode','PlanScopedRead']
            os._exit(42)
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,store,options,env=env,request=request)
        await run_turn(parent,options,registry,ctx,approve=ask,journal=store,
            request=lambda _o,_c:reply('',call('old-parent','Agent',{'task':'run original sync task'})),
            authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,
            permission_mode=permissions.getMode)
        raise AssertionError('did not interrupt actual owner')

    bg=BackgroundRuntime(store=store,workspaceRoot=root);manager=TaskManager(store,bg)
    recovery=RecoveryController(store,parent,bg,activate_continuation=manager.activate_continuation)
    staged={}
    definition=bundledAgentDefinitions(env)['general-purpose']
    def request(opts,_):
        requests.append(opts)
        if len(requests)==1:return reply('',call('forbidden','Write',{'path':'forbidden.txt','content':'must not run'}),
                                        call('read-old','PlanScopedRead',{'path':'old.txt'}))
        return reply('continued sync result')
    async def validate(candidate):
        from ruocun.agent.resume_agent import continuationToolPolicy
        messages=await continuationMessages(store,candidate)
        assert continuationToolPolicy(candidate)=='synchronous'
        prepared=prepareAgentRun(parent,ctx,registry,permissions,options,AgentRequest(candidate.instruction),definition,
            env=env,signal=threading.Event(),initial_messages=messages,is_async=False)
        restorePreparedContinuation(prepared,candidate)
        assert prepared.permission.getMode()=='plan' and prepared.ctx.setMode is not None
        staged[candidate.new_run]=prepared
    async def stage(candidate):
        return await manager.continue_run(staged.pop(candidate.new_run),candidate,request=request)
    recovery.validate_continuation=validate;recovery.continue_agent=stage
    try:
        await recovery.recover();await manager.bind()
        initial=await store.background_view();old,=initial.runs
        assert old.status=='interrupted' and store.blocked
        material=old.snapshot['recovery_material']
        assert material['toolPolicy']=='synchronous' and material['turnsRemaining']==2
        assert material['permissions']['mode']=='plan' and material['requestedMode'] is None
        assert material['turnLimit']==6 and material['toolRoster']==['ToolSearch','EnterPlanMode','ExitPlanMode','PlanScopedRead']
        assert any(m.get('tool_call_id')=='old-write' for m in material['messages'])
        old_file=root/'old.txt';old_stat=old_file.stat()
        command=f'/recovery continue {old.run_ref.task_id} finish new work'
        try:await recovery.command(command)
        except ValueError as error:assert '未决' in str(error)
        else:raise AssertionError('original parent effect was not resolved')
        assert not requests
        await recovery.command('/recovery resolve main old-parent original write confirmed')
        assert '新run' in await recovery.command(command)
        async with asyncio.timeout(8):
            while manager.get(old.run_ref.task_id).status!='completed':await asyncio.sleep(.01)
        await recovery.command(command)
        assert len(requests)==2 and requests[0]['messages'][-1]=={'role':'user','content':'finish new work'}
        assert [t['function']['name'] for t in requests[0]['tools']]==material['toolRoster']
        assert any(m.get('tool_call_id')=='forbidden' and '只读' in m['content'] for m in requests[1]['messages'])
        assert not (root/'forbidden.txt').exists()
        assert any(m.get('tool_call_id')=='old-write' for m in requests[0]['messages'])
        assert any(m.get('tool_call_id')=='read-old' and 'original effect' in m['content'] for m in requests[1]['messages'])
        assert old_file.read_text()=='original effect' and old_file.stat().st_mtime_ns==old_stat.st_mtime_ns
        final=await store.background_view()
        assert len(final.runs)==2 and len([r for r in final.tool_records if r.name=='Write'])==1
        old_record=next(run for run in final.runs if run.run_ref==old.run_ref)
        new_record=next(run for run in final.runs if run.run_ref!=old.run_ref)
        assert old_record.status=='interrupted' and new_record.status=='completed'
        assert new_record.snapshot['recovery_material']['toolPolicy']=='synchronous'
        assert new_record.snapshot['recovery_material']['turnsRemaining']==0
    finally:await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite interrupted owner")
def test_interrupted_synchronous_agent_preserves_tool_policy_and_remaining_turns(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    source = Path(ruocun.__file__).resolve().parents[1]
    args = [sys.executable, "-I", "-X", "utf8", "-c", _INTERRUPTED_SYNC,
            str(tmp_path), str(archive.resolve()), str(source)]
    seed = subprocess.run([*args, "seed"], text=True, encoding="utf-8", capture_output=True, timeout=45)
    assert seed.returncode == 42, seed.stderr + seed.stdout
    resumed = subprocess.run([*args, "resume"], text=True, encoding="utf-8", capture_output=True, timeout=45)
    assert resumed.returncode == 0, resumed.stderr + resumed.stdout


_LIFECYCLE_HOOKS = _CODE[:_CODE.index("async def scenario():")] + r'''
import os, threading, time
from dataclasses import replace
from ruocun.agent.agent_defs import AgentDefinition
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.run_agent import prepareAgentRun
from ruocun.agent.tasks import TaskManager
from ruocun.hooks.hooks import HookRuntime, HookSpec
from ruocun.tools.agent import AgentRequest

async def scenario():
    script=root/'agent-hook.py'
    script.write_text("""import json, os, pathlib, sys
data = json.load(sys.stdin)
event = os.environ['RUOCUN_HOOK_EVENT']
if event == 'PreToolUse':
 pathlib.Path('forbidden-parent-hook').touch()
else:
 assert data['hook_event_name'] == event and data['agent_type'] == 'hooked'
 with pathlib.Path('hook-order').open('a', encoding='utf-8') as out:
  print(event + ':' + data['agent_id'], file=out)
 print('source ' + event)
""", encoding='utf-8')
    command=f'"{sys.executable}" -I -X utf8 "{script}"'
    definition=AgentDefinition('hooked','child system',source='userSettings',
        hooks={'SubagentStart':(command,), 'SubagentStop':(command,)})
    parent=Session('parent system','gateway/synthetic',env={})
    conversation=await Conversation.open(root/'session','lifecycle-hooks',root,runtime,parent,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=conversation,workspaceRoot=root)
    manager=TaskManager(conversation,background)
    ctx=ToolContext(str(root),toolHooks=HookRuntime([HookSpec('PreToolUse',matcher='^Read$',command=command)],os.environ))
    ctx.agentHookRuntime=lambda active: HookRuntime([HookSpec(event,command=cmd)
        for event,commands in active.hooks.items() for cmd in commands],os.environ)
    options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':parent.model}
    registry=ToolRegistry();registry.register(agentTool);registry.register(readFileTool)
    rules=emptyPermissions();rules['allow']=['Read'];rules['defaultMode']='default'
    async def ask(*_):raise AssertionError('fixture uses explicit Read grant')
    permits=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,
        interactive=False,env={'ProgramData':str(root/'policy')})
    (root/'value.txt').write_text('scoped file',encoding='utf-8')
    try:
        await background.bind()
        await conversation.accept_user(parent,'run child')
        child_requests=[]
        def child_request(opts,_context):
            child_requests.append(opts['messages'])
            assert sum(m.get('content')=='[hook 注入的上下文]\nsource SubagentStart' for m in opts['messages'])==1
            assert all('source SubagentStop' not in str(m.get('content','')) for m in opts['messages'])
            if len(child_requests)==1:return reply('',call('read','Read',{'path':'value.txt'}))
            return reply('child completed')
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permits,conversation,options,env={},
            request=child_request,definitions={'hooked':definition})
        responses=iter([reply('',call('fg-parent','Agent',{'task':'run fg','agent_type':'hooked'})),reply('parent done')])
        foreground=await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:next(responses),
            authorize_batch=permits.authorizeBatch,call_scope=permits.callScope,permission_mode=permits.getMode)
        assert foreground.status=='complete' and len(child_requests)==2
        assert not (root/'forbidden-parent-hook').exists()
        assert any('scoped file' in m.get('content','') for m in child_requests[-1] if m['role']=='tool')
        assert all('source Subagent' not in str(m.get('content','')) for m in parent.messages)

        background_call=call('bg-parent','Agent',{'task':'run bg','agent_type':'hooked','background':True})
        parent.messages.append({'role':'assistant','content':None,'tool_calls':[background_call]})
        await conversation.save(parent)
        await conversation.intent('bg-parent','Agent',background_call['function']['arguments'],True)
        prepared=prepareAgentRun(parent,ctx,registry,permits,options,AgentRequest('run bg','hooked'),definition,
            env={},is_async=True,signal=threading.Event())
        ready=threading.Event()
        def background_request(opts,control):
            assert opts['messages'][-1]['content']=='[hook 注入的上下文]\nsource SubagentStart'
            ready.set()
            deadline=time.monotonic()+5
            while not control.cancel() and time.monotonic()<deadline:time.sleep(.01)
            assert control.cancel()
            return replace(reply(),cancelled=True)
        task=await manager.launch(prepared,description='run bg',parent=ToolRef('main','bg-parent'),request=background_request)
        await conversation.result('bg-parent','background accepted')
        parent.messages.append({'role':'tool','tool_call_id':'bg-parent','content':'background accepted'})
        await conversation.save(parent)
        assert await asyncio.to_thread(ready.wait,5)
        await conversation.intent('stop','TaskStop',json.dumps({'id':task.id}),True)
        assert await manager.cancel(task.id)=='canceling'
        async with asyncio.timeout(8):
            while task.status=='canceling':await asyncio.sleep(.01)
        assert task.status=='canceled',task.error
        await conversation.result('stop','cancellation requested')
        view=await conversation.background_view()
        synced=next(r for r in view.runs if r.snapshot.get('foreground') is True)
        assert synced.status=='completed'
        expected=['SubagentStart:'+synced.run_ref.task_id,'SubagentStop:'+synced.run_ref.task_id,
                  'SubagentStart:'+task.id,'SubagentStop:'+task.id]
        assert (root/'hook-order').read_text('utf-8').splitlines()==expected
        for scope in (synced.run_ref.run_id,task.runId):
            records=[tool for tool in view.tool_records if tool.tool_ref.scope==scope and tool.name.startswith('Subagent')]
            assert [(tool.name,tool.state,tool.intent.side_effect) for tool in records]==[
                ('SubagentStart','result_committed',True),('SubagentStop','result_committed',True)]
        assert not conversation.blocked

        from ruocun.agent.tasks import _Journal
        enter, release=asyncio.Event(),asyncio.Event()
        original_intent=_Journal.intent
        async def delay_start(self, call_id, name, args, effect):
            if name=='SubagentStart':
                enter.set()
                await release.wait()
            return await original_intent(self,call_id,name,args,effect)
        def forbidden_model(*_):
            raise AssertionError('cancel before admission cannot start a model')
        early_call=call('early-parent','Agent',{'task':'cancel before start','agent_type':'hooked','background':True})
        parent.messages.append({'role':'assistant','content':None,'tool_calls':[early_call]})
        await conversation.save(parent)
        await conversation.intent('early-parent','Agent',early_call['function']['arguments'],True)
        early=prepareAgentRun(parent,ctx,registry,permits,options,AgentRequest('cancel before start','hooked'),definition,
            env={},is_async=True,signal=threading.Event())
        _Journal.intent=delay_start
        try:
            early_task=await manager.launch(early,description='cancel before start',parent=ToolRef('main','early-parent'),
                                            request=forbidden_model)
            await conversation.result('early-parent','background accepted')
            async with asyncio.timeout(5):
                await enter.wait()
            await conversation.intent('early-stop','TaskStop',json.dumps({'id':early_task.id}),True)
            assert await manager.cancel(early_task.id)=='canceling'
            release.set()
            async with asyncio.timeout(8):
                while early_task.status=='canceling':await asyncio.sleep(.01)
            assert early_task.status=='canceled',early_task.error
            await conversation.result('early-stop','cancellation requested')
        finally:
            release.set()
            _Journal.intent=original_intent
        assert (root/'hook-order').read_text('utf-8').splitlines()==[*expected,'SubagentStop:'+early_task.id]
        early_records=[tool for tool in (await conversation.background_view()).tool_records
                       if tool.tool_ref.scope==early_task.runId]
        assert [(tool.name,tool.state) for tool in early_records]==[('SubagentStop','result_committed')]
        assert not conversation.blocked
    finally:
        await manager.close()
        await conversation.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real Windows hook commands and scoped SQLite receipts")
def test_source_agent_lifecycle_hooks_start_before_model_and_stop_on_cancel(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    source = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _LIFECYCLE_HOOKS,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=45)
    assert result.returncode == 0, result.stderr + result.stdout
