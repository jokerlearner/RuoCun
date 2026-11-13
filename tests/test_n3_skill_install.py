"""冻结 install.test.ts / skill_install.test.ts 及目录发布接缝。"""

import asyncio
import os
import subprocess
import threading
from pathlib import Path

from ruocun.platform.process_tree import ForegroundResult
from ruocun.skills.install import installSkills
from ruocun.tools.skill_install import makeSkillInstallTool
from ruocun.tools.types import ToolContext


def _skill(root: Path, name: str, body: str = "用 `Read` 工具") -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_bytes(f"---\nname: {name}\ndescription: x\n---\n{body}\n".encode())
    return directory


def test_install_copies_valid_skills_and_warns_about_invalid_and_bundled(tmp_path):
    source, workspace, user_root = tmp_path / "source", tmp_path / "workspace", tmp_path / "user"
    skill = _skill(source / "skills", "simplify", "用 `Read` 和 superpowers:debug")
    body = (skill / "SKILL.md").read_bytes()
    (skill / "assets").mkdir()
    (skill / "assets/icon.bin").write_bytes(b"\x00\x01\xff")
    git_admin = ".GIT" if os.name == "nt" else ".git"
    (skill / git_admin).mkdir()
    (skill / git_admin / "config").write_text("synthetic git metadata", encoding="utf-8")
    invalid = source / "skills" / "nofm"
    invalid.mkdir()
    (invalid / "SKILL.md").write_text("没有 frontmatter 的正文", encoding="utf-8")
    target = workspace / ".ruocun" / "skills" / "simplify"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_bytes(b"prior body")
    (target / "old-resource.txt").write_bytes(b"prior resource")
    result = asyncio.run(installSkills(str(source), "project", workspace, user_root, threading.Event()))
    assert result.installed == ("simplify",) and not result.error
    assert (target / "SKILL.md").read_bytes() == body == (skill / "SKILL.md").read_bytes()
    assert (target / "assets/icon.bin").read_bytes() == b"\x00\x01\xff"
    assert not (target / git_admin).exists()
    assert (target / "old-resource.txt").read_bytes() == b"prior resource"
    assert not (target.parent / "nofm").exists()
    report = result.format()
    assert "安装 1 个技能" in report and "缺 frontmatter" in report
    assert "自动按用途转换工具名" in report and "simplify" in report
    assert "覆盖了内置" in report and "/skills" in report


def test_install_reports_no_skill_markdown(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    result = asyncio.run(installSkills(str(source), "project", tmp_path / "ws", tmp_path / "user", threading.Event()))
    assert "未找到" in result.format() and not result.installed


def test_tool_requires_approval_and_is_deferred(tmp_path):
    tool = makeSkillInstallTool(tmp_path)
    assert tool.capability == "exec" and tool.approval == "required" and tool.shouldDefer
    assert tool.schema["required"] == ["source"]
    assert tool.schema["properties"]["source"]["minLength"] == 1
    assert tool.schema["properties"]["scope"]["enum"] == ["user", "project"]


def test_tool_installs_locally_and_registers_confirmed_scope(tmp_path):
    src, ws = tmp_path / "src", tmp_path / "ws"
    ws.mkdir()
    skill = _skill(src / "skills", "demo")
    confirmed = []
    ctx = ToolContext(str(ws), onSkillsInstalled=confirmed.append)
    tool = makeSkillInstallTool(tmp_path / "user")
    report = asyncio.run(tool.handler({"source": str(src), "scope": "project"}, ctx))
    assert "安装 1 个技能" in report and confirmed == ["project"]
    assert (ws / ".ruocun/skills/demo/SKILL.md").read_bytes() == (skill / "SKILL.md").read_bytes()
    if os.name == "nt":
        alias = tmp_path / "source-alias"
        subprocess.run([os.environ["COMSPEC"], "/d", "/c", "mklink", "/J", str(alias), str(src)],
                       check=True, capture_output=True)
        try:
            rejected = asyncio.run(tool.handler({"source": str(alias), "scope": "project"}, ctx))
            assert rejected.startswith("Error:") and confirmed == ["project"]
        finally:
            alias.rmdir()


def test_git_argv_clone_preferred_skills_and_default_user_scope(tmp_path, monkeypatch):
    cloned = []
    source = "https://synthetic.invalid/repo.git"
    workspace, user_root = tmp_path / "ws", tmp_path / "user"
    workspace.mkdir()
    ctx = ToolContext(str(workspace))
    git = tmp_path / "git.exe"
    monkeypatch.setattr("ruocun.skills.install.shutil.which", lambda executable: str(git))

    def runner(argv, cwd, signal, *, environ=None):
        assert argv[:-1] == [str(git), "clone", "--depth", "1", "--", source]
        assert Path(cwd) == workspace and signal is ctx.signal
        assert environ["GIT_TERMINAL_PROMPT"] == "0"
        clone = Path(argv[-1])
        cloned.append(clone)
        _skill(clone, "excluded")
        _skill(clone / "skills", "demo")
        return ForegroundResult("", "", 0, False, 0)

    report = asyncio.run(makeSkillInstallTool(user_root, run_git=runner).handler({"source": source}, ctx))
    assert "安装 1 个技能" in report and "用户级" in report
    assert (user_root / "skills/demo/SKILL.md").is_file()
    assert not (user_root / "skills/excluded").exists()
    assert len(cloned) == 1 and not cloned[0].exists()


def test_failed_publish_restores_complete_old_directory(tmp_path, monkeypatch):
    src, ws = tmp_path / "source", tmp_path / "workspace"
    _skill(src, "same", "new body")
    original = _skill(ws / ".ruocun/skills", "same", "old body")
    content = (original / "SKILL.md").read_bytes()
    rename = Path.rename

    def fail_publish(self, dest):
        if Path(dest) == original and self.name == "candidate":
            raise OSError("synthetic publish failure")
        return rename(self, dest)

    monkeypatch.setattr(Path, "rename", fail_publish)
    result = asyncio.run(installSkills(str(src), "project", ws, tmp_path / "user", threading.Event()))
    assert result.error and not result.installed
    assert (original / "SKILL.md").read_bytes() == content
    assert [p.name for p in original.parent.iterdir()] == ["same"]
    assert not list(original.parent.parent.glob(".skill-stage-*"))
