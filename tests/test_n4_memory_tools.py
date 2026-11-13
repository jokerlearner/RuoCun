"""Frozen MemoryRead and MemoryWrite tests against native Markdown files."""

import asyncio

import pytest

from ruocun.config.compat import DEFAULT_COMPATIBILITY
from ruocun.memory.secrets import findSecrets, redactSecrets
from ruocun.memory.store import MemoryStore, slug
from ruocun.memory.types import newMemory
from ruocun.tools.memory_read import makeMemoryReadTool
from ruocun.tools.memory_write import makeMemoryWriteTool
from ruocun.tools.types import ToolContext

TODAY = "2026-06-07"


@pytest.fixture
def memory(tmp_path):
    cwd, user = tmp_path / "project", tmp_path / "user"
    cwd.mkdir()
    store = MemoryStore(cwd, user, DEFAULT_COMPATIBILITY, today=lambda: TODAY)
    return store, makeMemoryReadTool(store), makeMemoryWriteTool(store), ToolContext(str(cwd)), user


@pytest.mark.parametrize(("query", "name", "text", "scope", "kind", "importance", "expected"), [
    ("emoji-skLabelNode-显示问号", "emoji-skLabelNode-显示问号", "emoji 用 SKLabelNode 会显示?,需 UIGraphicsImageRenderer",
     "project", "procedural", 8, "[procedural·重8·命中0]\nemoji 用 SKLabelNode 会显示?,需 UIGraphicsImageRenderer"),
    ("选项式", "用户偏好选项式引导", "用户偏好结构化选项,而非开放式提问", "user", "user", 5, "结构化选项"),
    ("立体声 crash", "avaudioengine-format-nil", "AVAudioEngine 用 format:nil 会自动协商为立体声,单声道 buffer 会 crash",
     "knowledge", "procedural", 5, "AVAudioEngine"),
    ("跨项目技术", "k1", "知识库里的跨项目技术事实", "knowledge", "procedural", 5, "知识库里的跨项目"),
    ("完全无关的量子物理", None, "", "project", "semantic", 5, "(暂无记忆)"),
])
def test_source_memory_read_exact_partial_and_across_scopes(memory, query, name, text, scope, kind, importance, expected):
    store, read, _, ctx, _ = memory

    async def scenario():
        if name is not None:
            await store.upsert(scope, newMemory(name=name, text=text, type=kind, today="2026-06-18", importance=importance))
        assert expected in await read.handler({"query": query}, ctx)

    asyncio.run(scenario())


def test_write_records_project_markdown(memory):
    store, _, write, ctx, _ = memory
    assert asyncio.run(write.handler({"text": "本项目用 vitest"}, ctx)) == "已记住(项目级):本项目用 vitest"
    file, = (store.cwd / ".ruocun" / "memory").glob("*.md")
    assert "type: semantic" in file.read_text(encoding="utf-8")
    assert "本项目用 vitest" in file.read_text(encoding="utf-8")


def test_procedural_write_records_knowledge_source_hash(memory):
    store, _, write, ctx, user = memory
    (store.cwd / "package.json").write_text('{"packageManager":"pnpm@9"}', encoding="utf-8")
    result = asyncio.run(write.handler({"text": "项目用 pnpm", "type": "procedural", "source": "package.json"}, ctx))
    assert result == "已记住(知识库):项目用 pnpm"
    file, = (user / "knowledge").glob("*.md")
    saved = file.read_text(encoding="utf-8")
    assert "type: procedural" in saved and "source: package.json" in saved
    assert "sourceHash: " in saved and "origin: project" in saved


@pytest.mark.parametrize("same_title", [True, False])
def test_write_deduplicates_only_equal_titles(memory, same_title):
    store, _, write, ctx, _ = memory

    async def scenario():
        await write.handler({"title": "包管理器 A", "text": "项目用 pnpm 安装依赖"}, ctx)
        result = await write.handler({
            "title": "包管理器 A" if same_title else "包管理器 B",
            "text": "项目用 pnpm 安装依赖包",
        }, ctx)
        assert ("已更新" if same_title else "已记住") in result
        assert len(await store.load()) == (1 if same_title else 2)

    asyncio.run(scenario())


def test_write_delete_removes_existing_file(memory):
    store, _, write, ctx, _ = memory

    async def scenario():
        await write.handler({"title": "临时事实", "text": "稍后要删"}, ctx)
        assert "已删除记忆" in await write.handler({"title": "临时事实", "delete": True}, ctx)
        assert not (store.cwd / ".ruocun" / "memory" / f"{slug('临时事实')}.md").exists()

    asyncio.run(scenario())


@pytest.mark.parametrize(("title", "expected"), [(None, "删除失败"), ("不存在的", "未找到匹配记忆")])
def test_write_delete_missing_title_or_target(memory, title, expected):
    _, _, write, ctx, _ = memory
    args = {"delete": True}
    if title:
        args["title"] = title
    assert expected in asyncio.run(write.handler(args, ctx))


def test_write_declaration_preserves_plan_auto_and_marks_actual_persistent_effect(memory):
    _, read, write, _, _ = memory
    assert (write.name, write.capability, write.approval, write.shouldDefer, write.persistentEffect) == (
        "MemoryWrite", "plan", "auto", False, True,
    )
    assert (read.name, read.capability, read.approval, read.schema["required"]) == (
        "MemoryRead", "read", "auto", ["query"],
    )
    assert write.schema["required"] == []


def test_frozen_secret_scanner_detects_credentials_and_refuses_memory_write(memory, monkeypatch):
    store, _, write, ctx, _ = memory
    samples = ("AKIA" + "1234567890ABCDEF", "-----BEGIN OPENSSH PRIVATE KEY-----",
               'token = "abcdefgh12345678"', "ghp_" + "a" * 36, "use the " + "sk-" + "a" * 30 + " key")
    assert all(findSecrets(text) for text in samples)

    async def hash_was_reached(*args):
        pytest.fail("credential rejection must happen before reading a source")

    monkeypatch.setattr("ruocun.tools.memory_write.hashMemorySource", hash_was_reached)
    for field in ("text", "title", "source"):
        args = {"text": "用户偏好清晰说明", "source": "fixture.txt", field: samples[-1]}
        response = asyncio.run(write.handler(args, ctx))
        assert "拒绝写入记忆" in response and "sk- 风格密钥" in response
        assert samples[-1] not in response
    assert not (store.cwd / ".ruocun").exists()


def test_frozen_secret_scanner_leaves_normal_text_unchanged():
    for text in ("the api returns a json object", "用户偏好 TypeScript,喜欢简洁实现", "const x = 1; // a short token"):
        assert findSecrets(text) == []


def test_frozen_secret_redaction_replaces_value():
    value = "AKIA" + "1234567890ABCDEF"
    assert redactSecrets("key " + value + " here") == "key [已隐去:AWS Access Key] here"
