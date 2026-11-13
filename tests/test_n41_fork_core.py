"""Frozen fork context and exact parent wire catalog at the child turn seam."""
from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ruocun.agent.fork_agent import (
    FORK_AGENT,
    buildForkContextMessages,
    forkRequestMessages,
)
from ruocun.agent.loop import run_turn
from ruocun.agent.run_agent import prepareAgentRun, runPreparedAgent
from ruocun.client.resilient import ResilientResult
from ruocun.client.types import ImageData, StreamChatOptions
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.session import Session
from ruocun.tools.agent import AgentRequest, agentTool
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.tools_for_mode import apiToolsForMode
from ruocun.tools.types import ToolContext


def _call(identity: str, name: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"id": identity, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def _reply(content: str, *calls: dict[str, Any]) -> ResilientResult:
    return ResilientResult("complete", [], {"role": "assistant", "content": content, "tool_calls": list(calls)},
                           None, "stop", [], {})


def test_frozen_fork_placeholder_constructed_and_unpaired_tail_filtered_for_wire() -> None:
    parent = [{"role": "system", "content": "SYS"}, {"role": "user", "content": "request"},
              {"role": "assistant", "content": "paired", "tool_calls": [_call("old", "Read", {})]},
              {"role": "tool", "tool_call_id": "old", "content": "saved"},
              {"role": "assistant", "content": "pending", "tool_calls": [_call("new", "Agent", {})]}]
    original = copy.deepcopy(parent)
    candidate = buildForkContextMessages(parent, "task")
    assert candidate[-2] == parent[-1] and candidate[-1]["content"][0]["text"] == "Fork 已启动 - 后台处理中"
    wire = forkRequestMessages(parent, "task")
    assert wire[:-1] == parent[:-1] and wire[-1]["role"] == "user"
    assert wire[-1]["content"][0]["text"] == "Fork 已启动 - 后台处理中"
    assert "<fork-boilerplate>" in wire[-1]["content"][-1]["text"]
    wire[2]["tool_calls"][0]["function"]["name"] = "changed in child"
    assert parent == original


class _Journal:
    async def save(self, session: Session) -> None:
        pass

    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> None:
        return None

    async def result(self, call_id: str, text: str, image_data: ImageData | None = None) -> None:
        pass

    async def replace_context(self, session: Session, messages: list[dict[str, Any]], *, reset_prompt: bool = True) -> None:
        session.messages = messages


def test_fork_uses_exact_parent_wire_catalog_and_independent_execution_pool(tmp_path: Path) -> None:
    async def scenario() -> None:
        (tmp_path / "read.txt").write_text("actual scoped file", encoding="utf-8")
        parent = Session("parent exact system", "Vendor/Actual-Case", env={})
        parent.messages.append({"role": "user", "content": "parent history"})
        registry = ToolRegistry()
        registry.register(agentTool)
        registry.register(replace(readFileTool, name="DeferredVisible", shouldDefer=True))
        registry.register(replace(readFileTool, name="DeferredHidden", shouldDefer=True))
        for number in range(6):
            registry.register(replace(readFileTool, name=f"mcp__fixture__read{number}"))
        assert "DeferredVisible" in registry.searchAndActivateDeferred("DeferredVisible", "en")

        async def unused_agent(_task: AgentRequest) -> str:
            raise AssertionError("recursive Agent launched another model")

        async def ask(_text: str) -> str:
            raise AssertionError("fixture only uses allowed read and denied nested Agent")

        async def approve(_name: str, _args: dict[str, Any]) -> bool:
            return False

        rules = emptyPermissions()
        rules["allow"] = ["DeferredVisible"]
        rules["defaultMode"] = "default"
        permissions = await createPermissionRuntime(tmp_path, tmp_path / "user", Compatibility(1, ()), parent,
            rules, ask, interactive=False, env={"ProgramData": str(tmp_path / "policy")})
        parent_ctx = ToolContext(str(tmp_path), lang="en", runAgent=unused_agent)
        options: StreamChatOptions = {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic-key"}
        requests: list[StreamChatOptions] = []

        def parent_request(opts: StreamChatOptions, _context: object) -> ResilientResult:
            requests.append(copy.deepcopy(opts))
            return _reply("prior result")

        result = await run_turn(parent, options, registry, parent_ctx, approve=approve,
            request=parent_request, api_tools=lambda: apiToolsForMode(registry, "normal", "en"))
        assert result.status == "complete" and parent_ctx.forkToolSnapshot is not None
        source = requests[0]["tools"]
        assert "DeferredVisible" in {tool["function"]["name"] for tool in source}
        assert "DeferredHidden" not in {tool["function"]["name"] for tool in source}
        assert "mcp__fixture__read5" not in {tool["function"]["name"] for tool in source}
        registry.searchAndActivateDeferred("DeferredHidden", "en")
        parent.messages.append({"role": "assistant", "content": "unfinished", "tool_calls": [_call("fork", "Agent", {})]})
        initial = forkRequestMessages(parent.messages, "continue independently")
        original = copy.deepcopy(parent.messages)
        prepared = prepareAgentRun(parent, parent_ctx, registry, permissions, options,
            AgentRequest("continue independently"), FORK_AGENT, env={"RUOCUN_SUBAGENT_MAX_TURNS": "3"},
            initial_messages=initial, exact_tools=parent_ctx.forkToolSnapshot, is_async=True)
        assert prepared.max_turns == 3
        assert prepared.registry.get("DeferredHidden") is None and prepared.registry.get("mcp__fixture__read5") is None

        def child_request(opts: StreamChatOptions, _context: object) -> ResilientResult:
            requests.append(copy.deepcopy(opts))
            if len(requests) == 2:
                return _reply("", _call("nested", "Agent", {"task": "must not run"}),
                              _call("read", "DeferredVisible", {"path": "read.txt"}))
            return _reply("fork complete")

        outcome = await runPreparedAgent(prepared, journal=_Journal(), request=child_request)
        assert outcome.status == "complete" and len(requests) == 3
        assert all(opts["tools"] == source and opts["model"] == parent.model for opts in requests[1:])
        assert requests[1]["messages"] == initial and parent.messages == original
        tools = {message["tool_call_id"]: message["content"] for message in requests[-1]["messages"] if message["role"] == "tool"}
        assert "不能再派子代理" in tools["nested"] and "actual scoped file" in tools["read"]
        assert prepared.permission.getMode() == permissions.getMode() == "default"

    asyncio.run(scenario())
