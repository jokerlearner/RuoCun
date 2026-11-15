"""解析 SKILL.md，并合并多个目录中的技能记录。

技能目录只携带供模型选择的元信息，正文等到调用时才读取。同名原生技能依加载顺序覆盖。
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from .types import Skill


def findUserInvocableSkill(skills: list[Skill], name: str) -> Skill | None:
    want = name.strip().lower()
    for skill in skills:
        if skill.get("userInvocable") is False:
            continue
        slug = skill.get("slug", "")
        namespace = f"{skill['namespace']}:" if skill.get("namespace") else ""
        if want in (slug.lower(), skill["name"].lower(), (namespace + slug).lower()):
            return skill
    return None


def skillCatalogLines(skills: list[Skill]) -> str:
    """把技能元信息编排成供模型查看的目录。"""
    lines: list[str] = []
    for skill in skills:
        if skill.get("modelInvokable") is False:
            continue
        name = skill["name"]
        trigger = f" 何时用:{skill['whenToUse']}" if skill.get("whenToUse") else ""
        namespace = f"{skill['namespace']}:" if skill.get("namespace") else ""
        callName = namespace + skill.get("slug", name)
        call = f"(调用名 {callName})" if callName.lower() != name.lower() else ""
        detail = (skill["description"] + trigger).encode("utf-16-le", errors="surrogatepass")
        # 按 UTF-16 单元折叠描述，保持与既有提示预算算法一致。
        detailText = detail[:440].decode("utf-16-le", errors="surrogatepass")
        lines.append(f"- {name}{call}:{detailText}")
    return "\n".join(lines)


def _parse(fallbackName: str, directory: str, raw: str) -> Skill | None:
    name, description = fallbackName, ""
    flags: Skill = {}
    match = re.fullmatch(r"---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)", raw)
    if match:
        for line in re.split(r"\r?\n", match[1]):
            index = line.find(":")
            if index <= 0:
                continue
            key, value = line[:index].strip().lower(), line[index + 1:].strip()
            if key == "name":
                name = value or name
            elif key == "description":
                description = value
            elif key in ("when_to_use", "when to use", "whentouse"):
                if value:
                    flags["whenToUse"] = value
                else:
                    flags.pop("whenToUse", None)
            elif key == "paths":
                paths = [re.sub(r"^[\"']|[\"']$", "", item).strip()
                         for item in re.split(r"[,\s]+", re.sub(r"^\[|\]$", "", value))]
                if any(paths):
                    flags["paths"] = [item for item in paths if item]
                else:
                    flags.pop("paths", None)
            elif key in ("disable-model-invocation", "disable_model_invocation"):
                if _truthy(value):
                    flags["modelInvokable"] = False
            elif key in ("user-invocable", "user_invocable"):
                if not _truthy(value):
                    flags["userInvocable"] = False
        body = match[2].strip()
    else:
        body = raw.strip()
    if not body:
        return None
    return {**flags, "name": name, "description": description, "slug": fallbackName,
            "body": body, "dir": directory}


def _truthy(value: str) -> bool:
    value = re.sub(r"^[\"']|[\"']$", "", value).strip()
    return value.lower() in ("true", "yes", "1", "on")


def _loadFrom(baseDir: str | Path, allowed_roots: tuple[Path, ...] | None = None) -> list[Skill]:
    directory = Path(baseDir)
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return []
    result: list[Skill] = []
    for entry in entries:
        if entry.is_dir():
            file, slug, resourceDir = entry / "SKILL.md", entry.name, entry
        elif entry.name.endswith(".md"):
            file, slug, resourceDir = entry, entry.name[:-3], directory
        else:
            continue
        try:
            if allowed_roots is not None:
                physical_dir = resourceDir.resolve(strict=True)
                file = file.resolve(strict=True)
                if not any(physical_dir.is_relative_to(root) for root in allowed_roots):
                    continue
                if not any(file.is_relative_to(root) for root in allowed_roots):
                    continue
            raw = file.read_bytes().decode("utf-8", errors="replace")
        except (OSError, RuntimeError):
            continue
        skill = _parse(slug, str(resourceDir), raw)
        if skill:
            skill["file"] = str(file)
            result.append(skill)
    return result


async def loadSkills(
    *dirs: str | Path, loaded_by_directory: list[list[Skill]] | None = None,
    allowed_roots: tuple[Path, ...] | None = None,
) -> list[Skill]:
    """合并多个原生技能目录，并在需要时生成外部技能候选。"""
    loaded = await asyncio.gather(*(asyncio.to_thread(_loadFrom, item, allowed_roots) for item in dirs))
    if loaded_by_directory is not None:
        loaded_by_directory.extend(loaded)
    byRealpath: dict[str, Skill] = {}
    for skills in loaded:
        for skill in skills:
            file = skill.get("file")
            key = file or f"{skill['dir']}/{skill.get('slug', '')}"
            if file:
                try:
                    key = str(Path(file).resolve(strict=True))
                except OSError:
                    pass
            byRealpath[key] = skill
    byName: dict[str, Skill] = {}
    for skill in byRealpath.values():
        byName[skill["name"]] = skill
    return list(byName.values())
