"""冻结 index.ts 的来源提取断言及 ADR-0012 最小接线确认；仅合成值。"""

import asyncio
import copy
import json
from dataclasses import replace

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


class MemoryJournal:
    """StoragePort 系统边界的内存替身；真实原子提交已由 Conversation 用例独审。"""

    def __init__(self):
        self.saved = []

    def redact(self, text):
        return text.replace("synthetic-key", "[REDACTED]")

    async def save(self, session):
        self.saved.append(copy.deepcopy((session.messages, session.usage)))

    async def replace_context(self, session, messages):
        self.saved.append(copy.deepcopy((messages, session.usage)))
        session.messages = copy.deepcopy(messages)
        session.lastPromptTokens = None
        session.lastSentLength = 0


def _manager(env=None, request=None, **options):
    values = {} if env is None else env
    values.setdefault("RUOCUN_COMPACT_RETAIN_TOKENS", "20")
    session = Session("SYS", "glm-5.2", env=values)
    journal = MemoryJournal()
    ctx = ToolContext("synthetic-workspace")
    notices = []
    manager = ContextManager(session, journal, ctx, {"provider": "zhipu", "apiKey": "synthetic-key"},
                             values, notices.append, request=request, **options)
    return manager, session, journal, ctx, values, notices


def _response(text, usage=None, *, status="complete", cancelled=False):
    return ResilientResult(status=status, deltas=[], message={"role": "assistant", "content": text},
                           usage=usage, finish_reason="stop", attempts=[], request_body={}, cancelled=cancelled)


def _compactable_history(session, request):
    # B keeps a recent verbatim tail, so a summary fixture needs an actual old span.
    session.addUser(request + "x" * 1600)
    session.messages.append({"role": "assistant", "content": "old evidence " + "y" * 400})
    session.addUser("最新请求原文")


@pytest.mark.parametrize("explicit_clear", [False, True])
def test_reopened_compaction_preserves_the_pin_until_a_confirmed_empty_todo_write(explicit_clear):
    # The two-process CLI red/green lives in evidence/test_todo_reopen_regression.py.
    async def scenario():
        manager, session, _, ctx, *_ = _manager(request=lambda _options, _context: _response("已核实的简短摘要"))
        session.addUser("压缩前的旧材料" * 400)
        session.messages.append({"role": "system", "content": "[当前任务清单]\n▶ 保留尚未完成的任务"})
        if explicit_clear:
            session.messages.extend([
                {"role": "assistant", "content": None, "tool_calls": [{"id": "clear-todo", "type": "function",
                 "function": {"name": "TodoWrite", "arguments": '{"todos":[]}'}}]},
                {"role": "tool", "tool_call_id": "clear-todo", "content": "(任务清单已清空)"},
            ])
        session.addUser("最新请求的原文" * 20)
        assert ctx.todos == []  # Reopened context no longer contains the old TodoWrite call.
        await manager.compact()
        assert any("保留尚未完成的任务" in str(item.get("content", ""))
                   for item in session.messages) is not explicit_clear
    asyncio.run(scenario())


def test_source_environment_defaults_and_native_alias_precedence():
    manager, session, _, _, _, _ = _manager({
        "RUOCUN_CONTEXT_WINDOW": "200000", "DAO_CONTEXT_WINDOW": "1000000",
        "RUOCUN_MAX_BUDGET": "2.5", "RUOCUN_MAX_TURNS": "7", "RUOCUN_MAX_BUDGET_HARD": "1",
    })
    assert manager.context_window == 200_000
    assert session.budgetCNY == 2.5
    assert manager.max_turns == 7 and manager.budget_hard is True
    default, session, *_ = _manager({"RUOCUN_MAX_BUDGET": "-2", "RUOCUN_MAX_TURNS": "0"})
    assert default.max_turns == float("inf")
    assert session.budgetCNY is None and default.budget_hard is False


