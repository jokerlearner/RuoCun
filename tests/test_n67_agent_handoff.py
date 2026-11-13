"""Source foreground Agent conversion with a confirmed, real tool pair."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun

_AGENT = r'''
import asyncio,json,os,re,subprocess,sys,threading
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.run_agent import createAgentRunner
from ruocun.agent.tasks import TaskManager
from ruocun.agent.worktree import createWorktree
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import AgentRequest
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.schema import objectSchema
from ruocun.tools.types import Tool,ToolContext
from ruocun.tools.write_file import writeFileTool

root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
mode=sys.argv[4]
project=root/'project';project.mkdir()
if mode=='remote':
    subprocess.run(['git','init','-q'],cwd=project,check=True)
    subprocess.run(['git','-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid',
                    'commit','--allow-empty','-qm','synthetic base'],cwd=project,check=True)

def call(id,name,args):
    return {'id':id,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}

def reply(text='',*calls):
    return ResilientResult('complete',[],{'role':'assistant','content':text,'tool_calls':list(calls)},None,'stop',[],{})

async def scenario():
    session=Session('parent','synthetic',env={})
    store=await Conversation.open(root/'session','n67',root,runtime,session,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=store,workspaceRoot=root)
    await background.bind()
    manager=TaskManager(store,background)
    ctx=ToolContext(str(project),taskManager=manager)
    if mode=='remote':
        ctx.createWorktree=lambda name: createWorktree(project,name,environ=os.environ)
    rules=emptyPermissions();rules['allow']=['Write']
    async def ask(_):raise AssertionError('local rule already authorizes Write')
    permission=await createPermissionRuntime(project,root/'config',Compatibility(1,()),session,rules,ask,
        interactive=False,env={'ProgramData':str(root/'policy')})
    waiting=asyncio.Event();release=asyncio.Event();new_model=threading.Event();allow_new=threading.Event()
    writes=[];requests=[];rosters=[];probes=[]
    async def write(args,child):
        text=await writeFileTool.handler(args,child)
        writes.append(Path(child.cwd or child.workspaceRoot)/args['path'])
        if len(writes)==1:
            waiting.set()
            await release.wait()
        return text
    registry=ToolRegistry();registry.register(replace(writeFileTool,handler=write))
    if mode=='fork':
        async def probe(_,child):
            probes.append(child.subagentDepth)
            return 'exact tool ran'
        registry.register(Tool('ExactProbe','synthetic exact tool',objectSchema({},[]),'read','auto',probe))
        ctx.forkToolSnapshot=registry.forkSnapshot(registry.toApiTools())
    def request(opts,_):
        requests.append(opts['messages'])
        rosters.append(opts['tools'])
        if len(requests)==1:
            return reply('',call('old-write','Write',{'path':'old.txt','content':'old once'}))
        if len(requests)==2:
            new_model.set()
            assert allow_new.wait(6)
            calls=[call('new-write','Write',{'path':'new.txt','content':'new once'})]
            if mode=='fork':calls.append(call('exact','ExactProbe',{}))
            return reply('',*calls)
        return reply('background complete')
    extra={'fork':True} if mode=='fork' else ({'isolation':'remote'} if mode=='remote' else {})
    parent_call=call('parent','Agent',{'task':'write files',**extra})
    session.messages.append({'role':'assistant','content':None,'tool_calls':[parent_call]})
    await store.save(session)
    await store.intent('parent','Agent',parent_call['function']['arguments'],True)
    runner=createAgentRunner(session,ctx,registry,permission,store,
        {'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':'synthetic'},
        env={'RUOCUN_SUBAGENT_MAX_TURNS':'5'},request=request)
    active=asyncio.create_task(runner(AgentRequest('write files',**extra)))
    try:
        async with asyncio.timeout(15):
            await waiting.wait()
            old=manager.running()[0]
            convert=asyncio.create_task(manager.convert_foreground())
            await asyncio.sleep(0)
            assert not convert.done()
            release.set()
            result=await active
            new_id=re.search(r'已转后台\((agent-[a-z0-9]+)\)',result)[1]
            assert new_id!=old.id and await convert==1
            await store.result('parent',result)
            ctx.signal.set()
            assert await asyncio.to_thread(new_model.wait,6)
            allow_new.set()
            while manager.get(new_id).status=='running':
                await asyncio.sleep(.01)
        assert manager.get(new_id).status=='completed' and old.status=='completed'
        assert [path.name for path in writes]==['old.txt','new.txt']
        assert [path.read_text() for path in writes]==['old once','new once'] and writes[0].parent==writes[1].parent
        if mode=='fork':
            assert rosters[0]==rosters[1]==rosters[2] and probes==[1]
        if mode=='remote':
            assert writes[0].parent.parent==project/'.ruocun'/'worktrees' and not (project/'new.txt').exists()
            assert '改动已保留' in manager.get(new_id).result
        assert sum(m.get('tool_call_id')=='old-write' for m in requests[1])==1
        view=await store.background_view()
        old_run=next(run for run in view.runs if run.run_ref.run_id==old.runId)
        new_run=next(run for run in view.runs if run.run_ref.task_id==new_id)
        assert old_run.snapshot['handoff_to']['run_id']==new_run.run_ref.run_id and old_run.status=='completed'
        assert new_run.snapshot['recovery_material']['turnsRemaining']==2
        if mode=='fork':
            assert new_run.kind=='fork' and old_run.snapshot['forkToolDigest']==new_run.snapshot['recovery_material']['toolRosterDigest']
        if mode=='remote':
            assert old_run.snapshot['isolation_tree']==new_run.snapshot['isolation_tree']
    finally:
        release.set();allow_new.set()
        await asyncio.gather(active,return_exceptions=True)
        await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
@pytest.mark.parametrize("mode", ["plain", "fork", "remote"])
def test_source_agent_handoff_stops_at_saved_boundary_with_independent_cancellation(tmp_path, mode, monkeypatch):
    if mode == "remote":
        local_git = Path("D:/study_software/Git/cmd/git.exe")
        if local_git.is_file():
            monkeypatch.setenv("PATH", str(local_git.parent) + os.pathsep + os.environ["PATH"])
        if shutil.which("git") is None:
            pytest.skip("Git unavailable")
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _AGENT,
                             str(tmp_path), str(archive.resolve()), str(source), mode],
                            capture_output=True, text=True, encoding="utf-8", timeout=40)
    assert result.returncode == 0, result.stderr + result.stdout
