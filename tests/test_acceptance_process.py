"""Owned real child processes with controlled failures at the subprocess boundary.

Injected Python API exceptions are not claims of real Windows kernel failures.
Each test independently reaps only the processes it created, including on red.
"""

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

from ruocun_acceptance import driver


def test_pipe_failure_joins_real_owned_child_before_reporting(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    owned = []
    outcome = None
    observed_running = None

    def start(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        owned.append(child)

        def broken_communicate(*_args, **_kwargs):
            raise OSError(5, "controlled communicate boundary")

        child.communicate = broken_communicate
        return child

    monkeypatch.setattr(subprocess, "Popen", start)
    case = driver.Case(
        "CONTROLLED.pipe", ("-c", "import time; time.sleep(30)"), 0, "",
        "Task03 owned-process cleanup requirement; controlled communicate failure",
    )
    try:
        outcome = driver.execute(case, Path(sys.executable), tmp_path)
        child = owned[0]
        observed_running = child.poll() is None
        assert not observed_running, "execute returned with its real owned child still running"
        assert outcome["status"] == "failed"
        assert outcome["exit"] == child.returncode
        assert outcome["cleanup"]["command_joined"] is True
        assert child.stdout.closed and child.stderr.closed
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
            child.stdout.close()
            child.stderr.close()
        (tmp_path / "fault-receipt.json").write_text(json.dumps({
            "delivery": "controlled communicate OSError after real Popen",
            "report": outcome, "running_when_execute_returned": observed_running,
            "test_cleanup": [{"pid": child.pid, "exit": child.returncode} for child in owned],
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cancellation_reports_actual_child_exit_separately(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    owned = []
    observed = {}

    def start(argv, **kwargs):
        # Deliberately replace only the OS subprocess boundary with a real slow
        # Python child. This does not claim that version/help themselves block.
        actual = [argv[0], "-I", "-X", "utf8", "-c", "import time; time.sleep(30)"]
        child = real_popen(actual, **kwargs)
        owned.append(child)
        communicate = child.communicate
        interrupted_once = False

        def interrupted(*_args, **_kwargs):
            nonlocal interrupted_once
            if not interrupted_once:
                interrupted_once = True
                raise KeyboardInterrupt
            return communicate(*_args, **_kwargs)

        child.communicate = interrupted
        return child

    monkeypatch.setattr(subprocess, "Popen", start)
    monkeypatch.setattr(sys, "argv", ["ruocun_acceptance", "offline", "--output", str(tmp_path / "out")])
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = driver.main()
        report = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
        observed.update(driver_exit=code, report=report)
        child = owned[0]
        assert child.poll() is not None
        assert len(owned) == 1
        assert [case["status"] for case in report["cases"]] == [
            "cancelled", "not-run", "not-run", "not-run",
        ]
        assert report["cases"][0]["exit"] == child.returncode
        assert report["cases"][0]["logical_exit"] == 130
        assert code == 130
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
            child.stdout.close()
            child.stderr.close()
        (tmp_path / "fault-receipt.json").write_text(json.dumps({
            "delivery": "controlled KeyboardInterrupt before communicate; real owned child",
            **observed, "test_cleanup": [{"pid": child.pid, "exit": child.returncode} for child in owned],
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def test_unconfirmed_cleanup_is_nonzero_and_does_not_claim_joined(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    owned = []
    observed = {}

    class UnobservableChild:
        def __init__(self, argv, **kwargs):
            actual = [argv[0], "-I", "-X", "utf8", "-c", "import time; time.sleep(30)"]
            self.real = real_popen(actual, **kwargs)
            owned.append(self.real)

        def __getattr__(self, name):
            return getattr(self.real, name)

        def communicate(self, *args, **kwargs):
            raise OSError(5, "controlled communicate boundary")

        def wait(self, *args, **kwargs):
            raise OSError(5, "controlled wait observation failure")

        def poll(self):
            raise OSError(5, "controlled poll observation failure")

    monkeypatch.setattr(subprocess, "Popen", UnobservableChild)
    monkeypatch.setattr(sys, "argv", ["ruocun_acceptance", "offline", "--output", str(tmp_path / "out")])
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = driver.main()
        report = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
        observed.update(driver_exit=code, report=report)
        assert code != 0
        case = report["cases"][0]
        assert case["status"] == "cleanup-failed"
        assert case["exit"] is None
        assert case["process"]["pid"] == owned[0].pid
        assert case["cleanup"]["command_joined"] is False
        assert {item["operation"] for item in case["cleanup"]["errors"]} >= {"poll", "wait"}
        assert report["cleanup"]["commands_joined"] is False
        assert len(owned) == 1
        assert all(item["status"] == "not-run" for item in report["cases"][1:])
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
            child.stdout.close()
            child.stderr.close()
        (tmp_path / "fault-receipt.json").write_text(json.dumps({
            "delivery": "controlled communicate/wait/poll API errors; actual kernel stop not denied",
            **observed, "test_cleanup": [{"pid": child.pid, "exit": child.returncode} for child in owned],
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def test_interrupt_during_exit_confirmation_is_not_reported_as_success(tmp_path, monkeypatch):
    real_popen = subprocess.Popen
    owned = []
    observed = {}

    def start(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        owned.append(child)
        communicate, wait = child.communicate, child.wait
        interrupted_once = False

        def interrupted_wait(*args, **kwargs):
            nonlocal interrupted_once
            if not interrupted_once:
                interrupted_once = True
                raise KeyboardInterrupt
            return wait(*args, **kwargs)

        def completed_communicate(*args, **kwargs):
            result = communicate(*args, **kwargs)
            child.wait = interrupted_wait
            return result

        child.communicate = completed_communicate
        return child

    monkeypatch.setattr(subprocess, "Popen", start)
    monkeypatch.setattr(sys, "argv", ["ruocun_acceptance", "offline", "--output", str(tmp_path / "out")])
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            code = driver.main()
        report = json.loads((tmp_path / "out/summary.json").read_text(encoding="utf-8"))
        observed.update(driver_exit=code, report=report)
        assert code == 130
        assert report["cases"][0]["status"] == "cancelled"
        assert report["cases"][0]["exit"] == 0
        assert report["cases"][0]["cleanup"]["command_joined"] is True
        assert len(owned) == 1
    finally:
        for child in owned:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
            child.stdout.close()
            child.stderr.close()
        (tmp_path / "fault-receipt.json").write_text(json.dumps({
            "delivery": "controlled wait KeyboardInterrupt after real CLI completion",
            **observed, "test_cleanup": [{"pid": child.pid, "exit": child.returncode} for child in owned],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
