"""冻结 glob.ts / walk.ts 的匹配与文件遍历（MIT）。"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Iterator

_IGNORE = {"node_modules", ".git", "dist", ".dao", ".ruocun", ".codeds"}


def globToRegExp(glob: str) -> re.Pattern[str]:
    parts: list[str] = []
    index = 0
    while index < len(glob):
        char = glob[index]
        if glob[index:index + 3] == "**/":
            parts.append("(?:.*/)?")
            index += 3
        elif glob[index:index + 2] == "**":
            parts.append(".*")
            index += 2
        else:
            parts.append("[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char))
            index += 1
    return re.compile("^" + "".join(parts) + "$")


def walkFiles(root: str) -> Iterator[tuple[str, str]]:
    if os.path.isfile(root):
        yield root, os.path.basename(root)
        return

    def rec(directory: str) -> Iterator[tuple[str, str]]:
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError:
            return
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    # Python 3.11在Windows把junction仍视作目录；Node Dirent跳过链接。
                    # 仅跳过递归遇到的reparse目录，显式root继续由外部访问审批处理。
                    if os.name == "nt" and entry.stat(follow_symlinks=False).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                        continue
                    if entry.name not in _IGNORE:
                        yield from rec(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    yield entry.path, Path(os.path.relpath(entry.path, root)).as_posix()
            except OSError:
                continue

    yield from rec(root)
