"""读写设置文件中的点号路径。

写入在同一文件锁内读取、更新对象并发布，已有配置无法解析或中间路径不是对象时保留原文件。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..platform.file_contract import AtomicFileError
from ..tools.paths import fileLock
from ..tools.types import ToolRejected
from .native_json import nativeJsonWriter, readNativeObjectForWrite

MISSING = object()

def setUserSetting(user_root: Path, setting: str, value: str | bool | int | float) -> None:
    root = user_root.absolute()
    target = root / "settings.json"
    with fileLock(str(target)):
        try:
            document = readNativeObjectForWrite(target)
            current = document
            keys = setting.split(".")
            for key in keys[:-1]:
                child = current.get(key)
                if child is None:
                    child = {}
                    current[key] = child
                if not isinstance(child, dict):
                    raise ValueError("设置路径经过非对象值")
                current = child
            current[keys[-1]] = value
            content = json.dumps(document, ensure_ascii=False, allow_nan=False, indent=2) + "\n"
        except (OSError, ValueError, TypeError, AtomicFileError) as error:
            raise ToolRejected(f"配置未写入，原文件已保留（{type(error).__name__}）。") from error
        with nativeJsonWriter(target) as publish:
            publish(content)


def readSetting(file: Path, setting: str) -> Any:
    try:
        value: Any = json.loads(file.read_text(encoding="utf-8"))
        for key in setting.split("."):
            if isinstance(value, dict):
                value = value.get(key, MISSING)
            elif isinstance(value, list) and key.isascii() and key.isdigit() and str(int(key)) == key:
                value = value[int(key)] if int(key) < len(value) else MISSING
            else:
                return MISSING
        return value
    except (OSError, ValueError, UnicodeError):
        return MISSING
