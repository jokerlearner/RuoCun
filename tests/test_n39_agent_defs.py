"""Frozen agent_defs parser and real child dispatch for an effective custom definition."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun
from ruocun.agent.agent_defs import parseAgentDefinition


def test_frozen_minimal_agent_definition_requires_name_and_body() -> None:
    minimal = parseAgentDefinition("agent", "---\r\nname: my-agent\r\ndescription: test\r\n---\r\nrole")
    assert minimal is not None and minimal.agent_type == "my-agent" and minimal.system_prompt == "role"
    assert minimal.source == "userSettings" and minimal.tools is None
    assert parseAgentDefinition("empty", "---\nname: empty\n---") is None
    assert parseAgentDefinition("unnamed", "---\ndescription: unnamed\n---\nbody") is None


def test_frozen_full_agent_definition_preserves_narrow_extensions() -> None:
    raw = '''---
name: reviewer
description: review
tools: 'Read, Grep, !Write'
disallowedTools: Edit
model: InHeRiT
permissionMode: plan
maxTurns: 50
skills: 'code-review'
memory: project
background: true
isolation: worktree
color: red
omitClaudeMd: true
initialPrompt: /review
effort: high
hooks:
  SubagentStart:
    - command: "echo start"
  SubagentStop:
    - command: "echo stop"
mcpServers:
  - slack
  - inline: { command: missing }
---
body'''
    definition = parseAgentDefinition("reviewer", raw)
    assert definition is not None
    assert definition.tools == ("Read", "Grep") and definition.disallowed_tools == {"Write"}
    assert definition.model == "inherit" and definition.permission_mode == "plan" and definition.max_turns == 50
    assert definition.skills == ("code-review",) and definition.memory == "project"
    assert definition.background and definition.isolation == "worktree" and definition.color == "red"
    assert definition.omit_project_instructions and definition.initial_prompt == "/review" and definition.effort == "high"
    assert definition.hooks == {"SubagentStart": ("echo start",), "SubagentStop": ("echo stop",)}
    assert definition.mcp_servers == ("slack",)
    wildcard = parseAgentDefinition("star", "---\nname: star\ntools: '* , !Write'\n---\nbody")
    assert wildcard is not None and wildcard.tools is None and wildcard.disallowed_tools == {"Write"}


_CODE = r'''
import asyncio,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.agent.agent_defs import loadAgentDefinitions
from ruocun.agent.bundled_agents import agentCatalog
from ruocun.agent.loop import run_turn
from ruocun.agent.run_agent import createAgentRunner
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility,CompatibilitySource
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
from ruocun.tools.agent import agentTool
from ruocun.tools.grep_files import grepFilesTool
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext
from ruocun.tools.write_file import writeFileTool
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

def call(identity,name,args):
    return {'id':identity,'type':'function','function':{'name':name,'arguments':json.dumps(args)}}

def reply(text='',*calls):
    return ResilientResult('complete',[],{'role':'assistant','content':text,'tool_calls':list(calls)},None,'stop',[],{})

def file(directory,name,text):
    directory.mkdir(parents=True,exist_ok=True)
    (directory/(name+'.md')).write_text(text,encoding='utf-8')

def role(name,body,fields=''):
    return f'---\nname: {name}\n{fields}---\n{body}'

async def scenario():
    home=root/'home';cwd=root/'workspace';cwd.mkdir()
    external=root/'compat';external.mkdir()
    for directory,body in [(external/'user','compat user'),(home/'agents','native user'),
                           (external/'project','compat project'),(cwd/'.ruocun'/'agents','custom winner')]:
        file(directory,'explore',role('explore',body,'tools: Read, !Grep\nmemory: project\nmodel: Gateway/EXACT\n'
             'permissionMode: default\nmaxTurns: 2\neffort: high\nskills: investigate\ninitialPrompt: initial note\n'))
    file(cwd/'.ruocun'/'agents','unsupported',role('unsupported','needs hook','hooks:\n  SubagentStart:\n    - command: "echo never"\n'))
    file(cwd/'.ruocun'/'agents'/'nested','nested',role('nested','not scanned'))
    compat=Compatibility(1,(CompatibilitySource('u','user','agents',str(external/'user')),
        CompatibilitySource('p','project','agents',str(external/'project'),str(cwd))))
    definitions=await loadAgentDefinitions(cwd,home,compat,env={})
    disabled=await loadAgentDefinitions(cwd,home,compat,env={},disabled=True)
    assert definitions['explore'].system_prompt=='custom winner' and definitions['explore'].source=='projectSettings'
    assert disabled['explore'].source=='built-in' and 'nested' not in definitions
    assert 'Gateway/EXACT' in agentCatalog({},'Parent/Model',definitions=definitions)
    parent=Session('private parent system','Parent/Model')
    conversation=await Conversation.open(root/'session','custom-agent',cwd,runtime,parent,'synthetic-key',resume=False)
    try:
        await conversation.accept_user(parent,'private parent input')
        async def ask(_text):raise AssertionError('explicit permissions decide this fixture')
        rules=emptyPermissions();rules['allow']=['Read','Write'];rules['defaultMode']='auto'
        permissions=await createPermissionRuntime(cwd,home,compat,parent,rules,ask,interactive=False,
            env={'ProgramData':str(root/'policy')})
        registry=ToolRegistry()
        for tool in (agentTool,grepFilesTool,readFileTool,writeFileTool):registry.register(tool)
        ctx=ToolContext(str(cwd),skills=[{'name':'investigate','slug':'investigate','body':'preloaded skills body'}])
        options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','model':parent.model}
        captured=[]
        memory=cwd/'.ruocun'/'agents'/'memory'/'explore'/'memory.md'
        def child_request(opts,_context):
            captured.append(opts)
            task=opts['messages'][1]['content']
            if task=='memory task' and len(captured)==1:
                return reply('',call('memory','Write',{'path':str(memory),'content':'persistent observation'}))
            if task=='read only' and len(captured)==3:
                return reply('',call('forbidden','Write',{'path':'should-not-exist.txt','content':'blocked'}))
            return reply('child final '+task)
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,conversation,options,env={},
            definitions=definitions,user_root=home,request=child_request,project_instructions='project context')
        replies=iter([reply('',call('a','Agent',{'task':'memory task','agent_type':'explore'})),
            reply('',call('b','Agent',{'task':'read only','agent_type':'explore','model':'override/CASE','mode':'plan'})),
            reply('',call('c','Agent',{'task':'needs hook','agent_type':'unsupported'})),reply('parent final')])
        result=await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:next(replies),
            authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,permission_mode=permissions.getMode)
        assert result.status=='complete'
        assert memory.read_text()=='persistent observation' and not (cwd/'should-not-exist.txt').exists()
        assert [o['model'] for o in captured]==['Gateway/EXACT']*2+['override/CASE']*2
        assert all(o['extra']['reasoning_effort']=='high' for o in captured)
        assert [t['function']['name'] for t in captured[0]['tools']]==['Read','Write']
        assert [t['function']['name'] for t in captured[2]['tools']]==['Read']
        assert 'custom winner' in captured[0]['messages'][0]['content']
        assert 'private parent input' not in json.dumps(captured[0]['messages'])
        assert 'initial note' in [m.get('content') for m in captured[0]['messages']]
        assert any('preloaded skills body' in m.get('content','') for m in captured[0]['messages'])
        assert len(captured)==4 and 'Hook' in next(m['content'] for m in parent.messages if m.get('tool_call_id')=='c')
        view=await conversation.background_view()
        assert all(run.snapshot['definitionVersion']==definitions['explore'].version for run in view.runs)
        assert all(run.snapshot['turnLimit']==2 for run in view.runs)
        assert [run.snapshot['permissionMode'] for run in view.runs]==['default','plan']
        assert permissions.getMode()=='auto'
    finally:await conversation.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite child dispatch")
def test_effective_definition_controls_actual_child_tools_model_skill_and_memory(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _CODE, str(tmp_path), str(archive.resolve()), str(package)],
        text=True, encoding="utf-8", capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout


_EXTERNAL = _CODE[:_CODE.index("async def scenario():")] + r'''
from ruocun.agent.runtime_context import buildRuntimeContext,isRuntimeContext

async def scenario():
    home=root/'home';workspace=root/'workspace';working=root/'worktree'
    workspace.mkdir();working.mkdir()
    blocked=root/'forbidden.txt';readable=root/'outside.txt';once=root/'allowed-once.txt'
    readable.write_text('outside private fixture',encoding='utf-8')
    file(workspace/'.ruocun'/'agents','role',role('role','fixture role',
        'permissionMode: bypassPermissions\nmemory: project\n'))
    compat=Compatibility(1,())
    definitions=await loadAgentDefinitions(workspace,home,compat,env={})
    parent=Session('parent system','Parent/Model')
    conversation=await Conversation.open(root/'session','child-external',workspace,runtime,parent,'synthetic-key',resume=False)
    try:
        await conversation.accept_user(parent,'test child path approval')
        async def ask(_text):raise AssertionError('test uses the parent structured approval')
        approvals=[]
        async def prompt(requests):
            decisions={}
            for item in requests:
                summary=item['summary'];approvals.append(summary)
                decisions[item['id']]='once' if summary.endswith(str(once)) and sum(s.endswith(str(once)) for s in approvals)==1 else 'deny'
            return decisions
        rules=emptyPermissions();rules['allow']=['Read','Write'];rules['defaultMode']='default'
        permissions=await createPermissionRuntime(workspace,home,compat,parent,rules,ask,interactive=True,
            approvalPrompt=prompt,env={'ProgramData':str(root/'policy')})
        registry=ToolRegistry()
        for tool in (agentTool,readFileTool,writeFileTool):registry.register(tool)
        ctx=ToolContext(str(workspace),cwd=str(working),approveExternalRead=permissions.approveExternalRead,
            approveExternalWrite=permissions.approveExternalWrite)
        options={'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic-key','model':parent.model}
        captured=[]
        def child_request(opts,_context):
            captured.append(opts)
            if len(captured)==1:
                return reply('',call('read','Read',{'path':str(readable)}),
                    call('blocked','Write',{'path':str(blocked),'content':'forbidden write'}),
                    call('once','Write',{'path':str(once),'content':'first allowed'}),
                    call('inside','Write',{'path':'local.txt','content':'inside actual cwd'}))
            if len(captured)==2:
                return reply('',call('again','Write',{'path':str(once),'content':'unexpected second grant'}))
            return reply('child final')
        ctx.runAgent=createAgentRunner(parent,ctx,registry,permissions,conversation,options,env={},
            definitions=definitions,user_root=home,request=child_request)
        replies=iter([reply('',call('a','Agent',{'task':'verify outside permissions','agent_type':'role'})),reply('parent final')])
        result=await run_turn(parent,options,registry,ctx,approve=ask,journal=conversation,request=lambda _o,_c:next(replies),
            authorize_batch=permissions.authorizeBatch,call_scope=permissions.callScope,permission_mode=permissions.getMode)
        assert result.status=='complete' and not blocked.exists()
        assert once.read_text()=='first allowed' and (working/'local.txt').read_text()=='inside actual cwd'
        last=captured[-1]['messages'];tool_text={m['tool_call_id']:m['content'] for m in last if m['role']=='tool'}
        assert all('未获授权访问' in tool_text[call_id] for call_id in ['read','blocked','again'])
        assert len(approvals)==4 and sum(s.endswith(str(once)) for s in approvals)==2
        system=last[0]['content']
        assert next(m for m in reversed(last) if isRuntimeContext(m))==buildRuntimeContext(ctx)
        assert str(working) not in system and str(workspace/'.ruocun'/'agents'/'memory'/'role'/'memory.md') in system
        assert str(working/'.ruocun'/'agents'/'memory') not in system
        assert permissions.getMode()=='default'
    finally:await conversation.close()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="real controlled SQLite child path approvals")
def test_child_bypass_uses_parent_outside_permission_and_original_project_memory(tmp_path):
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    package = Path(ruocun.__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", _EXTERNAL, str(tmp_path), str(archive.resolve()), str(package)],
        text=True, encoding="utf-8", capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr + result.stdout
