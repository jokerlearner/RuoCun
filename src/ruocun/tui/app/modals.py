"""冻结App.tsx选择/审批面板状态；所有按键仍由InputBroker路由。"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence

from prompt_toolkit.buffer import Buffer

from ...approval.types import ApprovalRequest
from ...i18n.i18n import t
from ...skills.control import SkillControls
from ..onboarding.select import Select, SelectItem
from .app import clean_text


def _normalized(value: str) -> str:
    return re.sub(r"^\d+[.、)]\s*", "", value.strip()).lower()


class Modal:
    def __init__(self, title: str, items: Sequence[SelectItem] = (), *, initial: int = 0, wrap: bool = False) -> None:
        self.title = clean_text(title)
        self.selection = Select(items, initialIndex=initial, wrap=wrap)
        self.kind = "select"
        self.multi = self.finished = self.warn = self.cancelled = False
        self.value: str | None = None
        self.checked: set[int] = set()
        self.option_count = len(items)
        self.fill_index = self.done_index = self.discuss_index = -1
        self.request: ApprovalRequest | None = None
        self.controls: SkillControls | None = None
        self._skill_rows: list[dict[str, object]] = []
        self.show_bundled = self.changed = False

    @classmethod
    def choice(cls, question: str, options: Sequence[str], multi: bool) -> Modal:
        reserved = {_normalized(value) for value in [t("ui.choice.fill"), t("ui.choice.discuss"), t("ui.choice.done"),
                    "其他", "其它", "以上都不是", "以上都不对", "都不是", "自定义", "自己输入", "手动输入",
                    "other", "none of the above", "none of these", "something else", "custom"]}
        cleaned = [value for value in options if _normalized(value) not in reserved]
        labels = [*cleaned, *([t("ui.choice.done")] if multi else []), t("ui.choice.fill"), t("ui.choice.discuss")]
        modal = cls(question, [{"label": label, "value": label} for label in labels])
        modal.kind, modal.multi, modal.option_count = "choice", multi, len(cleaned)
        modal.done_index = len(cleaned) if multi else -1
        modal.fill_index = len(cleaned) + int(multi)
        modal.discuss_index = modal.fill_index + 1
        return modal

    @classmethod
    def approval(cls, request: ApprovalRequest, index: int, total: int) -> Modal:
        modal = cls(t("ui.approval.title", f" ({index + 1}/{total})" if total > 1 else ""))
        modal.kind, modal.request = "approval", request
        return modal

    @classmethod
    def skills(cls, controls: SkillControls) -> Modal:
        modal = cls("")
        modal.kind, modal.controls = "skills", controls
        modal.refresh_skills()
        return modal

    @property
    def typing(self) -> bool:
        return self.kind == "choice" and self.selection.index == self.fill_index

    def _finish(self, value: str | None) -> None:
        self.finished, self.value = True, value

    def refresh_skills(self) -> None:
        assert self.controls is not None
        all_rows = self.controls.listSkills()
        visible = all_rows if self.show_bundled else [row for row in all_rows if not row["source"].startswith("内置")]
        self._skill_rows = [dict(row) for row in visible]
        self.selection.items = [{"label": f"{'● on ' if row['on'] else '○ off'} {row['name']} · {row['source']} · {row['detail'][:40]}",
                                 "value": row["name"]} for row in visible]
        self.selection.index = min(self.selection.index, max(0, len(visible) - 1))

    def handle(self, key: str, text: str, answer: Buffer) -> bool:
        if key == "escape":
            self.cancelled = True
            self._finish(None)
            return True
        if self.kind == "approval":
            assert self.request is not None
            if text == "y":
                self._finish("once")
            elif text == "n":
                self._finish("deny")
            elif text == "a" and not self.request.get("dangerous") and not self.request.get("noPersist"):
                self._finish("always")
            return True
        if key in {"up", "down"}:
            self.selection.move(-1 if key == "up" else 1)
            if self.typing:
                answer.reset()
            return True
        if self.kind == "skills":
            assert self.controls is not None
            if text == "t":
                self.show_bundled = not self.show_bundled
                self.selection.index = 0
                self.refresh_skills()
            elif text in {"a", "A", "b", "B", "i", "I"}:
                self.controls.batchSkills({"a": "all", "b": "bundled", "i": "installed"}[text.lower()], text.islower())
                self.changed = True
                if text.lower() == "b":
                    self.show_bundled = True
                self.refresh_skills()
            elif key == "enter" or text in "123456789" and len(text) == 1:
                index = int(text) - 1 if text.isdecimal() else self.selection.index
                if 0 <= index < len(self.selection.items):
                    row = self._skill_rows[index]
                    self.controls.setSkillEnabled(str(row["name"]), not row["on"])
                    self.changed = True
                    self.refresh_skills()
            return True
        if self.typing:
            if key == "enter":
                custom = answer.text.strip()
                picked = [self.selection.items[index]["value"] for index in sorted(self.checked)]
                if self.multi:
                    self._finish(", ".join([*picked, *([custom] if custom else [])]) or t("ui.choice.noneSelected"))
                else:
                    self._finish(custom or t("ui.choice.empty"))
                return True
            return False
        if len(text) == 1 and text in "123456789":
            index = int(text) - 1
            if index < len(self.selection.items):
                self.selection.index = index
                if self.kind == "select":
                    self._finish(self.selection.value)
                elif index < self.option_count:
                    if self.multi:
                        self._toggle(index)
                    else:
                        self._finish(self.selection.value)
                elif self.typing:
                    answer.reset()
                elif not self.multi and index == self.discuss_index:
                    self._finish(t("ui.choice.discussValue"))
            return True
        if self.kind == "select":
            if key == "enter":
                self._finish(self.selection.value)
            return True
        index = self.selection.index
        if key == "enter":
            if index == self.discuss_index:
                self._finish(t("ui.choice.discussValue"))
            elif index == self.done_index:
                if not self.checked:
                    self.warn = True
                else:
                    self._finish(", ".join(self.selection.items[value]["value"] for value in sorted(self.checked)))
            elif index < self.option_count:
                if self.multi:
                    self._toggle(index)
                else:
                    self._finish(self.selection.value)
        elif text == " " and self.multi and index < self.option_count:
            self._toggle(index)
        return True

    def _toggle(self, index: int) -> None:
        self.warn = False
        self.checked.symmetric_difference_update({index})

    def render(self, answer: str, rows: int) -> str:
        if self.kind == "approval":
            assert self.request is not None
            request = self.request
            key = "noPersist" if request.get("noPersist") else "sensitive" if request.get("dangerous") else "sensitivePlain" if request.get("sensitive") else "normal"
            return self.title + "\n  " + clean_text(request["summary"][:600]).replace("\n", "\n  ") + "\n" + t("ui.approval." + key)
        labels = self.selection.items
        count, index = len(labels), self.selection.index
        normal = self.option_count if self.kind == "choice" else count
        extras = count - normal
        window = max(5, min(normal, rows - 15 - extras))
        anchor = min(index, max(0, normal - 1))
        start = max(0, min(anchor - window // 2, max(0, normal - window)))
        lines = [self.title] if self.title else []
        if self.kind == "skills":
            assert self.controls is not None
            all_rows = self.controls.listSkills()
            bundled = sum(row["source"].startswith("内置") for row in all_rows)
            lines = [t("ui.skill.header", bundled, len(all_rows) - bundled, sum(row["on"] for row in all_rows),
                       t("ui.skill.showAll" if self.show_bundled else "ui.skill.showThird"))]
        if start:
            lines.append(t("ui.resume.more", start))
        shown = [*range(start, min(normal, start + window)), *range(normal, count)]
        if self.kind == "skills" and not labels:
            lines.append(t("ui.skill.empty", "" if self.show_bundled else t("ui.skill.thirdWord")))
        for item_index in shown:
            label = clean_text(labels[item_index]["label"])
            if self.kind == "choice":
                label = re.sub(r"^\s*(?:[A-Za-z]|\d+)[.)、]\s*", "", label)
                if item_index < self.option_count and self.multi:
                    label = ("[x] " if item_index in self.checked else "[ ] ") + label
                if item_index == self.fill_index and item_index == index:
                    label = clean_text(answer) or t("ui.choice.fillActive")
            lines.append(("❯ " if item_index == index else "  ") + f"{item_index + 1}. " + label)
        if start + window < normal:
            lines.append(t("ui.resume.moreBelow", normal - start - window))
        if self.kind == "choice":
            lines.append(t("ui.choice.hintFill" if self.typing else "ui.choice.hintMulti" if self.multi else "ui.choice.hintSingle"))
            if self.warn:
                lines.append(t("ui.choice.warn"))
        elif self.kind == "skills":
            lines.extend([t("ui.skill.help1"), t("ui.skill.help2")])
        return "\n".join(lines)


class SecretValidationModal(Modal):
    def __init__(self, title: str, validating: str, submit: Callable[[str], None]) -> None:
        super().__init__(title)
        self.validating = clean_text(validating)
        self.submit = submit
        self.busy = False

    @property
    def typing(self) -> bool:
        return not self.busy and not self.finished

    def handle(self, key: str, text: str, answer: Buffer) -> bool:
        if self.busy or key == "escape":
            return True
        if key in {"ctrl-c", "ctrl-d"}:
            self._finish(None)
            return True
        if key == "enter":
            if answer.text:
                self.busy = True
                self.submit(answer.text)
            else:
                self._finish(None)
            return True
        return False

    def render(self, answer: str, rows: int) -> str:
        return self.title + ("\n" + self.validating if self.busy else "")


class TrustModal(Modal):
    def handle(self, key: str, text: str, answer: Buffer) -> bool:
        if key in {"ctrl-c", "ctrl-d"}:
            self._finish(None)
        else:
            self._finish("yes" if key == "text" and text in {"y", "Y"} else "no")
        return True
