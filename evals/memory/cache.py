"""The frozen accept-cache.sh cold/warm check over real product audit rows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lib.creds import InvalidEvaluation


def _count(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    if type(value) is not int or value < 0:
        raise InvalidEvaluation("缓存用量字段无效。")
    return value


def gradeCache(path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise InvalidEvaluation("缓存审计记录格式无效。")
        if row.get("agent") != "main" or row.get("depth") != 0:
            continue
        turn, prompt, hit, miss = (_count(row, key) for key in ("turn", "prompt", "hit", "miss"))
        if hit + miss > prompt:
            raise InvalidEvaluation("缓存用量超过实际输入。")
        rows.append({"turn": turn, "prompt": prompt, "hit": hit, "miss": miss,
                     "ratio": hit / prompt if prompt else 0.0, "usageObserved": bool(hit or miss)})
    if len(rows) < 2 or not all(row["usageObserved"] for row in rows):
        return {"status": "unverified", "turns": rows, "reason": "缺少可比较的缓存用量回执。"}
    cold = float(rows[0]["ratio"])
    warm = max(float(row["ratio"]) for row in rows[1:])
    return {"status": "measured", "turns": rows, "coldRatio": cold, "warmRatio": warm,
            "warmIncreased": warm > cold, "warmTarget90": warm >= 0.90}
