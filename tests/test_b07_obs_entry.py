"""Ordinary trace/tool audit wiring with a local in-memory observation backend."""

import json
import os
import subprocess
import sys
from pathlib import Path

import ruocun


def test_ordinary_observation_correlates_turn_model_tool_and_flushes_without_replay(tmp_path):
    home,workspace=tmp_path/'home',tmp_path/'workspace'
    home.mkdir()
    workspace.mkdir()
    config=home/'config.json'
    config.write_text(json.dumps({'version':2,'activeProfile':'synthetic','profiles':{'synthetic':{
        'provider':'deepseek','model':'synthetic-obs','key':'synthetic-observer-key',
        'baseUrl':'http://127.0.0.1:1/v1'}}}),encoding='utf-8')
    code=r'''
import json,sys
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
sys.path.insert(0,sys.argv[1])
from ruocun.agent import runtime,run_agent
from ruocun.obs.backend import setBackend,setObsRedactor
from ruocun.client.resilient import ResilientResult
active=ContextVar('active',default=None)
spans=[];flushed=[];calls=[]
class Span:
    def __init__(self,options): self.options=options;self.parent=active.get();spans.append(self)
    def setAttributes(self,attrs): pass
    def end(self): pass
class Backend:
    def startSpan(self,options): return Span(options)
    @contextmanager
    def activate(self,span):
        token=active.set(span)
        try: yield
        finally: active.reset(token)
    def event(self,*args): pass
    def flush(self): flushed.append(True)
async def init(on,**kwargs):
    assert on
    setObsRedactor(kwargs['redact']);setBackend(Backend())
runtime.initObs=init
def request(opts,**kwargs):
    calls.append(opts)
    message={'role':'assistant','content':'synthetic done'}
    if len(calls)==1:
        message={'role':'assistant','content':'','tool_calls':[{'id':'synthetic-write','type':'function',
            'function':{'name':'Write','arguments':json.dumps({'path':'effect.txt','content':'exactly once'})}},
            {'id':'synthetic-agent','type':'function','function':{'name':'Agent',
             'arguments':json.dumps({'task':'synthetic child task','model':'synthetic-child'})}}]}
    return ResilientResult('complete',[],message,{'prompt_tokens':100,'completion_tokens':5},'stop',[],{})
runtime.streamChatResilient=request
run_agent.streamChatResilient=request
assert runtime.run_cli(['--config',sys.argv[2],'--cwd',sys.argv[3],'--no-memory','--no-skills',
    '--no-hooks','--no-mcp','--permission-mode','bypassPermissions','--obs'])==0
assert len(calls)==3 and (Path(sys.argv[3])/'effect.txt').read_text('utf-8')=='exactly once'
turn=next(span for span in spans if span.options['name']=='turn' and span.options['metadata']['identity']=='main')
llms=[span for span in spans if span.options['name']=='llm.call']
tool=next(span for span in spans if span.options['name']=='tool.Write')
assert len(llms)==3 and tool.parent is turn
child=next(span for span in spans if span.options['name']=='turn' and span.options['metadata']['identity']=='sub')
assert child.options['metadata']['taskId'] and child.options['metadata']['runId']
assert child.parent.options['name']=='tool.Agent'
assert sum(span.parent is turn for span in llms)==2 and sum(span.parent is child for span in llms)==1
identity=turn.options['sessionId']
assert identity and tool.options['sessionId']==identity
assert tool.options['metadata']['toolCallId']=='synthetic-write'
assert tool.options['metadata']['identity']=='main'
assert flushed==[True]
directory=next((Path.home()/'.ruocun/sessions').glob('*/'+identity))
events=[json.loads(line) for line in (directory/'tool-trace.jsonl').read_text('utf-8').splitlines()]
assert len(events)==2 and events[0]['name']=='Write' and events[0]['ok']
assert events[0]['sessionId']==identity and events[0]['toolCallId']=='synthetic-write'
cache=[json.loads(line) for line in (directory/'cache.jsonl').read_text('utf-8').splitlines()]
assert [event['agent'] for event in cache].count('main')==2
subs=[event for event in cache if event['agent']=='sub']
assert len(subs)==1 and subs[0]['subId']==child.options['metadata']['runId'] and subs[0]['depth']==1
print('synthetic-observation-entry-confirmed')
'''
    environment={key:os.environ[key] for key in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT') if key in os.environ}
    environment.update(HOME=str(home),USERPROFILE=str(home),APPDATA=str(home),LOCALAPPDATA=str(home),
                       ProgramData=str(home/'program-data'),TEMP=str(tmp_path),TMP=str(tmp_path),RUOCUN_LANG='zh')
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',code,str(Path(ruocun.__file__).resolve().parent.parent),
        str(config),str(workspace)],input='synthetic action\n/audit all\n/exit\n',text=True,capture_output=True,
        encoding='utf-8',env=environment,cwd=workspace,timeout=40)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert '工具调用审计' in result.stdout and 'synthetic-observation-entry-confirmed' in result.stdout
