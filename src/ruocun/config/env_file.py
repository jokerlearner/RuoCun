"""读取调用方指定的 .env 文件，用其中的默认值补充环境变量。

显式环境变量优先。解析接受简单的 KEY=VALUE、引号和注释。调用方也可以传入独立的环境映射，用于合成运行和检查。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import MutableMapping


def parseDotenv(content: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in content.split("\n"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        eq = line.find("=")
        if eq <= 0:
            continue
        key = line[:eq].strip()
        val = line[eq + 1:].strip()
        if (
            (val.startswith('"') and val.endswith('"'))
            or (val.startswith("'") and val.endswith("'"))
        ):
            val = val[1:-1]
        if key:
            out[key] = val
    return out


def loadDotenv(file: str | Path) -> dict[str, str]:
    try:
        return parseDotenv(Path(file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return {}


def applyDotenv(
    file: str | Path, environ: MutableMapping[str, str] | None = None,
) -> list[str]:
    """用 .env 补齐环境中缺失的值，返回实际补入的键名。"""
    target: MutableMapping[str, str] = os.environ if environ is None else environ
    applied: list[str] = []
    for key, value in loadDotenv(file).items():
        if key not in target:
            target[key] = value
            applied.append(key)
    return applied
