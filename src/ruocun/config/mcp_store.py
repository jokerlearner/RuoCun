"""Native MCP configuration writes using the existing private file contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .native_json import nativeJsonWriter, readNativeObjectForWrite


def writeMcpState(file: Path, value: dict[str, Any], *, user_root: Path) -> None:
    root = user_root.absolute()
    target = file.absolute()
    if target not in {root / "mcp.json", root / "mcp_state.json"}:
        raise ValueError("MCP 只可保存到原生用户配置。")
    content = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
    with nativeJsonWriter(target) as publish:
        readNativeObjectForWrite(target)
        publish(content)
