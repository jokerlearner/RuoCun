"""Run scoped checks with synthetic state and explicit source imports."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent


def main() -> int:
    label, mode, *arguments = sys.argv[1:]
    evidence = TASK / "evidence" / label
    evidence.mkdir(parents=True, exist_ok=False)
    state = evidence / "state"
    for name in ("home", "appdata", "localappdata", "tmp"):
        (state / name).mkdir(parents=True, exist_ok=True)
    env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({
        "HOME": str(state / "home"), "USERPROFILE": str(state / "home"),
        "APPDATA": str(state / "appdata"), "LOCALAPPDATA": str(state / "localappdata"),
        "TEMP": str(state / "tmp"), "TMP": str(state / "tmp"),
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), r"C:\Windows\System32")),
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
    })
    if mode == "pytest":
        code = (
            "import sys; "
            f"sys.path[:0] = {[str(ROOT / 'src'), str(ROOT / 'tests' / 'support')]!r}; "
            "import pytest; raise SystemExit(pytest.main(sys.argv[1:]))"
        )
        command = [sys.executable, "-I", "-B", "-X", "utf8", "-c", code,
                   "-q", "-p", "no:cacheprovider", "--basetemp", str(state / "pytest"), *arguments]
    else:
        command = [sys.executable, "-I", "-B", "-X", "utf8", "-m", mode, *arguments]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=180)
    (evidence / "stdout.txt").write_bytes(result.stdout)
    (evidence / "stderr.txt").write_bytes(result.stderr)
    (evidence / "command.json").write_text(json.dumps({
        "argv": command, "cwd": str(ROOT), "exit": result.returncode,
        "environment": "explicit allowlist; synthetic home/config/session/temp; source imports pinned",
        "real_model_calls": 0,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.stdout.decode("utf-8", errors="replace"))
    if result.stderr:
        print(result.stderr.decode("utf-8", errors="replace"), file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
