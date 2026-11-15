"""为 /files 生成已知文件的展示列表。实际读过哪些文件，由调用方提供。"""

from __future__ import annotations

import os
from collections.abc import Iterable


def filesReport(workspaceRoot: str, readFiles: Iterable[str]) -> str:
    files: list[str] = []
    for path in readFiles:
        try:
            relative = os.path.relpath(path, workspaceRoot)
        except ValueError:  # 跨盘路径无法相对化，沿用 Node path.relative 的绝对路径结果。
            relative = path
        files.append(path if relative == "." else relative)
    if not files:
        return "本会话尚未读取任何文件。"
    result = f"上下文中读过的文件({len(files)}):\n" + "\n".join("  " + path for path in files[:50])
    if len(files) > 50:
        result += f"\n  …等共 {len(files)} 个"
    return result