def test_source_window_lock_effort_first_argument_and_queries_do_not_add_user():
    async def scenario():
        manager, session, journal, _, env, _ = _manager()
        session.setModel("gpt-5")
        assert manager.context_window == 400_000
        assert "1,000,000" in await manager.command("/context-window 1M ignored")
        session.setModel("glm-5.2")
        assert manager.context_window == 1_000_000
        assert env["RUOCUN_CONTEXT_WINDOW"] == "1000000"
        assert "low" in await manager.command("/effort low ignored")
        assert env["RUOCUN_REASONING_EFFORT"] == "low"
        assert "当前思考强度:low" in await manager.command("/effort")
        assert "无效" in await manager.command("/effort ultra")
        assert await manager.command("/unrelated") is None
        assert session.messages == [{"role": "system", "content": "SYS"}]
        assert journal.saved == []
    asyncio.run(scenario())


def test_source_summary_request_commits_candidate_pins_todos_and_counts_usage_once(tmp_path):
    async def scenario():
        usage = {"prompt_tokens": 100, "completion_tokens": 10, "prompt_cache_hit_tokens": 90}

        def request(options, context):
            assert options["model"] == "synthetic-summary"
            assert options["extra"] == {"thinking": {"type": "disabled"}, "temperature": 0}
            assert "tools" not in options
            assert options["messages"][-1] == {"role": "user", "content": COMPACT_INSTRUCTION}
            assert context.cancel() is False
            options["onUsage"](usage)
            return _response("<分析>不保留的草稿</分析><摘要>继续完成原任务</摘要>", usage)

        manager, session, journal, ctx, _, notices = _manager({"RUOCUN_SUMMARY_MODEL": "synthetic-summary"}, request)
        manager.cache_sink = createCacheAuditSink(tmp_path, {})
        ctx.todos = [{"content": "完成原任务", "status": "in_progress"}]
        _compactable_history(session, "已确认原始请求")
        assert all(marker in COMPACT_INSTRUCTION for marker in
                   ("<分析>", "</分析>", "<摘要>", "</摘要>", "[早期对话摘要]", "[当前任务清单]"))
        assert "用户的原话" in COMPACT_INSTRUCTION and "未完成的请求" in COMPACT_INSTRUCTION
        await manager.compact()
        assert len(session.messages) == 5
        assert "继续完成原任务" in session.messages[1]["content"]
        assert "不保留的草稿" not in session.messages[1]["content"]
        assert session.messages[-2]["content"] == "最新请求原文"
        assert "▶ 完成原任务" in session.messages[-1]["content"]
        assert session.usage["promptTokens"] == 100 and session.usage["completionTokens"] == 10
        assert len(journal.saved) == 1 and notices
        event = json.loads((tmp_path / "cache.jsonl").read_text("utf-8"))
        assert event["agent"] == "summary" and event["model"] == "synthetic-summary"
        assert all(event["fp"][key] != "45h" for key in ("sys", "tools", "tail"))
        assert "已确认原始请求" not in (tmp_path / "cache.jsonl").read_text("utf-8")
    asyncio.run(scenario())


@pytest.mark.parametrize(("status", "text"), [
    ("failed", "失败请求带来的残余输出"), ("partial", "未完成摘要"), ("complete", "<摘要>  </摘要>"),
])
def test_confirmed_policy_preserves_context_on_failed_partial_or_empty_summary(status, text):
    async def scenario():
        usage = {"prompt_tokens": 120, "completion_tokens": 3}

        def request(options, context):
            options["onUsage"](usage)
            return _response(text, usage, status=status)

        manager, session, journal, _, _, notices = _manager(request=request)
        _compactable_history(session, "已确认请求及未压缩细节")
        original = copy.deepcopy(session.messages)
        with pytest.raises(CompactionFailed):
            await manager.compact()
        assert session.messages == original
        assert session.usage["promptTokens"] == 120
        assert journal.saved == [(original, session.usage)]
        assert notices == []
    asyncio.run(scenario())


