"""dotenv 简化方言（来源冻结 ``src/config/env_file.ts``，MIT）。

CFG-05 / D09:134：只加载 cwd 的 ``.env``；已有 process env（含空串）优先；
只支持简化 ``KEY=VALUE`` / 配对引号 / 注释方言，不引入 export、变量插值、
跨品牌扫描。``applyDotenv`` 的 ``environ`` 可注入合成映射，便于隔离测试。
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
    """把 .env 的键补进 environ，仅当该键尚未存在；返回实际补入的键名。"""
    target: MutableMapping[str, str] = os.environ if environ is None else environ
    applied: list[str] = []
    for key, value in loadDotenv(file).items():
        if key not in target:
            target[key] = value
            applied.append(key)
    return applied
