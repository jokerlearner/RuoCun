"""Frozen index/execute/gate integration with synthetic classifier and native audit."""
import asyncio
import json

from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.session import Session
from ruocun.tools.schema import objectSchema
from ruocun.tools.types import Tool


async def unused(args, ctx):
    return ""


WRITE = Tool("Write", "", objectSchema({}, []), "write", "required", unused)
BASH = Tool("Bash", "", objectSchema({}, []), "exec", "required", unused)


def test_runtime_classifier_audit_and_failed_fallback(tmp_path):
    async def scenario():
        session = Session("", "synthetic", env={})
        prompts, classified = [], []
        async def ask(text):
            prompts.append(text)
            return "y"
        runtime = await createPermissionRuntime(tmp_path, tmp_path/"user", Compatibility(1,()), session,
            {**emptyPermissions(), "deny":["Write(locked.txt)"]}, ask, interactive=True,
            env={"ProgramData":str(tmp_path/"program")})
        async def classifier(name, raw, messages):
            classified.append(messages)
            if "unknown" in raw:
                raise TimeoutError("synthetic timeout")
            return True
        runtime.bindClassifier(classifier, lambda: session.messages)
        runtime.bindAudit(tmp_path/"session", {})
        assert not await runtime.authorize(WRITE, '{"path":"locked.txt"}')
        assert classified == prompts == []
        assert await runtime.authorize(WRITE, '{"path":".ssh/id_rsa"}')
        assert classified[-1] is session.messages and prompts == []
        assert await runtime.authorize(WRITE, '{"path":".ssh/unknown"}')
        assert len(prompts) == 1
        rows = [json.loads(line) for line in (tmp_path/"session/perm-trace.jsonl").read_text(encoding="utf-8").splitlines()]
        assert [(r["decision"],r["source"]) for r in rows] == [("deny","rule"),("ask-approved","classifier"),("ask-approved","human")]
        # Explicit mode switch skips classifier, including noninteractive fallback.
        await runtime.command("/mode default")
        assert await runtime.authorize(WRITE, '{"path":"normal.txt"}')
        assert len(classified) == 2 and len(prompts) == 2
    asyncio.run(scenario())


def test_headless_failure_has_no_allow_and_audit_redacts(tmp_path):
    async def scenario():
        async def ask(text):
            raise AssertionError("headless must not ask stdin")
        runtime = await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),emptyPermissions(),ask,interactive=False,env={"ProgramData":str(tmp_path/"program")})
        async def classifier(name,raw,messages):
            return False
        runtime.bindClassifier(classifier, lambda: [])
        runtime.bindAudit(tmp_path/"session", {})
        assert not await runtime.authorize(WRITE, '{"path":".ssh/synthetic"}')
        assert not await runtime.authorize(BASH, json.dumps({"command":"npm install AKIA1234567890ABCDEF"}))
        text=(tmp_path/".ruocun/audit.log").read_text(encoding="utf-8")
        assert "AKIA1234567890ABCDEF" not in text
    asyncio.run(scenario())
