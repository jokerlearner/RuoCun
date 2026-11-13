"""Frozen store.test.ts CRUD and D09 native/compatible data boundaries."""

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from ruocun.config.compat import (
    DEFAULT_COMPATIBILITY,
    Compatibility,
    CompatibilitySource,
)
from ruocun.memory.frontmatter import serializeMemory
from ruocun.memory.store import (
    MemoryStore,
    keepKnowledgeForProject,
    projectIdOf,
    routeScope,
    slug,
)
from ruocun.memory.types import newMemory
from ruocun.tools.types import ToolRejected

TODAY = "2026-06-07"


def record(name, text="旧", **changes):
    return replace(newMemory(name=name, text=text, type="procedural", today=TODAY), **changes)


@pytest.fixture
def memory(tmp_path):
    cwd, user = tmp_path / "repo", tmp_path / "user"
    cwd.mkdir()
    store = MemoryStore(cwd, user, DEFAULT_COMPATIBILITY, today=lambda: TODAY)
    return store, cwd / ".ruocun" / "memory", user


def test_route_scope_by_type():
    assert [routeScope(kind) for kind in ("user", "feedback", "procedural", "semantic", "episodic")] == [
        "user", "user", "knowledge", "project", "project",
    ]


def test_project_id_uses_slug_of_directory_name():
    assert projectIdOf(Path("/Users/x/ClaudeProject/dao-code")) == "dao-code"
    assert projectIdOf(Path("/Users/x/My App")) == "my-app"


@pytest.mark.parametrize(("origin", "locked", "expected"), [
    ("dao-code", False, True), ("kids-game", False, False),
    (None, False, False), (None, True, True), ("kids-game", True, True),
])
def test_knowledge_filter_preserves_project_origin_and_locked(origin, locked, expected):
    assert keepKnowledgeForProject(record("note", origin=origin, locked=locked), "dao-code") is expected


def test_slug_source_examples():
    assert slug("Hello World!") == "hello-world"
    assert slug("提交不加 AI 署名") == "提交不加-ai-署名"
    assert slug("") == "mem"
    assert slug("a" * 41) == "a" * 40


def test_same_name_updates_in_place_with_max_importance_and_uses(memory):
    store, directory, user = memory
    assert not directory.exists() and not user.exists()

    async def scenario():
        initial = record("pnpm", "项目用 pnpm")
        assert (await store.upsert("project", initial)).action == "added"
        candidate = replace(initial, text="项目用 pnpm 安装依赖", importance=8, lastUsed="2026-06-08")
        assert (await store.upsert("project", candidate)).action == "updated"
        item, = await store.load()
        assert (item.memory.text, item.memory.importance, item.memory.uses) == ("项目用 pnpm 安装依赖", 8, 1)
        assert item.path == directory / "pnpm.md"
        assert item.scope == "project" and item.source is None
        assert not user.exists()  # first project write does not create user/knowledge roots

    asyncio.run(scenario())


def test_different_names_do_not_fuzzy_merge(memory):
    store, _, _ = memory

    async def scenario():
        await store.upsert("project", record("a", "用户用 pnpm 管理依赖"))
        assert (await store.upsert("project", record("b", "用户用 pnpm 作为包管理器"))).action == "added"
        assert {entry.memory.name for entry in await store.load()} == {"a", "b"}

    asyncio.run(scenario())


def test_locked_same_name_addition_preserves_original_bytes(memory):
    store, directory, _ = memory

    async def scenario():
        await store.upsert("project", record("x", locked=True))
        original = (directory / "x.md").read_bytes()
        result = await store.upsert("project", record("x", "新"))
        assert result.action == "added"
        assert result.name != "x"
        assert (directory / "x.md").read_bytes() == original
        assert {entry.memory.text for entry in await store.load()} == {"旧", "新"}

    asyncio.run(scenario())


def test_title_updates_on_existing_name(memory):
    store, _, _ = memory

    async def scenario():
        await store.upsert("project", record("t", title="旧标题"))
        assert (await store.upsert("project", record("t", "y", title="新标题"))).action == "updated"
        entry, = await store.load()
        assert entry.memory.title == "新标题"

    asyncio.run(scenario())


