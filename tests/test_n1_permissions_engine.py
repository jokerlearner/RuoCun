"""DAO engine.test.ts existing decision assertions; AST integration follows B."""
import asyncio
import json

import pytest

from ruocun.permissions.engine import decide, decideAsync, isSensitiveCall
from ruocun.permissions.settings import emptyPermissions


@pytest.mark.parametrize("tool,value,capability,mode,expected", [
    ("Bash", "npm run test", "exec", "bypassPermissions", "allow"),
    ("Bash", "rm -rf /", "exec", "bypassPermissions", "ask"),
    ("Write", "../.ssh/authorized_keys", "write", "bypassPermissions", "allow"),
    ("Edit", ".git/config", "write", "bypassPermissions", "allow"),
    ("Bash", "cat ~/.bashrc", "exec", "bypassPermissions", "allow"),
    ("Bash", "cat /etc/postfix/main.cf", "exec", "bypassPermissions", "allow"),
    ("Bash", "ls /etc/systemd/system/", "exec", "bypassPermissions", "allow"),
    ("Write", "/etc/hosts", "write", "bypassPermissions", "allow"),
    ("Bash", "echo x > ~/.bashrc", "exec", "bypassPermissions", "ask"),
    ("Bash", "echo x > /etc/postfix/main.cf", "exec", "bypassPermissions", "ask"),
    ("Write", "/etc/hosts", "write", "default", "ask"),
    ("Edit", ".git/config", "write", "default", "ask"),
    ("Bash", "cat /etc/postfix/main.cf > /tmp/x", "exec", "auto", "ask"),
    ("Bash", "cat ~/.ssh/id_rsa", "exec", "default", "ask"),
    ("Bash", "cat ~/.ssh/id_rsa", "exec", "auto", "ask"),
    ("Bash", "cat /etc/shadow", "exec", "default", "ask"),
    ("Read", "~/.ssh/id_rsa", "read", "default", "ask"),
    ("Read", "~/.ssh/id_rsa", "read", "auto", "ask"),
    ("Edit", "a/.ssh/id_rsa", "write", "auto", "ask"),
    ("Write", "src/app.ts", "write", "bypassPermissions", "allow"),
    ("Edit", "src/app.ts", "write", "auto", "allow"),
    ("Write", "src/new.ts", "write", "auto", "allow"),
    ("TodoWrite", "", "write", "auto", "allow"),
    ("WebSearch", "x", "network", "auto", "allow"),
    ("WebFetch", "http://x", "network", "auto", "allow"),
    ("Bash", "ls /Users/x/proj/sub/", "exec", "auto", "allow"),
    ("Bash", "cat package.json", "exec", "auto", "allow"),
    ("Bash", "git status", "exec", "auto", "allow"),
    ("Bash", "git log --oneline -20", "exec", "auto", "allow"),
    ("Bash", "ls -la | grep foo", "exec", "auto", "allow"),
    ("Bash", "pwd", "exec", "auto", "allow"),
    ("Bash", "rm -f a", "exec", "auto", "ask"),
    ("Bash", "git push", "exec", "auto", "ask"),
    ("Bash", "ls > out.txt", "exec", "auto", "ask"),
    ("Bash", "ls && rm -rf x", "exec", "auto", "ask"),
    ("Bash", "cat $(whoami)", "exec", "auto", "ask"),
    ("Bash", "find . -delete", "exec", "auto", "ask"),
    ("Bash", "npm test", "exec", "auto", "ask"),
    ("Bash", "ls /tmp", "exec", "default", "allow"),
    ("Bash", "find src -name '*.ts' | wc -l", "exec", "default", "allow"),
    ("Bash", "npm install", "exec", "default", "ask"),
    ("Read", "a", "read", "default", "allow"),
    ("Write", "a", "write", "default", "ask"),
    ("Edit", "a", "write", "auto", "allow"),
    ("Write", "a", "write", "auto", "allow"),
    ("Bash", "rm -rf /", "exec", "plan", "deny"),
    ("Write", "a", "write", "plan", "deny"),
    ("Read", "a", "read", "plan", "allow"),
    ("Bash", "ls /tmp", "exec", "plan", "deny"),
    ("MemoryWrite", "", "plan", "default", "allow"),
])
def test_decision(tool, value, capability, mode, expected):
    field = {"Bash": "command", "WebSearch": "query", "WebFetch": "url"}.get(tool, "path")
    assert decide({"toolName": tool, "argsJson": json.dumps({field: value}), "capability": capability, "mode": mode, "rules": emptyPermissions()}) == expected


@pytest.mark.parametrize("command,mode,rule_set,expected", [
    ("rm -rf /", "bypassPermissions", {"deny": ["Bash(rm:*)"]}, "deny"),
    ("rm -rf /", "default", {"allow": ["Bash"], "ask": ["Bash(rm:*)"]}, "ask"),
    ("npm run test", "default", {"allow": ["Bash(npm run test:*)"]}, "allow"),
    ("ls /tmp", "default", {"ask": ["Bash(ls:*)"]}, "ask"),
    ("ls /tmp", "auto", {"ask": ["Bash(ls:*)"]}, "ask"),
    ("python script.py", "auto", {"allow": ["Bash(python:*)"]}, "ask"),
    ("sudo apt update", "auto", {"allow": ["Bash(sudo:*)"]}, "ask"),
    ("node -e console.log(1)", "auto", {"allow": ["Bash(node:*)"]}, "ask"),
    ("python script.py", "default", {"allow": ["Bash(python:*)"]}, "allow"),
    ("ls -la", "auto", {"allow": ["Bash(ls:*)"]}, "allow"),
    ("echo hi", "auto", {"allow": ["Bash"]}, "ask"),
])
def test_rules(command, mode, rule_set, expected):
    assert decide({"toolName": "Bash", "argsJson": json.dumps({"command": command}), "capability": "exec", "mode": mode, "rules": {**emptyPermissions(), **rule_set}}) == expected


@pytest.mark.parametrize("tool,args,expected", [
    ("Write", '{"path":"a/.ssh/config"}', True),
    ("Bash", '{"command":"cat ~/.aws/credentials"}', True),
    ("Write", '{"path":"src/app.ts"}', False),
    ("Write", '{"path":"/Users/x/.dao/config.json"}', True),
    ("Write", '{"path":"/Users/x/.dao/skills/foo/SKILL.md"}', False),
])
def test_sensitive(tool, args, expected):
    assert isSensitiveCall(tool, args) is expected


def test_source_async_runtime_path():
    for command, expected in [("find src -name '*.ts' | wc -l", "allow"), ("git log --oneline -5", "allow"), ("npm install", "ask"), ("cat ~/.ssh/id_rsa", "ask")]:
        assert asyncio.run(decideAsync({"toolName": "Bash", "argsJson": json.dumps({"command": command}), "capability": "exec", "mode": "default", "rules": emptyPermissions()})) == expected
    assert asyncio.run(decideAsync({"toolName": "Bash", "argsJson": '{"command":"ls /tmp"}', "capability": "exec", "mode": "default", "rules": {**emptyPermissions(), "ask": ["Bash(ls:*)"]}})) == "ask"
