"""冻结index.ts启动Skills装配的D09最小适配，非35动态发现矩阵。"""

import asyncio

from ruocun.config.compat import (
    DEFAULT_COMPATIBILITY,
    Compatibility,
    CompatibilitySource,
)
from ruocun.skills import runtime
from ruocun.skills.runtime import loadRuntimeSkills


def _skill(directory, slug, body, *, paths=""):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.md").write_text(
        f"---\nname: {slug}\ndescription: fixture\n{paths}---\n{body}", encoding="utf-8"
    )


def test_d09_directory_order_and_disk_override_of_core(tmp_path):
    cwd, user_root = tmp_path / "project", tmp_path / "user"
    compat_user, compat_project = tmp_path / "old-user", tmp_path / "old-project"
    directories = [compat_user, user_root / "skills", compat_project, cwd / ".ruocun" / "skills"]
    for index, directory in enumerate(directories):
        _skill(directory, "rank", f"layer-{index}")
    _skill(directories[1], "user-rank", "native-user")
    _skill(directories[0], "user-rank", "compatible-user")
    _skill(directories[1], "project-rank", "native-user")
    _skill(directories[2], "project-rank", "compatible-project")
    _skill(directories[3], "simplify", "project simplify")
    _skill(directories[2], "disabled-skill", "disabled body")
    _skill(directories[2], "conditional-skill", "conditional body", paths="paths: **/*.swift\n")
    (user_root / "skills-disabled.json").write_text('["disabled-skill"]', encoding="utf-8")
    compatibility = Compatibility(1, (
        CompatibilitySource("u", "user", "skills", str(compat_user)),
        CompatibilitySource("p", "project", "skills", str(compat_project), str(cwd)),
        CompatibilitySource("p-last", "project", "skills", str(compat_project), str(cwd)),
    ))
    states = {}
    result = asyncio.run(loadRuntimeSkills(cwd, user_root, compatibility, sourceStates=states))
    by_name = {skill["name"]: skill for skill in result}
    assert by_name["rank"]["body"] == "layer-3"
    assert by_name["user-rank"]["body"] == "native-user"
    assert by_name["project-rank"]["body"] == "compatible-project"
    assert by_name["simplify"]["body"] == "project simplify"
    assert len([skill for skill in result if skill["name"] == "simplify"]) == 1
    assert by_name["debug"]["dir"] == ""
    assert by_name["debug"]["slug"] == "debug"
    assert states == {
        "u": "生效0项；被覆盖2项；禁用0项；paths未匹配0项",
        "p": "生效0项；被覆盖4项；禁用0项；paths未匹配0项",
        "p-last": "生效1项；被覆盖1项；禁用1项；paths未匹配1项",
    }


def test_no_skills_disables_disk_and_core(tmp_path):
    cwd, user_root = tmp_path / "project", tmp_path / "user"
    _skill(cwd / ".ruocun" / "skills", "disk", "disk body")
    assert asyncio.run(loadRuntimeSkills(cwd, user_root, DEFAULT_COMPATIBILITY, disabled=True)) == []


def test_native_disabled_names_filter_disk_and_core_without_writing_sources(tmp_path):
    cwd, user_root, old_root = tmp_path / "project", tmp_path / "user", tmp_path / "old"
    _skill(user_root / "skills", "diskoff", "disabled disk body")
    _skill(old_root / "skills", "compatible", "compatible body")
    native_disabled = user_root / "skills-disabled.json"
    old_disabled = old_root / "skills-disabled.json"
    native_disabled.write_text('["debug", "diskoff"]', encoding="utf-8")
    old_disabled.write_text('["verify"]', encoding="utf-8")
    before = {file: file.read_bytes() for file in (native_disabled, old_disabled, old_root / "skills" / "compatible.md")}
    compatibility = Compatibility(1, (
        CompatibilitySource("u", "user", "skills", str(old_root / "skills")),
    ))
    skills = asyncio.run(loadRuntimeSkills(cwd, user_root, compatibility))
    names = {skill["name"] for skill in skills}
    assert "debug" not in names
    assert "diskoff" not in names
    assert {"compatible", "verify"} <= names
    assert all(file.read_bytes() == content for file, content in before.items())


def test_startup_paths_match_once_and_do_not_fall_back_to_overridden_core(tmp_path):
    cwd, user_root = tmp_path / "project", tmp_path / "user"
    skill_dir = cwd / ".ruocun" / "skills"
    _skill(skill_dir, "a", "body of a")
    _skill(skill_dir, "b", "body of b", paths="paths: **/*.ts\n")
    _skill(skill_dir, "c", "body of c", paths="paths: **/*.py\n")
    _skill(skill_dir, "simplify", "disk body", paths="paths: **/*.py\n")
    (cwd / "src").mkdir()
    (cwd / "src" / "foo.ts").write_text("fixture", encoding="utf-8")
    result = asyncio.run(loadRuntimeSkills(cwd, user_root, DEFAULT_COMPATIBILITY))
    selected = [skill for skill in result if skill["name"] in {"a", "b", "c", "simplify"}]
    assert [skill["name"] for skill in selected] == ["a", "b"]
    assert len([skill for skill in result if skill["name"] == "b"]) == 1
    assert "paths" not in next(skill for skill in result if skill["name"] == "b")


def test_startup_matching_stops_at_source_4000_file_limit(tmp_path, monkeypatch):
    cwd, user_root = tmp_path / "project", tmp_path / "user"
    _skill(user_root / "skills", "inside", "inside body", paths="paths: inside.ts\n")
    _skill(user_root / "skills", "outside", "outside body", paths="paths: outside.py\n")

    def files(_):
        for index in range(3999):
            yield f"fixture-{index}.txt", f"fixture-{index}.txt"
        yield "inside.ts", "inside.ts"
        yield "outside.py", "outside.py"

    monkeypatch.setattr(runtime, "walkFiles", files)
    result = asyncio.run(loadRuntimeSkills(cwd, user_root, DEFAULT_COMPATIBILITY))
    names = {skill["name"] for skill in result}
    assert "inside" in names
    assert "outside" not in names