@pytest.mark.parametrize("locked", [False, True])
def test_same_title_dedup_prunes_only_unlocked_legacy_duplicates(memory, locked):
    store, directory, _ = memory

    async def scenario():
        initial = record("impl-status", "v1", title="完成状态")
        duplicate = record("proj-status-14-commit", "v2", title="完成状态", locked=locked)
        await store.upsert("project", initial)
        # Existing title drift is created by a hand edit, bypassing upsert.
        old_file = directory / f"{duplicate.name}.md"
        old_bytes = serializeMemory(duplicate).encode("utf-8")
        old_file.write_bytes(old_bytes)
        result = await store.upsert("project", record(slug("完成状态"), "v3", title="完成状态"))
        assert result.action == "updated"
        entries = await store.load()
        assert "v3" in {entry.memory.text for entry in entries}
        if locked:
            assert old_file.read_bytes() == old_bytes
        else:
            assert len(entries) == 1

    asyncio.run(scenario())


def test_d09_explicit_compatible_provenance_and_bad_native_file_stay_untouched(memory, tmp_path):
    _, directory, user = memory
    compat_dir = tmp_path / "old-memories"
    compat_dir.mkdir()
    raw = serializeMemory(record("same", "兼容材料")).encode("utf-8")
    (compat_dir / "same.md").write_bytes(raw)
    source = CompatibilitySource("old-user", "user", "memory", str(compat_dir))
    store = MemoryStore(directory.parents[1], user, Compatibility(1, (source,)), today=lambda: TODAY)

    async def scenario():
        entry, = await store.load()
        assert entry.scope == "user" and entry.source == source
        with pytest.raises(ToolRejected, match="只读"):
            await store.upsert("project", record("same", "禁止自动复制"))
        deleted = await store.delete("same")
        assert deleted.removed == () and deleted.readOnly
        assert (compat_dir / "same.md").read_bytes() == raw
        assert not directory.exists()
        await store.upsert("project", record("other"))
        original = directory / "other.md"
        before = original.read_bytes()
        with pytest.raises(ToolRejected, match="元数据"):
            await store.upsert("project", record("other", "多行\n正文", title="原题\n---\n后缀"))
        assert original.read_bytes() == before
        await store.upsert("project", record("other", "多行\n正文"))
        assert (await store.load(("project",)))[0].memory.text == "多行\n正文"
        target = directory / "bad.md"
        target.write_bytes(b"malformed fixture")
        with pytest.raises(ToolRejected, match="保留"):
            await store.upsert("project", record("bad", "不可覆盖"))
        assert target.read_bytes() == b"malformed fixture"

    asyncio.run(scenario())


def test_delete_by_title_matches_across_native_directories(memory):
    store, directory, user = memory

    async def scenario():
        await store.upsert("project", record("first", title="包管理器"))
        await store.upsert("user", record("second", title="不同标题"))
        (user / "memory" / "second.md").write_text(
            serializeMemory(record("second", title="包管理器")), encoding="utf-8",
        )
        removed = await store.delete("包管理器")
        assert removed.removed == ("first", "second")
        assert not (directory / "first.md").exists()
        assert not (user / "memory" / "second.md").exists()

    asyncio.run(scenario())


def test_delete_by_name_removes_the_file(memory):
    store, directory, _ = memory

    async def scenario():
        await store.upsert("project", record("target", title="备用标题"))
        assert (await store.delete("target")).removed == ("target",)
        assert not (directory / "target.md").exists()

    asyncio.run(scenario())


def test_delete_preserves_locked_file(memory):
    store, directory, _ = memory

    async def scenario():
        await store.upsert("project", record("locked", locked=True))
        original = (directory / "locked.md").read_bytes()
        removed = await store.delete("locked")
        assert removed.removed == () and removed.locked
        assert (directory / "locked.md").read_bytes() == original

    asyncio.run(scenario())


def test_delete_no_match_returns_empty(memory):
    store, directory, _ = memory
    assert asyncio.run(store.delete("不存在")).removed == ()
    assert not directory.exists()


def test_loading_skips_superseded_file_without_removing_it(memory):
    store, directory, _ = memory

    async def scenario():
        await store.upsert("project", record("old", status="superseded", supersededBy="new"))
        assert await store.load() == []
        entry, = await store.load(includeSuperseded=True)
        assert entry.memory.supersededBy == "new"
        assert (directory / "old.md").is_file()

    asyncio.run(scenario())
