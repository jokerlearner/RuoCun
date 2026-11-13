"""Run one explicit engineering command with synthetic state and a clean environment."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--state", type=Path, default=Path(".cache/boot"))
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--oracle-node", type=Path)
    parser.add_argument("--oracle-cache", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command: list[str] = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        parser.error("an explicit command is required")
    state = args.state.resolve()
    for part in ("home", "appdata", "localappdata", "tmp", "raw", "pip-cache"):
        (state / part).mkdir(parents=True, exist_ok=True)
    env = {
        "SYSTEMROOT": "C:\\Windows",
        "WINDIR": "C:\\Windows",
        "COMSPEC": "C:\\Windows\\System32\\cmd.exe",
        "PATH": os.pathsep.join(
            [str(Path(command[0]).resolve().parent), "C:\\Windows\\System32"]
        ),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "HOME": str(state / "home"),
        "USERPROFILE": str(state / "home"),
        "APPDATA": str(state / "appdata"),
        "LOCALAPPDATA": str(state / "localappdata"),
        "TEMP": str(state / "tmp"),
        "TMP": str(state / "tmp"),
        "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "PIP_CACHE_DIR": str(state / "pip-cache"),
    }
    if args.wheelhouse:
        env.update(PIP_NO_INDEX="1", PIP_FIND_LINKS=args.wheelhouse.resolve().as_uri())
    if args.oracle_node:
        env["RUOCUN_ORACLE_NODE"] = str(args.oracle_node.resolve())
        env["PATH"] += os.pathsep + r"D:\study_software\Git\cmd"
    if args.oracle_cache:
        env["RUOCUN_ORACLE_CACHE"] = str(args.oracle_cache.resolve())
    raw = state / "raw" / args.label
    raw.mkdir(exist_ok=False)
    result = subprocess.run(command, cwd=args.cwd.resolve(), env=env, capture_output=True)
    (raw / "stdout.bin").write_bytes(result.stdout)
    (raw / "stderr.bin").write_bytes(result.stderr)
    # Never display/log names or values from the caller's environment.
    values = [
        value.encode()
        for name, value in os.environ.items()
        if re.search(r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", name, re.I)
        and len(value) >= 8
    ]
    hit = any(value in result.stdout + result.stderr for value in values)
    receipt = {
        "argv": command,
        "cwd": str(args.cwd.resolve()),
        "exit": result.returncode,
        "environment": "explicit allowlist; synthetic home/config/temp; no PYTHONPATH",
        "sensitive_values_present": bool(values),
        "sensitive_match": hit,
        "cleanup": {"command_joined": True, "state_retained": True},
    }
    (raw / "command.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"label": args.label, "exit": result.returncode, "scan_hit": hit}))
    return 90 if hit else result.returncode


if __name__ == "__main__":
    sys.exit(main())
