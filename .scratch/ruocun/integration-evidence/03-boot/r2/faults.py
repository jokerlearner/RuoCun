"""Independent fault delivery against a newly installed wheel; real owned children.

This is controlled Python exception delivery, not actual OS corruption or Ctrl+C.
"""
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

from ruocun_acceptance import driver

BASE = Path.cwd() / "r2-faults"
BASE.mkdir(exist_ok=False)
HERE = Path(__file__).parent
REAL_POPEN = subprocess.Popen
OWNED = []
MODE = ""
results = {}


class FaultChild:
    def __init__(self, argv, **kwargs):
        actual = argv if MODE == "confirmation-interrupt" else [
            argv[0], "-I", "-X", "utf8", "-c", "import time; time.sleep(30)"]
        self.real = REAL_POPEN(actual, **kwargs)
        self.actual_argv = actual
        self.wait_interrupted = False
        OWNED.append(self)

    def __getattr__(self, name):
        return getattr(self.real, name)

    def communicate(self, *args, **kwargs):
        if MODE in ("pipe-oserror", "unconfirmed"):
            raise OSError(5, "controlled synthetic wait boundary")
        if MODE == "cancel":
            raise KeyboardInterrupt
        return self.real.communicate(*args, **kwargs)

    def wait(self, *args, **kwargs):
        if MODE == "unconfirmed":
            raise OSError(5, "controlled wait cannot observe")
        if MODE == "confirmation-interrupt" and not self.wait_interrupted:
            self.wait_interrupted = True
            raise KeyboardInterrupt
        return self.real.wait(*args, **kwargs)

    def poll(self):
        if MODE == "unconfirmed":
            raise OSError(5, "controlled poll cannot observe")
        return self.real.poll()


def reap(children):
    for child in children:
        if child.real.poll() is None:
            child.real.kill()
        child.real.wait(timeout=10)
        child.real.stdout.close()
        child.real.stderr.close()


old_argv = sys.argv
try:
    subprocess.Popen = FaultChild
    for MODE in ("pipe-oserror", "cancel", "unconfirmed", "confirmation-interrupt"):
        before = len(OWNED)
        try:
            if MODE == "pipe-oserror":
                target = BASE / MODE
                target.mkdir()
                outcome = driver.execute(driver.Case("CONTROLLED.pipe", ("-c", "import time; time.sleep(30)"),
                                                     0, "", "independent Task03 failed-wait cleanup requirement"),
                                         Path(sys.executable), target)
                child = OWNED[-1].real
                observed_running = child.poll() is None
                results[MODE] = {"case": outcome, "running_at_execute_return": observed_running}
                assert not observed_running
                assert outcome["status"] == "failed" and outcome["logical_exit"] == 1
                assert outcome["exit"] == child.returncode and outcome["exit"] is not None
                assert outcome["cleanup"]["command_joined"] and outcome["cleanup"]["streams_closed"]
                assert child.stdout.closed and child.stderr.closed
            else:
                output = BASE / MODE
                sys.argv = ["ruocun_acceptance", "offline", "--output", str(output)]
                with contextlib.redirect_stdout(io.StringIO()):
                    code = driver.main()
                report = json.loads((output / "summary.json").read_text(encoding="utf-8"))
                first = report["cases"][0]
                results[MODE] = {"driver_exit": code, "report": report}
                assert len(OWNED) - before == 1
                assert all(c["status"] == "not-run" for c in report["cases"][1:])
                assert report["status"] != "passed"
                if MODE == "unconfirmed":
                    assert code == 1 and first["status"] == report["status"] == "cleanup-failed"
                    assert first["exit"] is None and first["cleanup"]["command_joined"] is False
                    assert report["cleanup"]["commands_joined"] is False
                    assert {x["operation"] for x in first["cleanup"]["errors"]} >= {"wait", "poll"}
                else:
                    child = OWNED[-1].real
                    assert code == first["logical_exit"] == 130 and first["status"] == "cancelled"
                    assert first["exit"] == child.poll() and first["exit"] is not None
                    assert first["cleanup"]["command_joined"] and first["cleanup"]["streams_closed"]
                    if MODE == "confirmation-interrupt":
                        assert first["exit"] == 0 and first["output_complete"] is True
                        assert any(e["operation"] == "wait" and e["exception"] == "KeyboardInterrupt"
                                   for e in first["cleanup"]["errors"])
        finally:
            created = OWNED[before:]
            reap(created)
            results.setdefault(MODE, {})["reviewer_cleanup"] = [
                {"pid": p.real.pid, "actual_argv": p.actual_argv,
                 "real_exit": p.real.returncode, "streams_closed": p.real.stdout.closed and p.real.stderr.closed}
                for p in created]
            (HERE / "faults.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
finally:
    subprocess.Popen = REAL_POPEN
    sys.argv = old_argv
    reap(OWNED)
print("four independent real-child failure/cancellation/observation-boundary checks passed; owned children reaped")
