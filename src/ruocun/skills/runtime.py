"""冻结index.ts的启动Skills装配（MIT），目录身份沿D09显式source map。"""

from __future__ import annotations

import asyncio
from collections.abc import Set as AbstractSet
from pathlib import Path

from ..config.compat import Compatibility
from ..tools.glob import globToRegExp, walkFiles
from .bundled import BUNDLED_SKILLS
from .control import SkillControls, readDisabledNames
from .discover import SkillDiscovery
from .skills import loadSkills
from .types import Skill

SKILLS_HEADER = (
    "\n\n# 按任务加载 Skill\n"
    "收到任务先看下面的触发条件。某项有可能适用，就先用 Skill 读出它的完整流程，"
    "再提问、答复或调用其它工具。已加载的流程适用到当前任务，包括其中的用户选择、确认和各阶段要求。"
    "遇到冲突时，以安全约束、当前用户指令和实际证据为准。\n"
)


def _startupVisible(skills: list[Skill], cwd: Path, *, retain_unmatched: bool = False) -> list[Skill]:
    conditional = [skill for skill in skills if skill.get("paths")]
    if not conditional:
        return skills
    patterns = [(skill["name"], [globToRegExp(pattern) for pattern in skill["paths"]])
                for skill in conditional]
    matched: set[str] = set()
    scanned = 0
    for _, relative in walkFiles(str(cwd)):
        scanned += 1
        if scanned > 4000:
            break
        for name, regexps in patterns:
            if name not in matched and any(regexp.search(relative) for regexp in regexps):
                matched.add(name)
        if len(matched) == len(conditional):
            break
    visible: list[Skill] = []
    for skill in skills:
        if not skill.get("paths"):
            visible.append(skill)
        elif skill["name"] in matched:
            preActivated = skill.copy()
            preActivated.pop("paths", None)
            visible.append(preActivated)
        elif retain_unmatched:
            visible.append(skill)
    return visible


def _disabledNames(userRoot: Path) -> set[str]:
    return readDisabledNames(userRoot)


async def loadRuntimeSkills(
    cwd: Path, userRoot: Path, compatibility: Compatibility, *, disabled: bool = False,
    sourceStates: dict[str, str] | None = None,
    controls: SkillControls | None = None,
    discovery: SkillDiscovery | None = None,
) -> list[Skill]:
    """装配启动可见Skills，将尚未匹配的条件技能交给可选会话发现池。"""
    if disabled:
        if discovery is not None:
            discovery.disable_disk()
        if sourceStates is not None:
            for source in compatibility.sources:
                if source.resource == "skills":
                    sourceStates[source.id] = "已禁用（--no-skills，未加载）"
        return []
    sources = [source for source in compatibility.sources if source.resource == "skills"]
    disk_enabled = discovery is None or discovery.disk_enabled
    if not disk_enabled:
        if sourceStates is not None:
            for source in sources:
                sourceStates[source.id] = "已禁用（磁盘技能通道，未加载）"
        sources = []
    userSources = [source for source in sources if source.scope == "user"]
    projectSources = [source for source in sources
                      if source.scope == "project" and source.workspace is not None
                      and Path(source.workspace).resolve() == cwd.resolve()]
    directorySources = [*userSources, None, *projectSources, None]
    directories = [Path(source.path) for source in userSources]
    directories.append(userRoot / "skills")
    directories.extend(Path(source.path) for source in projectSources)
    directories.append(cwd / ".ruocun" / "skills")
    loaded: list[list[Skill]] = []
    disk: list[Skill] = []
    if disk_enabled:
        disk = await loadSkills(*directories, loaded_by_directory=loaded
                                if sourceStates is not None or controls is not None else None)
    diskNames = {skill["name"] for skill in disk}
    disabledNames = _disabledNames(userRoot)
    if controls is not None:
        labels = (["兼容·用户"] * len(userSources) + ["用户"]
                  + ["兼容·项目"] * len(projectSources) + ["项目"]) if disk_enabled else []
        controls.set_catalog(disk, {id(skill): label for label, items in zip(labels, loaded, strict=True)
                                   for skill in items})
        controls.disabled = disabledNames.copy()
    core: list[Skill] = []
    for bundled in BUNDLED_SKILLS:
        if (not bundled.get("core") or bundled["name"] in diskNames
                or bundled["name"] in disabledNames):
            continue
        skill: Skill = {"name": bundled["name"], "description": bundled["description"],
                        "body": bundled["body"], "dir": "", "slug": bundled["name"]}
        if bundled.get("modelInvokable") is False:
            skill["modelInvokable"] = False
        if bundled.get("userInvocable") is False:
            skill["userInvocable"] = False
        core.append(skill)
    visible = [*core, *(skill for skill in disk if skill["name"] not in disabledNames)]
    result = await asyncio.to_thread(_startupVisible, visible, cwd, retain_unmatched=discovery is not None)
    if discovery is not None:
        result = discovery.initConditionalPool(result)
    if sourceStates is not None and disk_enabled:
        winners = {id(skill) for skill in disk}
        visibleNames = {skill["name"] for skill in result}
        for owner, items in zip(directorySources, loaded, strict=True):
            if owner is None:
                continue
            effective = overwritten = disabledCount = unmatched = 0
            for skill in items:
                if id(skill) not in winners:
                    overwritten += 1
                elif skill["name"] in disabledNames:
                    disabledCount += 1
                elif skill["name"] in visibleNames:
                    effective += 1
                else:
                    unmatched += 1
            sourceStates[owner.id] = (f"生效{effective}项；被覆盖{overwritten}项；"
                                      f"禁用{disabledCount}项；paths未匹配{unmatched}项")
    return result


async def loadInstalledSkills(directory: Path, active: list[Skill], disabled: AbstractSet[str]) -> list[Skill]:
    """为已确认安装的原生目录提案；入口保存目录后才扩活列表。"""
    try:
        physical = await asyncio.to_thread(directory.resolve, strict=True)
        if physical != directory.absolute():
            return []
        installed = await loadSkills(directory, allowed_roots=(physical,))
    except (OSError, RuntimeError):
        return []
    known = {skill["name"].lower() for skill in active}
    return [skill for skill in installed if skill["name"].lower() not in known
            and skill["name"] not in disabled and not skill.get("paths")]
