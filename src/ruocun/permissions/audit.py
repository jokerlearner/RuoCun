"""Frozen permissions/audit.ts (MIT), best-effort native workspace audit."""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from ..config.compat import resolve_env
from .secrets import redactSecrets


def auditDecision(workspaceRoot: str | Path, iso: str, entry: Mapping[str, str], env: Mapping[str, str] | None = None) -> None:
    if resolve_env("AUDIT", os.environ if env is None else env) == "0":
        return
    try:
        directory = Path(workspaceRoot) / ".ruocun"
        directory.mkdir(parents=True, exist_ok=True)
        row = {"t": iso, **{key: redactSecrets(value) for key, value in entry.items()}}
        with (directory / "audit.log").open("a", encoding="utf-8", errors="backslashreplace", newline="\n") as audit:
            audit.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError:
        pass
