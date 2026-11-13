"""Real 15-second installed-driver deadline against one owned leaf process."""
import json
import subprocess
import sys
import time
from pathlib import Path

from ruocun_acceptance import driver

output = Path.cwd() / "deadline"
output.mkdir(exist_ok=False)
real_popen = subprocess.Popen
created = []


def capture(*args, **kwargs):
    child = real_popen(*args, **kwargs)
    created.append(child)
    return child


started = time.monotonic()
try:
    subprocess.Popen = capture
    outcome = driver.execute(driver.Case("CONTROLLED.deadline", ("-c", "import time; time.sleep(30)"),
                                        0, "", "D21/Task03 actual driver deadline; owned leaf process"),
                             Path(sys.executable), output)
    elapsed = time.monotonic() - started
    result = {"case": outcome, "elapsed_seconds": elapsed,
              "observed_child_exit": created[0].poll(), "child_exited": created[0].poll() is not None,
              "delivery": "real communicate timeout after 15 seconds; not exception injection"}
    assert outcome["status"] == "failed" and outcome["reason"] == "15 second command deadline"
    assert 14 < elapsed < 25 and result["child_exited"]
    (Path(__file__).parent / "deadline.json").write_text(json.dumps(result, indent=2) + "\n")
finally:
    subprocess.Popen = real_popen
    for child in created:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=10)
print("real deadline failed nonzero case and owned leaf process kill/join verified")
