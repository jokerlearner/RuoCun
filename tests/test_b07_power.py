"""Frozen wakelock.ts routes and the approved W5 absence of Windows inhibition."""

from __future__ import annotations

import os
import subprocess
import sys
import time


def test_windows_power_capability_is_explicit_and_never_spawns():
    from ruocun.tui.wakelock import acquireWakeLock, getWakeLockCapability

    def forbidden(*args, **kwargs):
        raise AssertionError("Windows must not acquire a native power lock")
    lock = acquireWakeLock(platform="win32", environ={}, spawn=forbidden)
    assert lock.status == "unsupported" and "Windows" in lock.reason and "无防" in lock.reason
    assert getWakeLockCapability(platform="win32")["supported"] is False
    lock()
    lock()
    assert lock.status == "unsupported"


def test_source_posix_backends_alias_disable_missing_backend_and_release_once():
    from ruocun.tui.wakelock import acquireWakeLock

    calls, processes = [], []
    class Process:
        pid = 123
        alive, terminated, waits = True, 0, 0
        def poll(self):
            return None if self.alive else 0
        def terminate(self):
            self.alive = False
            self.terminated += 1
        def kill(self):
            raise AssertionError("normal release did not need forced kill")
        def wait(self, timeout=None):
            assert not self.alive
            self.waits += 1
            return 0
    def spawn(argv, **kwargs):
        calls.append((tuple(argv), kwargs))
        process = Process()
        processes.append(process)
        return process
    mac = acquireWakeLock(platform="darwin", environ={"DAO_NO_WAKELOCK": "1", "RUOCUN_NO_WAKELOCK": ""}, spawn=spawn)
    linux = acquireWakeLock(platform="linux", environ={"RUOCUN_NO_WAKELOCK": "0"}, spawn=spawn)
    assert calls[0][0] == ("caffeinate", "-i")
    assert calls[1][0] == ("systemd-inhibit", "--what=idle:sleep", "--why=ruocun 长任务", "--mode=block", "sleep", "infinity")
    assert mac.status == linux.status == "requested"
    mac()
    mac()
    linux()
    assert mac.status == linux.status == "released"
    assert [(process.terminated, process.waits) for process in processes] == [(1, 1), (1, 1)]
    assert len(calls) == 2
    assert acquireWakeLock(platform="darwin", environ={"RUOCUN_NO_WAKELOCK": "1"}, spawn=spawn).status == "disabled"
    assert len(calls) == 2
    def missing(*args, **kwargs):
        raise FileNotFoundError("synthetic missing backend")
    assert acquireWakeLock(platform="darwin", environ={}, spawn=missing).status == "unavailable"


def test_actual_synthetic_power_process_release_reaps_before_return(tmp_path):
    from ruocun.tui.wakelock import acquireWakeLock

    started, processes = tmp_path / "started", []
    def spawn(argv, **kwargs):
        program = f"import time;from pathlib import Path;Path({str(started)!r}).write_text('synthetic');time.sleep(60)"
        process = subprocess.Popen([sys._base_executable, "-I", "-c", program], env=dict(os.environ),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)
        processes.append(process)
        return process
    lock = acquireWakeLock(platform="darwin", environ={}, spawn=spawn)
    try:
        deadline = time.monotonic() + 3
        while not started.exists():
            assert time.monotonic() < deadline
            time.sleep(.01)
        assert processes[0].poll() is None
        lock()
        assert lock.status == "released" and processes[0].poll() is not None
        lock()
    finally:
        lock()
