"""Native JSON object protection and scoped private publication."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
    verify_private_file,
)
from ..tools.paths import atomicWrite


def readNativeObjectForWrite(path: Path) -> dict[str, Any]:
    """Reject malformed existing objects before any caller replaces their data."""
    try:
        if sys.platform == "win32" and path.exists():
            verify_private_file(path)
        obj: Any = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, dict):
            return obj
        raise ValueError("现有配置不是对象，已保留原文件并停止保存")
    except FileNotFoundError:
        return {}


@contextmanager
def nativeJsonWriter(path: Path) -> Iterator[Callable[[str], None]]:
    """Keep directory protection alive across validation and publication."""
    root = path.parent
    if os.name == "nt":
        root.parent.mkdir(parents=True, exist_ok=True)
        with PrivateDirectory(root):
            def publish(content: str) -> None:
                atomic_publish(path, content.encode("utf-8"))

            yield publish
    else:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)

        def publish(content: str) -> None:
            atomicWrite(str(path), content)
            path.chmod(0o600)

        yield publish
