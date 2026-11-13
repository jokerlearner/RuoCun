"""Controlled exception delivery at the installed driver seam; actual owned children.

The injected delivery is not a real terminal Ctrl+C/OS pipe-error claim.
It checks cleanup accounting by observing the real Popen child after each return.
"""
import contextlib
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

from ruocun_acceptance import driver

OUT = Path.cwd() / "faults"
OUT.mkdir(exist_ok=False)
EVIDENCE = Path(__file__).parent
real_popen = subprocess.Popen
created = []
fault = None


class InterruptOnce:
    def __init__(self, *args, **kwargs):
        self.real = real_popen(*args, **kwargs)
        self.used = False
        created.append(self.real)

    def communicate(self, *args, **kwargs):
        if not self.used:
            self.used = True
            raise fault("controlled driver wait boundary")
        return self.real.communicate(*args, **kwargs)

    def kill(self):
        return self.real.kill()

    @property
    def returncode(self):
        return self.real.returncode


case = driver.Case("CONTROLLED.slow", ("-c", "import time; time.sleep(30)"), 0, "",
                   "independent Task03 cancellation/cleanup requirement; synthetic owned process")
old_cases, old_argv = driver.offline_cases, sys.argv
results = {}
try:
    subprocess.Popen = InterruptOnce
    fault = KeyboardInterrupt
    driver.offline_cases = lambda version: [case, driver.Case("CONTROLLED.after", ("-m", "ruocun", "-v"), 0,
                                                              "RuoCun", "next case must not run after cancellation")]
    sys.argv = ["ruocun_acceptance", "offline", "--output", str(OUT / "cancel")]
    with contextlib.redirect_stdout(io.StringIO()):
        code = driver.main()
    cancel = json.loads((OUT / "cancel/summary.json").read_text(encoding="utf-8"))
    assert code != 0
    assert [c["status"] for c in cancel["cases"]] == ["cancelled", "not-run"]
    assert created[-1].poll() is not None
    results["keyboard_interrupt"] = {"delivery": "controlled Python exception; real child kill/join",
                                     "driver_exit": code, "report": cancel,
                                     "observed_child_exit": created[-1].returncode,
                                     "no_live_child": True}
    fault = OSError
    outcome = driver.execute(case, Path(sys.executable), OUT)
    running = created[-1].poll() is None
    results["pipe_oserror"] = {"delivery": "controlled OSError from communicate after real spawn",
                               "report": outcome, "child_still_running_when_execute_returned": running,
                               "candidate_claimed_command_joined": outcome["cleanup"]["command_joined"]}
finally:
    subprocess.Popen = real_popen
    driver.offline_cases, sys.argv = old_cases, old_argv
    for child in created:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)
    results["reviewer_cleanup"] = {"owned_children_exited": all(p.poll() is not None for p in created),
                                   "actual_exit_codes": [p.returncode for p in created]}
    results["installed_driver"] = {"path": driver.__file__, "sha256": hashlib.sha256(Path(driver.__file__).read_bytes()).hexdigest()}
    (EVIDENCE / "cancellation.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
assert not results["pipe_oserror"]["child_still_running_when_execute_returned"], "driver claimed joined while real child still running after communicate OSError"
print("cancellation and wait-error cleanup verified")
