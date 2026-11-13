"""Frozen capability and live discovery behavior via an independent MCP peer."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from support.mcp_http import HttpFixture

from ruocun.mcp.mcp import McpManager
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext


def test_source_resources_prompts_visibility_notifications_and_elicitation(tmp_path):
    async def scenario():
        registry, notices = ToolRegistry(), []
        manager = McpManager(registry, {"mcpServers": {"caps": {
            "command": sys.executable, "args": ["-I", "-X", "utf8", str(Path(__file__).parent / "support/mcp_caps.py"), str(tmp_path / "peer")]}}},
            tmp_path, os.environ, on_server_change=notices.append)
        ctx = ToolContext(str(tmp_path))

        async def call(name, arguments=None):
            return await registry.dispatch("mcp__caps__" + name, json.dumps(arguments or {}), ctx)

        try:
            await manager.init()
            assert manager.connectedCount == 1, manager.getServerStatus()
            assert registry.countMcpTools() == 10
            assert sum(registry.isMcpVisible(tool["function"]["name"]) for tool in registry.toApiTools()) == 5
            assert not registry.isMcpVisible("mcp__caps__late_tool")
            assert "late_tool" in registry.searchAndActivateMcp("late_tool")
            assert registry.isMcpVisible("mcp__caps__late_tool")
            assert await call("list_resources") == "fixture://readme(说明)\nfixture://plain"
            assert await call("read_resource", {"uri": "fixture://readme/中文 path"}) == "原文\n[二进制内容 application/octet-stream @ fixture://binary]"
            assert await call("list_prompts") == "template(说明)\nplain"
            assert await call("get_prompt", {"name": "template", "arguments": {"word": "传入"}}) == (
                'user: 传入\nassistant: {"type":"image","data":"YWJj","mimeType":"image/png"}')
            assert json.loads(await call("ask"))["action"] == "decline"

            async def elicit(message, schema):
                assert message == "合成问题" and schema["properties"]["choice"]["type"] == "string"
                return {"action": "accept", "content": {"choice": "确认"}}
            manager.on_elicit = elicit
            assert json.loads(await call("ask")) == {"action": "accept", "content": {"choice": "确认"}}
            assert await call("change") == "actual change result"
            async with asyncio.timeout(3):
                while registry.get("mcp__caps__fresh") is None:
                    await asyncio.sleep(.01)
            assert registry.get("mcp__caps__echo") is None
            assert any("工具列表已更新" in notice for notice in notices)
        finally:
            await manager.close()
        assert registry.countMcpTools() == 0
        wire = [json.loads(line) for line in (tmp_path / "peer/wire.jsonl").read_text(encoding="utf-8").splitlines()]
        assert sum(row.get("method") == "tools/list" for row in wire) >= 2
        assert next(row for row in wire if row.get("method") == "prompts/get")["params"]["arguments"] == {"word": "传入"}
        assert next(row for row in wire if row.get("method") == "resources/read")["params"]["uri"] == "fixture://readme/中文 path"
    asyncio.run(scenario())


def test_source_add_persists_native_whole_server_with_frozen_disabled_exception(tmp_path):
    from ruocun.config.mcp_store import writeMcpState

    async def scenario(fixture):
        root = tmp_path / "native"
        config_file, disabled_file = root / "mcp.json", root / "mcp_state.json"
        await asyncio.to_thread(writeMcpState, config_file, {"unrelated": 1, "mcpServers": {"old": {"command": "keep"}}}, user_root=root)

        async def persist(file, value):
            await asyncio.to_thread(writeMcpState, file, value, user_root=root)

        manager = McpManager(ToolRegistry(), {"mcpServers": {}}, tmp_path, os.environ, disabled_file=disabled_file, persist=persist)
        try:
            await manager.toggle("new", False)
            new = {"url": fixture.url + "/mcp", "env": {"SYNTHETIC_API_KEY": "synthetic-value"}}
            await manager.addServer("new", new, config_file)
            assert manager.connectedCount == 1 and manager.getServerStatus()[0]["disabled"] is False
            assert json.loads(disabled_file.read_text(encoding="utf-8")) == {"disabled": ["new"]}
            saved = json.loads(config_file.read_text(encoding="utf-8"))
            assert saved == {"unrelated": 1, "mcpServers": {"old": {"command": "keep"}, "new": new}}
            assert "synthetic-value" not in manager.redact("synthetic-value")
            actual_digest = manager.executionConfigDigest
            await manager.addServer("new", {**new, "url": fixture.url + "/replacement"}, config_file)
            assert manager.config["mcpServers"]["new"]["url"].endswith("/replacement")
            assert manager.executionConfigDigest == actual_digest

            async def fail_save(*_):
                raise OSError("synthetic failed add")
            manager._persist = fail_save
            try:
                await manager.addServer("unknown", {"command": "bad"}, config_file)
            except OSError:
                pass
            else:
                raise AssertionError("unconfirmed save reported success")
            assert "unknown" not in manager.config["mcpServers"]
        finally:
            await manager.close()
    with HttpFixture() as fixture:
        asyncio.run(scenario(fixture))
