"""Frozen tool_audit.test.ts and the required redacted observational boundary."""

import json


def test_source_call_one_line_args120_and_redact_before_truncation(tmp_path):
    from ruocun.tools.tool_audit import createToolAuditSink

    sink = createToolAuditSink(tmp_path, {}, redact=lambda text: text.replace("synthetic-current-key", "[key]"))
    sink.call("Read", "read", True, 12, "x" * 300)
    secret = "sk" + "-" + "A" * 24
    sink.call("Write", "write", False, 8, "synthetic-current-key " + secret + " " + "😀" * 100,
              metadata={"sessionId": "synthetic-session", "taskId": "synthetic-task",
                        "runId": "synthetic-run", "toolCallId": "synthetic-call"})
    raw = (tmp_path / "tool-trace.jsonl").read_text("utf-8")
    events = [json.loads(line) for line in raw.split("\n") if line]
    assert events[0] == {**events[0], "kind": "call", "name": "Read", "cap": "read", "ok": True, "durationMs": 12}
    assert isinstance(events[0]["ts"], int) and len(events[0]["args"]) == 120
    assert "synthetic-current-key" not in raw and secret not in raw
    assert events[1]["args"].startswith("[key] [已隐去:")
    assert len(events[1]["args"].encode("utf-16-le", errors="surrogatepass")) == 240
    assert events[1]["toolCallId"] == "synthetic-call" and events[1]["runId"] == "synthetic-run"


def test_source_switch_noop_native_precedence_and_io_failure_bypass(tmp_path):
    from ruocun.tools.tool_audit import createToolAuditSink

    for index, values in enumerate(({"RUOCUN_TOOL_AUDIT": "0"}, {"RUOCUN_AUDIT": "0"},
                                    {"RUOCUN_TOOL_AUDIT": "0", "DAO_TOOL_AUDIT": "1"})):
        directory = tmp_path / str(index)
        createToolAuditSink(directory, values).call("x", "read", True, 1, "")
        assert not (directory / "tool-trace.jsonl").exists()
    specific = tmp_path / "specific"
    createToolAuditSink(specific, {"RUOCUN_AUDIT": "0", "RUOCUN_TOOL_AUDIT": "1"}).call("x", "read", True, 1, "")
    assert (specific / "tool-trace.jsonl").exists()
    broken = tmp_path / "not-a-directory"
    broken.write_text("preserve existing file", encoding="utf-8")
    createToolAuditSink(broken, {}).call("x", "read", True, 1, "")
    assert broken.read_text("utf-8") == "preserve existing file"


def test_source_summary_error_rate_duration_sort_and_format():
    from ruocun.tools.tool_audit import formatToolReport, summarizeToolTrace

    events = [{"kind": "call", "name": name, "ok": ok, "durationMs": duration}
              for name, ok, duration in [("A", True, 10), ("A", False, 30), ("B", True, 5)]]
    stats = summarizeToolTrace(events)
    assert stats[0] == {"name": "A", "calls": 2, "errors": 1, "maxMs": 30, "totalMs": 40,
                        "errorRate": .5, "avgMs": 20}
    assert "错误率" in formatToolReport(stats)
    assert "  A                  调用    2 · 错误率  50% · 均 20ms · 峰 30ms" in formatToolReport(stats)
    assert formatToolReport([]) == "暂无工具调用记录。"


def test_source_reader_skips_missing_bad_lines_and_non_call_events(tmp_path):
    from ruocun.tools.tool_audit import readAllToolTraces, summarizeToolTrace

    assert readAllToolTraces(tmp_path / "missing") == []
    (tmp_path / "session").mkdir()
    event = {"kind": "call", "ts": 1, "name": "Read", "cap": "read", "ok": True, "durationMs": 4,
             "args": "line\u2028separator"}
    (tmp_path / "session" / "tool-trace.jsonl").write_text(json.dumps(event, ensure_ascii=False) + "\n{broken\n\n",
                                                           encoding="utf-8")
    assert readAllToolTraces(tmp_path) == [event]
    assert summarizeToolTrace([{"kind": "other"}, *readAllToolTraces(tmp_path)])[0]["calls"] == 1
