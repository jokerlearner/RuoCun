"""REC-01/02/03/09/15 expectations through real child processes and disk SQLite.

Prepared in advance; execute only after an explicit complete candidate SHA.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading

import pytest

PROBE = Path(__file__).with_name("store_probe.py").resolve()
REPO = Path(__file__).resolve().parents[4]
ARCHIVE = REPO / "tests/fixtures/sqlite-dll-win-x64-3540100.zip"


def argv(root: Path, action: str) -> list[str]:
    return [sys.executable, "-I", "-X", "utf8", str(PROBE), action, str(root), str(ARCHIVE)]


def run(root: Path, action: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv(root, action), capture_output=True, text=True, encoding="utf-8", timeout=30)


def passed(root: Path, action: str) -> dict:
    child = run(root, action)
    assert child.returncode == 0, child.stderr
    return json.loads(child.stdout)


def snapshot(directory: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.iterdir() if p.is_file()}


def test_public_save_and_restart_ignores_poisoned_side_exports(tmp_path: Path) -> None:
    assert passed(tmp_path, "save") == {"saved_revision": 1, "owner_epoch": 1}
    directory = tmp_path / "private"
    (directory / "state.json").write_text('{"messages":[{"content":"wrong-side-value"}]}', encoding="utf-8")
    (directory / "events.jsonl").write_text('{"content":"wrong-side-value"}\n', encoding="utf-8")
    actual = passed(tmp_path, "readonly")
    assert actual["messages"] == [{"role": "user", "content": "独立保存中文"}]
    assert actual["revision"] == actual["delivered_revision"] == 1
    assert actual["accepted_inputs"] == [{"input_id": "input-1", "seq": 1, "payload": "已确认排队", "attachment_refs": [], "state": "queued"}]
    assert actual["usage"] == {"promptTokens": 7, "completionTokens": 3}
    assert actual["title"] == "独立标题"
    record = passed(tmp_path, "runtime")
    assert record["version"] == "3.54.1" and record["gate"] == "met"
    assert record["compile_options"] and record["driver_extension_sha256"]


def test_live_owner_rejection_then_killed_owner_recovery_with_retained_handle(tmp_path: Path) -> None:
    child = subprocess.Popen(argv(tmp_path, "hold"), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8")
    reply: queue.Queue[str] = queue.Queue()
    reader = threading.Thread(target=lambda: reply.put(child.stdout.readline()), daemon=True)
    reader.start()
    try:
        ready = json.loads(reply.get(timeout=30))
        reader.join(timeout=1)
        assert not reader.is_alive()
        assert ready == {"ready": True, "owner_epoch": 1}
        assert passed(tmp_path, "expect-live-owner") == {"live_owner_rejected": True}
        child.terminate()  # Terminate only this owned Popen process handle.
        child.communicate(timeout=15)
        assert child.poll() is not None
        # Keep Popen and its process handle alive throughout the takeover check.
        recovered = passed(tmp_path, "claim")
        assert recovered["owner_epoch"] == 2
        assert recovered["checkpoint"]["revision"] == 1
        assert recovered["checkpoint"]["messages"] == [{"role": "user", "content": "独立保存中文"}]
    finally:
        if child.poll() is None:
            child.terminate()
            child.communicate(timeout=15)
        reader.join(timeout=2)
        assert not reader.is_alive()


@pytest.mark.parametrize("mutation", ["future", "dao", "zero", "missing-checkpoint", "checkpoint-revision"])
def test_untrusted_database_is_rejected_without_overwriting_main_file(tmp_path: Path, mutation: str) -> None:
    passed(tmp_path, "save")
    passed(tmp_path, "mutate-" + mutation)
    before = hashlib.sha256((tmp_path / "private/session.db").read_bytes()).hexdigest()
    result = run(tmp_path, "claim")
    assert result.returncode != 0, "untrusted database was accepted"
    after = hashlib.sha256((tmp_path / "private/session.db").read_bytes()).hexdigest()
    assert before == after, "rejected database main file was modified"
    assert "VersionRejectError" in result.stderr or "MissingCheckpointError" in result.stderr or "CorruptDatabaseError" in result.stderr


def test_real_database_transactions_fence_and_roll_back(tmp_path: Path) -> None:
    assert passed(tmp_path, "atomic") == {"run_event_rollback": True, "epoch_fenced": True, "tool_identity_checked": True}


def test_real_sqlite_full_does_not_ack_or_consume_event(tmp_path: Path) -> None:
    assert passed(tmp_path, "disk-full") == {"sqlite_full_observed": True, "checkpoint_and_delivery_rollback": True}


def test_readonly_main_database_bytes_remain_unchanged(tmp_path: Path) -> None:
    passed(tmp_path, "save")
    before = snapshot(tmp_path / "private")
    assert passed(tmp_path, "readonly")["revision"] == 1
    after = snapshot(tmp_path / "private")
    assert before["session.db"] == after["session.db"]
    print(json.dumps({"readonly_file_changes": sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))}))


@pytest.mark.parametrize("scenario", ["worker-cancel", "worker-lost-ack"])
def test_real_worker_cancel_unknown_commit_and_close_resources(tmp_path: Path, scenario: str) -> None:
    assert passed(tmp_path, scenario) == {"scenario": scenario, "real_disk": True, "thread_joined": True, "namespace_released": True}


@pytest.mark.parametrize("scenario", ["result-run", "result-event-run", "result-event-session", "run-event-run", "run-event-session"])
def test_conflicting_result_run_event_association_is_rejected_atomically(tmp_path: Path, scenario: str) -> None:
    action = "association-" + scenario
    assert passed(tmp_path, action) == {"rejected_atomically": action}
