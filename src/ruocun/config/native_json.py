"""为账户、设置和 MCP 等配置提供受保护的 JSON 读取和发布。

读入现有文件时检查对象结构，在 Windows 上还核对文件权限。发布时由上下文管理器维持目标目录的保护，直至写入完成。
"""

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
    """读取待修改的配置对象，拒绝覆盖已损坏的配置。"""
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
    """在私有目录保护期间提供配置发布函数。"""
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
