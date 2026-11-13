"""REC-05 real Windows process cuts using the existing Conversation journal."""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows product storage")

_BOOT = "import runpy, sys; sys.path.insert(0, sys.argv[1]); sys.argv = sys.argv[2:]; runpy.run_path(sys.argv[0], run_name='__main__')"


@pytest.mark.parametrize(("cut", "tool", "state", "changed"), [
    ("before-intent", "Write", "not_started", False),
    ("after-intent", "Edit", "outcome_unknown", False),
    ("after-effect", "Write", "outcome_unknown", True),
    ("before-result", "Edit", "outcome_unknown", True),
    ("after-result", "Write", "result_committed", True),
])
def test_real_file_operation_recovers_three_times(tmp_path, cut, tool, state, changed):
    fixtures = Path(__file__).parent / "fixtures"
    child_script = fixtures / "n2-editjournal/recovery_child.py"
    archive = fixtures / "sqlite-dll-win-x64-3540100.zip"
    package_root = Path(ruocun.__file__).resolve().parents[1]
    args = [sys.executable, "-I", "-X", "utf8", "-c", _BOOT, str(package_root),
            str(child_script), str(tmp_path), str(archive), cut, tool]
    (tmp_path / "workspace").mkdir()
    target = tmp_path / "workspace/target.txt"
    target.write_bytes(b"before\n")
    ready = tmp_path / "ready"
    stdout, stderr = tmp_path / "cut.stdout", tmp_path / "cut.stderr"
    with stdout.open("wb") as out, stderr.open("wb") as err:
        child = subprocess.Popen([*args, "0"], stdout=out, stderr=err,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            deadline = time.monotonic() + 15
            while not ready.is_file() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            assert ready.is_file(), stderr.read_text(encoding="utf-8")
            assert ready.read_text(encoding="utf-8") == cut
            assert child.poll() is None, "child must be alive at the measured cut"
        finally:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=10)
    assert child.returncode != 0

    reopened = []
    for reopen_number in range(1, 4):
        result = subprocess.run([*args, str(reopen_number)], capture_output=True, text=True, encoding="utf-8",
                                timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode == 0, result.stderr + result.stdout
        observed = json.loads(result.stdout)
        checked = "reopened"
        if reopen_number == 3:
            checked = {"before-intent": "failed-intent-before-dispatch",
                       "after-result": "cached-foreground-result"}.get(cut, checked)
        assert observed == {"cut": cut, "state": state, "blocked": state == "outcome_unknown",
                            "pairs": int(state != "outcome_unknown"), "changed": changed, "checked": checked}
        assert target.read_bytes() == (b"after\n" if changed else b"before\n")
        for log in ("dispatch.log", "effects.log"):
            path = tmp_path / log
            actual = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
            assert actual == ([tool] if changed else [])
        reopened.append(observed)
    print(json.dumps({"cut": cut, "tool": tool, "ownedExit": child.returncode, "reopened": reopened}))
