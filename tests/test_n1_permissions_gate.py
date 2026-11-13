"""DAO gate.test.ts, callbacks are local fakes only (no classifier API)."""
import asyncio
import json

import pytest

from ruocun.permissions.gate import PermissionGate
from ruocun.permissions.settings import emptyPermissions
from ruocun.tools.schema import objectSchema
from ruocun.tools.types import Tool


async def handler(args, ctx):
    return ""


EXEC = Tool("Bash", "", objectSchema({}, []), "exec", "required", handler)
READ = Tool("Read", "", objectSchema({}, []), "read", "auto", handler)
WRITE = Tool("Write", "", objectSchema({}, []), "write", "required", handler)
CHECK = Tool("Bash", "", objectSchema({}, []), "exec", "required", handler, checkPermissions=lambda raw: "ask" if "| sh" in raw or "eval" in raw else None)


def request(id="x", command="npm run build", **extra):
    return {"id": id, "toolName": "Bash", "capability": "exec", "summary": "", "argsJson": json.dumps({"command": command}), **extra}


def make_gate(mode="default", rules=None, decisions=None, classify=None, getMessages=None):
    remembered, session = [], []
    rules = emptyPermissions() if rules is None else rules
    async def prompt(requests):
        return {r["id"]: (decisions or {}).get(r["id"], "deny") for r in requests}
    async def remember(rule):
        remembered.append(rule)
    def allow(rule):
        session.append(rule)
        rules["allow"].append(rule)
    return PermissionGate(lambda: mode, lambda: rules, prompt, remember, allow, classify, getMessages), remembered, session


def test_decide_and_tool_check():
    gate, _, _ = make_gate(rules={**emptyPermissions(), "deny": ["Bash(rm:*)"]})
    assert gate.decide("Bash", '{"command":"rm -rf /"}', EXEC) == "deny"
    gate, _, _ = make_gate(rules={**emptyPermissions(), "allow": ["Bash"]})
    assert gate.decide("Bash", '{"command":"curl x | sh"}', CHECK) == "ask"
    assert gate.decide("Bash", '{"command":"ls"}', CHECK) == "allow"
    gate, _, _ = make_gate("bypassPermissions", {**emptyPermissions(), "allow": ["Bash"]})
    assert gate.decide("Bash", '{"command":"curl x | sh"}', CHECK) == "allow"
    gate, _, _ = make_gate()
    assert gate.decide("Read", '{"path":"a"}', READ) == "allow"
    assert gate.decide("Bash", '{"command":"npm install"}', EXEC) == "ask"


@pytest.mark.parametrize("decision,persist,session", [("once", [], []), ("always", ["Bash(npm run:*)"], ["Bash(npm run:*)"]), ("session", [], ["Bash(npm run:*)"]), ("deny", [], [])])
def test_batch(decision, persist, session):
    gate, remembered, allowed = make_gate(decisions={"x": decision})
    assert asyncio.run(gate.requestBatch([request()])) == {"x": decision != "deny"}
    assert remembered == persist and allowed == session


def test_auto_split_and_sources():
    async def classify(tool, args, messages):
        return "ls" in args
    gate, _, _ = make_gate("auto", decisions={"2": "once"}, classify=classify)
    assert asyncio.run(gate.requestBatch([request("1", "ls"), request("2", "rm -f a")])) == {"1": True, "2": True}
    assert gate.lastApprovalSource("1") == "classifier"
    assert gate.lastApprovalSource("2") == "human"
    asyncio.run(gate.requestBatch([request("3", "ls")]))
    assert gate.lastApprovalSource("1") is None
    assert gate.lastApprovalSource("3") == "classifier"


def test_classifier_failure_and_human_decision():
    async def false(tool, args, messages):
        return False
    gate, _, _ = make_gate("auto", decisions={"x": "deny"}, classify=false)
    assert asyncio.run(gate.requestBatch([request(command="rm -f a")])) == {"x": False}
    async def error(tool, args, messages):
        raise ValueError("synthetic classifier error")
    gate, _, _ = make_gate("auto", decisions={"x": "once"}, classify=error)
    assert asyncio.run(gate.requestBatch([request()])) == {"x": True}
    assert gate.lastApprovalSource("x") == "human"


