"""读取内置技能的停用状态，并组织技能选择器的列表与启停操作。"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Iterable, Mapping
from pathlib import Path
from typing import Any, TypedDict

from ..platform.windows.durable_file import atomic_publish
from .bundled import BUNDLED_SKILLS
from .types import Skill


def _reject_constant(value: str) -> None:
    raise ValueError("非法JSON常量")


def readDisabledNames(userRoot: Path) -> set[str]:
    try:
        raw = json.loads((userRoot / "skills-disabled.json").read_text(encoding="utf-8"),
                         parse_constant=_reject_constant)
    except (OSError, UnicodeError, ValueError):
        return set()
    if raw is None:
        return set()
    if not isinstance(raw, (list, str)):
        raise ValueError("skills-disabled.json 必须是名称数组")
    return {item for item in raw if isinstance(item, str)}


def toggleBundled(disabled: set[str], names: Iterable[str], on: bool) -> None:
    for name in names:
        if on:
            disabled.discard(name)
        else:
            disabled.add(name)


class SkillRow(TypedDict):
    name: str
    on: bool
    source: str
    detail: str


def _invocation_mark(skill: Mapping[str, Any]) -> str:
    return "·仅手动" if skill.get("modelInvokable") is False else (
        "·仅自动" if skill.get("userInvocable") is False else "")


class SkillControls:
    def __init__(self, userRoot: Path, cwd: Path) -> None:
        self.userRoot, self.cwd = userRoot, cwd
        self.disabled = readDisabledNames(userRoot)
        self._disk: list[Skill] = []
        self._labels: dict[int, str] = {}
        self.blocked = False

    def set_catalog(self, disk: list[Skill], labels: dict[int, str]) -> None:
        self._disk, self._labels = disk, labels

    def listSkills(self) -> list[SkillRow]:
        disk_names = {skill["name"] for skill in self._disk}
        rows: list[SkillRow] = []
        for skill in BUNDLED_SKILLS:
            if not skill.get("core"):
                continue
            name = skill["name"]
            rows.append({"name": name, "on": name not in self.disabled and name not in disk_names,
                         "source": ("内置·被覆盖" if name in disk_names else "内置") + _invocation_mark(skill),
                         "detail": skill["description"]})
        for disk in self._disk:
            source = self._labels.get(id(disk), "项目" if disk["dir"].startswith(str(self.cwd)) else "用户")
            rows.append({"name": disk["name"], "on": disk["name"] not in self.disabled,
                         "source": source + _invocation_mark(disk), "detail": disk["description"]})
        return rows

    def _publish(self, candidate: set[str]) -> None:
        if self.blocked:
            raise RuntimeError("技能设置保存未确认，请重开核对后再修改。")
        file = self.userRoot / "skills-disabled.json"
        try:
            raw = json.loads(file.read_text(encoding="utf-8"), parse_constant=_reject_constant)
        except FileNotFoundError:
            raw = None
        except (ValueError, UnicodeError) as exc:
            raise ValueError("技能禁用文件JSON损坏，保留原文件；修复后再切换。") from exc
        if raw is not None and (not isinstance(raw, (list, str))
                                or isinstance(raw, list) and any(not isinstance(name, str) for name in raw)):
            raise ValueError("技能禁用文件包含无法保留的条目，保留原文件；修复后再切换。")
        data = json.dumps(sorted(candidate), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        try:
            atomic_publish(file, data)
        except Exception:
            self.blocked = True
            raise
        self.disabled = candidate

    def setSkillEnabled(self, name: str, on: bool) -> None:
        candidate = self.disabled.copy()
        toggleBundled(candidate, [name], on)
        self._publish(candidate)

    def batchSkills(self, scope: str, on: bool) -> None:
        bundled = [skill["name"] for skill in BUNDLED_SKILLS if skill.get("core")]
        installed = [skill["name"] for skill in self._disk]
        if scope not in {"bundled", "installed", "all"}:
            raise ValueError("未知技能批量范围。")
        names = bundled if scope == "bundled" else installed if scope == "installed" else bundled + installed
        candidate = self.disabled.copy()
        toggleBundled(candidate, names, on)
        self._publish(candidate)


async def runSkillPicker(controls: SkillControls, ask: Callable[[str], Awaitable[str | None]]) -> str:
    show_bundled = changed = False
    while True:
        all_rows = controls.listSkills()
        rows = all_rows if show_bundled else [row for row in all_rows if not row["source"].startswith("内置")]
        prompt = "技能 · " + ("全部" if show_bundled else "仅第三方") + "（切换后重启生效）\n"
        prompt += "\n".join(f"{index}. {'开' if row['on'] else '关'} {row['name']} [{row['source']}] {row['detail']}"
                            for index, row in enumerate(rows, 1))
        prompt += "\n数字/回车切换；t 显/隐内置；a/A 全部开/关；b/B 内置开/关；i/I 安装开/关；Esc关闭。"
        answer = await ask(prompt)
        if answer is None:
            return "技能设置已保存，重启生效。" if changed else ""
        answer = answer.strip()
        if answer == "t":
            show_bundled = not show_bundled
        elif answer in {"a", "A", "b", "B", "i", "I"}:
            controls.batchSkills({"a": "all", "b": "bundled", "i": "installed"}[answer.lower()], answer.islower())
            changed = True
            if answer.lower() == "b":
                show_bundled = True
        else:
            index = 0 if answer == "" else int(answer) - 1 if answer.isascii() and answer.isdecimal() else -1
            if 0 <= index < len(rows):
                row = rows[index]
                controls.setSkillEnabled(row["name"], not row["on"])
                changed = True
