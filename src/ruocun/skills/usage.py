"""读写技能使用记录，并按调用频次和时间衰减计算排序分数。"""

from __future__ import annotations

import asyncio
import json
import math
from datetime import date
from pathlib import Path
from typing import Literal, TypedDict, cast

from ..platform.file_contract import AtomicFileError
from ..platform.windows.durable_file import AtomicPublishPreReplaceError, atomic_publish


class UsageEntry(TypedDict):
    count: int
    lastUsedAt: str


UsageMap = dict[str, UsageEntry]
UsageSaveResult = Literal["saved", "failed", "unknown"]


def recordUsage(usage: UsageMap, name: str, today: str) -> UsageMap:
    count = usage[name]["count"] if name in usage else 0
    return {**usage, name: {"count": count + 1, "lastUsedAt": today}}


def usageScore(usage: UsageMap, name: str, today: str) -> float:
    if name not in usage:
        return 0
    entry = usage[name]
    try:
        days = abs((date.fromisoformat(today) - date.fromisoformat(entry["lastUsedAt"])).days)
    except ValueError:
        days = 0
    return entry["count"] * max(math.pow(0.5, days / 7), 0.1)


def _read(file: Path) -> UsageMap:
    raw = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or any(
        not isinstance(value, dict) or type(value.get("count")) is not int
        or not isinstance(value.get("lastUsedAt"), str) for value in raw.values()
    ):
        raise ValueError("技能用量文件格式损坏")
    return cast(UsageMap, raw)


async def loadUsage(userRoot: Path) -> UsageMap:
    try:
        return await asyncio.to_thread(_read, userRoot / "skill-usage.json")
    except (OSError, ValueError):
        return {}


def _save(file: Path, usage: UsageMap) -> UsageSaveResult:
    try:
        _read(file)
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        return "failed"  # 先从原文件读取已有记录，读取失败时保留该文件供核实。
    try:
        data = json.dumps(usage, ensure_ascii=False, indent=2).encode("utf-8", errors="backslashreplace")
        atomic_publish(file, data)
    except AtomicPublishPreReplaceError as exc:
        return "unknown" if exc.replacement_uncertain else "failed"
    except (OSError, AtomicFileError):
        return "unknown"
    return "saved"


async def saveUsage(userRoot: Path, usage: UsageMap) -> UsageSaveResult:
    """尝试保存一次使用记录，返回调用方可据以决定是否继续计数的结果。"""
    return await asyncio.to_thread(_save, userRoot / "skill-usage.json", usage)
