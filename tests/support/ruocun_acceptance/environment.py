"""Synthetic environment for development acceptance subprocesses."""

from __future__ import annotations

import os
from pathlib import Path


def isolated_env(root: Path, executable: Path) -> dict[str, str]:
    for part in ("home", "appdata", "localappdata", "tmp"):
        (root / part).mkdir(parents=True, exist_ok=True)
    paths = [str(executable.resolve().parent)]
    env = {
        "HOME": str(root / "home"), "USERPROFILE": str(root / "home"),
        "APPDATA": str(root / "appdata"), "LOCALAPPDATA": str(root / "localappdata"),
        "TEMP": str(root / "tmp"), "TMP": str(root / "tmp"),
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
    }
    if os.name == "nt":
        env.update(SYSTEMROOT="C:\\Windows", WINDIR="C:\\Windows")
        paths.append("C:\\Windows\\System32")
    env["PATH"] = os.pathsep.join(paths)
    return env
