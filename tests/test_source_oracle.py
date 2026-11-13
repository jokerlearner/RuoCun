"""CLI/fake HTTP seam confirmed in spec T-02 and T-N1; no product package needed."""

import json
import os
from pathlib import Path

import pytest
from oracle import driver as oracle

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def oracle_run():
    node = os.environ.get("RUOCUN_ORACLE_NODE")
    cache = os.environ.get("RUOCUN_ORACLE_CACHE")
    return lambda output, **kwargs: oracle.run_oracle(
        ROOT,
        output,
        node=Path(node) if node else None,
        cache=Path(cache) if cache else None,
        **kwargs,
    )


@pytest.mark.oracle
def test_frozen_cli_returns_read_result_to_model_in_plan_mode(tmp_path, oracle_run):
    """Read oracle: read_file.test.ts offset/limit and loop.test.ts plan contract."""
    result = oracle_run(tmp_path / "evidence")
    assert result["source"]["status"] == "passed", result
    trace = json.loads(
        (tmp_path / "evidence/requests.json").read_text(encoding="utf-8")
    )
    assert len(trace) == 2
    first, second = (request["body"] for request in trace)
    assert first["model"] == "deepseek-v4-pro"
    assert first["stream"] is True
    assert first["parallel_tool_calls"] is True
    names = [tool["function"]["name"] for tool in first["tools"]]
    assert "Read" in names and "TodoWrite" in names
    assert not {"Write", "Edit", "Bash"}.intersection(names)
    read = next(
        tool["function"]
        for tool in first["tools"]
        if tool["function"]["name"] == "Read"
    )
    assert read["parameters"]["required"] == ["path"]
    assert read["parameters"]["properties"]["offset"]["minimum"] == 1
    results = {
        message["tool_call_id"]: message["content"]
        for message in second["messages"]
        if message["role"] == "tool"
    }
    assert results == {"call_plan": "▶ 读取材料", "call_read": "2\t口腔研究"}
    assert result["port"]["status"] == "not-run"
    assert result["classification"] == "UNVERIFIED"
    network = [
        json.loads(line)
        for line in (tmp_path / "evidence/network.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    allowed_network = [
        record
        for record in network
        if record["allowed"] and record["url"].startswith(("http:", "https:"))
    ]
    assert len(allowed_network) == 2
    assert all(
        record["method"] == "POST"
        and record["url"].startswith("http://127.0.0.1:")
        and record["url"].endswith("/v1/chat/completions")
        for record in allowed_network
    )
    assert result["cleanup"]["child_exited"] is True
    assert result["cleanup"]["server_closed"] is True


@pytest.mark.oracle
def test_headless_rejects_read_first_batch_then_accepts_plan_and_read(
    tmp_path, oracle_run
):
    """execute.ts headless enforcement, through the actual CLI and model wire."""
    result = oracle_run(tmp_path / "evidence", scenario="read-first")
    assert result["source"]["status"] == "passed", result
    trace = json.loads(
        (tmp_path / "evidence/requests.json").read_text(encoding="utf-8")
    )
    assert len(trace) == 3
    rejected = [
        message for message in trace[1]["body"]["messages"] if message["role"] == "tool"
    ]
    assert len(rejected) == 1
    assert "TodoWrite" in rejected[0]["content"]
    assert "2\t口腔研究" not in rejected[0]["content"]
    final_results = [
        message["content"]
        for message in trace[2]["body"]["messages"]
        if message["role"] == "tool"
    ]
    assert final_results[-2:] == ["▶ 读取材料", "2\t口腔研究"]


@pytest.mark.oracle
def test_deadline_stops_cli_and_closes_local_transport(tmp_path, oracle_run):
    result = oracle_run(tmp_path / "evidence", scenario="stall", timeout=10)
    assert result["source"]["status"] == "canceled", result
    assert result["classification"] == "UNVERIFIED"
    assert result["cleanup"]["child_exited"] is True
    assert result["cleanup"]["server_closed"] is True
    assert result["cleanup"]["tree_stop_requested"] is True
    trace = json.loads(
        (tmp_path / "evidence/requests.json").read_text(encoding="utf-8")
    )
    assert len(trace) == 1


@pytest.mark.parametrize(
    "source,port,approved,confirmed,expected",
    [
        ("passed", "not-run", False, False, "UNVERIFIED"),
        ("failed", "failed", False, False, "UNVERIFIED"),
        ("failed", "not-run", False, True, "SOURCE-DEFECT"),
        ("passed", "failed", False, False, "PORT-REGRESSION"),
        ("passed", "failed", True, False, "INTENTIONAL-DELTA"),
        ("environment-error", "not-run", False, False, "ENV"),
        ("passed", "environment-error", False, False, "ENV"),
        ("passed", "passed", False, False, None),
        ("canceled", "not-run", False, False, "UNVERIFIED"),
    ],
)
def test_outcome_classification_keeps_unverified_and_confirmed_failures_separate(
    source, port, approved, confirmed, expected
):
    assert (
        oracle.classify_outcomes(
            source, port, approved_delta=approved, source_defect_confirmed=confirmed
        )
        == expected
    )
