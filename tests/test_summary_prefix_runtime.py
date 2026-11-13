"""Regressions for B: actual request envelope and original prefix compaction."""
import asyncio
import copy
import json

import pytest

from ruocun.agent.context_runtime import (
    COMPACT_INSTRUCTION,
    CompactionFailed,
    ContextManager,
)
from ruocun.client.resilient import ResilientResult
from ruocun.session.cache_audit import createCacheAuditSink
from ruocun.session.session import Session
from ruocun.tools.types import ToolContext


class Journal:
    def __init__(self):
        self.saved = []

    def redact(self, value):
        return value.replace("synthetic-key", "[REDACTED]")

    async def save(self, session):
        self.saved.append(copy.deepcopy(session.messages))

    async def replace_context(self, session, messages):
        self.saved.append(copy.deepcopy(messages))
        session.messages = copy.deepcopy(messages)


def setup(request, *, env=None):
    values = {"RUOCUN_CONTEXT_WINDOW": "20000", "RUOCUN_COMPACT_RETAIN_TOKENS": "20",
              "RUOCUN_COMPACT_SUMMARY_MAX_TOKENS": "256", **(env or {})}
    session = Session("SYS", "synthetic-prefix", env=values)
    session.addUser("原始事实" * 1600)
    session.messages.append({"role": "assistant", "content": "已核实" * 100})
    session.addUser("近期要求" * 30)
    options = {"model": session.model, "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
               "apiKey": "synthetic-key", "tools": [], "maxTokens": 1024}
    journal = Journal()
    manager = ContextManager(session, journal, ToolContext("synthetic-prefix-workspace"), options,
                             values, lambda _message: None, request=request)
    return manager, session, journal


def reply(*, tool=False):
    message = {"role": "assistant", "content": "<摘要>原始要求仍待完成</摘要>"}
    if tool:
        message["tool_calls"] = [{"id": "synthetic-call", "type": "function",
                                  "function": {"name": "Write", "arguments": "{}"}}]
    return ResilientResult("complete", [], message,
                           {"prompt_tokens": 1000, "completion_tokens": 20, "prompt_cache_hit_tokens": 950},
                           "tool_calls" if tool else "stop", [], {})


def test_summary_uses_current_tools_mode_and_original_prefix_without_mutating_request(tmp_path):
    async def scenario():
        sent = []
        def request(options, _context):
            sent.append(copy.deepcopy(options))
            return reply()
        manager, session, _ = setup(request)
        manager.cache_sink = createCacheAuditSink(tmp_path, {})
        tools = [{"type": "function", "function": {"name": name, "parameters": {"type": "object"}}}
                 for name in ("Second", "First")]
        actual = {**manager.options, "tools": tools, "parallelToolCalls": True,
                  "extra": {"thinking": {"type": "enabled"}, "reasoning_effort": "high",
                            "tool_choice": "required", "max_tokens": 3000}}
        before = copy.deepcopy(actual)
        original = copy.deepcopy(session.messages)
        await manager.compact(request_options=actual)
        summary = sent[0]
        assert summary["tools"] == tools
        assert summary["parallelToolCalls"] is True
        assert summary["extra"]["thinking"] == {"type": "enabled"}
        assert summary["extra"]["reasoning_effort"] == "high"
        assert "tool_choice" not in summary["extra"] and "max_tokens" not in summary["extra"]
        assert manager.request_body(summary)["max_tokens"] == 256
        assert summary["messages"][-1] == {"role": "user", "content": COMPACT_INSTRUCTION}
        prefix = summary["messages"][:-1]
        assert prefix == original[:len(prefix)]
        assert actual == before
        event = json.loads((tmp_path / "cache.jsonl").read_text("utf-8"))
        assert event["agent"] == "summary" and event["fp"]["sys"] != "45h"
        assert event["fp"]["tools"] != "45h" and event["fp"]["tail"] != "45h"
        assert "synthetic-key" not in (tmp_path / "cache.jsonl").read_text("utf-8")
    asyncio.run(scenario())


def test_summary_rejects_text_plus_tool_call_and_keeps_context_and_usage_once():
    async def scenario():
        manager, session, journal = setup(lambda _options, _context: reply(tool=True))
        original = copy.deepcopy(session.messages)
        with pytest.raises(CompactionFailed):
            await manager.compact(request_options={**manager.options, "tools": [{"type": "function"}]})
        assert session.messages == original and journal.saved == [original]
        assert session.usage["promptTokens"] == 1000
    asyncio.run(scenario())


def test_original_prefix_budget_failure_keeps_images_and_never_sends():
    async def scenario():
        calls = []
        manager, session, _ = setup(lambda options, _context: calls.append(options), env={
            "RUOCUN_CONTEXT_WINDOW": "2000", "RUOCUN_COMPACT_RETAIN_TOKENS": "20"})
        session.messages[1]["content"] = [{"type": "text", "text": "old" * 250},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,synthetic"}},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,synthetic"}}]
        original = copy.deepcopy(session.messages)
        with pytest.raises(CompactionFailed, match="窗口"):
            await manager.compact()
        assert not calls and session.messages == original
    asyncio.run(scenario())


def test_explicit_other_summary_model_preserves_existing_lightweight_mode():
    async def scenario():
        sent = []
        def request(options, _context):
            sent.append(copy.deepcopy(options))
            return reply()
        manager, _, _ = setup(request, env={"RUOCUN_SUMMARY_MODEL": "other-summary"})
        await manager.compact(request_options={**manager.options, "tools": [{"type": "function"}],
                                               "extra": {"thinking": {"type": "enabled"}}})
        assert sent[0]["model"] == "other-summary" and "tools" not in sent[0]
        assert sent[0]["extra"]["thinking"] == {"type": "disabled"}
    asyncio.run(scenario())


def test_context_query_does_not_replace_the_current_dynamic_request_for_manual_summary():
    async def scenario():
        sent = []
        def request(options, _context):
            sent.append(copy.deepcopy(options))
            return reply()
        manager, session, _ = setup(request)
        tools = [{"type": "function", "function": {"name": "Activated", "parameters": {"type": "object"}}}]
        actual = {**manager.options, "messages": session.messages, "tools": tools,
                  "extra": {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}}
        await manager.before_request(actual)
        await manager.command("/context")
        await manager.command("/context-window 20K")
        await manager.compact()
        assert sent[0]["tools"] == tools and sent[0]["extra"]["reasoning_effort"] == "high"
    asyncio.run(scenario())


def test_model_preview_summary_sources_name_the_actual_old_system_that_was_read():
    async def scenario():
        sent = []
        def request(options, _context):
            sent.append(copy.deepcopy(options))
            return reply()
        manager, session, _ = setup(request, env={"RUOCUN_CONTEXT_WINDOW": "3000"})
        original = copy.deepcopy(session.messages)
        prepared = await manager.prepare_model_change({**manager.options, "model": "target-prefix",
                                                       "maxTokens": 512}, "NEW TARGET SYSTEM")
        assert sent and sent[0]["model"] == "target-prefix"
        assert sent[0]["messages"][0] == original[0]
        assert prepared.messages[0]["content"] == "NEW TARGET SYSTEM"
        assert prepared.rewrite.expected_messages == tuple(original)
        summary = next(item for item in prepared.rewrite.derived if item.kind == "summary")
        assert 0 in summary.source_indices
        assert session.messages == original
    asyncio.run(scenario())
