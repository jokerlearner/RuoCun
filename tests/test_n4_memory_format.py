"""Frozen memory types, frontmatter, hash and source validation assertions."""

import asyncio
from dataclasses import replace

import pytest

from ruocun.memory.frontmatter import parseMemoryFile, serializeMemory
from ruocun.memory.hash import contentHash
from ruocun.memory.types import newMemory
from ruocun.memory.validate import hashMemorySource, validateMemory

TODAY = "2026-06-07"
OLD_MARKDOWN = (
    "---\nname: y\ntype: user\nimportance: 3\ncreated: 2026-06-01\n"
    "lastUsed: 2026-06-02\nstatus: active\n---\n用户偏好 TypeScript\n"
)


def test_new_memory_fills_defaults():
    item = newMemory(name="uses-pnpm", text="用 pnpm", type="semantic", today=TODAY)
    assert (item.name, item.text, item.type, item.importance) == ("uses-pnpm", "用 pnpm", "semantic", 5)
    assert (item.status, item.created, item.lastUsed, item.locked) == ("active", TODAY, TODAY, False)


def test_frontmatter_serializes_then_parses_back_equal():
    item = newMemory(name="x", text="用 pnpm 安装", type="procedural", today=TODAY, importance=7,
                     source="package.json#packageManager", sourceHash="abc")
    text = serializeMemory(item)
    assert text.startswith("---\n")
    assert parseMemoryFile("x", text) == item


def test_frontmatter_tolerates_missing_optional_fields():
    item = parseMemoryFile("y", OLD_MARKDOWN)
    assert item is not None
    assert (item.type, item.text, item.source) == ("user", "用户偏好 TypeScript", None)
    assert parseMemoryFile("y", OLD_MARKDOWN.replace("\n", "\r\n")) == item


def test_frontmatter_returns_none_on_garbage():
    assert parseMemoryFile("z", "no frontmatter here") is None


def test_frontmatter_round_trips_origin():
    item = newMemory(name="k", text="cli-highlight 返回纯文本", type="procedural",
                     today="2026-07-01", origin="dao-code")
    assert item.origin == "dao-code"
    text = serializeMemory(item)
    assert "origin: dao-code" in text
    recovered = parseMemoryFile("k", text)
    assert recovered is not None and recovered.origin == "dao-code"


def test_frontmatter_round_trips_title():
    item = newMemory(name="no-ai-sig", title="提交不加 AI 署名",
                     text="提交一律不加署名。为什么:用户要求。怎么用:不写 Co-Authored-By。",
                     type="feedback", today="2026-06-25", importance=9)
    assert item.title == "提交不加 AI 署名"
    assert parseMemoryFile("no-ai-sig", serializeMemory(item)) == item


def test_frontmatter_accepts_older_file_without_title():
    item = parseMemoryFile("y", OLD_MARKDOWN)
    assert item is not None and item.title is None


def test_content_hash_is_stable_and_sensitive():
    assert contentHash("abc") == "ba7816bf8f01cfea"
    assert contentHash("abd") != contentHash("abc")


@pytest.mark.parametrize(("source", "file_content", "hash_text", "valid_until", "expected"), [
    (None, None, None, None, "ok"),
    ("user_stated", None, None, None, "ok"),
    ("inferred", None, None, None, "ok"),
    ("user_stated", None, None, "2026-06-05", "stale"),
    ("inferred", None, None, "2026-06-05", "stale"),
    ("gone.txt", None, "OLD", None, "stale"),
    ("f.txt", "NEW", "OLD", None, "changed"),
    ("f.txt", "SAME", "SAME", None, "ok"),
    (None, None, None, "2026-06-05", "stale"),
])
def test_source_validation_verdict(tmp_path, source, file_content, hash_text, valid_until, expected):
    if file_content is not None:
        (tmp_path / source).write_text(file_content, encoding="utf-8")
    item = newMemory(name="c", text="x", type="semantic", today=TODAY,
                     source=source, sourceHash=contentHash(hash_text) if hash_text is not None else None)
    assert asyncio.run(validateMemory(replace(item, validUntil=valid_until), tmp_path, TODAY)) == expected


@pytest.mark.parametrize("source", ["user_stated", "inferred"])
def test_evidence_labels_are_not_hashed_but_explicit_paths_are_validated(tmp_path, source):
    file = tmp_path / source
    file.write_text("original", encoding="utf-8")
    assert asyncio.run(hashMemorySource(tmp_path, source)) is None
    path = f"./{source}"
    digest = asyncio.run(hashMemorySource(tmp_path, path))
    assert digest == contentHash("original")
    item = newMemory(name="file-fact", text="fact", type="semantic", today=TODAY,
                     source=path, sourceHash=digest)
    assert asyncio.run(validateMemory(item, tmp_path, TODAY)) == "ok"
    file.write_text("changed", encoding="utf-8")
    assert asyncio.run(validateMemory(item, tmp_path, TODAY)) == "changed"
    file.unlink()
    assert asyncio.run(validateMemory(item, tmp_path, TODAY)) == "stale"
