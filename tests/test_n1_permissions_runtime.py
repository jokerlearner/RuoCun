"""Source index/settings/gate/path assembly and commands /plan, adapted for D09."""
import asyncio
import json

from ruocun.config.compat import Compatibility, CompatibilitySource
from ruocun.config.trust import addTrusted
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.session import Session
from ruocun.tools.schema import objectSchema
from ruocun.tools.tool_batch import BatchCall
from ruocun.tools.types import Tool


async def unused(args, ctx):
    return ""


WRITE = Tool("Write", "", objectSchema({}, []), "write", "required", unused)
READ = Tool("Read", "", objectSchema({}, []), "read", "auto", unused)


def test_source_sandbox_bypass_needs_current_human_approval(tmp_path):
    async def scenario():
        requests = []

        async def prompt(batch):
            requests.extend(batch)
            return {item["id"]: "always" for item in batch}

        bash = Tool("Bash", "", objectSchema({}, []), "exec", "required", unused)
        runtime = await createPermissionRuntime(
            tmp_path, tmp_path / "user", Compatibility(1, ()), Session("", "fixture", env={}),
            emptyPermissions(), unused, interactive=True, yolo=True, approvalPrompt=prompt,
            env={"ProgramData": str(tmp_path / "program")},
        )
        raw = json.dumps({"command": "echo synthetic", "dangerouslyDisableSandbox": True})
        for call_id in ("first", "second"):
            assert await runtime.authorizeBatch([BatchCall(call_id, bash, raw, "allow")]) == {call_id: True}
        assert [request["id"] for request in requests] == ["first", "second"]
        assert all(request["noPersist"] and "沙箱" in request["summary"] for request in requests)
        assert await runtime.authorizeBatch([BatchCall("denied", bash, raw, "deny")]) == {"denied": False}
        assert len(requests) == 2

    asyncio.run(scenario())


def write(file, permissions):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"permissions": permissions, "other": "keep"}), encoding="utf-8")


def test_d09_tiers_trust_and_readonly_sources(tmp_path):
    async def scenario():
        cwd, user, program = tmp_path / "project", tmp_path / "user", tmp_path / "program"
        cwd.mkdir()
        native = [user / "settings.json", cwd / ".ruocun/settings.json", cwd / ".ruocun/settings.local.json", program / "RuoCun/managed-settings.json"]
        compatible = [tmp_path / (name + ".json") for name in ("olduser", "oldproject", "oldlocal", "oldmanaged")]
        sources = []
        for index, (old, current) in enumerate(zip(compatible, native)):
            write(old, {"allow": [f"Read(old{index})"], "defaultMode": "auto"})
            write(current, {"allow": [f"Read(native{index})"], "defaultMode": "default"})
            sources.append(CompatibilitySource(str(index), "user" if index == 0 else "managed" if index == 3 else "project", "settings_local" if index == 2 else "settings", str(old), str(cwd) if index in (1, 2) else None))
        before = {p: p.read_bytes() for p in compatible}
        async def ask(prompt):
            return "n"
        cli = {**emptyPermissions(), "allow": ["Read(cli)"], "defaultMode": "plan"}
        runtime = await createPermissionRuntime(cwd, user, Compatibility(1, tuple(sources)), Session("", "fixture", env={}), cli, ask, interactive=False, env={"ProgramData": str(program)})
        assert runtime.getMode() == "default"  # managed native > CLI plan
        assert runtime.getRules()["allow"] == ["Read(old0)", "Read(native0)", "Read(cli)", "Read(old3)", "Read(native3)"]
        assert "信任" in runtime.sourceStates["1"]
        await addTrusted(cwd, userRoot=user)
        runtime = await createPermissionRuntime(cwd, user, Compatibility(1, tuple(sources)), Session("", "fixture", env={}), cli, ask, interactive=False, env={"ProgramData": str(program)})
        assert runtime.getRules()["allow"] == ["Read(old0)", "Read(native0)", "Read(old1)", "Read(native1)", "Read(old2)", "Read(native2)", "Read(cli)", "Read(old3)", "Read(native3)"]
        assert "覆盖" in runtime.sourceStates["0"]
        assert "只读" in await runtime.command("/permissions remove allow Read(old0)")
        await runtime.command("/permissions add deny Write(locked.txt)")
        assert json.loads(native[2].read_text(encoding="utf-8"))["other"] == "keep"
        assert "Write(locked.txt)" in runtime.getRules()["deny"]
        assert before == {p: p.read_bytes() for p in compatible}
    asyncio.run(scenario())


