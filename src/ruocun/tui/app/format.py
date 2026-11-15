"""为终端展示限制行数，并从工具结果中提取任务清单。"""

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
