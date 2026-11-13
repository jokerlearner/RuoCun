"""冻结permissions/rules.test.ts的公开规则接缝。"""

import pytest

from ruocun.permissions.rules import evaluate, parseRule, ruleMatches, splitBashCommands


def test_parse_rule():
    assert parseRule("Bash") == {"tool": "Bash"}
    assert parseRule("Bash(npm run test:*)") == {"tool": "Bash", "specifier": "npm run test:*"}
    assert parseRule("Edit(src/**)") == {"tool": "Edit", "specifier": "src/**"}
    assert parseRule("mcp__server__tool") == {"tool": "mcp__server__tool"}


@pytest.mark.parametrize(("rule", "tool", "value", "expected"), [
    ("Bash", "Bash", "rm -rf /", True),
    ("Bash(npm run test:*)", "Bash", "npm run test", True),
    ("Bash(npm run test:*)", "Bash", "npm run test -- --watch", True),
    ("Bash(npm run test:*)", "Bash", "npm install", False),
    ("Bash(git status)", "Bash", "git status -s", False),
    ("Bash", "Read", "x", False),
    ("Edit(src/**)", "Edit", "src/a/b.ts", True),
    ("Edit(src/**)", "Edit", "lib/x.ts", False),
    ("Read(*.env)", "Read", "secret.env", True),
    ("Read(*.env)", "Read", "config.json", False),
    ("Read(//tmp/**)", "Read", "/tmp/x/y", True),
    ("WebFetch(domain:example.com)", "WebFetch", "https://api.example.com/x", True),
    ("WebFetch(domain:example.com)", "WebFetch", "https://evil.com", False),
    ("Bash(ls:*)", "Bash", "ls -la", True),
    ("Bash(ls:*)", "Bash", "lsof", False),
    ("Bash(ls:*)", "Bash", "lsattr", False),
    ("Bash(git commit:*)", "Bash", "git config user.name", False),
    ("Bash(grep:*)", "Bash", "xargs grep -r pattern", True),
    ("Bash(grep:*)", "Bash", "xargs -n1 grep pattern", False),
])
def test_source_rule_matches(rule, tool, value, expected):
    assert ruleMatches(parseRule(rule), {"ccTool": tool, "value": value}) is expected
    if rule == "Read(*.env)" and value == "secret.env":
        # JS RegExp without /u counts UTF-16 units, including '?' matches.
        assert not ruleMatches(parseRule("Read(secret?.txt)"), {"ccTool": "Read", "value": "secret😀.txt"})


@pytest.mark.parametrize(("command", "allow", "ask", "deny", "expected"), [
    ("rm -rf /", ["Bash"], [], ["Bash(rm:*)"], "deny"),
    ("rm -rf /", ["Bash"], ["Bash(rm:*)"], [], "ask"),
    ("rm -rf /", ["Bash(rm:*)"], [], [], "allow"),
    ("rm -rf /", ["Bash(npm:*)"], [], [], None),
    ("cd /tmp && rm -rf /", ["Bash(cd:*)"], [], ["Bash(rm -rf:*)"], "deny"),
    ("npm i && git status", ["Bash(npm:*)", "Bash(git:*)"], [], [], "allow"),
    ("npm run build && rm -rf x", ["Bash(npm run build)"], [], [], None),
    ("npm i && deploy", ["Bash(npm:*)"], ["Bash(deploy)"], [], "ask"),
    ("timeout 10 rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("nohup rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("nice -n 5 rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("time rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("stdbuf -o0 npm test", ["Bash(npm:*)"], [], [], "allow"),
    ("nohup timeout 10 npm test", ["Bash(npm:*)"], [], [], "allow"),
    ("FOO=bar rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("DOCKER_HOST=tcp://evil docker ps", [], [], ["Bash(docker:*)"], "deny"),
    ("FOO=bar deploy prod", [], ["Bash(deploy:*)"], [], "ask"),
    ("NODE_ENV=prod npm test", ["Bash(npm:*)"], [], [], "allow"),
    ("DOCKER_HOST=tcp://evil docker ps", ["Bash(docker:*)"], [], [], None),
    ("FOO=bar nohup timeout 5 rm -rf /tmp", [], [], ["Bash(rm:*)"], "deny"),
    ("cd /tmp && rm -rf x", ["Bash(cd:*)"], [], [], None),
    ("echo hello && rm -rf /", ["Bash(echo:*)"], [], ["Bash(rm:*)"], "deny"),
    ("python script.py > /tmp/out", ["Bash(python:*)"], [], [], "allow"),
    ("rm -rf /tmp > /dev/null", [], [], ["Bash(rm:*)"], "deny"),
    ("npm test 2>&1", ["Bash(npm:*)"], [], [], "allow"),
    ("cd /fixture/fishing && git status", ["Bash(cd /fixture/fishing && git status)"], [], [], "allow"),
    ("cd /tmp && deploy prod", ["Bash(cd /tmp && deploy prod)"], ["Bash(deploy:*)"], [], "ask"),
    ("cd /tmp && rm -rf x", ["Bash(cd /tmp && rm -rf x)"], [], ["Bash(rm:*)"], "deny"),
    ("git status", ["Bash(git status)"], [], [], "allow"),
])
def test_source_bash_evaluate(command, allow, ask, deny, expected):
    assert evaluate({"allow": allow, "ask": ask, "deny": deny}, {"ccTool": "Bash", "value": command}) == expected


def test_source_split_commands():
    assert splitBashCommands("cd /tmp && rm -rf x") == ["cd /tmp", "rm -rf x"]
    assert splitBashCommands("a || b ; c | d") == ["a", "b", "c", "d"]
    assert splitBashCommands("npm test") == ["npm test"]
