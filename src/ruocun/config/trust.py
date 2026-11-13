"""Reference config/trust.ts (MIT), native-only trust receipt per D09.

Only project settings/hooks use this gate. Compatibility source selection is
the caller's responsibility, and no legacy trust receipt is read or written.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Mapping

from .compat import trust


def _rejectConstant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _file(userRoot: Path | None) -> Path:
    return (userRoot if userRoot is not None else Path.home() / ".ruocun") / "trusted.json"


def hasProjectConfig(root: str | Path) -> bool:
    return any((Path(root) / ".ruocun" / name).exists() for name in ("settings.json", "settings.local.json", "hooks.json"))


async def isTrusted(root: str | Path, *, userRoot: Path | None = None) -> bool:
    try:
        values = json.loads(_file(userRoot).read_text(encoding="utf-8"), parse_constant=_rejectConstant)
        return isinstance(values, list) and str(root) in values
    except (OSError, ValueError, UnicodeError):
        return False


async def addTrusted(root: str | Path, *, userRoot: Path | None = None) -> None:
    file = _file(userRoot)
    try:
        values = json.loads(file.read_text(encoding="utf-8"), parse_constant=_rejectConstant)
    except FileNotFoundError:
        values = []
    # ADR-0013: never overwrite damaged trust receipts with an empty list.
    if not isinstance(values, list):
        raise ValueError(f"{file}: 信任记录不是数组，保留原文件")
    if str(root) in values:
        return
    values.append(str(root))
    content = json.dumps(values, ensure_ascii=False, indent=2).encode("utf-8")
    file.parent.mkdir(parents=True, exist_ok=True)
    stream = tempfile.NamedTemporaryFile(dir=file.parent, prefix=f".{file.name}.", suffix=".tmp", delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, file)
    finally:
        temporary.unlink(missing_ok=True)


async def shouldTrustProject(
    root: str | Path, *, userRoot: Path | None = None,
    environ: Mapping[str, str] | None = None, projectConfigPresent: bool | None = None,
) -> bool:
    if trust(os.environ if environ is None else environ):
        return True
    present = hasProjectConfig(root) if projectConfigPresent is None else projectConfigPresent
    return not present or await isTrusted(root, userRoot=userRoot)
