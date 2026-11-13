"""冻结tui/app/format.ts（MIT）的展示纯函数。"""

import re
from typing import TypeVar

T = TypeVar("T")


def clampLines(lines: list[T], maximum: float) -> dict[str, object]:
    if len(lines) <= maximum:
        return {"shown": lines, "hidden": 0}
    return {"shown": lines[:int(maximum)], "hidden": len(lines) - int(maximum)}


def parseTodoResult(content: str) -> list[dict[str, str]]:
    statuses = {"☐": "pending", "▶": "in_progress", "☑": "completed"}
    result = []
    for line in content.split("\n"):
        match = re.match(r"^([☐▶☑])\s+(.*)$", line.strip())
        if match:
            result.append({"status": statuses[match[1]], "content": match[2]})
    return result
