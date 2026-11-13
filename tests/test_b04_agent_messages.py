"""Frozen scatter, TaskSend and MessageParent tool behavior."""

import asyncio
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import ruocun
from ruocun.tools.agent import agentTool
from ruocun.tools.types import ToolContext


def test_scatter_preserves_order_and_never_launches_cancelled_queue():
    async def scenario():
        ctx = ToolContext("synthetic")
        ready, release = asyncio.Event(), asyncio.Event()
        started = []

        async def run(request):
            started.append(request.task)
            if len(started) == 10:
                ready.set()
            await release.wait()
            return "R:" + request.task

        ctx.runAgent = run
        tasks = [f"t{index}" for index in range(15)]
        active = asyncio.create_task(agentTool.handler({"tasks": tasks}, ctx))
        try:
            async with asyncio.timeout(3):
                await ready.wait()
            assert started == tasks[:10]
            ctx.signal.set()
            release.set()
            result = await active
            assert started == tasks[:10]
            assert result.index("R:t0") < result.index("R:t9")
            assert "子代理 15/15" in result and "未启动" in result
        finally:
            release.set()
            await asyncio.gather(active, return_exceptions=True)

    asyncio.run(scenario())


_DURABLE = r'''
import asyncio,json,sys,threading
from dataclasses import replace
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
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import AgentRequest
from ruocun.tools.message_parent import messageParentTool
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.task_send import taskSendTool
from ruocun.tools.types import ToolContext

root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
(root/'alpha.txt').write_text('alpha source')
(root/'beta.txt').write_text('beta source')

def call(id,name,args):
    return {'id':id,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}

def reply(text='',*calls):
    return ResilientResult('complete',[],{'role':'assistant','content':text,'tool_calls':list(calls)},None,'stop',[],{})

async def scenario():
    session=Session('parent','synthetic',env={})
    store=await Conversation.open(root/'session','b04-43',root,runtime,session,'synthetic-key',resume=False)
    background=BackgroundRuntime(store=store,workspaceRoot=root)
    await background.bind()
    manager=TaskManager(store,background)
    ctx=ToolContext(str(root),taskManager=manager,sendToTask=manager.send)
    async def ask(_):raise AssertionError('Read and MessageParent are local allowed operations')
    permission=await createPermissionRuntime(root,root/'config',Compatibility(1,()),session,emptyPermissions(),ask,
        interactive=False,env={'ProgramData':str(root/'policy')})
    registry=ToolRegistry()
    starts={'alpha':threading.Event(),'beta':threading.Event()}
    read_entered=asyncio.Event();read_release=asyncio.Event()
    captured={'alpha':[],'beta':[]}

    async def read(args,child):
        result=await readFileTool.handler(args,child)
        if args['path']=='alpha.txt':
            read_entered.set()
            await read_release.wait()
        return result

    registry.register(replace(readFileTool,handler=read));registry.register(messageParentTool)
    options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'deepseek','model':'synthetic'}
    definition=bundledAgentDefinitions({})['general-purpose']

    def responder(label):
        def respond(opts,_):
            requests=captured[label]
            requests.append(opts['messages'])
            assert 'MessageParent' in [tool['function']['name'] for tool in opts['tools']]
            if len(requests)==1:
                assert starts[label].wait(8)
                return reply('',call(label+'-read','Read',{'path':label+'.txt'}))
            if len(requests)==2:
                return reply('',call(label+'-progress','MessageParent',{'kind':'progress','message':label+' progress'}),
                    call(label+'-attention','MessageParent',{'message':label+' question'}))
            return reply(label+' complete')
        return respond

    async def launch(label):
        args={'task':label,'background':True}
        await store.intent(label,'Agent',json.dumps(args),True)
        prepared=prepareAgentRun(session,ctx,registry,permission,options,AgentRequest(label),definition,env={},
            is_async=True,signal=threading.Event())
        task=await manager.launch(prepared,description=label,parent=store.current_agent_parent(),request=responder(label))
        await store.result(label,'started '+task.id)
        return task

    async def send(id,task,text):
        args={'id':task.id,'message':text}
        await store.intent(id,'TaskSend',json.dumps(args,ensure_ascii=False),True)
        result=await taskSendTool.handler(args,ctx)
        await store.result(id,result)
        assert '已发送给' in result

    try:
        alpha=await launch('alpha');beta=await launch('beta')
        starts['alpha'].set()
        async with asyncio.timeout(12):
            await read_entered.wait()
            await send('send-1',alpha,'first correction')
            await send('send-2',alpha,'second correction')
            await send('send-3',beta,'other correction')
            assert not background.events()
            read_release.set();starts['beta'].set()
            while alpha.status=='running' or beta.status=='running':await asyncio.sleep(.02)
        assert alpha.status==beta.status=='completed'
        for label,expected in (('alpha',['[追加指令] first correction','[追加指令] second correction']),
                               ('beta',['[追加指令] other correction'])):
            for request in captured[label][1:]:
                assert [m['content'] for m in request if m.get('role')=='user' and m['content'].startswith('[追加指令]')]==expected
        assert sorted((event.snapshot.taskId,event.message,event.snapshot.progress)
                      for event in background.events() if event.type=='message')==sorted(
            [(alpha.id,'alpha question','alpha progress'),(beta.id,'beta question','beta progress')])
        view=await store.background_view()
        assert all(not run.snapshot.get('task_inbox') for run in view.runs)
    finally:
        read_release.set()
        for gate in starts.values():gate.set()
        await manager.close();await store.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
def test_source_messages_bind_fifo_and_attention_to_the_correct_saved_run(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _DURABLE,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout


def test_source_task_send_and_message_parent_keep_direction_and_terminal_guard():
    from ruocun.tools.message_parent import messageParentTool
    from ruocun.tools.task_send import taskSendTool

    async def scenario():
        sent, resumed, reported = [], [], []

        async def send(task, message):
            sent.append((task, message))
            return task == "running"

        async def resume(task, message):
            resumed.append((task, message))
            if task == "one-shot":
                raise ValueError("一次性 agent，不支持恢复")

        async def report(message, kind):
            reported.append((message, kind))
            return True

        ctx = ToolContext("synthetic", sendToTask=send, resumeAgent=resume)
        statuses = {"ended": "completed", "one-shot": "completed", "canceling": "canceling"}
        ctx.taskManager = SimpleNamespace(get=lambda task: SimpleNamespace(status=statuses[task]) if task in statuses else None)
        assert "已发送给 running" in await taskSendTool.handler({"id": "running", "message": "纠偏"}, ctx)
        assert "无法发送" in await taskSendTool.handler({"id": "missing", "message": "x"}, ctx)
        assert "已恢复" in await taskSendTool.handler({"id": "ended", "message": "继续"}, ctx)
        assert "一次性" in await taskSendTool.handler({"id": "one-shot", "message": "继续"}, ctx)
        assert "正在取消" in await taskSendTool.handler({"id": "canceling", "message": "x"}, ctx)
        assert sent[0] == ("running", "纠偏") and resumed == [("ended", "继续"), ("one-shot", "继续")]
        assert "你不是后台子代理" in await messageParentTool.handler({"message": "x"}, ctx)
        ctx.messageParent = report
        assert "已发送" in await messageParentTool.handler({"message": "question"}, ctx)
        assert "不触发" in await messageParentTool.handler({"message": "progress", "kind": "progress"}, ctx)
        assert reported == [("question", "attention"), ("progress", "progress")]

    asyncio.run(scenario())
