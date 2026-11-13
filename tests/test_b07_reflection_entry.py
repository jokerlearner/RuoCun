"""Source turn-end fork/cadence on the ordinary pipe entry, synthetic model only."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun


@pytest.mark.skipif(sys.platform != 'win32', reason='controlled SQLite Windows runtime')
def test_ordinary_reflection_is_opt_in_forks_prefix_and_audits_actual_usage(tmp_path):
    home, workspace=tmp_path/'home', tmp_path/'workspace'
    home.mkdir()
    workspace.mkdir()
    config=home/'config.json'
    config.write_text(json.dumps({'version':2,'activeProfile':'synthetic','profiles':{'synthetic':{
        'provider':'zhipu','model':'synthetic-reflect','key':'synthetic-reflection-key',
        'baseUrl':'http://127.0.0.1:1/v1'}}}),encoding='utf-8')
    code=r'''
import copy,json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ruocun.agent import runtime
from ruocun.client.resilient import ResilientResult
sent=[]
def request(opts,**kwargs):
    messages=opts['messages']
    reflective='〈全部已记标题〉' in str(messages[-1].get('content','')) or 'mergeInto' in str(messages[-1].get('content',''))
    if reflective:
        prior=next(item for item in reversed(sent) if not item[0])
        assert messages[:-1]==prior[1]['messages']
        assert opts['tools']==prior[1]['tools']
        text=json.dumps({'onTrack':False,'advisory':'synthetic direction advice','memories':[
            {'title':'合成项目事实','text':'合成项目使用本地fixture','type':'semantic','importance':7}],
            'corrections':[],'confirmed':[]})
    else: text='synthetic answer'
    sent.append((reflective,copy.deepcopy(opts)))
    return ResilientResult('complete',[],{'role':'assistant','content':text},
        {'prompt_tokens':100,'completion_tokens':10,'prompt_tokens_details':{'cached_tokens':50}},'stop',[],{})
runtime.streamChatResilient=request
result=runtime.run_cli(['--config',sys.argv[2],'--cwd',sys.argv[3],'--no-skills', '--no-hooks','--no-mcp','--reflect-memory'])
assert result==0,result
primary=[opts for reflective,opts in sent if not reflective]
forks=[opts for reflective,opts in sent if reflective]
assert len(primary)==2 and len(forks)==2,(len(primary),len(forks))
assert any(m.get('content')=='[反思]\nsynthetic direction advice' for m in primary[1]['messages'])
files=list((Path(sys.argv[3])/'.ruocun/memory').glob('*.md'))
assert len(files)==1 and '合成项目使用本地fixture' in files[0].read_text('utf-8')
events=[]
for file in (Path.home()/'.ruocun/sessions').rglob('cache.jsonl'):
    events.extend(json.loads(line) for line in file.read_text('utf-8').splitlines())
assert [e['agent'] for e in events].count('distill')==2,[e['agent'] for e in events]
assert [e['agent'] for e in events].count('main')==2
print('synthetic-reflection-entry-confirmed')
'''
    environment={key:os.environ[key] for key in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT') if key in os.environ}
    environment.update(HOME=str(home),USERPROFILE=str(home),APPDATA=str(home),LOCALAPPDATA=str(home),
        ProgramData=str(home/'program-data'),TEMP=str(tmp_path),TMP=str(tmp_path),RUOCUN_REFLECT_SYNC='1',RUOCUN_LANG='zh')
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',code,str(Path(ruocun.__file__).resolve().parent.parent),
        str(config),str(workspace)],input='synthetic first\nsynthetic second\n/exit\n',capture_output=True,
        text=True,encoding='utf-8',env=environment,cwd=workspace,timeout=45)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert 'synthetic-reflection-entry-confirmed' in result.stdout
