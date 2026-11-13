"""冻结 discover.test.ts 的语义迁移，以及启动池与确认边界。"""

import asyncio
from pathlib import Path

import pytest

from ruocun.config.compat import (
    DEFAULT_COMPATIBILITY,
    Compatibility,
    CompatibilitySource,
)
from ruocun.skills.discover import SkillDiscovery
from ruocun.skills.runtime import loadRuntimeSkills
from ruocun.skills.types import Skill


def _skill(name: str, paths: list[str] | None = None) -> Skill:
    skill: Skill = {"name": name, "slug": name.lower(), "description": f"skill {name}",
                    "body": f"body of {name}", "dir": "/tmp"}
    if paths is not None:
        skill["paths"] = paths
    return skill


def _prepare(discovery, paths, active, disabled=frozenset()):
    return asyncio.run(discovery.prepare(paths, active, disabled=disabled))


@pytest.mark.parametrize(("skills", "visible", "pending"), [
    ([_skill("a"), _skill("b", ["*.ts"]), _skill("c", ["src/**"])], ["a"], 2),
    ([_skill("a", [])], ["a"], 0),
    ([_skill("a"), _skill("b")], ["a", "b"], 0),  # b 是启动扫描命中后清除了 paths 的副本。
])
def test_init_conditional_pool(tmp_path, skills, visible, pending):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    active = discovery.initConditionalPool(skills)
    assert [skill["name"] for skill in active] == visible
    assert discovery.pending_count == pending


@pytest.mark.parametrize(("skills", "paths", "names", "pending"), [
    ([_skill("ts-skill", ["**/*.ts"]), _skill("py-skill", ["**/*.py"])], ["src/foo.ts"], ["ts-skill"], 1),
    ([_skill("ts-skill", ["*.ts"])], ["src/foo.py"], [], 1),
    ([_skill("ts-skill", ["*.ts"])], ["a.py", "b.ts"], ["ts-skill"], 0),
    ([_skill("ts-skill", ["*.ts"])], ["../other/dir/a.ts"], [], 1),
    ([], ["a.ts"], [], 0),
])
def test_activate_conditional_pool(tmp_path, skills, paths, names, pending):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    active = discovery.initConditionalPool(skills)
    candidate = _prepare(discovery, [str(tmp_path / path) for path in paths], active)
    assert [skill["name"] for skill in candidate.activated] == names
    discovery.confirm(candidate, active)
    assert discovery.pending_count == pending


def test_conditional_skill_activates_once(tmp_path):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    active = discovery.initConditionalPool([_skill("ts-skill", ["*.ts"])])
    first = _prepare(discovery, [str(tmp_path / "a.ts")], active)
    discovery.confirm(first, active)
    second = _prepare(discovery, [str(tmp_path / "b.ts")], active)
    assert len(first.activated) == 1
    assert not second.activated


@pytest.mark.parametrize(("parent", "create", "expected"), [
    ("sub", True, True),
    ("node_modules/pkg", True, False),
    (".", True, False),
    ("sub/deep", False, False),
])
def test_discover_directory(tmp_path, parent, create, expected):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    directory = tmp_path / parent / ".ruocun" / "skills"
    if create:
        directory.mkdir(parents=True)
    candidate = _prepare(discovery, [str(tmp_path / parent / "file.ts")], [])
    assert candidate.directories == ((directory,) if expected else ())


def test_positive_directory_cache(tmp_path):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    directory = tmp_path / "sub" / ".ruocun" / "skills"
    directory.mkdir(parents=True)
    path = str(tmp_path / "sub" / "file.ts")
    first = _prepare(discovery, [path], [])
    discovery.confirm(first, [])
    assert first.directories == (directory,)
    assert not _prepare(discovery, [path], []).directories


def test_missing_directory_can_appear_after_first_access(tmp_path):
    discovery = SkillDiscovery(tmp_path, disk_enabled=True)
    parent = tmp_path / "sub"
    parent.mkdir()
    path = str(parent / "file.ts")
    first = _prepare(discovery, [path], [])
    discovery.confirm(first, [])
    assert not first.directories
    directory = parent / ".ruocun" / "skills"
    directory.mkdir(parents=True)
    assert _prepare(discovery, [path], []).directories == (directory,)


def _put(directory, slug, *, fields="", body="synthetic body"):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.md").write_text(
        f"---\nname: {slug}\ndescription: synthetic {slug}\n{fields}---\n{body}\n", encoding="utf-8",
    )


def test_startup_and_discovery_candidates_respect_d09_and_s03(tmp_path, monkeypatch):
    cwd, user_root = tmp_path / "workspace", tmp_path / "user"
    native = cwd / ".ruocun" / "skills"
    _put(native, "pending", fields="paths: **/*.ts\n")
    _put(native, "startup", fields="paths: **/*.py\n")
    (cwd / "exists.py").touch()
    nested = cwd / "outer" / "inner"
    declared = nested / ".dao" / "skills"
    compatibility = Compatibility(1, (
        CompatibilitySource("explicit", "project", "skills", str(declared), str(cwd)),
    ))
    discovery = SkillDiscovery(cwd, disk_enabled=True)
    active = asyncio.run(loadRuntimeSkills(cwd, user_root, compatibility, discovery=discovery))
    assert discovery.pending_count == 1
    assert [skill["name"] for skill in active if skill["name"] in {"startup", "pending"}] == ["startup"]
    _put(nested / ".ruocun" / "skills", "nested", fields="paths: *.rs\n", body="deep")
    _put(nested.parent / ".ruocun" / "skills", "nested", fields="paths: *.rs\n", body="shallow")
    _put(nested / ".ruocun" / "skills", "disabled")
    _put(nested.parent / ".dao" / "skills", "unregistered")
    _put(declared, "legacy")
    path = str(nested / "new.ts")
    before = active.copy()
    is_dir = Path.is_dir

    def denied_entry(entry):
        if entry == nested / ".ruocun" / "skills" / "nested.md":
            raise PermissionError("synthetic directory entry denied")
        return is_dir(entry)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "is_dir", denied_entry)
        unreadable = _prepare(discovery, [path], active, {"disabled"})
    assert not unreadable.discovered
    assert [skill["name"] for skill in unreadable.activated] == ["pending"]
    candidate = _prepare(discovery, [path], active, {"disabled"})
    assert active == before and discovery.pending_count == 1
    assert [skill["name"] for skill in candidate.discovered] == ["nested"]
    assert candidate.discovered[0]["body"] == "shallow"
    assert [skill["name"] for skill in candidate.activated] == ["pending"]
    assert "动态发现" in candidate.catalog_messages[0] and "条件" in candidate.catalog_messages[1]
    # 放弃提案后仍能重新发现；只在确认后发布目录缓存和活列表。
    assert _prepare(discovery, [path], active, {"disabled"}) == candidate
    discovery.confirm(candidate, active)
    assert [skill["name"] for skill in active[len(before):]] == ["nested", "pending"]
    assert discovery.pending_count == 0
    off = SkillDiscovery(cwd, disk_enabled=False)
    core = asyncio.run(loadRuntimeSkills(cwd, user_root, compatibility, discovery=off))
    assert core and all(not skill["dir"] for skill in core)
    assert not asyncio.run(loadRuntimeSkills(cwd, user_root, DEFAULT_COMPATIBILITY, disabled=True, discovery=off))
    assert not _prepare(off, [path], []).directories
