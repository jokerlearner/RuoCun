"""冻结 exec_shell.test.ts 前台断言；Windows 命令仅适配方言。"""

import asyncio
import base64
import os
import threading
import time
from pathlib import Path

import pytest

from ruocun.tools.exec_shell import execShellTool
from ruocun.tools.types import ToolContext


def windows_script(script: str) -> str:
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    engine = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    return f'"{engine}" -NoProfile -NonInteractive -EncodedCommand {encoded}'


def test_foreground_stdout_and_exit(tmp_path: Path) -> None:
    out = asyncio.run(execShellTool.handler(
        {"command": "echo fg-hello"}, ToolContext(workspaceRoot=str(tmp_path))
    ))
    assert "fg-hello" in out
    assert "[exit 0," in out


def run(command: str, path: Path, **kwargs: object) -> str:
    return asyncio.run(execShellTool.handler(
        {"command": command}, ToolContext(workspaceRoot=str(path), **kwargs)  # type: ignore[arg-type]
    ))


def test_nonzero_exit_clears_pending_writes(tmp_path: Path) -> None:
    pending = {"/app/compress.rs"}
    out = run("exit 3", tmp_path, pendingUnverifiedWrites=pending)
    assert "[exit 3," in out
    assert not pending


@pytest.mark.parametrize("seconds", [2, 15])
def test_sleep_guard_preserves_pending_writes(tmp_path: Path, seconds: int) -> None:
    pending = {"/app/compress.rs"}
    out = run(f"sleep {seconds}", tmp_path, pendingUnverifiedWrites=pending)
    assert "不要用 sleep" in out
    assert "[exit" not in out
    assert pending


def test_short_sleep_and_compound_are_not_blocked(tmp_path: Path) -> None:
    assert "不要用 sleep" not in run("sleep 1", tmp_path)
    compound = windows_script("Start-Sleep -Seconds 0.1; echo done") if os.name == "nt" else "sleep 0.1 && echo done"
    assert "done" in run(compound, tmp_path)


def test_python_inline_small_file_is_blocked_without_backups(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("hello", encoding="utf-8")
    pending = {"notes.txt"}
    out = run("python3 -c \"open('notes.txt')\"", tmp_path, pendingUnverifiedWrites=pending)
    assert "不用写 python 脚本" in out
    assert "notes.txt" in out
    assert "[exit" not in out
    assert "[自动备份]" not in out
    assert pending


def test_python_inline_streak_nudges_once_and_resets(tmp_path: Path) -> None:
    run("echo reset-streak", tmp_path)
    for index in range(4):
        out = run(f'python3 -c "print({index})"', tmp_path)
        assert ("[提示]" in out) == (index == 2)
        if index == 2:
            assert "Grep" in out
    run("echo reset-streak", tmp_path)
    assert "[提示]" not in run('python -c "print(1)"', tmp_path)


@pytest.mark.parametrize(("command", "headless", "done"), [
    ("echo 'malloc(): corrupted top size'", True, False),
    ("exit 139", True, False), ("exit 137", True, True),
    ("echo ok", True, True), ("echo 'Segmentation fault (core dumped)'", False, True),
])
def test_crash_rearms_plan_only_in_headless(
    tmp_path: Path, command: str, headless: bool, done: bool,
) -> None:
    gate = {"done": True}
    run(command, tmp_path, headless=headless, todoWriteRequired=gate)
    assert gate["done"] is done


def test_crash_without_gate_still_returns(tmp_path: Path) -> None:
    assert "[exit" in run("echo 'stack smashing detected'", tmp_path, headless=True)


@pytest.mark.parametrize("name", ["main.db", "app.sqlite3", "dump.rdb", "log.aof",
                                  "vault.kdbx", "table.dbf", "state.db3"])
def test_database_backup_before_execution_keeps_first_copy(tmp_path: Path, name: str) -> None:
    db = tmp_path / name
    db.write_text("v1", encoding="utf-8")
    wal = tmp_path / (name + "-wal")
    wal.write_text("wal-content", encoding="utf-8")
    previous_backup = tmp_path / (name + ".dao-backup")
    previous_backup.write_text("old backup", encoding="utf-8")
    command = f"echo '{db}'"
    out = run(command, tmp_path)
    assert "[自动备份]" in out
    assert name in out
    assert ".ruocun-backup" in out
    assert Path(str(db) + ".ruocun-backup").read_text(encoding="utf-8") == "v1"
    assert previous_backup.read_text(encoding="utf-8") == "old backup"
    assert Path(str(wal) + ".ruocun-backup").read_text(encoding="utf-8") == "wal-content"
    db.write_text("v2-corrupted-by-something-else", encoding="utf-8")
    assert "[自动备份]" not in run(command, tmp_path)
    assert Path(str(db) + ".ruocun-backup").read_text(encoding="utf-8") == "v1"


def test_database_reference_inside_python_inline_is_backed_up(tmp_path: Path) -> None:
    (tmp_path / "main.db").write_text("content", encoding="utf-8")
    out = run('python3 -c "import sqlite3; sqlite3.connect(\'main.db\').execute(\'SELECT 1\')"', tmp_path)
    assert "[自动备份]" in out
    assert (tmp_path / "main.db.ruocun-backup").read_text(encoding="utf-8") == "content"


def test_no_database_reference_has_no_backup_notice(tmp_path: Path) -> None:
    assert "[自动备份]" not in run("echo no-db-here", tmp_path)


def test_background_is_rejected_without_execution(tmp_path: Path) -> None:
    # ADR-0011明确差异，来源后台/转后台用例不宣称通过。
    pending = {"changed.py"}
    out = asyncio.run(execShellTool.handler(
        {"command": "echo bg", "background": True},
        ToolContext(workspaceRoot=str(tmp_path), pendingUnverifiedWrites=pending),
    ))
    assert "不支持 background=true" in out
    assert "命令未执行" in out
    assert pending


def test_declares_required_exec_tool() -> None:
    assert execShellTool.name == "Bash"
    assert execShellTool.capability == "exec"
    assert execShellTool.approval == "required"


def test_abort_foreground_returns_promptly(tmp_path: Path) -> None:
    stop = threading.Event()
    command = windows_script("Start-Sleep -Seconds 5") if os.name == "nt" else "sh -c 'sleep 5'"
    timer = threading.Timer(.1, stop.set)
    timer.start()
    start = time.monotonic()
    try:
        out = run(command, tmp_path, signal=stop)
    finally:
        timer.join()
    assert "[已中断," in out
    assert time.monotonic() - start < 3
