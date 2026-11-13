"""冻结toggle.test.ts三例/App.test.tsx两例的文字控件适配；真实Terminal另验。"""

import asyncio
import json

import pytest

from ruocun.skills.control import SkillControls, runSkillPicker, toggleBundled


def test_bundled_off_preserves_disk_entries():
    disabled = {"my-disk-skill"}
    toggleBundled(disabled, ["simplify", "debugging", "tdd"], False)
    assert disabled == {"my-disk-skill", "simplify", "debugging", "tdd"}


def test_bundled_on_preserves_disk_entries():
    disabled = {"simplify", "tdd", "my-disk-skill"}
    toggleBundled(disabled, ["simplify", "debugging", "tdd"], True)
    assert disabled == {"my-disk-skill"}


def test_bundled_off_is_idempotent():
    disabled = set()
    toggleBundled(disabled, ["simplify", "debugging", "tdd"], False)
    snapshot = disabled.copy()
    toggleBundled(disabled, ["simplify", "debugging", "tdd"], False)
    assert disabled == snapshot


def controls(tmp_path):
    control = SkillControls(tmp_path / "user", tmp_path / "project")
    disk = {"name": "my-skill", "description": "自定义", "body": "body", "dir": str(tmp_path)}
    control.set_catalog([disk], {id(disk): "用户"})
    return control


def test_picker_defaults_to_third_party_enter_toggles_and_t_shows_core(tmp_path):
    control, prompts = controls(tmp_path), []
    answers = iter(["", "t", None])

    async def ask(prompt):
        prompts.append(prompt)
        return next(answers)

    asyncio.run(runSkillPicker(control, ask))
    assert "仅第三方" in prompts[0] and "my-skill" in prompts[0]
    assert "simplify" not in prompts[0]
    assert "simplify" in prompts[-1]
    assert "my-skill" in json.loads((control.userRoot / "skills-disabled.json").read_text())
    assert "my-skill" in SkillControls(control.userRoot, tmp_path).disabled


def test_picker_I_disables_installed_b_enables_core_and_cancel_preserves_choice(tmp_path):
    control = controls(tmp_path)
    answers = iter(["I", "b", None])

    async def ask(prompt):
        return next(answers)

    asyncio.run(runSkillPicker(control, ask))
    assert control.disabled == {"my-skill"}
    assert not next(row for row in control.listSkills() if row["name"] == "my-skill")["on"]
    assert next(row for row in control.listSkills() if row["name"] == "simplify")["on"]
    # ADR13必要适配：损坏原文件不被一次开关操作覆盖。
    file = control.userRoot / "skills-disabled.json"
    malformed = b'["my-skill",NaN]'
    file.write_bytes(malformed)
    with pytest.raises(ValueError, match="保留原文件"):
        control.setSkillEnabled("my-skill", True)
    assert file.read_bytes() == malformed
