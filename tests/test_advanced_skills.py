"""冻结 src/skills/skills.test.ts 的静态 Skills 语义断言。"""

import asyncio
import os
import subprocess

from ruocun.skills.skills import findUserInvocableSkill, loadSkills, skillCatalogLines


def test_loads_directory_and_flat_markdown(tmp_path):
    project = tmp_path / "p"
    (project / "pdf").mkdir(parents=True)
    (project / "pdf" / "SKILL.md").write_text(
        "---\nname: pdf\ndescription: 处理 PDF\n---\nPDF 步骤……", encoding="utf-8"
    )
    (project / "commit.md").write_text(
        "---\ndescription: 规范提交\n---\n提交步骤……", encoding="utf-8"
    )
    skills = asyncio.run(loadSkills(project, tmp_path / "nouser"))
    assert sorted(skill["name"] for skill in skills) == ["commit", "pdf"]
    assert "PDF 步骤" in next(skill["body"] for skill in skills if skill["name"] == "pdf")


def test_parses_invocation_flags_with_absent_defaults(tmp_path):
    for name, flag in (("manual", "disable-model-invocation: true\n"),
                       ("autoonly", "user-invocable: false\n"), ("plain", "")):
        (tmp_path / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: d\n{flag}---\n正文", encoding="utf-8"
        )
    skills = {skill["name"]: skill for skill in asyncio.run(loadSkills(tmp_path))}
    assert skills["manual"]["modelInvokable"] is False
    assert skills["autoonly"]["userInvocable"] is False
    assert "modelInvokable" not in skills["plain"]
    assert "userInvocable" not in skills["plain"]


def test_captures_when_to_use_and_directory_slug(tmp_path):
    (tmp_path / "brainstorming").mkdir()
    (tmp_path / "brainstorming" / "SKILL.md").write_text(
        "---\nname: Brainstorming Ideas Into Designs\ndescription: Socratic refinement\n"
        "when_to_use: before writing code for any feature\n---\n正文", encoding="utf-8"
    )
    skill = asyncio.run(loadSkills(tmp_path))[0]
    assert skill["name"] == "Brainstorming Ideas Into Designs"
    assert skill["whenToUse"] == "before writing code for any feature"
    assert skill["slug"] == "brainstorming"


def test_parses_paths_with_commas_spaces_brackets_and_quotes(tmp_path):
    (tmp_path / "swift.md").write_text(
        '---\nname: swift\ndescription: x\npaths: ["**/*.swift", "**/*.m"]\n---\n正文',
        encoding="utf-8",
    )
    (tmp_path / "plain.md").write_text(
        "---\nname: plain\ndescription: x\n---\n正文", encoding="utf-8"
    )
    skills = {skill["name"]: skill for skill in asyncio.run(loadSkills(tmp_path))}
    assert skills["swift"]["paths"] == ["**/*.swift", "**/*.m"]
    assert "paths" not in skills["plain"]


def test_catalog_formats_trigger_and_different_slug():
    output = skillCatalogLines([{
        "name": "Debugging", "description": "系统化调试", "whenToUse": "出错时",
        "slug": "systematic-debugging",
    }])
    assert "Debugging" in output
    assert "系统化调试" in output
    assert "何时用:出错时" in output
    assert "调用名 systematic-debugging" in output


def test_catalog_excludes_manual_only_and_namespaces_plugin():
    output = skillCatalogLines([
        {"name": "手动", "description": "x", "modelInvokable": False},
        {"name": "Foo", "description": "y", "slug": "foo", "namespace": "sp"},
    ])
    assert "手动" not in output
    assert "调用名 sp:foo" in output


def test_catalog_limits_description_and_trigger_to_220_characters():
    output = skillCatalogLines([{"name": "N", "description": "d" * 500}])
    assert len(output) < 240


def test_user_call_matches_slug_name_namespace_and_excludes_auto_only():
    skills = [
        {"name": "TDD", "description": "d", "slug": "tdd", "body": "b1", "dir": ""},
        {"name": "Auto Only", "description": "d", "slug": "autoonly", "body": "b2", "dir": "",
         "userInvocable": False},
        {"name": "Plug", "description": "d", "slug": "plug", "namespace": "sp",
         "body": "b3", "dir": ""},
    ]
    assert findUserInvocableSkill(skills, "tdd")["name"] == "TDD"
    assert findUserInvocableSkill(skills, "TDD")["name"] == "TDD"
    assert findUserInvocableSkill(skills, "sp:plug")["name"] == "Plug"
    assert findUserInvocableSkill(skills, "autoonly") is None
    assert findUserInvocableSkill(skills, "nope") is None


def test_same_real_file_loaded_through_two_paths_is_only_kept_once(tmp_path):
    real = tmp_path / "real"
    (real / "tdd").mkdir(parents=True)
    (real / "tdd" / "SKILL.md").write_text(
        "---\nname: tdd\ndescription: x\n---\n正文", encoding="utf-8"
    )
    link_root = tmp_path / "linkroot"
    link_root.mkdir()
    alias = link_root / "tdd-alias"
    if os.name == "nt":
        # 对应来源目录symlink fixture；junction不要求Windows符号链接权限。
        subprocess.run([os.environ["COMSPEC"], "/d", "/c", "mklink", "/J", str(alias), str(real / "tdd")],
                       check=True, capture_output=True)
    else:
        alias.symlink_to(real / "tdd", target_is_directory=True)
    skills = asyncio.run(loadSkills(real, link_root))
    assert len([skill for skill in skills if "正文" in skill["body"]]) == 1
