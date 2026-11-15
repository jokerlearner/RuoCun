"""根据会话访问的文件发现附近技能，并激活路径条件命中的候选。

prepare 先生成候选目录和提示，调用方确认提示已能随会话使用后，confirm 再写入扫描记录与激活状态。
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Iterable
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from pathlib import Path

from ..tools.glob import globToRegExp
from .skills import loadSkills, skillCatalogLines
from .types import Skill


@dataclass(frozen=True, slots=True)
class DiscoveryCandidate:
    directories: tuple[Path, ...] = ()
    discovered: tuple[Skill, ...] = ()
    activated: tuple[Skill, ...] = ()
    catalog_messages: tuple[str, ...] = ()


def _fileKeys(skills: Iterable[Skill]) -> set[Path]:
    keys: set[Path] = set()
    for skill in skills:
        if file := skill.get("file"):
            path = Path(file)
            try:
                path = path.resolve(strict=True)
            except (OSError, RuntimeError):
                pass
            keys.add(path)
    return keys


class SkillDiscovery:
    """维护会话内待激活技能和已确认扫描的目录。"""

    def __init__(self, cwd: Path, *, disk_enabled: bool) -> None:
        self.cwd = cwd.resolve()
        self.disk_enabled = disk_enabled
        self._checked_dirs: set[Path] = set()
        self._pending: dict[str, tuple[Skill, list[re.Pattern[str]]]] = {}

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def disable_disk(self) -> None:
        self.disk_enabled = False
        self._pending.clear()

    def initConditionalPool(self, skills: Iterable[Skill]) -> list[Skill]:
        self._pending.clear()
        if not self.disk_enabled:
            return list(skills)
        active = []
        for skill in skills:
            if patterns := skill.get("paths"):
                self._pending[skill["name"]] = (skill, [globToRegExp(pattern) for pattern in patterns])
            else:
                active.append(skill)
        return active

    def _scan(self, paths: tuple[str, ...], checked: set[Path]) -> tuple[tuple[Path, ...], tuple[Path, ...], list[str]]:
        found: dict[Path, Path] = {}
        relative_paths: list[str] = []
        for path in paths:
            file = Path(os.path.abspath(self.cwd / path))
            try:
                relative = file.relative_to(self.cwd)
                if not relative.parts or not file.resolve().is_relative_to(self.cwd):
                    continue
            except (OSError, RuntimeError, ValueError):
                continue
            relative_paths.append(relative.as_posix())
            parent = file.parent
            while parent != self.cwd:
                native = parent / ".ruocun" / "skills"
                if "node_modules" not in str(parent) and native not in checked and native not in found:
                    try:
                        physical = native.resolve(strict=True)
                        if physical.is_dir() and physical.is_relative_to(self.cwd):
                            found[native] = physical
                    except (OSError, RuntimeError):
                        pass  # 缺失目录仍可在后续访问时重新发现。
                parent = parent.parent
        directories = tuple(sorted(found, key=lambda item: -len(item.parts)))
        return directories, tuple(found.values()), relative_paths

    async def prepare(
        self, paths: Iterable[str], active: list[Skill], *, disabled: AbstractSet[str],
    ) -> DiscoveryCandidate:
        if not self.disk_enabled:
            return DiscoveryCandidate()
        access = tuple(paths)
        if not access:
            return DiscoveryCandidate()
        # 先用状态快照做文件扫描，调用方确认候选后才更新待激活项和目录记录。
        snapshot = tuple(active)
        pending = tuple(self._pending.items())
        blocked = frozenset(disabled)
        directories, roots, relative_paths = await asyncio.to_thread(
            self._scan, access, self._checked_dirs.copy(),
        )
        names = {skill["name"].lower() for skill in snapshot}
        discovered: list[Skill] = []
        if directories:
            try:
                known_files = await asyncio.to_thread(_fileKeys, (*snapshot, *(item[0] for _, item in pending)))
                # 扫描顺序从深到浅。合并时后加载的目录覆盖前面的同名项。
                for skill in await loadSkills(*directories, allowed_roots=roots):
                    name = skill["name"]
                    if name in blocked or name.lower() in names or Path(skill["file"]) in known_files:
                        continue
                    discovered.append(skill)
            except (OSError, RuntimeError):
                discovered.clear()  # 一批目录读取失败后，路径条件匹配仍可独立完成。
        activated: list[Skill] = []
        for name, (skill, patterns) in pending:
            if name in blocked:
                continue
            if any(pattern.search(path) for path in relative_paths for pattern in patterns):
                activated.append(skill)
        messages = []
        for items, header in (
            (discovered, "动态发现 skill(本次会话已加载,匹配任务时先用 skill 工具加载其正文)"),
            (activated, "条件 skill 已激活(路径匹配,本次会话已加载)"),
        ):
            if lines := skillCatalogLines(items):
                messages.append(f"\n# {header}\n{lines}")
        return DiscoveryCandidate(directories, tuple(discovered), tuple(activated), tuple(messages))

    def confirm(self, candidate: DiscoveryCandidate, active: list[Skill]) -> None:
        """在调用方确认候选生效后，记下目录并激活匹配的技能。"""
        self._checked_dirs.update(candidate.directories)
        for skill in candidate.activated:
            self._pending.pop(skill["name"], None)
        active.extend(candidate.discovered)
        active.extend(candidate.activated)
