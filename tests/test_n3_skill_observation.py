"""冻结 usage.test.ts 与 skill_audit.test.ts 的六个行为。"""

import asyncio
import json
import sys

import pytest

from ruocun.skills.skill_audit import (
    createSkillAuditSink,
    readAllSkillTraces,
    summarizeSkillTrace,
)
from ruocun.skills.usage import loadUsage, recordUsage, saveUsage, usageScore


def test_record_usage_increments_count_and_replaces_date(tmp_path):
    usage = recordUsage({}, "pdf", "2026-06-10")
    usage = recordUsage(usage, "pdf", "2026-06-13")
    assert usage["pdf"] == {"count": 2, "lastUsedAt": "2026-06-13"}
    if sys.platform == "win32":
        root = tmp_path / "native"
        assert asyncio.run(saveUsage(root, usage)) == "saved"
        assert asyncio.run(loadUsage(root)) == usage
        file = root / "skill-usage.json"
        file.write_bytes(b"{broken usage")
        assert asyncio.run(loadUsage(root)) == {}
        assert asyncio.run(saveUsage(root, usage)) == "failed"
        assert file.read_bytes() == b"{broken usage"


def test_usage_score_half_life_and_floor():
    usage = {"fresh": {"count": 4, "lastUsedAt": "2026-06-13"},
             "old": {"count": 4, "lastUsedAt": "2026-04-01"}}
    assert usageScore(usage, "fresh", "2026-06-13") == pytest.approx(4)
    assert usageScore(usage, "fresh", "2026-06-20") == pytest.approx(2)
    assert usageScore(usage, "old", "2026-06-13") == pytest.approx(0.4)
    assert usageScore(usage, "never", "2026-06-13") == 0


def test_skill_audit_writes_one_jsonl_row_per_load(tmp_path):
    session = tmp_path / "session"
    sink = createSkillAuditSink(session, {})
    sink.loaded(1, "tsx-conv")
    sink.loaded(2, "debugging")
    trace = session / "skill-trace.jsonl"
    lines = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert [(item["kind"], item["round"], item["name"]) for item in lines] == [
        ("loaded", 1, "tsx-conv"), ("loaded", 2, "debugging"),
    ]
    unicode_name = {**lines[-1], "name": "debugging\u2028note"}
    unicode_row = (json.dumps(unicode_name, ensure_ascii=False) + "\n").encode("utf-8")
    trace.write_bytes(b"\xff\n" + trace.read_bytes() + unicode_row)
    assert readAllSkillTraces(tmp_path) == [*lines, unicode_name]


def test_skill_audit_disabled_does_not_create_file(tmp_path):
    sink = createSkillAuditSink(tmp_path, {"RUOCUN_SKILL_AUDIT": "0"})
    sink.loaded(1, "a")
    assert not (tmp_path / "skill-trace.jsonl").exists()


def test_summarize_counts_unique_rounds_and_orders_by_loads():
    events = [{"kind": "loaded", "round": round_id, "ts": 0, "name": name}
              for round_id, name in [(1, "A"), (1, "A"), (2, "A"), (3, "B")]]
    assert summarizeSkillTrace(events) == [
        {"name": "A", "loaded": 2, "total": 3}, {"name": "B", "loaded": 1, "total": 1},
    ]


def test_summarize_skips_old_offered_and_activated_events():
    events = [{"kind": "offered", "round": 1, "ts": 0, "input": "x", "candidates": [{"name": "Z", "score": 3}]},
              {"kind": "loaded", "round": 1, "ts": 0, "name": "A"}]
    assert summarizeSkillTrace(events) == [{"name": "A", "loaded": 1, "total": 1}]
