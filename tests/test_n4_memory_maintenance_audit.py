"""Frozen memory_audit.test.ts assertions for the two maintenance events."""

import json

from ruocun.memory.memory_audit import (
    createMemoryAuditSink,
    formatMemoryReport,
    summarizeMemoryTrace,
)


def test_distilled_writes_one_event(tmp_path):
    createMemoryAuditSink(tmp_path, {}).distilled(5, 3, 2)
    row, = (tmp_path / "memory-trace.jsonl").read_text(encoding="utf-8").splitlines()
    event = json.loads(row)
    assert (event["kind"], event["extracted"], event["added"], event["updated"]) == ("distilled", 5, 3, 2)


def test_disabled_memory_audit_writes_nothing(tmp_path):
    createMemoryAuditSink(tmp_path, {"RUOCUN_MEMORY_AUDIT": "0"}).distilled(5, 3, 2)
    assert not (tmp_path / "memory-trace.jsonl").exists()


def test_distill_summary_and_report():
    summary = summarizeMemoryTrace([{"kind": "distilled", "ts": 0, "extracted": 5, "added": 3, "updated": 2}])
    assert summary["distill"] == {"extracted": 5, "added": 3, "updated": 2}
    assert "抽取 5" in formatMemoryReport(summary)


def test_consolidation_summary_aggregates_counts_and_reasons():
    events = [
        {"kind": "consolidated", "ts": 0, "scope": "user", "groups": 2, "superseded": 3,
         "reasons": ["画像维度收敛", "技术偏好并入"]},
        {"kind": "consolidated", "ts": 0, "scope": "project", "groups": 1, "superseded": 1,
         "reasons": ["两条完成状态去重"]},
    ]
    summary = summarizeMemoryTrace(events)
    assert summary["consolidation"] == {
        "runs": 2, "groups": 3, "superseded": 4,
        "reasons": ["画像维度收敛", "技术偏好并入", "两条完成状态去重"],
    }
    assert "合并 pass" in formatMemoryReport(summary) and "画像维度收敛" in formatMemoryReport(summary)


def test_report_without_consolidation_omits_consolidation_row():
    summary = summarizeMemoryTrace([])
    assert "consolidation" not in summary and "合并 pass" not in formatMemoryReport(summary)


def test_consolidated_writes_scope_counts_and_reasons(tmp_path):
    payload = {"scope": "knowledge", "groups": 2, "superseded": 4, "reasons": ["合成重复"]}
    createMemoryAuditSink(tmp_path, {}).consolidated(payload)
    row, = (tmp_path / "memory-trace.jsonl").read_text(encoding="utf-8").splitlines()
    event = json.loads(row)
    assert event["kind"] == "consolidated" and all(event[key] == value for key, value in payload.items())
