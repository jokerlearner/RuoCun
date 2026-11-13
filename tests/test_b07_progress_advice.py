"""Frozen loop.ts progress advisor; executable values override stale comments."""

import copy

from test_mvp_loop import Model, Registry, call, reply, run

from ruocun.session.session import Session


def test_source_default_disabled_and_enabled_gaps_shrink_4_3_2_with_notice():
    from ruocun.agent.progress_advice import createProgressAdvice

    disabled = createProgressAdvice({})
    assert all(disabled.step(["Read"]) is None for _ in range(10))
    assert disabled.stuckAdviceCount == disabled.totalStuckEvents == 0 and disabled.notice is None
    state = createProgressAdvice({})
    assert state.gaps == (4, 3, 2)
    assert all(state.step(["Read"], enabled=True) is None for _ in range(3))
    first = state.step(["Read"], enabled=True)
    assert first.startswith("[进度提醒] 已连续 4 轮")
    assert all(part in first for part in ("小脚本", "命令结果", "verify", "AskUserQuestion"))
    assert "${" not in first
    assert state.notice == "\n[进度提醒:已连续 4 轮无实质推进]\n"
    assert state.nextAdviceAt == 7
    assert all(state.step(["Read"], enabled=True) is None for _ in range(2))
    second = state.step(["Read"], enabled=True)
    assert second.startswith("[进度提醒·第2次] 7 轮")
    assert "先前 1 次提醒" in second and "AskUserQuestion" in second
    assert "${" not in second
    assert state.nextAdviceAt == 9 and "第2次" in state.notice
    assert state.step(["Read"], enabled=True) is None and state.notice is None
    assert "第3次" in state.step(["Read"], enabled=True) and state.nextAdviceAt == 11


def test_source_actual_work_and_only_real_background_polls_reset_stall():
    from ruocun.agent.progress_advice import createProgressAdvice

    state = createProgressAdvice({})
    for name in ("Write", "Edit", "NotebookEdit", "Bash"):
        state.step(["Read"], enabled=True)
        assert state.step([name], enabled=True) is None
        assert state.noProgress == state.stuckAdviceCount == 0 and state.nextAdviceAt == 4
    assert state.step(["TodoWrite"], enabled=True) is None and state.noProgress == 1
    assert state.step(["BashOutput", "TaskOutput", "TaskGet", "TaskList"], runningBackground=True, enabled=True) is None
    assert state.noProgress == 0
    state.step(["BashOutput"], runningBackground=False, enabled=True)
    state.step(["TaskOutput", "Read"], runningBackground=True, enabled=True)
    state.step([], runningBackground=True, enabled=True)
    assert state.noProgress == 3
    assert "进度提醒" in state.step(["TodoWrite"], enabled=True)


def test_source_sparse_edits_do_not_erase_cumulative_stuck_escape_escalation():
    from ruocun.agent.progress_advice import createProgressAdvice

    state = createProgressAdvice({})
    for occurrence in range(1, 4):
        for _ in range(3):
            assert state.step(["Read"], enabled=True) is None
        advice = state.step(["Read"], enabled=True)
        assert state.totalStuckEvents == occurrence and state.stuckAdviceCount == 1
        if occurrence < 3:
            assert advice.startswith("[进度提醒]")
        else:
            assert advice.startswith("[进度提醒·本会话第3次卡住] 再次连续 4 轮")
            assert "调试输出" in advice and "AskUserQuestion" in advice
            assert "${" not in advice and "本会话第3次卡住" in state.notice
        state.step(["Write"], enabled=True)
        assert state.noProgress == state.stuckAdviceCount == 0
        assert state.totalStuckEvents == occurrence


def test_source_finite_positive_env_gaps_native_precedence_and_noninteractive_fallback():
    from ruocun.agent.progress_advice import createProgressAdvice

    state = createProgressAdvice({"DAO_ADVISE_GAPS": "9", "RUOCUN_ADVISE_GAPS": "2,invalid,0,-1,Infinity,0x2"})
    assert state.gaps == (2, 2)
    assert state.step(["Read"], interactive=False, enabled=True) is None
    advice = state.step(["Read"], interactive=False, enabled=True)
    assert "AskUserQuestion" not in advice
    assert advice.startswith("[进度提醒] 已连续 2 轮")
    assert "阻塞点和取舍" in advice and "${" not in advice
    assert createProgressAdvice({"RUOCUN_ADVISE_GAPS": "", "DAO_ADVISE_GAPS": "1"}).gaps == (4, 3, 2)
    assert createProgressAdvice({"DAO_ADVISE_GAPS": "NaN,0,-3"}).gaps == (4, 3, 2)
    fractional = createProgressAdvice({"RUOCUN_ADVISE_GAPS": "1.5"})
    assert all(fractional.step(["Read"], enabled=True) is None for _ in range(4))


def test_source_progress_advice_is_saved_after_tool_pair_and_visible_in_next_request():
    # Frozen loop.test.ts:845–884, using the actual default threshold in loop.ts.
    session = Session("SYS", "m", env={})
    session.addUser("synthetic task")
    registry = Registry()
    model = Model([*(reply(calls=[call(call_id=f"read-{i}")]) for i in range(1, 6)), reply("done")])
    saved, notices, appended = [], [], []

    class Journal:
        async def intent(self, call_id, name, args, effect):
            return None

        async def result(self, call_id, text):
            pass

        async def save(self, current):
            saved.append(copy.deepcopy(current.messages))

        async def replace_context(self, current, messages, *, reset_prompt=True):
            assert not reset_prompt
            assert saved[-1] == current.messages == messages[:-1]
            assert messages[-2] == {"role": "tool", "tool_call_id": "read-4", "content": "1\tcode"}
            current.messages = messages
            await self.save(current)
            appended.append(messages[-1])

    def notice(text):
        assert saved[-1][-1] == appended[-1]
        notices.append(text)

    result = run(session, model, registry, journal=Journal(), notice=notice,
                 progress_advice=True, interactive=False, model_recovery_env={})

    assert result.status == "complete" and len(model.requests) == 6 and len(registry.executed) == 5
    assert len(appended) == 1 and appended[0]["role"] == "system"
    assert appended[0]["content"].startswith("[进度提醒] 已连续 4 轮")
    assert "AskUserQuestion" not in appended[0]["content"]
    assert notices == ["\n[进度提醒:已连续 4 轮无实质推进]\n"]
    first, next_request, last_request = [request["messages"] for request in model.requests[-3:]]
    assert appended[0] not in first
    assert next_request[-1] == appended[0] and next_request[-2]["tool_call_id"] == "read-4"
    assert last_request[:len(next_request)] == next_request
    assert saved[-1] == session.messages == [*last_request, {"role": "assistant", "content": "done"}]
