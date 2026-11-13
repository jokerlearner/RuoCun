"""Preserve the frozen comparison evidence and test the native Shell tool contract."""
import asyncio
import hashlib
import json
import re
import zipfile
from pathlib import Path

from ruocun.tools.exec_shell_kill import execShellKillTool
from ruocun.tools.exec_shell_poll import execShellPollTool
from ruocun.tools.types import ToolContext


def _source(text, key, following):
    exported = text.split("export const", 1)[1]
    expression = re.search(r"\b" + key + r":\s*(.*?)\n\s*" + following + r":", exported, re.S)[1]
    return "".join(json.loads(value) for value in re.findall(r'"(?:\\.|[^"\\])*"', expression))


def test_native_shell_tool_help_and_frozen_evidence():
    project = Path(__file__).resolve().parents[1]
    archive = project / ".scratch/ruocun-discovery/reference/dao-f17e189-7ac654a0dc06/source.zip"
    records = json.loads((project / "tests/fixtures/n15-shell-tool-contracts.json").read_text("utf-8"))
    with zipfile.ZipFile(archive) as frozen:
        for tool, stem in ((execShellPollTool, "exec_shell_poll"), (execShellKillTool, "exec_shell_kill")):
            assert tool.descriptionEn is not None
            payload = frozen.read("src/tools/" + stem + ".ts")
            text = payload.decode("utf-8").replace("\r", "")
            resource = records[stem]
            assert resource["_source"]["sha256"] == hashlib.sha256(payload).hexdigest()
            for key, following in (("description", "descriptionEn"), ("descriptionEn", "capability")):
                original = _source(text, key, following)
                assert resource["_source"][key] == original
                adapted = original
                for replacement in resource["adaptations"][key]:
                    assert replacement["from"] in adapted
                    adapted = adapted.replace(replacement["from"], replacement["to"])
                help_text = getattr(tool, key)
                assert help_text != adapted
                assert ".dao/bg/" not in help_text and "SIGTERM" not in help_text
                if tool.name == "BashOutput":
                    assert "runnerDir" in help_text
                    assert ("会收到通知" if key == "description" else "automatically") in help_text
                else:
                    assert "BashOutput" in help_text
            assert tool.schema["properties"]["id"]["type"] == "string"
            assert tool.schema["required"] == ["id"] and tool.approval == "auto"


def test_existing_messages_follow_context_language(tmp_path):
    class Manager:
        status = "running"
        reason = None
        async def poll(self, run_id):
            return {"status": self.status, "stdout": "", "stderr": "", "runnerDir": str(tmp_path), "exitCode": 0}
        async def cancel(self, run_id):
            return {"status": self.status, **({"reason": self.reason} if self.reason else {})}
    async def scenario():
        context = ToolContext(str(tmp_path), lang="en")
        assert "not bound" in await execShellPollTool.handler({"id": "synthetic-contract"}, context)
        context.managedShell = manager = Manager()
        assert "still running" in await execShellPollTool.handler({"id": "synthetic-contract"}, context)
        assert "recent check" in await execShellPollTool.handler({"id": "synthetic-contract"}, context)
        manager.status = "completed"
        assert "Status: exited" in await execShellPollTool.handler({"id": "synthetic-contract"}, context)
        manager.status = "not-found"
        assert "No active run" in await execShellKillTool.handler({"id": "synthetic-contract"}, context)
        manager.status = "canceling"
        assert "Requested termination" in await execShellKillTool.handler({"id": "synthetic-contract"}, context)
        context.lang = "zh"
        assert "已向 synthetic-contract 请求终止" in await execShellKillTool.handler({"id": "synthetic-contract"}, context)
        manager.status = "unknown"
        manager.reason = "synthetic authentication unconfirmed"
        assert "未发出" in await execShellKillTool.handler({"id": "synthetic-contract"}, context)
        context.lang = "en"
        assert "no termination request" in await execShellKillTool.handler({"id": "synthetic-contract"}, context)
    asyncio.run(scenario())
