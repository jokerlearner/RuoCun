"""ArchiveRead is a bounded public read tool, scoped by its runtime context."""

import asyncio
import json

import pytest

from ruocun.tools.types import ToolContext


def test_archive_read_returns_the_authorized_original_text_page():
    from ruocun.tools.archive_read import makeArchiveReadTool

    async def read(_identity, _offset, _limit):
        return {"id": "summary-1", "text": "原始工具结果", "total": 6, "next_offset": None}

    ctx = ToolContext("synthetic-workspace", archiveRead=read)
    result = asyncio.run(makeArchiveReadTool().handler({"id": "summary-1"}, ctx))
    assert json.loads(result)["text"] == "原始工具结果"


def test_preparing_a_normal_child_does_not_inherit_parent_archive_authority(tmp_path):
    from ruocun.agent.agent_defs import AgentDefinition
    from ruocun.agent.run_agent import prepareAgentRun
    from ruocun.config.compat import Compatibility
    from ruocun.permissions.runtime import createPermissionRuntime
    from ruocun.permissions.settings import emptyPermissions
    from ruocun.session.session import Session
    from ruocun.tools.agent import AgentRequest
    from ruocun.tools.archive_read import makeArchiveReadTool
    from ruocun.tools.registry import ToolRegistry
    from ruocun.tools.types import ToolRejected

    async def scenario():
        async def parent_read(_identity, _offset, _limit):
            return {"text": "private parent history"}

        async def ask(_message):
            return "deny"

        parent = Session("parent", "synthetic")
        ctx = ToolContext(str(tmp_path), archiveRead=parent_read)
        registry = ToolRegistry()
        registry.register(makeArchiveReadTool())
        permission = await createPermissionRuntime(tmp_path, tmp_path / "config", Compatibility(1, ()), parent,
            emptyPermissions(), ask, interactive=False, env={"ProgramData": str(tmp_path / "policy")})
        prepared = prepareAgentRun(parent, ctx, registry, permission, {"model": parent.model},
            AgentRequest(task="independent task"), AgentDefinition("general-purpose", "child", tools=("ArchiveRead",)), env={})
        tool = prepared.registry.get("ArchiveRead")
        assert tool is not None
        with pytest.raises(ToolRejected):
            await tool.handler({"id": "parent-record"}, prepared.ctx)
    asyncio.run(scenario())


def test_archive_read_respects_an_explicit_current_permission_denial(tmp_path):
    from ruocun.config.compat import Compatibility
    from ruocun.permissions.runtime import createPermissionRuntime
    from ruocun.permissions.settings import emptyPermissions
    from ruocun.session.session import Session
    from ruocun.tools.archive_read import makeArchiveReadTool

    async def scenario():
        async def ask(_message):
            raise AssertionError("explicit deny must not ask")
        rules = emptyPermissions()
        rules["deny"] = ["ArchiveRead"]
        permission = await createPermissionRuntime(tmp_path, tmp_path / "config", Compatibility(1, ()),
            Session("SYS", "synthetic"), rules, ask, interactive=False,
            env={"ProgramData": str(tmp_path / "policy")})
        assert not await permission.authorize(makeArchiveReadTool(), '{"id":"summary-1"}')
    asyncio.run(scenario())
