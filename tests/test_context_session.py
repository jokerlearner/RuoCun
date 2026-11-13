"""冻结 src/session/session.test.ts 的 10 项 Session 语义（MIT）。"""

import pytest

from ruocun.session.session import Session


def test_starts_with_system_and_given_model():
    s = Session("SYS", "deepseek-v4-pro", env={})
    assert s.messages == [{"role": "system", "content": "SYS"}]
    assert s.model == "deepseek-v4-pro" and s.mode == "normal"


def test_appends_user_messages():
    s = Session("SYS", "m", env={})
    s.addUser("hi")
    assert s.messages == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "hi"}]


def test_clear_resets_to_system():
    s = Session("SYS", "m", env={})
    s.addUser("a")
    s.messages.append({"role": "assistant", "content": "b"})
    s.lastPromptTokens, s.lastSentLength = 50000, 10
    s.clear()
    assert s.messages == [{"role": "system", "content": "SYS"}]
    assert s.lastPromptTokens is None and s.lastSentLength == 0


def test_set_model_keeps_messages():
    s = Session("SYS", "m", env={})
    s.addUser("a")
    s.setModel("deepseek-v4-flash")
    assert s.model == "deepseek-v4-flash" and len(s.messages) == 2


def test_toggle_mode():
    s = Session("SYS", "m", env={})
    assert s.toggleMode() == s.mode == "plan"
    assert s.toggleMode() == "normal"


def test_accumulates_usage_and_cache_ratio():
    s = Session("SYS", "deepseek-v4-pro", env={})
    for hit in (900, 800):
        s.addUsage({"prompt_tokens": 1000, "completion_tokens": 50,
                    "prompt_cache_hit_tokens": hit, "prompt_cache_miss_tokens": 1000 - hit})
    assert s.usage["promptTokens"] == 2000
    assert s.usage["completionTokens"] == 100 and s.usage["cacheHitTokens"] == 1700
    assert s.cacheHitRatio() == pytest.approx(.85)
    assert "命中率 85.0%" in s.usageSummary()


def test_missing_cache_and_empty_sessions():
    s = Session("S", "m", env={})
    s.addUsage({"prompt_tokens": 100, "completion_tokens": 10})
    assert s.usage["cacheHitTokens"] == 0 and s.cacheHitRatio() == 0
    assert "暂无" in Session("S", "m", env={}).usageSummary()


def test_cache_bust_fires_for_high_prefix_collapse():
    s = Session("S", "m", env={})
    hits = []
    s.onCacheBust(hits.append)
    s.addUsage({"prompt_tokens": 20000, "prompt_cache_hit_tokens": 19000})
    assert hits == []
    s.addUsage({"prompt_tokens": 21000, "prompt_cache_hit_tokens": 1000})
    assert len(hits) == 1
    assert hits[0]["from"] == pytest.approx(.95, abs=.1)
    assert hits[0]["to"] == pytest.approx(.05, abs=.1)


def test_cache_bust_changed_prefix_dimension():
    s = Session("S", "m", env={})
    hits = []
    s.onCacheBust(hits.append)
    s.notePrefix({"model": "pro", "sys": "h1", "tools": "t1", "tail": "x"})
    s.addUsage({"prompt_tokens": 20000, "prompt_cache_hit_tokens": 19000})
    s.notePrefix({"model": "pro", "sys": "h2", "tools": "t1", "tail": "x"})
    s.addUsage({"prompt_tokens": 21000, "prompt_cache_hit_tokens": 500})
    assert hits[0]["changed"] == ["sys"]


def test_first_small_and_healthy_calls_do_not_warn():
    s = Session("S", "m", env={})
    hits = []
    s.onCacheBust(hits.append)
    for prompt, hit in ((18000, 0), (19000, 18000), (20000, 19000), (500, 0)):
        s.addUsage({"prompt_tokens": prompt, "prompt_cache_hit_tokens": hit})
    assert hits == []
