"""Frozen memory_audit reflected/corrected reporting and failure-bypass semantics."""

import json


def test_source_reflection_trace_counts_details_recent_notes_and_switch(tmp_path):
    from ruocun.memory.memory_audit import (
        createMemoryAuditSink,
        formatReflectReport,
        summarizeReflectTrace,
    )

    sink = createMemoryAuditSink(tmp_path, {})
    sink.corrected({"target": "old fact", "action": "revise", "reason": "verified"})
    sink.reflected({"ran": True, "onTrack": False, "advisoryInjected": True, "memAdded": 1,
                    "memMerged": 2, "interval": 2, "note": "正在核对目标", "corrected": 1, "confirmed": 3})
    sink.reflected({"ran": False, "onTrack": True, "advisoryInjected": False, "memAdded": 0,
                    "memMerged": 0, "interval": 3})
    events = [json.loads(line) for line in (tmp_path / "memory-trace.jsonl").read_text("utf-8").splitlines()]
    summary = summarizeReflectTrace(events)
    assert summary["rounds"] == 2 and summary["ran"] == 1 and summary["advisories"] == 1
    assert summary["corrected"] == 1 and summary["confirmed"] == 3 and summary["lastInterval"] == 3
    assert summary["correctedDetails"][0]["reason"] == "verified"
    report = formatReflectReport(summary)
    assert "节奏跳过 1" in report and "正在核对目标" in report and "old fact" in report
    disabled = tmp_path / "disabled"
    createMemoryAuditSink(disabled, {"RUOCUN_AUDIT": "0"}).reflected({"ran": True, "onTrack": True,
        "advisoryInjected": False, "memAdded": 0, "memMerged": 0, "interval": 1})
    assert not (disabled / "memory-trace.jsonl").exists()


def test_source_recall_write_aggregation_and_all_session_read(tmp_path):
    from ruocun.memory.memory_audit import (
        createMemoryAuditSink,
        formatMemoryReport,
        readAllMemoryTraces,
        summarizeMemoryTrace,
    )

    sink = createMemoryAuditSink(tmp_path / "session-a", {})
    sink.recalled(4, 2, 1, {"project": 3}, 2)
    sink.wrote("project", False)
    sink.wrote("project", True)
    with (tmp_path / "session-a" / "memory-trace.jsonl").open("a", encoding="utf-8") as stream:
        stream.write("invalid json\n")
    summary = summarizeMemoryTrace(readAllMemoryTraces(tmp_path))
    assert summary["recall"]["foreign"] == 2
    assert summary["writes"] == 2 and summary["writesMerged"] == 1
    assert summary["byType"]["project"] == {"total": 2, "merged": 1}
    assert "合并率 50%" in formatMemoryReport(summary)
