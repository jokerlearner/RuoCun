"""Windows语言/Job适配所必需的最小确认，不计为DAO来源测试。"""

import asyncio
import base64
import ctypes as C
import json
import os
import sys
import threading
import time
from ctypes import wintypes as W
from pathlib import Path
from typing import Any

import pytest

from ruocun.tools.exec_shell import cleanupDbBackups, execShellTool
from ruocun.tools.types import ToolContext

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Job最小适配确认")

_WORKER = '''import json, os, subprocess, sys, time
from pathlib import Path
root = Path(sys.argv[1])
if len(sys.argv) > 3:
    print("grandchild-alive", flush=True)
    count = 0
    while True:
        (root / "ticks.txt").write_text(str(count), encoding="ascii")
        count += 1
        time.sleep(.02)
else:
    child = subprocess.Popen([sys.executable, "-I", __file__, str(root), sys.argv[2], "grand"],
                             creationflags=subprocess.CREATE_NO_WINDOW)
    (root / "owned.json").write_text(json.dumps([os.getpid(), child.pid]), encoding="utf-8")
    if sys.argv[2] == "orphan":
        print("shell-done", flush=True)
    else:
        time.sleep(60)
'''


def _kernel() -> Any:
    k = C.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    k.WaitForSingleObject.restype = W.DWORD
    k.CloseHandle.argtypes = [W.HANDLE]
    return k


def _command(tmp_path: Path, mode: str) -> str:
    script = tmp_path / "owned_worker.py"
    script.write_text(_WORKER, encoding="utf-8")
    payload = f"& '{sys.executable}' '-I' '{script}' '{tmp_path}' '{mode}'"
    encoded = base64.b64encode(payload.encode("utf-16-le")).decode("ascii")
    engine = Path(os.environ.get("SYSTEMROOT", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    return f'"{engine}" -NoProfile -NonInteractive -EncodedCommand {encoded}'


def test_cancel_returns_only_after_real_child_and_grandchild_exit(tmp_path: Path) -> None:
    async def scenario() -> None:
        stop = threading.Event()
        owner_thread = threading.get_ident()
        chunks = []
        def output(stream, text):
            assert threading.get_ident() == owner_thread
            chunks.append((stream, text))
        task = asyncio.create_task(execShellTool.handler(
            {"command": _command(tmp_path, "cancel")},
            ToolContext(workspaceRoot=str(tmp_path), signal=stop, onShellOutput=output),
        ))
        handles: list[Any] = []
        k = _kernel()
        try:
            deadline = time.monotonic() + 10
            while not (tmp_path / "owned.json").exists():
                assert not task.done(), "Shell提前结束，未观察到自有子孙"
                assert time.monotonic() < deadline
                await asyncio.sleep(.02)
            pids = json.loads((tmp_path / "owned.json").read_text(encoding="utf-8"))
            for pid in pids:
                handle = k.OpenProcess(0x100000 | 0x1000, False, pid)
                assert handle, "只能查询本测试刚创建的进程"
                handles.append(handle)
                assert k.WaitForSingleObject(handle, 0) == 258
            while not (tmp_path / "ticks.txt").exists():
                assert time.monotonic() < deadline
                await asyncio.sleep(.02)
            stop.set()
            out = await task
            assert "[已中断," in out
            states = [k.WaitForSingleObject(handle, 0) for handle in handles]
            assert states == [0, 0]
            final_bytes = (tmp_path / "ticks.txt").read_bytes()
            final_count = len(chunks)
            await asyncio.sleep(.1)
            assert (tmp_path / "ticks.txt").read_bytes() == final_bytes
            assert len(chunks) == final_count
            assert "实时输出不可用" not in out
            (tmp_path / "resource-receipt.json").write_text(json.dumps({
                "owned_pids": pids, "wait_states_after_handler": states,
                "owned_processes_still_running": [],
            }), encoding="utf-8")
        finally:
            stop.set()
            if not task.done():
                await task
            for handle in handles:
                k.CloseHandle(handle)

    asyncio.run(scenario())


def test_parent_exit_does_not_wait_for_inherited_pipe(tmp_path: Path) -> None:
    start = time.monotonic()
    out = asyncio.run(execShellTool.handler(
        {"command": _command(tmp_path, "orphan")}, ToolContext(workspaceRoot=str(tmp_path))
    ))
    assert "shell-done" in out
    assert "[exit 0," in out
    assert time.monotonic() - start < 3
    k = _kernel()
    pids = json.loads((tmp_path / "owned.json").read_text(encoding="utf-8"))
    for pid in pids:
        handle = k.OpenProcess(0x100000 | 0x1000, False, pid)
        if handle:
            try:
                assert k.WaitForSingleObject(handle, 0) == 0
            finally:
                k.CloseHandle(handle)
        else:
            assert C.get_last_error() == 87


def test_cleanup_retains_preexisting_and_replaced_backups(tmp_path: Path) -> None:
    # 首版对来源扫删清理的已登记差异；路径不能证明当前文件归属。
    backup = tmp_path / "main.db.ruocun-backup"
    backup.write_text("user-backup", encoding="utf-8")
    assert asyncio.run(cleanupDbBackups(str(tmp_path))) == 0
    assert backup.read_text(encoding="utf-8") == "user-backup"
