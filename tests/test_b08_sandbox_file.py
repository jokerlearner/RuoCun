"""Frozen sandbox.test.ts:7–25 and the Windows execution boundary in ADR-0008."""

import asyncio
import json
import os
import threading

import pytest


def test_source_sandbox_default_off_explicit_override_and_platform_error():
    from ruocun.platform.sandbox import sandboxActive, sandboxSpawn

    assert not sandboxActive({})
    assert sandboxSpawn("ls", "/tmp", environ={}) is None
    assert sandboxSpawn("ls", "/tmp", environ={"RUOCUN_SANDBOX": "", "DAO_SANDBOX": "1"}) is None
    assert not sandboxActive({"DAO_SANDBOX": "1"})
    enabled = {"RUOCUN_SANDBOX": "1"}
    assert sandboxSpawn("ls", "/tmp", True, environ=enabled, platform="win32") is None
    assert sandboxSpawn("ls -l", "/tmp/work", environ=enabled, platform="win32") == {
        "error": "当前平台不支持沙箱(仅 macOS/Linux)",
    }


def test_source_sandbox_platform_file_routes_and_missing_binaries():
    from ruocun.platform.sandbox import sandboxSpawn

    enabled = {"RUOCUN_SANDBOX": "1"}
    checked = []

    def exists(path):
        checked.append(path)
        return path in ("/usr/local/bin/bwrap", "/usr/bin/sandbox-exec")

    linux = sandboxSpawn("ls -l", "/tmp/work", environ=enabled, platform="linux", exists=exists)
    assert checked == ["/usr/bin/bwrap", "/bin/bwrap", "/usr/local/bin/bwrap"]
    assert linux == {"file": "/usr/local/bin/bwrap", "args": [
        "--ro-bind", "/", "/", "--bind", "/tmp/work", "/tmp/work", "--tmpfs", "/tmp",
        "--proc", "/proc", "--dev", "/dev", "--die-with-parent", "/bin/sh", "-c", "ls -l",
    ]}
    mac = sandboxSpawn("ls -l", '/tmp/a"b', environ=enabled, platform="darwin", exists=exists)
    assert mac["file"] == "/usr/bin/sandbox-exec" and mac["args"][-3:] == ["/bin/sh", "-c", "ls -l"]
    assert mac["args"][0] == "-p"
    assert mac["args"][1] == (
        '(version 1) (allow default) (deny file-write*) '
        '(allow file-write* (subpath "/tmp/a\\\"b") (subpath "/tmp") (subpath "/private/tmp") '
        '(subpath "/private/var/folders") (literal "/dev/null") (literal "/dev/stdout") '
        '(literal "/dev/stderr") (literal "/dev/dtracehelper"))'
    )
    for platform, executable in (("linux", "bwrap"), ("darwin", "sandbox-exec")):
        result = sandboxSpawn("ls", "/tmp/work", environ=enabled, platform=platform, exists=lambda _: False)
        assert executable in result["error"]


@pytest.mark.skipif(os.name != "nt", reason="Windows native refusal and real ordinary cmd")
def test_windows_bash_refuses_before_backup_or_runner_and_allows_ordinary_shell(tmp_path):
    from ruocun.platform.shell_plan import buildShellPlan
    from ruocun.tools.exec_shell import execShellTool
    from ruocun.tools.managed_shell import ManagedShellManager
    from ruocun.tools.types import ToolContext, ToolRejected

    database = tmp_path / "fixture.db"
    database.write_text("existing test data", encoding="utf-8")
    command = "echo ok>shell-result.txt & type fixture.db"
    output = tmp_path / "shell-result.txt"
    backup = tmp_path / "fixture.db.ruocun-backup"
    enabled = {**os.environ, "RUOCUN_SANDBOX": "1"}
    selected_plan = buildShellPlan(command, str(tmp_path), environ=enabled, analyze=False)

    class UnexpectedStore:
        async def prepare(self, *_):
            pytest.fail("unsupported sandbox prepared a durable runner")

    async def scenario():
        ctx = ToolContext(str(tmp_path), getShellPlan=lambda *_: selected_plan)
        managed = ManagedShellManager(tmp_path / "session", "synthetic", UnexpectedStore())
        with pytest.raises(ToolRejected, match="当前平台不支持沙箱"):
            await execShellTool.handler({"command": command}, ctx)
        ctx.managedShell = managed
        for background in (False, True):
            with pytest.raises(ToolRejected, match="当前平台不支持沙箱"):
                await execShellTool.handler({"command": command, "background": background}, ctx)
            with pytest.raises(ToolRejected, match="当前平台不支持沙箱"):
                await managed.execute(selected_plan, threading.Event(), background=background)
        # The frozen background branch does not forward the foreground override.
        with pytest.raises(ToolRejected, match="当前平台不支持沙箱"):
            await execShellTool.handler({"command": command, "background": True, "dangerouslyDisableSandbox": True}, ctx)
        assert not output.exists() and not backup.exists() and not (tmp_path / "session").exists()
        ctx.managedShell = None
        assert execShellTool.checkPermissions(json.dumps({"command": command, "dangerouslyDisableSandbox": True})) == "ask"
        assert "exit 0" in await execShellTool.handler({"command": command, "dangerouslyDisableSandbox": True}, ctx)
        assert output.read_text().strip() == "ok" and backup.read_text() == "existing test data"
        output.unlink()
        ctx.getShellPlan = lambda *_: buildShellPlan(command, str(tmp_path), environ={**enabled, "RUOCUN_SANDBOX": "0"},
                                                     analyze=False)
        assert "exit 0" in await execShellTool.handler({"command": command}, ctx)
        assert output.read_text().strip() == "ok"

    asyncio.run(scenario())
