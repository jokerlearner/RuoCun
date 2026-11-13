"""Frozen MCP config, tool schema and actual independent stdio round trips."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from ruocun.mcp.mcp import McpManager, loadMcpConfig, unpack
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.tool_batch import UnknownToolOutcome
from ruocun.tools.types import ToolContext


def test_source_config_whole_server_override_and_result_unpack(tmp_path):
    first = tmp_path / "user.json"
    second = tmp_path / "project.json"
    first.write_text(json.dumps({"mcpServers": {"one": {"command": "old", "args": ["old"], "env": {"old": "v"}}}}))
    second.write_text(json.dumps({"mcpServers": {"one": {"command": "new"}, "two": {"command": "second"}}}))
    bad = tmp_path / "bad.json"
    bad.write_text("{")
    cfg = asyncio.run(loadMcpConfig([first, bad, tmp_path / "missing", second]))
    assert cfg == {"mcpServers": {"one": {"command": "new"}, "two": {"command": "second"}}}
    assert unpack({"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}) == "a\nb"
    assert unpack({"content": [{"type": "image", "data": "fixture"}]}) == '{"type":"image","data":"fixture"}'
    assert unpack({"content": []}) == "(无输出)"


def test_source_real_stdio_schema_environment_isolation_and_no_unknown_replay(tmp_path):
    async def scenario():
        fixture = Path(__file__).parent / "support" / "mcp_server.py"
        runtime = tmp_path / "server"
        registry = ToolRegistry()
        manager = McpManager(registry, {"mcpServers": {
            "missing": {"command": str(tmp_path / "missing.exe")},
            "controlled": {"command": sys.executable, "args": ["-I", "-X", "utf8", str(fixture.resolve()), str(runtime), "原文 参数"],
                           "env": {"SYNTHETIC_SERVER": "configured"}},
        }}, tmp_path, {**os.environ, "SYNTHETIC_PARENT": "inherited"})
        try:
            await manager.init()
            assert manager.connectedCount == 1
            statuses = manager.getServerStatus()
            assert statuses[0]["ok"] is False and statuses[1]["ok"] is True
            api = registry.toApiTools()
            assert [tool["function"]["name"] for tool in api] == [
                "mcp__controlled__echo", "mcp__controlled__reject", "mcp__controlled__crash",
            ]
            assert api[0]["function"]["parameters"]["$schema"].endswith("draft-07/schema#")
            assert api[0]["function"]["parameters"]["properties"]["msg"]["type"] == ["string", "null"]
            tool = registry.get("mcp__controlled__echo")
            assert tool.capability == "network" and tool.persistentEffect is True
            ctx = ToolContext(str(tmp_path))
            output = await registry.dispatch("mcp__controlled__echo", '{"msg":null,"extra":{"n":1}}', ctx)
            assert output == '{"msg":null,"extra":{"n":1}}\n{"type":"resource_link","uri":"fixture://plain","name":"fixture","custom":null}'
            rejected = await registry.dispatch("mcp__controlled__reject", "{}", ctx)
            assert "synthetic tool rejection" in rejected
            try:
                await registry.dispatch("mcp__controlled__crash", "{}", ctx)
            except UnknownToolOutcome:
                pass
            else:
                raise AssertionError("the remote side effect lost its response")
            assert (runtime / "effects").read_text() == "1"
        finally:
            await manager.close()
        rows = [json.loads(line) for line in (runtime / "wire.jsonl").read_text("utf-8").splitlines()]
        assert rows[0]["cwd"] == str(tmp_path) and rows[0]["sentinel"] == "inherited"
        assert rows[0]["configured"] == "configured" and rows[0]["arguments"] == ["原文 参数"]
        initialize = next(row["in"] for row in rows if row.get("in", {}).get("method") == "initialize")
        assert initialize["params"]["clientInfo"]["name"] == "ruocun"
        assert "elicitation" in initialize["params"]["capabilities"]
        assert len([row for row in rows if row.get("in", {}).get("method") == "tools/call"]) == 3

    asyncio.run(scenario())



def test_source_windows_cmd_starts_with_declared_argv_and_closes_real_server(tmp_path):
    if os.name != "nt":
        return
    import _winapi

    async def scenario():
        fixture = (Path(__file__).parent / "support" / "mcp_server.py").resolve()
        runtime = tmp_path / "batch server"
        wrapper = tmp_path / "MCP 测试.cmd"
        wrapper.write_text(f'@echo off\n"{sys.executable}" -I -X utf8 "{fixture}" "{runtime}" "batch argument"\n',
                           encoding="utf-8")
        registry = ToolRegistry()
        manager = McpManager(registry, {"mcpServers": {"batch": {"command": str(wrapper)}}},
                             tmp_path, os.environ)
        await manager.init()
        assert manager.connectedCount == 1, manager.getServerStatus()
        pid = int((runtime / "pid").read_text())
        handle = _winapi.OpenProcess(0x100000, False, pid)
        try:
            output = await registry.dispatch("mcp__batch__echo", '{"msg":"actual stdio"}', ToolContext(str(tmp_path)))
            assert "actual stdio" in output
            await manager.close()
            assert _winapi.WaitForSingleObject(handle, 0) == _winapi.WAIT_OBJECT_0
        finally:
            _winapi.CloseHandle(handle)
            await manager.close()
        rows = [json.loads(line) for line in (runtime / "wire.jsonl").read_text("utf-8").splitlines()]
        assert rows[-1] == {"closed": "stdin-eof"}
        assert rows[0]["arguments"] == ["batch argument"] and registry.countByPrefix("mcp__batch__") == 0

    asyncio.run(scenario())
