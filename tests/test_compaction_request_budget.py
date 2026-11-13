"""Final public request preparation respects context and explicit output caps."""

import asyncio

import pytest

from ruocun.agent.context_runtime import ContextManager
from ruocun.client.client import buildRequestBody
from ruocun.session.session import Session
from ruocun.tools.types import ToolContext


def test_small_window_default_output_limit_matches_the_sent_request():
    session = Session("SYS", "synthetic-budget")
    options = {"model": session.model, "provider": "zhipu", "messages": session.messages}
    manager = ContextManager(session, object(), ToolContext("synthetic-workspace"), options,
                             {"RUOCUN_CONTEXT_WINDOW": "1000"}, lambda _text: None)
    prepared = manager.prepare_request(options)
    assert buildRequestBody(prepared, env={})["max_tokens"] == 250
    assert "maxTokens" not in options


def test_extra_output_limit_cannot_exhaust_the_context_window():
    session = Session("SYS", "synthetic-budget")
    options = {"model": session.model, "provider": "zhipu", "messages": session.messages,
               "extra": {"max_tokens": 1000}}
    manager = ContextManager(session, object(), ToolContext("synthetic-workspace"), options,
                             {"RUOCUN_CONTEXT_WINDOW": "1000"}, lambda _text: None)
    with pytest.raises(ValueError, match="output"):
        manager.prepare_request(options)


def test_current_tool_definitions_trigger_pressure_before_any_api_usage():
    session = Session("SYS", "synthetic-budget")
    options = {"model": session.model, "provider": "zhipu", "messages": session.messages,
               "tools": [{"type": "function", "function": {"name": "Read", "description": "x" * 3000,
                          "parameters": {"type": "object"}}}]}
    manager = ContextManager(session, object(), ToolContext("synthetic-workspace"), options,
                             {"RUOCUN_CONTEXT_WINDOW": "1000"}, lambda _text: None)
    assert session.lastPromptTokens is None
    assert manager.needs_compaction(options)


def test_first_request_stops_without_sending_an_indivisible_oversized_input():
    from ruocun.agent.loop import run_turn
    from ruocun.tools.registry import ToolRegistry

    async def scenario():
        session = Session("SYS", "synthetic-budget")
        session.addUser("x" * 4000)
        original = list(session.messages)
        options = {"model": session.model, "provider": "zhipu", "messages": session.messages}
        ctx = ToolContext("synthetic-workspace")
        manager = ContextManager(session, object(), ctx, options,
                                 {"RUOCUN_CONTEXT_WINDOW": "1000"}, lambda _text: None)

        def request(_options, _context):
            raise AssertionError("oversized first request must not reach the provider")

        async def approve(_name, _args):
            return False

        result = await run_turn(session, options, ToolRegistry(), ctx, approve=approve, request=request,
                                request_preflight=manager.before_request)
        assert result.status == "compaction_failed"
        assert session.messages == original
    asyncio.run(scenario())


def test_target_model_is_qualified_before_the_current_model_or_projection_changes():
    async def scenario():
        session = Session("OLD SYSTEM", "old-model")
        session.addUser("latest requirement")
        original = list(session.messages)
        manager = ContextManager(session, object(), ToolContext("synthetic-workspace"),
            {"model": session.model, "provider": "zhipu"}, {"RUOCUN_CONTEXT_WINDOW": "1000"}, lambda _text: None)
        with pytest.raises(ValueError, match="output"):
            await manager.prepare_model_change({"model": "new-model", "provider": "zhipu", "maxTokens": 1000}, "NEW SYSTEM")
        assert session.model == "old-model" and session.messages == original
        prepared = await manager.prepare_model_change({"model": "new-model", "provider": "zhipu"}, "NEW SYSTEM")
        assert prepared.messages == [{"role": "system", "content": "NEW SYSTEM"}, *original[1:]]
        assert session.model == "old-model" and session.messages == original
    asyncio.run(scenario())


def test_server_context_recovery_does_not_resend_when_compaction_makes_no_progress():
    from ruocun.agent.loop import run_turn
    from ruocun.client.resilient import ResilientResult
    from ruocun.tools.registry import ToolRegistry

    async def scenario():
        session = Session("SYS", "synthetic-budget")
        session.addUser("latest request")
        sent = []
        def request(options, _context):
            sent.append(options)
            return ResilientResult("failed", [], {}, None, None, [], {},
                                   error="maximum context length exceeded")
        async def compact():
            return "no safe span"
        async def approve(_name, _args):
            return False
        result = await run_turn(session, {"model": session.model}, ToolRegistry(), ToolContext("synthetic"),
                                approve=approve, request=request, compact=compact)
        assert len(sent) == 1
        assert result.status == "compaction_failed"
    asyncio.run(scenario())


def test_same_model_on_another_provider_refreshes_the_actual_window():
    session = Session("SYS", "glm-5.1")
    options = {"model": session.model, "provider": "qianfan",
               "baseUrl": "https://qianfan.baidubce.com/v2/tokenplan/personal"}
    manager = ContextManager(session, object(), ToolContext("synthetic"), options, {}, lambda _text: None)
    assert manager.context_window == 198000
    options.update(provider="zhipu", baseUrl="https://open.bigmodel.cn/api/coding/paas/v4")
    assert manager.context_window == 1000000
