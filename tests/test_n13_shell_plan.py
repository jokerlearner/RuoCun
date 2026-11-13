"""D10 actual-dialect adapter confirmation, reusing existing permission seam."""
import asyncio
import base64
import json
import os
from pathlib import Path

import pytest

from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.platform.shell_plan import buildShellPlan
from ruocun.session.session import Session
from ruocun.tools.exec_shell import execShellTool
from ruocun.tools.types import ToolContext, ToolRejected


def test_default_plan_native_command_line(tmp_path):
    plan = buildShellPlan('echo "中文 a&b"', str(tmp_path))
    assert plan.command == 'echo "中文 a&b"' and plan.cwd == str(tmp_path.resolve())
    if os.name == "nt":
        assert plan.dialect == "cmd" and Path(plan.argv[0]).name.lower() == "cmd.exe"
        assert plan.argv[1:4] == ("/d", "/s", "/c")
        assert plan.commandLine.endswith(' /d /s /c "echo "中文 a&b""')


def test_plan_decision_and_real_execution(tmp_path):
    async def scenario():
        prompts = []
        async def ask(text):
            prompts.append(text)
            return "n"
        runtime = await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),
            {**emptyPermissions(),"deny":["Bash(echo blocked:*)"]},ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        assert not await runtime.authorize(execShellTool, json.dumps({"command":"echo blocked"}))
        assert prompts == []
        command = 'echo allowed'
        assert await runtime.authorize(execShellTool,json.dumps({"command":command}))
        ctx=ToolContext(str(tmp_path),getShellPlan=runtime.getShellPlan)
        out=await execShellTool.handler({"command":command},ctx)
        assert "allowed" in out and "[exit 0," in out
        with pytest.raises(ToolRejected):
            await execShellTool.handler({"command":"echo unapproved"},ctx)
    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "nt", reason="cmd adapter")
def test_unknown_cmd_expansion_stays_human(tmp_path):
    async def scenario():
        prompts, classified = [], []
        async def ask(text):
            prompts.append(text)
            return "n"
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),emptyPermissions(),ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        async def classifier(*args):
            classified.append(args)
            return True
        runtime.bindClassifier(classifier,lambda:[])
        assert not await runtime.authorize(execShellTool,json.dumps({"command":"echo %SYNTHETIC%"}))
        assert len(prompts) == 1 and classified == [] and "cmd.exe" in prompts[0]
    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "nt", reason="actual Windows interpreter")
def test_encoded_powershell_inner_deny_does_not_execute_parser_input(tmp_path):
    async def scenario():
        target=tmp_path/"parser-must-not-execute.txt"
        script=f"Set-Content -LiteralPath '{target}' -Value synthetic"
        encoded=base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        engine=Path(os.environ.get("SYSTEMROOT",r"C:\Windows"))/"System32/WindowsPowerShell/v1.0/powershell.exe"
        command=f'"{engine}" -NoProfile -NonInteractive -EncodedCommand {encoded}'
        async def ask(text):
            raise AssertionError("inner deny must not ask")
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),
            {**emptyPermissions(),"deny":["Bash(Set-Content:*)"]},ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        assert not await runtime.authorize(execShellTool,json.dumps({"command":command}))
        assert not target.exists()
    asyncio.run(scenario())


def test_batch_plan_context_is_retained_by_dispatch_task(tmp_path):
    async def scenario():
        async def ask(text):
            return "y"
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),emptyPermissions(),ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        assert await runtime.authorize(execShellTool,'{"command":"echo first"}')
        ready=asyncio.Event()
        release=asyncio.Event()
        async def old_task():
            ready.set()
            await release.wait()
            assert runtime.getShellPlan("echo first",str(tmp_path)).command == "echo first"
            with pytest.raises(ToolRejected):
                runtime.getShellPlan("echo second",str(tmp_path))
        task=asyncio.create_task(old_task())
        await ready.wait()
        assert await runtime.authorize(execShellTool,'{"command":"echo second"}')
        with pytest.raises(ToolRejected):
            runtime.getShellPlan("echo first",str(tmp_path))
        release.set()
        await task
    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "nt", reason="cmd native commandline")
def test_cmd_approved_redirection_preserves_unicode_spaced_path(tmp_path):
    async def scenario():
        target=tmp_path/"中文 空格.txt"
        async def ask(text):
            assert str(target) in text and "cmd.exe" in text
            return "y"
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),emptyPermissions(),ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        command=f'echo synthetic>"{target}"'
        assert await runtime.authorize(execShellTool,json.dumps({"command":command}))
        out=await execShellTool.handler({"command":command},ToolContext(str(tmp_path),getShellPlan=runtime.getShellPlan))
        assert "[exit 0," in out and target.read_bytes().strip() == b"synthetic"
    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "nt", reason="actual cmd lookup")
def test_cwd_script_shadow_is_not_readonly(tmp_path):
    async def scenario():
        (tmp_path/"whoami.cmd").write_text("@echo shadow\n",encoding="ascii")
        prompts, classified = [], []
        async def ask(text):
            prompts.append(text)
            return "n"
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),emptyPermissions(),ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        async def classifier(*args):
            classified.append(args)
            return True
        runtime.bindClassifier(classifier,lambda:[])
        assert not await runtime.authorize(execShellTool,'{"command":"whoami"}')
        assert len(prompts) == 1 and classified == []
    asyncio.run(scenario())


@pytest.mark.skipif(os.name != "nt", reason="actual PowerShell AST")
def test_powershell_call_operator_preserves_inner_deny(tmp_path):
    async def scenario():
        script="& cmd /c 'del target.txt'"
        encoded=base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        engine=Path(os.environ.get("SYSTEMROOT",r"C:\Windows"))/"System32/WindowsPowerShell/v1.0/powershell.exe"
        command=f'"{engine}" -NoProfile -NonInteractive -EncodedCommand {encoded}'
        async def ask(text):
            raise AssertionError("nested deny must not ask")
        runtime=await createPermissionRuntime(tmp_path,tmp_path/"user",Compatibility(1,()),Session("","synthetic",env={}),
            {**emptyPermissions(),"deny":["Bash(del:*)"]},ask,interactive=True,env={"ProgramData":str(tmp_path/"program")})
        assert not await runtime.authorize(execShellTool,json.dumps({"command":command}))
    asyncio.run(scenario())
