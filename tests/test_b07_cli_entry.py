"""Frozen CLI token/command cases on real ordinary composition, synthetic credentials."""

import json
import os
import subprocess
import sys
from pathlib import Path

import ruocun


def test_source_known_values_unknown_tokens_and_positional_prompt_are_separate():
    from ruocun.agent.runtime import _parse_cli

    args=_parse_cli(['--model','synthetic-model','--unknown','hello','synthetic-model',
                     '--api-key','synthetic-cli-key','--provider','deepseek','--verbose'])
    assert args.prompt==['--unknown hello']  # Frozen global Set also removes repeated flag values.
    assert args.model=='synthetic-model' and args.api_key=='synthetic-cli-key' and args.verbose
    assert _parse_cli(['-c','synthetic-id','--no-web']).resume=='synthetic-id'
    assert _parse_cli(['--continue','--no-web']).resume=='latest'
    legacy = _parse_cli(['--continue=latest', '/recovery'])
    assert legacy.resume == 'latest' and legacy.prompt == ['/recovery']
    assert _parse_cli(['--','--model','literal']).prompt==['--model literal']
    assert _parse_cli(['  ']).prompt==[]
    upgraded = _parse_cli(['--upgrade-session', 'synthetic-id', '--cwd', str(Path.cwd())])
    assert upgraded.upgrade_session == 'synthetic-id' and upgraded.prompt == []
    oracle=json.loads((Path(__file__).resolve().parents[1]/
        '.scratch/ruocun-next24h/evidence/batch-07/n70/catalog/cli-source-oracle.json').read_text('utf-8'))
    for name,case in oracle['cases'].items():
        actual=_parse_cli(case['argv'])
        expected='hello' if name=='double_dash_is_prompt' else case['argvPrompt']
        assert ' '.join(actual.prompt)==expected,name
        assert actual.model==case['cliModel'],name
        expected_resume=case['cliResumeId'] or ('latest' if case['continueFlag'] else None)
        assert actual.resume==expected_resume,name


def test_ordinary_queries_temp_credentials_paths_and_operator_skill_install(tmp_path):
    home,workspace=tmp_path/'home',tmp_path/'workspace'
    home.mkdir()
    workspace.mkdir()
    source=workspace/'fixture-skill'
    source.mkdir()
    (source/'SKILL.md').write_text('---\nname: fixture\ndescription: synthetic fixture\n---\nsynthetic body\n',encoding='utf-8')
    code=r'''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from ruocun.agent import runtime
from ruocun.cli import main
from ruocun.client.resilient import ResilientResult
root=Path(sys.argv[2])
calls=[]
def no_model(*args,**kwargs):
    calls.append(True)
    raise AssertionError('queries must not call a model')
runtime.streamChatResilient=no_model
assert main(['Skill','add',str(root/'fixture-skill'),'--project'])==0
assert (root/'.ruocun/skills/fixture-skill/SKILL.md').read_text('utf-8').endswith('synthetic body\n')
assert runtime.run_cli(['--cwd',str(root),'--api-key','synthetic-cli-key','--provider','deepseek',
    '--no-memory','--no-skills','--no-hooks','--no-mcp','--debug'])==0
assert not calls
assert not (Path.home()/'.ruocun/config.json').exists()
def path_model(options,**kwargs):
    calls.append(options)
    return ResilientResult('complete',[],{'role':'assistant','content':'synthetic path response'},None,'stop',[],{})
runtime.streamChatResilient=path_model
options=['--cwd',str(root),'--api-key','synthetic-cli-key','--provider','deepseek',
    '--no-memory','--no-skills','--no-hooks','--no-mcp']
assert runtime.run_cli([*options,'/tmp/a.py'])==0
assert len(calls)==1 and calls[0]['messages'][-1]['content']=='/tmp/a.py'
assert calls[0]['apiKey']=='synthetic-cli-key'
assert runtime.run_cli([*options,'/unknown-command'])==2 and len(calls)==1
assert not any('synthetic-cli-key' in file.read_text('utf-8',errors='ignore')
    for file in (Path.home()/'.ruocun/sessions').rglob('*.jsonl'))
print('synthetic-cli-entry-confirmed')
'''
    environment={key:os.environ[key] for key in ('SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT') if key in os.environ}
    environment.update(HOME=str(home),USERPROFILE=str(home),APPDATA=str(home),LOCALAPPDATA=str(home),
                       ProgramData=str(home/'program-data'),TEMP=str(tmp_path),TMP=str(tmp_path),RUOCUN_LANG='zh')
    result=subprocess.run([sys.executable,'-I','-X','utf8','-c',code,str(Path(ruocun.__file__).resolve().parent.parent),str(workspace)],
        input='/help\n/doctor\n/agents\n/tasks\n/lang zh\n/Config\n/audit all\n/status\n/quit --keep-background\n',
        capture_output=True,text=True,encoding='utf-8',env=environment,cwd=workspace,timeout=40)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert 'ruocun doctor' in result.stdout and '自定义子代理' in result.stdout
    assert 'Windows 本轮' in result.stdout and 'synthetic-cli-entry-confirmed' in result.stdout


def test_native_terminator_keeps_permission_and_meta_flags_literal(monkeypatch):
    from ruocun.agent import runtime
    from ruocun.cli import main

    received = []

    async def capture(args):
        received.append(args)
        return 0

    monkeypatch.setattr(runtime, '_run', capture)
    assert main(['--', '--permission-mode', 'bypassPermissions', '--version', 'synthetic']) == 0
    assert received[-1].prompt == ['--permission-mode bypassPermissions --version synthetic']
    assert 'defaultMode' not in received[-1].permissions
    assert main(['--permission-mode', 'plan', 'trust', 'synthetic']) == 0
    assert not received[-1].trust_workspace
    assert main(['--allow', '--api-key', 'synthetic-overlap', 'question']) == 0
    assert received[-1].api_key == 'synthetic-overlap'
    assert received[-1].prompt == ['--allow question']
    parsed = runtime._parse_cli(['--api-key', 'synthetic-first', '--api-key', 'synthetic-second', 'question'])
    assert parsed.api_key == 'synthetic-first'
    assert parsed.prompt == ['question']
