"""Source rules async branch adapted to an injected parser until candidate B."""
import asyncio

from ruocun.permissions.rules import evaluateWithAst


def test_async_rule_branches():
    async def simple(command):
        return {"kind": "simple", "subcommands": ["echo 'a;b'"]}

    async def complex_command(command):
        return {"kind": "too-complex", "reason": "command substitution"}

    async def fallback(command):
        return {"kind": "fallback"}

    rules = {"allow": ["Bash(echo:*)"], "ask": [], "deny": []}
    assert asyncio.run(evaluateWithAst(rules, {"ccTool": "Bash", "value": "echo 'a;b'"}, parseBash=simple)) == "allow"
    assert asyncio.run(evaluateWithAst(rules, {"ccTool": "Bash", "value": "echo $(cat x)"}, parseBash=complex_command)) == "ask"
    assert asyncio.run(evaluateWithAst({**rules, "deny": ["Bash(echo:*)"]}, {"ccTool": "Bash", "value": "echo $(cat x)"}, parseBash=complex_command)) == "deny"
    assert asyncio.run(evaluateWithAst(rules, {"ccTool": "Bash", "value": "echo x; unknown"}, parseBash=fallback)) is None
