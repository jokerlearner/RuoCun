"""Independent process entry for the complete ticket-07 save/restart path."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows controlled SQLite")


def test_store_demo_saves_real_local_chat_and_recovers_in_new_process(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    root = tmp_path / "demo"
    command = [sys.executable, "-I", "-X", "utf8", "-m", "ruocun.session.demo",
               "--workspace", str(root), "--archive", str(archive.resolve())]
    result = subprocess.run(command, capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "passed"
    assert report["answer"] == "你好，世界 😀"
    assert report["saved_revision"] == report["restored_revision"] == 1
    assert report["saved_owner_epoch"] == 1 and report["restored_owner_epoch"] == 2
    assert report["operation_receipt_revision"] == 1
    assert report["sqlite_version"] == "3.54.1"
    assert report["wire_request_validated"] and report["server_closed"]
    assert report["processes_exited"]
    assert "sk-synthetic" not in result.stdout
    before = (root / "session/session.db").read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert repeated.returncode != 0
    assert (root / "session/session.db").read_bytes() == before
