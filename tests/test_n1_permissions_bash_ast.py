"""DAO permissions/bash/bash_ast.test.ts assertions (MIT)."""
import asyncio

import pytest

from ruocun.permissions.bash.bash_ast import parseBashForSecurity


@pytest.mark.parametrize("command,kind", [
    ("npm test", "simple"), ("npm i && git status", "simple"),
    ("echo hello | grep foo", "simple"), ("", "simple"),
    ("echo hello > /tmp/out", "simple"), ("NODE_ENV=prod npm test", "simple"),
    ("echo $(rm -rf /)", "too-complex"), ("echo `rm -rf /`", "too-complex"),
    ("(rm -rf /)", "simple"), ("echo {a,b,c}", "too-complex"),
    ("for i in 1 2 3; do echo $i; done", "too-complex"),
    ("for x in foo bar; do echo hi; done", "simple"),
    ("if true; then echo yes; fi", "simple"), ("while true; do echo hi; done", "simple"),
    ("eval 'rm -rf /'", "too-complex"), ("source /tmp/evil.sh", "too-complex"),
    ("echo hello\\&\\&world", "simple"), ("echo 'hello && world'", "simple"),
    ("echo 'a | b'", "simple"), ('echo "$(rm -rf /)"', "too-complex"),
    ('jq \'.system("rm -rf /")\'', "too-complex"),
    ("zmodload zsh/system", "too-complex"), ("exec rm -rf /", "too-complex"),
    ("trap 'rm -rf /' EXIT", "too-complex"),
])
def test_source_kind(command, kind):
    result = asyncio.run(parseBashForSecurity(command))
    assert result["kind"] == kind
    if command == "npm test":
        assert result["subcommands"] == ["npm test"]
    elif command == "npm i && git status":
        assert result["subcommands"] == ["npm i", "git status"]
    elif command == "":
        assert result["subcommands"] == []
    elif command == "echo hello | grep foo":
        assert len(result["subcommands"]) == 2
    elif command in ("echo hello > /tmp/out", "NODE_ENV=prod npm test", "echo 'hello && world'", "echo 'a | b'"):
        assert len(result["subcommands"]) == 1
    elif command == "(rm -rf /)":
        assert any("rm -rf /" in sub for sub in result["subcommands"])
    elif command in ("for x in foo bar; do echo hi; done", "while true; do echo hi; done"):
        assert any("echo hi" in sub for sub in result["subcommands"])
    elif command == "if true; then echo yes; fi":
        assert any("true" in sub for sub in result["subcommands"])
        assert any("echo yes" in sub for sub in result["subcommands"])


def test_source_cases_without_hard_kind_assertion():
    # Frozen tests have only conditional empty branches for these two inputs.
    for command in ("case x in a) echo a;; esac", "echo $((1+1))"):
        result = asyncio.run(parseBashForSecurity(command))
        if result["kind"] == "too-complex":
            pass
