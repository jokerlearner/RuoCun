"""冻结identity.test.ts与bash_preprocess.test.ts的来源断言。"""

import json

import pytest

from ruocun.permissions.bash_preprocess import (
    extractOutputRedirections,
    isCompoundCommand,
    stripAllLeadingEnvVars,
    stripSafeWrappers,
)
from ruocun.permissions.identity import rememberRule, toCcIdentity


@pytest.mark.parametrize(("name", "args", "expected"), [
    ("Bash", {"command": "npm test"}, {"ccTool": "Bash", "value": "npm test"}),
    ("Read", {"path": "src/a.ts"}, {"ccTool": "Read", "value": "src/a.ts"}),
    ("Edit", {"path": "src/a.ts"}, {"ccTool": "Edit", "value": "src/a.ts"}),
    ("Write", {"path": "out.txt"}, {"ccTool": "Write", "value": "out.txt"}),
    ("ListDir", {"path": "src"}, {"ccTool": "LS", "value": "src"}),
    ("Grep", {"pattern": "foo", "path": "src"}, {"ccTool": "Grep", "value": "src"}),
    ("Glob", {"glob": "**/*.ts"}, {"ccTool": "Glob", "value": "**/*.ts"}),
    ("WebFetch", {"url": "https://x.com/a"}, {"ccTool": "WebFetch", "value": "https://x.com/a"}),
    ("WebSearch", {"query": "claude"}, {"ccTool": "WebSearch", "value": "claude"}),
    ("mcp__github__search", {}, {"ccTool": "mcp__github__search", "value": ""}),
    ("MemoryWrite", {}, None), ("TodoWrite", {}, None), ("Agent", {}, None),
])
def test_source_identity(name, args, expected):
    assert toCcIdentity(name, json.dumps(args)) == expected


def test_source_invalid_identity_json():
    assert toCcIdentity("Bash", "{bad json") == {"ccTool": "Bash", "value": ""}


@pytest.mark.parametrize(("name", "args", "expected"), [
    ("Bash", {"command": "npm run build"}, "Bash(npm run:*)"),
    ("Bash", {"command": "ls -la"}, "Bash(ls:*)"),
    ("Bash", {"command": "cat a | grep b"}, "Bash(cat a | grep b)"),
    ("Bash", {"command": "cat > f << EOF\nx\nEOF"}, "Bash(cat > f << EOF\nx\nEOF)"),
    ("Bash", {"command": "rm -rf /"}, "Bash(rm:*)"),
    ("Bash", {"command": "cat ~/.aws/credentials"}, "Bash(cat ~/.aws/credentials:*)"),
    ("WebSearch", {"query": "some specific query"}, "WebSearch"),
    ("Edit", {"path": "src/a.ts"}, "Edit(src/a.ts)"),
    ("WebFetch", {"url": "https://api.example.com/x"}, "WebFetch(domain:api.example.com)"),
    ("mcp__github__search", {}, "mcp__github__search"), ("MemoryWrite", {}, None),
])
def test_source_remember(name, args, expected):
    assert rememberRule(name, json.dumps(args)) == expected


@pytest.mark.parametrize(("command", "expected"), [
    ("time npm test", "npm test"), ("nohup npm test", "npm test"),
    ("nice npm test", "npm test"), ("nice -n 5 npm test", "npm test"),
    ("stdbuf -o0 npm test", "npm test"), ("timeout 10 npm test", "npm test"),
    ("timeout 5s npm test", "npm test"), ("timeout -k 2 10 npm test", "npm test"),
    ("timeout --kill-after=2 10 npm test", "npm test"), ("timeout --foreground 10 npm test", "npm test"),
    ("NODE_ENV=prod npm test", "npm test"), ("RUST_LOG=debug cargo build", "cargo build"),
    ("CI=true npm test", "npm test"), ("PATH=/evil npm test", "PATH=/evil npm test"),
    ("LD_PRELOAD=/evil.so npm test", "LD_PRELOAD=/evil.so npm test"),
    ("NODE_ENV=prod timeout 10 npm test", "npm test"),
    ("nohup NODE_ENV=prod npm test", "NODE_ENV=prod npm test"),
    ("# comment\nnpm test", "npm test"), ("# comment\nnpm test\n# another", "npm test"),
    ("npm test", "npm test"), ("git status", "git status"),
])
def test_source_wrappers(command, expected):
    assert stripSafeWrappers(command) == expected


@pytest.mark.parametrize(("command", "expected"), [
    ("FOO=bar rm -rf /", "rm -rf /"), ("DOCKER_HOST=tcp://evil docker ps", "docker ps"),
    ("MY_VAR=val cmd", "cmd"), ("FOO='bar baz' cmd", "cmd"), ('FOO="bar baz" cmd', "cmd"),
    ("FOO=bar BAZ=qux cmd", "cmd"), ("# comment\nFOO=bar cmd", "cmd"), ("npm test", "npm test"),
])
def test_source_strip_all_env(command, expected):
    assert stripAllLeadingEnvVars(command) == expected


@pytest.mark.parametrize(("command", "expected"), [
    ("echo hello > /tmp/out", "echo hello"), ("echo hello >> /tmp/out", "echo hello"),
    ("cmd 2> /tmp/err", "cmd"), ("cmd 2>&1", "cmd"), ("cmd &> /tmp/all", "cmd"),
    ("cmd >/dev/null", "cmd"), ("echo hello", "echo hello"), ("cmd > /tmp/out 2> /tmp/err", "cmd"),
])
def test_source_redirections(command, expected):
    assert extractOutputRedirections(command) == expected


def test_source_compound_detection():
    assert all(isCompoundCommand(value) for value in ("cd /tmp && rm -rf x", "cmd1 || cmd2", "cmd1; cmd2", "cmd1 | cmd2", "cmd1\ncmd2"))
    assert not isCompoundCommand("npm test")
    assert not isCompoundCommand("git status")
