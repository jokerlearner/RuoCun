"""Approved cwd snapshot lifecycle at the shared request-preparation seam."""
import asyncio
import copy

import pytest

from ruocun.agent.context_runtime import CompactionFailed, ContextManager
from ruocun.agent.runtime_context import buildRuntimeContext, isRuntimeContext
from ruocun.client.resilient import ResilientResult
from ruocun.session.session import Session
from ruocun.tools.types import ToolContext


class Journal:
    def __init__(self):
        self.saved = []

    def redact(self, text):
        return text

    async def save(self, session):
        self.saved.append(copy.deepcopy(session.messages))

    async def replace_context(self, session, messages, *, reset_prompt=True):
        self.saved.append(copy.deepcopy(messages))
        session.messages = copy.deepcopy(messages)


def test_cwd_snapshot_is_persisted_after_input_and_deduplicated_across_reopen_and_directory_changes(tmp_path):
    async def scenario():
        workspace = tmp_path / "workspace"
        checkout = tmp_path / "checkout"
        workspace.mkdir()
        checkout.mkdir()
        ctx = ToolContext(str(workspace), cwd=str(workspace))
        session = Session("STABLE SYSTEM", "synthetic-cwd", env={})
        session.addUser("the actual task")
        original = copy.deepcopy(session.messages)
        journal = Journal()
        options = {"model": session.model, "maxTokens": 256, "messages": session.messages}
        env = {"RUOCUN_CONTEXT_WINDOW": "20000"}
        manager = ContextManager(session, journal, ctx, options, env, lambda _text: None)
        prepared = await manager.before_request(options)
        assert session.messages[:2] == original
        snapshot = session.messages[-1]
        assert snapshot["role"] == "user" and snapshot["content"].startswith("<ruocun-runtime-context>")
        assert journal.saved == [session.messages] and prepared["messages"] == session.messages
        await manager.before_request(options)
        assert len(journal.saved) == 1
        reopened = Session("STABLE SYSTEM", session.model, env={})
        reopened.messages = copy.deepcopy(journal.saved[-1])
        fresh = ContextManager(reopened, journal, ctx, options, env, lambda _text: None)
        await fresh.before_request(options)
        assert len(journal.saved) == 1 and reopened.messages[-1] == snapshot
        before_change = copy.deepcopy(reopened.messages)
        ctx.cwd = str(checkout)
        await fresh.before_request(options)
        assert reopened.messages[:-1] == before_change
        assert reopened.messages[-1] != snapshot
        ctx.cwd = None
        await fresh.before_request(options)
        assert reopened.messages[-1] == snapshot and len(journal.saved) == 3
    asyncio.run(scenario())


def test_runtime_tail_does_not_make_an_unanswered_first_user_eligible_for_summary():
    async def scenario():
        session = Session("SYSTEM", "synthetic-cwd", env={})
        session.addUser("x" * 2100)
        original = copy.deepcopy(session.messages)
        sent = []

        def summary(options, _context):
            sent.append(options)
            return ResilientResult("complete", [], {"role": "assistant", "content": "<摘要>compressed</摘要>"},
                                   None, "stop", [], {})

        options = {"model": session.model, "maxTokens": 256}
        manager = ContextManager(session, Journal(), ToolContext("synthetic-workspace"), options,
            {"RUOCUN_CONTEXT_WINDOW": "2000", "RUOCUN_COMPACT_THRESHOLD_RATIO": ".35", "RUOCUN_COMPACT_RETAIN_TOKENS": "20",
             "RUOCUN_COMPACT_SUMMARY_MAX_TOKENS": "128"}, lambda _text: None, request=summary)
        with pytest.raises(CompactionFailed):
            await manager.before_request(options)
        assert session.messages[:2] == original
        assert not sent
    asyncio.run(scenario())


def test_automatic_summary_reinjects_a_removed_snapshot_without_pinning_the_first_user():
    async def scenario():
        session = Session("SYSTEM", "synthetic-cwd", env={})
        session.addUser("original task " * 100)
        ctx, journal, sent = ToolContext("synthetic-workspace"), Journal(), []

        def summary(options, _context):
            sent.append(copy.deepcopy(options))
            return ResilientResult("complete", [], {"role": "assistant", "content": "<摘要>Verified work; follow the latest requirement.</摘要>"},
                                   None, "stop", [], {})

        options = {"model": session.model, "maxTokens": 256}
        manager = ContextManager(session, journal, ctx, options,
            {"RUOCUN_CONTEXT_WINDOW": "6000", "RUOCUN_COMPACT_THRESHOLD_RATIO": ".5",
             "RUOCUN_COMPACT_RETAIN_TOKENS": "20", "RUOCUN_COMPACT_SUMMARY_MAX_TOKENS": "128"},
            lambda _text: None, request=summary)
        await manager.before_request(options)
        old_snapshot = copy.deepcopy(session.messages[-1])
        session.messages.extend([{"role": "assistant", "content": "verified old evidence " * 450},
                                 {"role": "user", "content": "latest requirement " * 5}])
        original = copy.deepcopy(session.messages)
        prepared = await manager.before_request(options)
        assert len(sent) == 1
        prefix = sent[0]["messages"][:-1]
        assert prefix == original[:len(prefix)] and old_snapshot in prefix
        assert original[1] not in session.messages
        assert sum(isRuntimeContext(message) for message in session.messages) == 1
        assert session.messages[-1] == buildRuntimeContext(ctx)
        assert prepared["messages"] == journal.saved[-1] == session.messages
    asyncio.run(scenario())


def test_snapshot_journal_failure_keeps_the_original_projection_and_marker_text_is_not_a_snapshot():
    async def scenario():
        session = Session("summary mentions <ruocun-runtime-context>", "synthetic-cwd", env={})
        session.addUser("<ruocun-runtime-context> user task about a tag")
        original = copy.deepcopy(session.messages)

        class FailedJournal(Journal):
            async def replace_context(self, current, messages, *, reset_prompt=True):
                assert current.messages == original
                raise RuntimeError("synthetic snapshot commit refused")

        options = {"model": session.model, "maxTokens": 256}
        ctx = ToolContext("synthetic-workspace")
        manager = ContextManager(session, FailedJournal(), ctx, options,
                                 {"RUOCUN_CONTEXT_WINDOW": "20000"}, lambda _text: None)
        with pytest.raises(RuntimeError, match="snapshot commit"):
            await manager.before_request(options)
        assert session.messages == original
        journal = Journal()
        manager = ContextManager(session, journal, ctx, options,
                                 {"RUOCUN_CONTEXT_WINDOW": "20000"}, lambda _text: None)
        await manager.before_request(options)
        assert session.messages == [*original, buildRuntimeContext(ctx)]
    asyncio.run(scenario())
