"""Necessary seams for bounded automatic learning and legacy reflection."""
import asyncio
import copy
import threading

import pytest

from ruocun.agent.reflection_runtime import ControlledLearningSignal, ReflectionRuntime
from ruocun.agent.runtime import _parse_cli
from ruocun.session.session import Session


class Conversation:
    blocked = False
    reflection_state = None

    def __init__(self):
        self.agent_tool_batches = asyncio.Lock()
        self.journal = {}

    async def set_reflection_state(self, session, state, *, advisories=()):
        self.reflection_state = copy.deepcopy(state)
        session.messages.extend({"role": "system", "content": text} for text in advisories)

    async def scoped_intent(self, ref, *args, **kwargs):
        return self.journal.get(ref)

    async def scoped_result(self, ref, text):
        self.journal[ref] = text


def fixture(*, budget=None, failing=False):
    conversation = Conversation()
    session = Session("synthetic-system", "synthetic-model", env={})
    analyses, writes, notices = [], [], []

    async def analyze(messages):
        analyses.append(copy.deepcopy(messages))
        if failing:
            raise RuntimeError("synthetic-analysis-failure")
        return {"onTrack": True, "advisory": None, "memories": [], "corrections": [], "confirmed": []}

    async def apply(result):
        assert conversation.agent_tool_batches.locked()
        writes.append(result)
        return {"added": 1, "merged": 0, "corrections": [], "confirmed": 0}

    runtime = ReflectionRuntime(conversation, session, enabled=True, analyze=analyze, apply=apply,
        audit=lambda event: None, notice=notices.append, env={"RUOCUN_REFLECT_EVERY": "1"},
        controlled=True, controlled_budget=budget)
    return runtime, session, conversation, analyses, writes, notices


def test_deepseek_and_compaction_do_not_force_learning_without_evidence():
    async def scenario():
        runtime, session, _, analyses, writes, _ = fixture()
        session.messages.append({"role": "user", "content": "你好，介绍一下当前任务。"})
        await runtime.after_turn("one", provider="deepseek", compaction_imminent=True)
        assert analyses == [] and writes == []
        await runtime.close()
    asyncio.run(scenario())


def test_controlled_learning_is_saved_before_normal_turn_returns_and_not_duplicated():
    async def scenario():
        runtime, session, _, analyses, writes, notices = fixture()
        session.messages.append({"role": "user", "content": "以后这个项目必须先验证再交付，请记住这个约定。"})
        await runtime.after_turn("one", provider="deepseek")
        assert len(analyses) == 1 and len(writes) == 1
        assert notices and "新增1条" in notices[0]
        await runtime.after_turn("one", provider="deepseek")
        await runtime.close()
        assert len(writes) == 1
    asyncio.run(scenario())


def test_analysis_budget_survives_session_switch_and_does_not_stop_primary_work():
    async def scenario():
        budget = {"analyses": 0}
        runtime, session, conversation, analyses, writes, notices = fixture(budget=budget)
        for index in range(8):
            session.messages.append({"role": "user", "content": f"以后请记住当前项目约定{index}，不要只凭猜测。"})
            await runtime.after_turn(str(index), provider="deepseek")
        assert len(analyses) == len(writes) == budget["analyses"] == 6
        assert conversation.blocked is False
        assert sum("6次自动学习" in notice for notice in notices) == 1
        second, other, _, calls, _, _ = fixture(budget=budget)
        other.messages.append({"role": "user", "content": "以后请记住另外一条约定。"})
        await second.after_turn("new-session", provider="deepseek")
        assert not calls
    asyncio.run(scenario())


def test_failed_analysis_halts_learning_for_this_program_without_writing():
    async def scenario():
        budget = {"analyses": 0}
        runtime, session, conversation, analyses, writes, notices = fixture(budget=budget, failing=True)
        session.messages.append({"role": "user", "content": "请记住：以后必须核对证据。"})
        await runtime.after_turn("one", provider="deepseek")
        session.messages.append({"role": "user", "content": "以后请记住另一个约定。"})
        await runtime.after_turn("two", provider="deepseek")
        assert len(analyses) == 1 and not writes and budget["halted"] == 1
        assert not conversation.blocked and any("不自动重试" in notice for notice in notices)
    asyncio.run(scenario())


def test_pause_during_learning_discards_completed_result_before_any_write():
    async def scenario():
        runtime, session, conversation, _, writes, _ = fixture()
        session.messages.append({"role": "user", "content": "以后请记住这个项目的交付约定。"})
        started, finish = asyncio.Event(), asyncio.Event()
        shutdown, turn = threading.Event(), threading.Event()
        generation = {"current": True}
        signal = ControlledLearningSignal(shutdown, turn, lambda: generation["current"])

        async def analyze(messages):
            started.set()
            await finish.wait()
            return {"onTrack": True, "advisory": None, "memories": [], "corrections": [], "confirmed": []}

        runtime.analyze = analyze
        task = asyncio.create_task(runtime.after_turn("pause", provider="deepseek", cancelled=signal.is_set))
        await started.wait()
        turn.set()
        generation["current"] = False
        finish.set()
        await task
        assert writes == [] and conversation.reflection_state["phase"] == "skipped"
        assert "result" not in conversation.reflection_state and signal.is_set()
    asyncio.run(scenario())


@pytest.mark.parametrize("arguments,mode,prompt", [([], "off", []),
    (["--memory-learning", "controlled"], "controlled", []),
    (["--memory-learning=controlled", "--", "hello"], "controlled", ["hello"]),
    (["--memory-learning", "off", "hello"], "off", ["hello"])])
def test_learning_mode_is_not_sent_as_prompt(arguments, mode, prompt):
    parsed = _parse_cli(arguments)
    assert parsed.memory_learning == mode and parsed.prompt == prompt


@pytest.mark.parametrize("arguments", [["--memory-learning"], ["--memory-learning", "everything"],
                                      ["--memory-learning="]])
def test_invalid_learning_mode_fails_before_any_execution(arguments):
    with pytest.raises(SystemExit):
        _parse_cli(arguments)
