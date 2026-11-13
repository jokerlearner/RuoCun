"""DAO approval store/stdin_prompt existing cases (MIT)."""
import asyncio
import json

from ruocun.approval.stdin_prompt import makeApprovalPrompt
from ruocun.approval.store import appendAlwaysApproved, loadAlwaysApproved


def request(id):
    return {"id": id, "toolName": "Bash", "capability": "exec", "summary": "$ cmd-" + id}


def test_store(tmp_path):
    file = tmp_path / ".ruocun" / "approvals.json"
    assert asyncio.run(loadAlwaysApproved(file)) == set()
    asyncio.run(appendAlwaysApproved(file, "Write"))
    assert "Write" in asyncio.run(loadAlwaysApproved(file))
    asyncio.run(appendAlwaysApproved(file, "Write"))
    assert json.loads(file.read_text(encoding="utf-8")) == ["Write"]


def test_noninteractive_and_empty():
    calls = []
    async def ask(prompt):
        calls.append(prompt)
        return "y"
    assert asyncio.run(makeApprovalPrompt(ask, False)([request("1"), request("2")])) == {"1": "deny", "2": "deny"}
    assert asyncio.run(makeApprovalPrompt(ask, True)([])) == {}
    assert calls == []


def test_answers():
    answers = iter(["y", "a", "n", "garbage"])
    async def ask(prompt):
        return next(answers)
    assert asyncio.run(makeApprovalPrompt(ask, True)([request(str(i)) for i in range(1, 5)])) == {"1": "once", "2": "always", "3": "deny", "4": "deny"}


def test_prompt_hints():
    prompts = []
    async def ask(prompt):
        prompts.append(prompt)
        return "a"
    prompt = makeApprovalPrompt(ask, True)
    assert asyncio.run(prompt([{**request("s"), "sensitive": True}])) == {"s": "always"}
    assert "[a]始终允许(同类不再问)" in prompts[-1]
    assert asyncio.run(prompt([{**request("d"), "sensitive": True, "dangerous": True}])) == {"d": "deny"}
    assert "[y]是(仅本次) [n]否" in prompts[-1] and "[a]" not in prompts[-1]
    assert asyncio.run(prompt([{**request("p"), "noPersist": True}])) == {"p": "deny"}
    assert "[a]" not in prompts[-1]
    asyncio.run(prompt([request("n")]))
    assert "[a]始终允许(记住,同类不再问)" in prompts[-1]
