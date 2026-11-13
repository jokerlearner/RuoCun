"""Frozen index.ts eval and explicit disable switches at the ordinary CLI entry."""

import os
import subprocess
import sys
from pathlib import Path

import ruocun


def test_eval_preserves_bundled_skills_and_hooks_without_loading_disk_channels(tmp_path):
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    code = r'''
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from ruocun.agent import runtime
from ruocun.cli import main
from ruocun.client.resilient import ResilientResult
from ruocun.hooks.hooks import HookRuntime
from ruocun.mcp.mcp import McpManager
from ruocun.memory.frontmatter import serializeMemory
from ruocun.memory.types import newMemory
from ruocun.platform.process_tree import ForegroundResult

workspace = Path.cwd()
user = Path.home() / '.ruocun'
project = workspace / '.ruocun'
target = workspace / 'nested' / 'actual-read.txt'
disk = project / 'skills' / 'disk-fixture' / 'SKILL.md'
nested = target.parent / '.ruocun' / 'skills' / 'nested-fixture' / 'SKILL.md'
agent = user / 'agents' / 'fixture.md'
instruction = workspace / 'RUOCUN.md'
hook_file = user / 'hooks.json'
mcp_file = user / 'mcp.json'
memory = user / 'memory' / 'fixture.md'

def put(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

put(target, 'synthetic-read-evidence')
put(disk, '---\nname: disk-fixture\ndescription: synthetic-disk-skill\n---\nbody\n')
put(nested, '---\nname: nested-fixture\ndescription: synthetic-nested-skill\n---\nbody\n')
put(agent, '---\nname: fixture-agent\ndescription: synthetic-custom-agent\n---\nrole\n')
put(instruction, 'synthetic-project-instructions\n')
put(hook_file, json.dumps({'SessionStart': [{'command': 'synthetic-hook-command'}]}))
put(mcp_file, json.dumps({'mcpServers': {'fixture': {'command': 'must-not-launch.exe'}}}))
put(memory, serializeMemory(newMemory(name='fixture', text='synthetic-recalled-memory', type='user',
                                     today=date.today().isoformat(), title='Fixture memory')))
config = user / 'config.json'
put(config, json.dumps({'version': 2, 'activeProfile': 'fixture', 'profiles': {'fixture': {
    'provider': 'deepseek', 'model': 'fixture-model', 'key': 'synthetic-local-credential',
    'baseUrl': 'http://127.0.0.1:1'}}}))

observed = set()
watched = {disk, nested, agent, instruction, hook_file, mcp_file}
original_read_text = Path.read_text
original_read_bytes = Path.read_bytes

def observe_read(path, *args, **kwargs):
    if path in watched:
        observed.add(path)
    return original_read_text(path, *args, **kwargs)

def observe_bytes(path, *args, **kwargs):
    if path in watched:
        observed.add(path)
    return original_read_bytes(path, *args, **kwargs)

Path.read_text = observe_read
Path.read_bytes = observe_bytes
hook_calls = []
mcp_calls = []

async def hook_command(self, spec, event, ctx, signal):
    assert spec.command == 'synthetic-hook-command' and event == 'SessionStart'
    hook_calls.append(event)
    return ForegroundResult('synthetic-hook-context', '', 0, False, 0)

async def mcp_init(self):
    assert self.config['mcpServers']['fixture']['command'] == 'must-not-launch.exe'
    mcp_calls.append('init')

HookRuntime._command = hook_command
McpManager.init = mcp_init
requests = []

def tool_call(call_id, name, args):
    return {'id': call_id, 'type': 'function', 'function': {'name': name, 'arguments': json.dumps(args)}}

def model(options, **kwargs):
    requests.append(options)
    if len(requests) == 1:
        assistant = {'role': 'assistant', 'content': '', 'tool_calls': [
            tool_call('fixture-todo', 'TodoWrite', {'todos': [{'content': 'Read fixture', 'status': 'in_progress'}]}),
            tool_call('fixture-read', 'Read', {'path': str(target)}),
        ]}
    else:
        assistant = {'role': 'assistant', 'content': 'fixture-done'}
    return ResilientResult('complete', [], assistant, None, 'stop', [], {})

runtime.streamChatResilient = model

def run(flags):
    requests.clear()
    observed.clear()
    hook_calls.clear()
    mcp_calls.clear()
    assert main(['--config', str(config), '--permission-mode', 'bypassPermissions', *flags, 'read fixture']) == 0
    assert len(requests) == 2
    assert requests[0]['messages'][-1]['content'] == 'read fixture', 'CLI switches must not reach the prompt'
    sent = '\n'.join(str(item.get('content', '')) for item in requests[-1]['messages'])
    tools = {item['function']['name'] for item in requests[0]['tools']}
    assert 'synthetic-read-evidence' in sent  # Real Read occurred after TodoWrite in every mode.
    assert 'MemoryRead' in tools and 'MemoryWrite' in tools
    return sent, tools

sent, tools = run([])
assert {'WebSearch', 'WebFetch'} <= tools
assert watched <= observed
assert hook_calls == ['SessionStart'] and mcp_calls == ['init']
for marker in ('synthetic-disk-skill', 'synthetic-nested-skill', 'synthetic-custom-agent',
               'synthetic-project-instructions', 'synthetic-hook-context', 'synthetic-recalled-memory', '- debug:'):
    assert marker in sent, marker

sent, tools = run(['--eval'])
assert not {'WebSearch', 'WebFetch'} & tools
assert observed == {hook_file}
assert hook_calls == ['SessionStart'] and not mcp_calls
assert '- debug:' in sent and 'synthetic-hook-context' in sent
for marker in ('synthetic-disk-skill', 'synthetic-nested-skill', 'synthetic-custom-agent',
               'synthetic-project-instructions', 'synthetic-recalled-memory'):
    assert marker not in sent, marker

sent, tools = run(['--eval', '--no-skills', '--no-hooks'])
assert not observed and not hook_calls and not mcp_calls
assert '- debug:' not in sent and 'synthetic-hook-context' not in sent
assert not {'WebSearch', 'WebFetch'} & tools
print('eval-entry-confirmed')
'''
    environment = {
        key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT") if key in os.environ
    }
    environment.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                       ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh")
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(Path(ruocun.__file__).resolve().parent.parent)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8", env=environment,
        cwd=workspace, timeout=40,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "eval-entry-confirmed" in result.stdout
