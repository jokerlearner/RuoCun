"""冻结 src/session/cache_audit.test.ts 的来源断言（MIT）；仅合成日志。"""

import json
from pathlib import Path

from ruocun.session.cache_audit import (
    createCacheAuditSink,
    divergence,
    formatCacheReport,
)


def _input(*, sys: str = "S", turn: int = 0, hit: int = 900, **extra):
    return {
        "agent": "main", "depth": 0, "turn": turn, "model": "pro",
        "usage": {"prompt_tokens": 1000, "completion_tokens": 10, "total_tokens": 1010,
                  "prompt_cache_hit_tokens": hit, "prompt_cache_miss_tokens": 1000 - hit},
        "sys": sys, "tools": "T", "tail": "", **extra,
    }


def _events(directory: Path):
    return [json.loads(line) for line in (directory / "cache.jsonl").read_text("utf-8").splitlines()]


def test_appends_one_event_with_ratio_and_fingerprint(tmp_path):
    sink = createCacheAuditSink(tmp_path, {})
    sink.record(_input())
    events = _events(tmp_path)
    assert len(events) == 1
    assert events[0]["agent"] == "main"
    assert events[0]["ratio"] == .9
    assert events[0]["hit"] == 900
    assert events[0]["changed"] == []
    assert isinstance(events[0]["fp"]["sys"], str)


def test_changed_dimension_records_lengths_and_delta(tmp_path):
    sink = createCacheAuditSink(tmp_path, {})
    sink.record(_input(sys="SYSTEM-A"))
    sink.record(_input(sys="SYSTEM-B-longer", turn=1, hit=50))
    event = _events(tmp_path)[1]
    assert event["changed"] == ["sys"]
    assert event["delta"]["sys"]["fromLen"] == 8
    assert event["delta"]["sys"]["toLen"] == 15


def test_subagent_does_not_pollute_main_previous_content(tmp_path):
    sink = createCacheAuditSink(tmp_path, {})
    sink.record(_input(sys="MAIN"))
    sink.record(_input(sys="SUB", agent="sub", subId="ab", depth=1, hit=0))
    sink.record(_input(sys="MAIN", turn=1))
    assert _events(tmp_path)[2]["changed"] == []


def test_cache_audit_zero_is_noop_with_no_file(tmp_path):
    sink = createCacheAuditSink(tmp_path, {"RUOCUN_CACHE_AUDIT": "0"})
    sink.record(_input())
    assert not (tmp_path / "cache.jsonl").exists()


def test_distill_same_prefix_reports_divergence_at_end(tmp_path):
    sink = createCacheAuditSink(tmp_path, {})
    prefix = '[{"role":"user","content":"hi"},{"role":"assistant","content":"yo"}]'
    sink.record(_input(turn=5, msgs=prefix))
    sink.record(_input(agent="distill", hit=500, msgs=prefix))
    events = _events(tmp_path)
    assert events[0]["fp"]["msgs"] == events[1]["fp"]["msgs"]
    assert events[1]["delta"]["vsMain"]["firstDiffAt"] == len(prefix)


def test_distill_changed_prefix_reports_first_divergence(tmp_path):
    sink = createCacheAuditSink(tmp_path, {})
    prefix = '[{"role":"user","content":"hi"},{"role":"assistant","content":"yo"}]'
    changed = '[{"role":"user","content":"hi"},{"role":"assistant","content":"YO-DIFFERENT"}]'
    sink.record(_input(turn=5, msgs=prefix))
    sink.record(_input(agent="distill", hit=200, msgs=changed))
    events = _events(tmp_path)
    assert events[0]["fp"]["msgs"] != events[1]["fp"]["msgs"]
    assert events[1]["delta"]["vsMain"]["firstDiffAt"] < len(changed)
    assert events[1]["delta"]["vsMain"]["sample"]


def test_divergence_reports_offset_and_new_sample():
    difference = divergence("hello world", "hello brave world")
    assert difference["firstDiffAt"] == 6
    assert difference["sample"].startswith("brave")
    # Python 必要适配确认：来源偏移是 UTF-16 代码单元，非 Unicode 码点。
    assert divergence("😀x", "😀y") == {"firstDiffAt": 2, "sample": "y"}


def test_format_report_has_each_turn_and_changed_dimension():
    events = [
        {"ts": 1000, "agent": "main", "depth": 0, "turn": 0, "model": "pro", "prompt": 20000,
         "hit": 19000, "miss": 1000, "completion": 5, "ratio": .95, "fp": {}, "changed": []},
        {"ts": 2000, "agent": "main", "depth": 0, "turn": 1, "model": "pro", "prompt": 21000,
         "hit": 1000, "miss": 20000, "completion": 5, "ratio": .05, "fp": {}, "changed": ["sys"]},
    ]
    output = formatCacheReport(events)
    assert "t0" in output
    assert "破:sys" in output