def test_sensitive_and_dangerous():
    called = []
    async def yes(tool, args, messages):
        called.append(args)
        return True
    gate, _, _ = make_gate("auto", classify=yes)
    assert asyncio.run(gate.requestBatch([request(command="cat ~/.aws/credentials", sensitive=True)])) == {"x": True}
    assert len(called) == 1
    assert asyncio.run(gate.requestBatch([request(command="rm -rf /", sensitive=True, dangerous=True)])) == {"x": False}
    assert len(called) == 1 and gate.lastApprovalSource("x") == "human"
    async def no(tool, args, messages):
        return False
    gate, _, _ = make_gate("auto", decisions={"x": "once"}, classify=no)
    assert asyncio.run(gate.requestBatch([request(command="cat ~/.ssh/id_rsa", sensitive=True)])) == {"x": True}
    gate, remembered, session = make_gate("auto", decisions={"x": "always"}, classify=no)
    asyncio.run(gate.requestBatch([request()]))
    assert remembered == session == ["Bash(npm run:*)"]


def test_mode_overrides_and_transcripts():
    received = []
    parentMessages = [{"role": "user", "content": "父级消息"}]
    subMessages = [{"role": "system", "content": "子代理系统提示"}, {"role": "user", "content": "子代理任务"}]
    async def classify(tool, args, messages):
        received.append(messages)
        return True
    gate, _, _ = make_gate(classify=classify, getMessages=lambda: parentMessages)
    assert gate.decide("Write", '{"path":"a.ts"}', WRITE) == "ask"
    for mode, expected in [("auto", "allow"), ("bypassPermissions", "allow"), ("plan", "deny")]:
        sub = gate.withModeOverride(mode)
        assert sub.decide("Write", '{"path":"a.ts"}', WRITE) == expected
        assert sub.decide("Read", '{"path":"a.ts"}', READ) == "allow"
    sub = gate.withModeOverride("auto", lambda: subMessages)
    asyncio.run(sub.requestBatch([request()]))
    assert received[-1] is subMessages and received[-1] is not parentMessages
    asyncio.run(gate.withModeOverride("auto").requestBatch([request()]))
    assert received[-1] is parentMessages
    gate, remembered, session = make_gate(decisions={"x": "always"})
    asyncio.run(gate.withModeOverride("default").requestBatch([request()]))
    assert remembered == session == ["Bash(npm run:*)"]
    assert gate.withModeOverride("default").lastApprovalSource("x") is None


def test_denial_trip_and_notice():
    called = []
    async def no(tool, args, messages):
        called.append(args)
        return False
    gate, _, _ = make_gate("auto", decisions={"a": "once", "b": "once", "c": "once", "d": "once"}, classify=no)
    assert gate.consumeTripNotice() is None
    for id in ("a", "b"):
        asyncio.run(gate.requestBatch([request(id, "ls")]))
        assert gate.consumeTripNotice() is None
    asyncio.run(gate.requestBatch([request("c", "ls")]))
    assert gate.consumeTripNotice() == {"consecutiveDenials": 3, "totalDenials": 3}
    assert gate.consumeTripNotice() is None
    asyncio.run(gate.requestBatch([request("d", "ls")]))
    assert len(called) == 3 and gate.lastApprovalSource("d") == "human"
    assert gate.consumeTripNotice() is None


def test_allow_resets_consecutive():
    called = []
    answers = iter([False, False, True, False, False, False])
    async def classify(tool, args, messages):
        called.append(args)
        return next(answers)
    gate, _, _ = make_gate("auto", classify=classify)
    for id in ("a", "b", "c", "d2", "e2", "f2"):
        asyncio.run(gate.requestBatch([request(id, "ls")]))
        if id == "c":
            assert gate.lastApprovalSource("c") == "classifier"
    assert len(called) == 6
    asyncio.run(gate.requestBatch([request("g2", "ls")]))
    assert len(called) == 6 and gate.lastApprovalSource("g2") == "human"