def test_request_exception_keeps_received_usage_and_saves_original_context():
    async def scenario():
        def request(options, context):
            options["onUsage"]({"prompt_tokens": 90, "completion_tokens": 2})
            raise RuntimeError("synthetic request unavailable")

        manager, session, journal, *_ = _manager(request=request)
        _compactable_history(session, "已保存的原始请求")
        original = copy.deepcopy(session.messages)
        with pytest.raises(CompactionFailed):
            await manager.compact()
        assert session.messages == original
        assert session.usage["promptTokens"] == 90
        assert journal.saved == [(original, session.usage)]
    asyncio.run(scenario())


def test_truncated_summary_preserves_the_original_context():
    async def scenario():
        def request(options, context):
            return replace(_response("<摘要>incomplete but short</摘要>"), finish_reason="length")

        manager, session, journal, *_ = _manager(request=request)
        session.addUser("最初约束" + "x" * 1600)
        session.messages.append({"role": "assistant", "content": "已核实" + "y" * 400})
        session.addUser("最新请求")
        original = copy.deepcopy(session.messages)
        with pytest.raises(CompactionFailed):
            await manager.compact()
        assert session.messages == original
        assert journal.saved == [(original, session.usage)]
    asyncio.run(scenario())


def test_compaction_commits_the_original_source_mapping_and_recent_text():
    async def scenario():
        class ArchiveJournal(MemoryJournal):
            def __init__(self):
                super().__init__()
                self.rewrites = []

            async def compact_context(self, session, messages, *, rewrite):
                self.rewrites.append(rewrite)
                await self.replace_context(session, messages)

        manager, session, _, _, _, _ = _manager(
            {"RUOCUN_COMPACT_RETAIN_TOKENS": "20"}, lambda _o, _c: _response("<摘要>已核实旧约束</摘要>"))
        journal = ArchiveJournal()
        manager.journal = journal
        session.addUser("早期约束" + "x" * 2000)
        session.messages.append({"role": "assistant", "content": "旧证据" + "y" * 1000})
        session.addUser("最新请求必须原样保留")
        original = copy.deepcopy(session.messages)
        await manager.compact()
        assert len(journal.rewrites) == 1
        assert list(journal.rewrites[0].expected_messages) == original
        assert journal.rewrites[0].derived[0].kind == "summary"
        assert session.messages[-1]["content"] == "最新请求必须原样保留"
    asyncio.run(scenario())


def test_cancelled_summary_does_not_replace_context_even_with_complete_text():
    async def scenario():
        def request(options, context):
            options["onUsage"]({"prompt_tokens": 80, "completion_tokens": 2})
            ctx.signal.set()
            return _response("<摘要>已经返回的文本</摘要>", cancelled=True)

        manager, session, journal, ctx, _, _ = _manager(request=request)
        _compactable_history(session, "原对话必须保留")
        original = copy.deepcopy(session.messages)
        with pytest.raises(InterruptedError):
            await manager.compact()
        assert session.messages == original
        assert session.usage["promptTokens"] == 80
        assert journal.saved == [(original, session.usage)]
    asyncio.run(scenario())


def test_source_context_cost_status_queries_show_current_process_scope_and_do_not_append_messages():
    async def scenario():
        manager, session, journal, _, _, _ = _manager(
            {"RUOCUN_MAX_BUDGET": "2"}, permission_mode=lambda: "bypassPermissions",
        )
        session.usage["promptTokens"] = 4000  # R1 恢复的累计token，没有伪造历史费用桶。
        session.lastPromptTokens = 170_000
        original = copy.deepcopy(session.messages)
        cost = await manager.command("/cost")
        assert "累计token（可能含历史）" in cost and "本次进程费用" in cost
        assert "历史费用不完整" in cost and "2.00" in cost
        assert await manager.command("/usage") == cost
        assert "170,000 / 200,000 tok (85%)" in await manager.command("/context")
        status = await manager.command("/status")
        assert "模式 bypassPermissions · 开关 免审批" in status and "思考 max" in status
        assert not manager.should_compact()  # 回合间检查粗估，不把上轮实际值当本轮全部输入。
        assert session.messages == original and journal.saved == []
        session.addUser("x" * 510_000)
        assert manager.should_compact()
    asyncio.run(scenario())
