"""Frozen cadence, health and independent reflection-result parsing expectations."""

import json


def test_source_adaptive_cadence_and_progress_reset():
    from ruocun.agent.reflect_cadence import applyOutcome, initCadence, tickCadence

    first = tickCadence(initCadence())
    assert first["run"]
    quiet = applyOutcome(first["next"], True)
    second = tickCadence(quiet)
    assert quiet["interval"] == 2 and not second["run"]
    assert tickCadence(second["next"])["run"]
    for _ in range(10):
        quiet = applyOutcome(quiet, True)
    assert quiet["interval"] == 3
    assert applyOutcome(quiet, False)["interval"] == 1
    assert tickCadence(applyOutcome(quiet, True, 1), 1)["run"]


def test_source_health_failures_even_with_writes_repeat_errors_and_refocus():
    from ruocun.agent.turn_health import (
        assessTurn,
        defaultHealthConfig,
        errSignature,
        initHealth,
    )

    state, config = initHealth(), defaultHealthConfig({})
    for _ in range(2):
        decision = assessTurn(state, {"progressed": True, "toolFailures": 1}, config, {"longTask": False})
        assert not decision["challenger"]
        state = decision["next"]
    decision = assessTurn(state, {"progressed": True, "toolFailures": 1}, config, {"longTask": False})
    assert decision["challenger"] and decision["reason"] == "failure-streak"
    assert decision["next"]["failureStreak"] == 0
    repeated = assessTurn(initHealth(), {"progressed": False, "toolFailures": 1, "errSig": "same"}, config, {"longTask": False})
    repeated = assessTurn(repeated["next"], {"progressed": False, "toolFailures": 1, "errSig": "same"}, config, {"longTask": False})
    assert repeated["challenger"] and repeated["reason"] == "repeated-error"
    state = initHealth()
    for _ in range(3):
        decision = assessTurn(state, {"progressed": True, "toolFailures": 0}, config, {"longTask": True})
        state = decision["next"]
    assert decision["refocuser"] and decision["reason"] == "refocus-cadence"
    assert errSignature("Error 12 at /tmp/a 0x123") == errSignature("Error 999 at /other/b 0x999")
    assert defaultHealthConfig({"RUOCUN_REFOCUS_EVERY": "0"})["refocusEvery"] == 0


def test_source_reflection_independent_sections_noise_and_invalid_fallback():
    from ruocun.agent.reflect_result import parseReflectResult

    safe = {"onTrack": True, "advisory": None, "memories": [], "corrections": [], "confirmed": []}
    assert parseReflectResult("模型胡言乱语没有 JSON") == safe
    assert parseReflectResult('好的\n```json\n{"onTrack":true,"advisory":null,"memories":[]}\n```') == safe
    result = parseReflectResult(json.dumps({"onTrack": True, "advisory": "在轨继续", "note": "在写测试故判在轨",
        "memories": [{"title": "好的一条", "text": "完整事实", "type": "user"}, {"title": "缺正文", "type": "user"}],
        "corrections": [{"target": "旧事实A", "action": "supersede", "reason": "有实测"},
                        {"target": "旧事实B", "action": "revise", "newText": "新的完整事实"},
                        {"target": "X", "action": "revise"}, {"target": "Y", "action": "delete"}],
        "confirmed": ["A", "", "  ", "B"]}))
    assert result["onTrack"] and result["advisory"] is None and result["note"] == "在写测试故判在轨"
    assert len(result["memories"]) == 1 and len(result["corrections"]) == 2 and result["confirmed"] == ["A", "B"]
    assert not parseReflectResult('{"advisory":"有问题"}')["onTrack"]
    assert parseReflectResult('{"onTrack":false,"advisory":{},"memories":[{"title":"t","text":"x","type":"semantic"}]}')["memories"]
