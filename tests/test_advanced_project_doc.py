"""冻结project_doc.test.ts六条来源语义及D09必要显式兼容接线。"""

from ruocun.config.compat import Compatibility, CompatibilitySource
from ruocun.project_doc import loadProjectInstructions


def test_no_instruction_files_is_empty(tmp_path):
    assert loadProjectInstructions(tmp_path, userRoot=tmp_path / "native") == ""


def test_native_instructions_loaded_and_engineering_files_ignored(tmp_path):
    (tmp_path / "RUOCUN.md").write_text("产品约定", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("工程agents约定", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("工程claude约定", encoding="utf-8")
    out = loadProjectInstructions(tmp_path, userRoot=tmp_path / "native")
    assert "产品约定" in out
    assert "工程agents约定" not in out and "工程claude约定" not in out


def test_engineering_files_are_not_fallback_instructions(tmp_path):
    (tmp_path / "AGENTS.md").write_text("工程约定", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("工程约定", encoding="utf-8")
    assert loadProjectInstructions(tmp_path, userRoot=tmp_path / "native") == ""


def test_local_instruction_overlays_same_level(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "RUOCUN.md").write_text("提交规范", encoding="utf-8")
    (tmp_path / "RUOCUN.local.md").write_text("私有偏好", encoding="utf-8")
    out = loadProjectInstructions(tmp_path, userRoot=tmp_path / "native")
    assert out.index("提交规范") < out.index("私有偏好")


def test_git_ancestor_chain_is_general_then_specific(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "RUOCUN.md").write_text("根约定", encoding="utf-8")
    sub = tmp_path / "packages" / "app"
    sub.mkdir(parents=True)
    (sub / "RUOCUN.md").write_text("子包约定", encoding="utf-8")
    out = loadProjectInstructions(sub, userRoot=tmp_path / "native")
    assert out.index("根约定") < out.index("子包约定")


def test_no_git_only_reads_current_directory(tmp_path):
    (tmp_path / "RUOCUN.md").write_text("无关父级", encoding="utf-8")
    sub = tmp_path / "nested"
    sub.mkdir()
    (sub / "RUOCUN.md").write_text("当前目录", encoding="utf-8")
    out = loadProjectInstructions(sub, userRoot=tmp_path / "native")
    assert "当前目录" in out and "无关父级" not in out


def test_explicit_compatibility_and_native_priority_with_content_dedup(tmp_path):
    (tmp_path / ".git").write_text("gitdir: synthetic", encoding="utf-8")
    user = tmp_path / "native"
    user.mkdir()
    (user / "RUOCUN.md").write_text("原生用户偏好", encoding="utf-8")
    old_user = tmp_path / "legacy-user.md"
    old_user.write_text("兼容用户偏好", encoding="utf-8")
    old_project = tmp_path / "DAO.md"
    old_project.write_text("兼容项目约定", encoding="utf-8")
    (tmp_path / "RUOCUN.md").write_text("原生项目约定", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "RUOCUN.md").write_text("  兼容用户偏好 \n", encoding="utf-8")
    (sub / "RUOCUN.local.md").write_text("本级私有偏好", encoding="utf-8")
    compatibility = Compatibility(1, (
        CompatibilitySource("old-user", "user", "instructions", str(old_user)),
        CompatibilitySource("old-project", "project", "instructions", str(old_project), str(sub)),
    ))
    states = {}
    out = loadProjectInstructions(sub, userRoot=user, compatibility=compatibility, sourceStates=states)
    expected = ["兼容用户偏好", "原生用户偏好", "兼容项目约定", "原生项目约定", "本级私有偏好"]
    assert [out.index(value) for value in expected] == sorted(out.index(value) for value in expected)
    assert out.count("兼容用户偏好") == 1
    assert "old-user" in out and "old-project" in out
    assert states == {"old-user": "生效：内容已注入", "old-project": "生效：内容已注入"}
