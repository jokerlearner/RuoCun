"""Frozen HTTP/SSE requests and the pinned SDK redirect adaptation."""

from __future__ import annotations

import asyncio
import os

import pytest
from support.mcp_http import HttpFixture

from ruocun.mcp.mcp import McpManager
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext


@pytest.mark.parametrize("transport,path", [("http", "/mcp"), ("sse", "/sse")])
def test_source_real_http_sse_headers_and_close(tmp_path, transport, path):
    with HttpFixture() as fixture:
        async def scenario():
            registry = ToolRegistry()
            manager = McpManager(registry, {"mcpServers": {"fixture": {
                "type": transport, "url": fixture.url + path, "headers": {"X-Synthetic": "expected"},
                "command": "must-not-run"}}}, tmp_path, os.environ)
            try:
                await manager.init()
                assert manager.connectedCount == 1, manager.getServerStatus()
                result = await registry.dispatch("mcp__fixture__echo", '{"msg":"原文"}', ToolContext(str(tmp_path)))
                assert result == "actual:原文"
            finally:
                await manager.close()
            assert registry.countByPrefix("mcp__fixture__") == 0
        asyncio.run(scenario())
        assert fixture.wire and all(row["headers"]["X-Synthetic"] == "expected" for row in fixture.wire)
        assert any(row.get("body", {}).get("method") == "tools/call" for row in fixture.wire)
        if transport == "http":
            assert fixture.wire[-1]["method"] == "DELETE"
        else:
            assert fixture.sse_closed.wait(2)


def test_source_http_cross_origin_307_preserves_method_and_strips_authorization(tmp_path):
    with HttpFixture() as target, HttpFixture() as redirect:
        redirect.redirect = target.url + "/mcp"
        async def scenario():
            registry = ToolRegistry()
            manager = McpManager(registry, {"mcpServers": {"redirect": {"url": redirect.url + "/mcp",
                "headers": {"Authorization": "Bearer synthetic-token", "X-Synthetic": "forwarded"}}}}, tmp_path, os.environ)
            try:
                await manager.init()
                assert manager.connectedCount == 1, manager.getServerStatus()
                assert "synthetic-token" not in manager.redact("failure: Bearer synthetic-token")
                assert await registry.dispatch("mcp__redirect__echo", '{"msg":"forwarded"}', ToolContext(str(tmp_path))) == "actual:forwarded"
            finally:
                await manager.close()
        asyncio.run(scenario())
        assert all(row["headers"].get("Authorization") == "Bearer synthetic-token" for row in redirect.wire)
        posts = [row for row in target.wire if row["method"] == "POST"]
        assert [row["body"]["method"] for row in posts] == ["initialize", "notifications/initialized", "tools/list", "tools/call"]
        assert all(row["headers"]["X-Synthetic"] == "forwarded" and "Authorization" not in row["headers"] for row in posts)



def test_source_disabled_state_survives_reopen_and_reconnect_cannot_enable(tmp_path):
    from ruocun.config.mcp_store import writeMcpState

    async def scenario(fixture):
        user = tmp_path / "user"
        state = user / "mcp_state.json"
        config = {"mcpServers": {"one": {"url": fixture.url + "/mcp"}}}

        async def persist(file, value):
            await asyncio.to_thread(writeMcpState, file, value, user_root=user)

        manager = McpManager(ToolRegistry(), config, tmp_path, os.environ, disabled_file=state, persist=persist)
        await manager.init()
        try:
            await manager.toggle("one", False)
            count = len(fixture.wire)
            await manager.reconnect("one")
            assert len(fixture.wire) == count and manager.getServerStatus()[0]["disabled"] is True
        finally:
            await manager.close()
        reopened = McpManager(ToolRegistry(), config, tmp_path, os.environ, disabled_file=state, persist=persist)
        try:
            await reopened.init()
            assert reopened.connectedCount == 0
            await reopened.toggle("one", True)
            assert reopened.connectedCount == 1 and reopened.getServerStatus()[0]["disabled"] is False

            async def fail_save(*_):
                raise OSError("synthetic save failure")
            reopened._persist = fail_save
            try:
                await reopened.toggle("one", False)
            except OSError:
                pass
            else:
                raise AssertionError("save failure was hidden")
            assert reopened.connectedCount == 1 and reopened.getServerStatus()[0]["disabled"] is False
        finally:
            await reopened.close()

    with HttpFixture() as fixture:
        asyncio.run(scenario(fixture))
