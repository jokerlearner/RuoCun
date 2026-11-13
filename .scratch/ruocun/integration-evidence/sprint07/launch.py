"""Independent review runner: never inspects the caller's environment."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def clean_env(state: Path, executable: Path) -> dict[str, str]:
    for part in ("home", "appdata", "localappdata", "tmp", "pip-cache"):
        (state / part).mkdir(parents=True, exist_ok=True)
    return {
        "SYSTEMROOT": r"C:\Windows", "WINDIR": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
        "PATH": os.pathsep.join((str(executable.parent), r"C:\Windows\System32")),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "HOME": str(state / "home"), "USERPROFILE": str(state / "home"),
        "APPDATA": str(state / "appdata"), "LOCALAPPDATA": str(state / "localappdata"),
        "TEMP": str(state / "tmp"), "TMP": str(state / "tmp"),
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_INPUT": "1",
        "PIP_CACHE_DIR": str(state / "pip-cache"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", type=Path)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    repo = Path(__file__).resolve().parents[4]
    state = repo / ".cache" / "sprint07-review"
    raw = state / "raw" / args.label
    raw.mkdir(parents=True, exist_ok=False)
    environment = clean_env(state, Path(command[0]).resolve())
    if args.wheelhouse:
        environment.update(PIP_NO_INDEX="1", PIP_FIND_LINKS=args.wheelhouse.resolve().as_uri())
    result = subprocess.run(command, cwd=args.cwd or repo,
                            env=environment,
                            capture_output=True)
    combined = result.stdout + result.stderr
    hits = bool(re.search(rb"sk-[A-Za-z0-9_-]{16,}|Bearer [A-Za-z0-9_.-]{16,}|PRIVATE KEY-----", combined))
    (raw / "stdout.bin").write_bytes(result.stdout)
    (raw / "stderr.bin").write_bytes(result.stderr)
    (raw / "command.json").write_text(json.dumps({
        "argv": command, "cwd": str(args.cwd or repo), "exit": result.returncode,
        "environment": "explicit allowlist; synthetic home/config/temp; caller environment never inspected",
        "sensitive_pattern_match": hits, "command_joined": True,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"label": args.label, "exit": result.returncode, "pattern_hit": hits}))
    return 90 if hits else result.returncode


if __name__ == "__main__":
    sys.exit(main())
