"""Frozen shadow Git snapshot/restore semantics using synthetic repository data."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from time import monotonic

import pytest

_WINDOWS_GIT = Path("D:/study_software/Git/cmd/git.exe")


@pytest.fixture
def git(monkeypatch):
    if os.name == "nt" and _WINDOWS_GIT.is_file():
        monkeypatch.setenv("PATH", str(_WINDOWS_GIT.parent) + os.pathsep + os.environ["PATH"])
    path = shutil.which("git")
    if path is None:
        pytest.skip("Git unavailable")

    def run(cwd, *args):
        return subprocess.run([path, *args], cwd=cwd, check=True, capture_output=True).stdout

    return run


def test_source_checkpoint_enable_disable_and_settings(tmp_path, git):
    from ruocun.session.checkpoint import createCheckpointer, readCheckpointEnabled

    assert not createCheckpointer(tmp_path).enabled
    assert not createCheckpointer(tmp_path, enabled=True, environ={**os.environ, "RUOCUN_NO_CHECKPOINT": "1"}).enabled
    assert not (tmp_path / ".ruocun" / "shadow.git").exists()
    user, project = tmp_path / "user.json", tmp_path / "project.json"
    user.write_text('{"checkpoint":{"enabled":true}}', encoding="utf-8")
    project.write_text('{"checkpoint":{"enabled":false}}', encoding="utf-8")
    assert not readCheckpointEnabled(user, project)
    project.write_text('{"checkpoint":{"enabled":"false"}}', encoding="utf-8")
    assert readCheckpointEnabled(user, project)
    assert createCheckpointer(tmp_path, environ={**os.environ, "RUOCUN_CHECKPOINT": "1"}).enabled
    assert (tmp_path / ".ruocun" / "shadow.git").is_dir() and not (tmp_path / ".git").exists()


def test_source_checkpoint_restore_keeps_pre_restore_and_real_git(tmp_path, git):
    from ruocun.session.checkpoint import createCheckpointer

    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Synthetic")
    git(tmp_path, "config", "user.email", "synthetic@example.invalid")
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("v1", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("*.ignored\n", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "real repo base")
    real_head = git(tmp_path, "rev-parse", "HEAD")
    real_index = (tmp_path / ".git" / "index").read_bytes()
    cp = createCheckpointer(tmp_path, enabled=True)
    ref1 = cp.snapshot("turn1")
    assert ref1
    a.write_text("v2", encoding="utf-8")
    b.write_text("new", encoding="utf-8")
    (tmp_path / "keep.ignored").write_text("ignored user data", encoding="utf-8")
    (tmp_path / "artifact.bin").write_bytes(b"\0" * 1024)
    assert cp.snapshot("turn2")
    assert [item["label"] for item in cp.list()] == ["turn2", "turn1"]
    a.write_text("unsnapshotted", encoding="utf-8")
    assert cp.restore(ref1)
    assert a.read_text("utf-8") == "v1" and not b.exists()
    assert (tmp_path / "keep.ignored").read_text("utf-8") == "ignored user data"
    assert (tmp_path / "artifact.bin").read_bytes() == b"\0" * 1024
    assert cp.list()[0]["label"] == "回退前自动快照"
    assert cp.restore(cp.list()[0]["ref"])
    assert a.read_text("utf-8") == "unsnapshotted" and b.read_text("utf-8") == "new"
    assert git(tmp_path, "rev-parse", "HEAD") == real_head
    assert (tmp_path / ".git" / "index").read_bytes() == real_index


def test_source_checkpoint_refuses_ignored_collision(tmp_path, git):
    from ruocun.session.checkpoint import createCheckpointer

    item = tmp_path / "owned.txt"
    item.write_text("target file", encoding="utf-8")
    cp = createCheckpointer(tmp_path, enabled=True)
    target = cp.snapshot("target")
    assert target
    item.unlink()
    assert cp.snapshot("without file")
    item.mkdir()
    protected = item / "generated.bin"
    protected.write_bytes(b"preserve ignored bytes")
    assert not cp.restore(target)
    assert protected.read_bytes() == b"preserve ignored bytes"


def test_source_checkpoint_slow_git_stops_without_replaying(tmp_path, git, monkeypatch):
    from ruocun.session.checkpoint import createCheckpointer

    cp = createCheckpointer(tmp_path, enabled=True, environ={**os.environ, "RUOCUN_CHECKPOINT_TIMEOUT_MS": "300"})
    assert cp.enabled
    real_run = subprocess.run
    attempts = 0

    def stall_add(argv, *args, **kwargs):
        nonlocal attempts
        if "--git-dir" in argv and "add" in argv:
            attempts += 1
            argv = [sys.executable, "-I", "-c", "import time; time.sleep(5)"]
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", stall_add)
    start = monotonic()
    assert cp.snapshot("slow Git") is None and monotonic() - start < 4
    assert cp.snapshot("do not replay") is None and attempts == 1
