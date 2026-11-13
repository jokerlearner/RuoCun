"""Independent installed CLI/driver checks with synthetic state and real subprocesses."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from ruocun_acceptance.environment import isolated_env

OUT = Path.cwd()
assert "Firstcode" not in str(OUT)
PRODUCT = OUT / "product/Scripts/python.exe"
CONSOLE = OUT / "product/Scripts/ruocun.exe"
REPORT = Path(__file__).parent / "boundaries.json"
receipts = []


def run(label, argv, expected):
    case_root = OUT / "checks" / label
    case_root.mkdir(parents=True, exist_ok=False)
    result = subprocess.run([str(p) for p in argv], cwd=case_root,
                            env=isolated_env(case_root, Path(argv[0])), capture_output=True, timeout=45)
    for n, data in (("stdout", result.stdout), ("stderr", result.stderr)):
        (case_root / (n + ".bin")).write_bytes(data)
    receipts.append({"label": label, "argv": [str(p) for p in argv], "cwd": str(case_root),
                     "expected_exit": expected, "exit": result.returncode,
                     "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                     "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
                     "cleanup": {"command_joined": True}})
    REPORT.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert result.returncode == expected, label
    return result


def acceptance(label, suite, expected, *extra):
    output = OUT / "outputs" / label
    result = run(label, [sys.executable, "-I", "-X", "utf8", "-m", "ruocun_acceptance", suite,
                         "--python", PRODUCT, "--output", output, *extra], expected)
    return json.loads(result.stdout)


version = run("console-priority", [CONSOLE, "--help", "--unknown-synthetic", "-v"], 0)
assert version.stdout.replace(b"\r\n", b"\n") == b"RuoCun v0.1.0.dev0\n" and not version.stderr
for flag, label in (("--help", "long-help"), ("-h", "short-help")):
    help_result = run(label, [CONSOLE, flag], 0)
    assert "用法：ruocun [选项] [提示词]" in help_result.stdout.decode("utf-8")
passed = acceptance("offline", "offline", 0)
assert len(passed["cases"]) == 4 and all(c["status"] == "passed" for c in passed["cases"])
for suite in ("oracle", "runtime", "protocol", "live", "terminal", "install"):
    report = acceptance(suite, suite, 1)
    assert len(report["cases"]) == 1 and report["cases"][0]["status"] == "not-run"
    assert report["cases"][0]["reason"]
empty = acceptance("empty", "offline", 1, "--case", "unknown-synthetic")
assert empty["cases"][0]["status"] == "not-run"
run("unknown-suite", [sys.executable, "-I", "-X", "utf8", "-m", "ruocun_acceptance", "unknown"], 2)
missing = run("missing-python", [sys.executable, "-I", "-X", "utf8", "-m", "ruocun_acceptance", "offline",
              "--python", OUT / "absent.exe", "--output", OUT / "outputs/missing-python"], 1)
assert all(c["status"] == "failed" for c in json.loads(missing.stdout)["cases"])
resource = OUT / "product/Lib/site-packages/ruocun/resources/help.zh-CN.txt"
original = resource.read_bytes()
backup = resource.with_suffix(".review-missing")
assert not backup.exists()
resource.rename(backup)
try:
    run("resource-missing-version", [CONSOLE, "--version"], 0)
    run("resource-missing-help", [CONSOLE, "--help"], 70)
    broken = acceptance("resource-missing-offline", "offline", 1)
    states = {c["id"]: c["status"] for c in broken["cases"]}
    assert states == {"ENT-01.version": "passed", "ENT-01.help": "failed",
                      "ENT-01.resource": "failed", "ENT-01.unimplemented": "passed"}
finally:
    backup.rename(resource)
    assert resource.read_bytes() == original
restored = acceptance("restored-offline", "offline", 0)
assert all(c["status"] == "passed" for c in restored["cases"])
print("external console/version/help, offline4, six not-run suites, selection/errors and restored resource verified")
