"""Frozen index.ts /audit composition, confined to the selected native session root."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

from ..memory.memory_audit import (
    formatMemoryReport,
    formatReflectReport,
    summarizeMemoryTrace,
    summarizeReflectTrace,
)
from ..permissions.perm_audit import formatPermReport, summarizePermTrace
from ..session.cache_audit import formatCacheReport
from ..skills.skill_audit import (
    formatSkillReport,
    readAllSkillTraces,
    summarizeSkillTrace,
)
from ..tools.tool_audit import formatToolReport, summarizeToolTrace

_CATEGORIES = {"memory", "reflect", "tools", "perms", "cache", "skills", "all"}


def _read(directory: Path, name: str) -> list[Any]:
    try:
        file = directory / name
        if file.resolve().parent != directory.resolve():
            return []
        raw = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    events = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def auditCommand(args: Sequence[str], *, sessionsRoot: Path, currentId: str,
                 redact: Callable[[str], str]) -> str:
    if not args or args[0] not in _CATEGORIES:
        return f"用法：/audit <memory|reflect|tools|perms|cache|skills|all> [会话 ID]\n省略 ID 时查看当前会话 {currentId}。"
    identity = args[1] if len(args) > 1 else currentId
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identity):
        return "无效会话ID，未读取其它目录。"
    directory = sessionsRoot / identity
    if directory.resolve().parent != sessionsRoot.resolve():
        return "无效会话路径，未读取其它目录。"
    selected = args[0]
    sections = []
    def want(category: str) -> bool:
        return selected in {category, "all"}
    if want("memory"):
        sections.append(formatMemoryReport(summarizeMemoryTrace(_read(directory, "memory-trace.jsonl"))))
    if want("reflect"):
        sections.append(formatReflectReport(summarizeReflectTrace(_read(directory, "memory-trace.jsonl"))))
    if want("tools"):
        sections.append(formatToolReport(summarizeToolTrace(_read(directory, "tool-trace.jsonl"))))
    if want("perms"):
        sections.append(formatPermReport(summarizePermTrace(_read(directory, "perm-trace.jsonl"))))
    if want("cache"):
        sections.append(formatCacheReport(cast(Any, _read(directory, "cache.jsonl"))))
    if want("skills"):
        sections.append(formatSkillReport(summarizeSkillTrace(readAllSkillTraces(sessionsRoot))))
    return redact(f"审计 · 会话 {identity} · 目录 {directory}\n" + "\n\n".join(sections))
