"""Frozen runAgent.ts named-MCP initialization and per-owner final cleanup."""

import subprocess
import sys
from pathlib import Path

import ruocun

_CODE = r'''
import asyncio,json,os,sys,threading
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.agent_defs import AgentDefinition
from ruocun.agent.agent_mcp import createAgentMcpFactory
from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.loop import run_turn
from ruocun.agent.run_agent import createAgentRunner,prepareAgentRun,openPreparedAgentMcp,closePreparedAgentMcp,_background_prepared
from ruocun.agent.tasks import TaskManager
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.contract import ToolRef
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import agentTool,AgentRequest,AgentFailure
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext
root=Path(sys.argv[1]);fixture=Path(sys.argv[4])
runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))
def call(id,name,args):return {'id':id,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}
def reply(text='',*calls):return ResilientResult('complete',[],{'role':'assistant','content':text,'tool_calls':list(calls)},None,'stop',[],{})
async def scenario():
 parent=Session('parent','synthetic',env={})
 store=await Conversation.open(root/'session','agent-mcp',root,runtime,parent,'synthetic-key',resume=False)
 try:
  await store.accept_user(parent,'parent request')
  rules=emptyPermissions();rules['allow']=['Agent','mcp__dedicated__echo','mcp__dedicated__crash']
  async def ask(_prompt):raise AssertionError('no synthetic approval needed')
  permits=await createPermissionRuntime(root,root/'config',Compatibility(1,()),parent,rules,ask,interactive=False,env={})
  registry=ToolRegistry();registry.register(agentTool)
  ctx=ToolContext(str(root))
  config={'mcpServers':{'dedicated':{'command':sys.executable,'args':['-I','-X','utf8',str(fixture),str(root/'server')]},
                        'broken':{'command':str(root/'not-an-executable.exe')}}}
  ctx.agentMcpRuntime=createAgentMcpFactory(config,dict(os.environ),redact=store.redact)
  definition=AgentDefinition('dedicated','dedicated role',tools=('Read',),mcp_servers=('absent','broken','dedicated'))
  options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','provider':'openai','model':'synthetic'}
  captured=[]
  def child_request(opts,_context):
   captured.append(opts)
   assert 'mcp__dedicated__echo' in [t['function']['name'] for t in opts['tools']]
   return reply('',call('child-mcp','mcp__dedicated__echo',{'msg':'dedicated success'})) if len(captured)==1 else reply('CHILD-DONE')
  ctx.runAgent=createAgentRunner(parent,ctx,registry,permits,store,options,env=dict(os.environ),
                                definitions={'dedicated':definition},request=child_request)
  replies=iter([reply('',call('parent-agent','Agent',{'task':'child task','agent_type':'dedicated'})),reply('PARENT-DONE')])
  result=await run_turn(parent,options,registry,ctx,approve=ask,journal=store,request=lambda *_a:next(replies),
                        authorize_batch=permits.authorizeBatch,call_scope=permits.callScope,permission_mode=permits.getMode)
  assert result.status=='complete',result
  assert len(captured)==2,store.redacted_messages(parent.messages)
  view=await store.background_view()
  assert any(t.name=='mcp__dedicated__echo' for t in view.tool_records),store.redacted_messages(captured[-1]['messages'])
  tool=next(t for t in view.tool_records if t.name=='mcp__dedicated__echo')
  assert tool.tool_ref.scope!='main' and tool.state=='result_committed'
  assert not registry.countMcpTools()
  rows=[json.loads(line) for line in (root/'server'/'wire.jsonl').read_text('utf-8').splitlines()]
  assert rows[-1]=={'closed':'stdin-eof'}
  assert sum(row.get('in',{}).get('method')=='tools/call' for row in rows)==1
  # Connection preparation does not grant a missing parent journal identity.
  try:await ctx.runAgent(AgentRequest('no journal','dedicated'))
  except RuntimeError:pass
  else:raise AssertionError('agent ran without a current parent intent')
  rows=[json.loads(line) for line in (root/'server'/'wire.jsonl').read_text('utf-8').splitlines()]
  assert rows[-1]=={'closed':'stdin-eof'} and len(captured)==2
  # A new owner rebuilds handlers; closing the old owner's connection cannot break it.
  prepared=prepareAgentRun(parent,ctx,registry,permits,options,AgentRequest('next','dedicated'),definition,env=dict(os.environ))
  await openPreparedAgentMcp(prepared)
  rebound=_background_prepared(prepared)
  await openPreparedAgentMcp(rebound)
  await closePreparedAgentMcp(prepared)
  output=await rebound.registry.dispatch('mcp__dedicated__echo','{"msg":"new owner"}',rebound.ctx)
  assert 'new owner' in output
  # A prepared transport is also closed when launch is refused before any journal grant.
  manager=TaskManager(store,BackgroundRuntime(store=store,workspaceRoot=root))
  stopped=threading.Event();stopped.set()
  try:await manager.launch(rebound,description='not started',parent=ToolRef('main','absent'),parent_signal=stopped)
  except AgentFailure:pass
  else:raise AssertionError('canceled parent launched')
  assert rebound.mcp_runtime.manager.connectedCount==0
  await closePreparedAgentMcp(rebound)
  # The ordinary child journal must retain an actual remote write with a lost reply.
  await store.accept_user(parent,'unknown child request')
  ctx.runAgent=createAgentRunner(parent,ctx,registry,permits,store,options,env=dict(os.environ),
   definitions={'dedicated':definition},request=lambda *_a:reply('',call('lost-child','mcp__dedicated__crash',{})))
  result=await run_turn(parent,options,registry,ctx,approve=ask,journal=store,
   request=lambda *_a:reply('',call('unknown-parent','Agent',{'task':'unknown child','agent_type':'dedicated'})),
   authorize_batch=permits.authorizeBatch,call_scope=permits.callScope,permission_mode=permits.getMode)
  assert result.status=='outcome_unknown' and store.blocked,result
  view=await store.background_view()
  assert any(t.name=='mcp__dedicated__crash' and t.state=='started' for t in view.tool_records)
  assert any(run.status=='unknown' for run in view.runs)
  assert (root/'server'/'effects').read_text()=='1'
 finally:await store.close()
asyncio.run(scenario())
'''


def test_named_agent_mcp_uses_child_journal_and_rebuilds_closed_owner(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    fixture = Path(__file__).parent / "support/mcp_server.py"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _CODE, str(tmp_path),
                             str(archive.resolve()), str(package), str(fixture.resolve())],
                            capture_output=True, text=True, encoding="utf-8", timeout=50)
    assert result.returncode == 0, result.stdout + result.stderr