def test_final_args_remember_and_external_paths(tmp_path):
    async def scenario():
        cwd, user = tmp_path / "project", tmp_path / "user"
        cwd.mkdir()
        prompts, answers = [], iter(["a", "y", "y"])
        async def ask(prompt):
            prompts.append(prompt)
            return next(answers)
        cli = {**emptyPermissions(), "defaultMode": "default", "deny": ["Write(locked.txt)"], "additionalDirectories": [str(tmp_path / "extra")]}
        readonly = tmp_path / "skills"
        runtime = await createPermissionRuntime(cwd, user, Compatibility(1, ()), Session("", "fixture", env={}), cli, ask, interactive=True, env={"ProgramData": str(tmp_path / "program")}, readOnlyRoots=(readonly,))
        assert not await runtime.authorize(WRITE, '{"path":"locked.txt"}')
        assert prompts == []
        assert await runtime.authorize(WRITE, '{"path":"safe.txt","content":"synthetic"}')
        assert "Write(safe.txt)" in json.loads((cwd / ".ruocun/settings.local.json").read_text(encoding="utf-8"))["permissions"]["allow"]
        assert await runtime.authorize(WRITE, '{"path":"safe.txt","content":"synthetic"}')
        assert len(prompts) == 1
        assert await runtime.approveExternalRead(str(readonly / "resource.md"))
        assert await runtime.approveExternalRead(str(tmp_path / "extra/data.txt"))
        assert await runtime.approveExternalWrite(str(tmp_path / "extra/data.txt"))
        assert await runtime.approveExternalWrite(str(readonly / "resource.md"))
        assert await runtime.approveExternalWrite(str(readonly / "resource.md"))
        assert len(prompts) == 2  # same-call preflight and handler share once
        assert await runtime.authorize(READ, '{"path":"safe.txt"}')
        assert await runtime.approveExternalWrite(str(readonly / "resource.md"))
        assert len(prompts) == 3
    asyncio.run(scenario())


def test_mode_commands_follow_source_toggle(tmp_path):
    async def scenario():
        async def ask(prompt):
            raise AssertionError("query/mode commands must not ask")
        runtime = await createPermissionRuntime(tmp_path, tmp_path / "user", Compatibility(1, ()), Session("", "fixture", env={}), emptyPermissions(), ask, interactive=False, env={"ProgramData": str(tmp_path / "program")})
        assert runtime.getMode() == "auto"
        assert not runtime.isMutatingCommand("/mode")
        assert not runtime.isMutatingCommand("/permissions list")
        assert not runtime.isMutatingCommand("/permissions add")
        assert not runtime.isMutatingCommand("/permissions add allow")
        assert not runtime.isMutatingCommand("/permissions add nope rule")
        assert not runtime.isMutatingCommand("/permissions remove allow")
        assert runtime.isMutatingCommand("/permissions add allow Read(a.txt)")
        assert runtime.isMutatingCommand("/permissions remove deny Bash(rm:*)")
        assert runtime.isMutatingCommand("/plan")
        await runtime.command("/plan")
        assert runtime.getMode() == "plan"
        await runtime.command("/plan")
        assert runtime.getMode() == "auto"
        await runtime.command("/mode default")
        assert runtime.getMode() == "default"
        runtime.setMode("plan")
        assert runtime.getMode() == "plan"
        runtime.setMode("normal")
        assert runtime.getMode() == "auto"  # source setMode clears the override
        await runtime.command("/bypass")
        assert runtime.getMode() == "bypassPermissions"
        await runtime.command("/yolo")
        assert runtime.getMode() == "auto"
        assert not await runtime.approveExternalWrite(str(tmp_path.parent / "external.txt"))
        assert await runtime.command("/unrelated") is None
    asyncio.run(scenario())
