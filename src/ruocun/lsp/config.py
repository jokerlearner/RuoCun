"""按配置读取顺序合并语言服务器定义，再按文件选择匹配的服务器。"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any


async def loadLspConfig(files: Sequence[str | Path]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for file in files:
        try:
            value = json.loads(await asyncio.to_thread(Path(file).read_text, encoding="utf-8"))
            if isinstance(value, dict) and isinstance(value.get("servers"), dict):
                servers.update(value["servers"])
        except (OSError, ValueError):
            continue
    return {"servers": servers}


def resolveServerForFile(config: dict[str, Any], filePath: str) -> dict[str, Any] | None:
    extension = Path(filePath).suffix.lower()
    for name, server in config.get("servers", {}).items():
        if isinstance(server, dict) and any(isinstance(ext, str) and ext.lower() == extension
                                            for ext in server.get("extensions", [])):
            return {"name": name, "server": server}
    return None
