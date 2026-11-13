"""冻结 src/tools/write_file.test.ts 的首版语义断言。"""

import asyncio
import json
from pathlib import Path

import pytest

from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext
from ruocun.tools.write_file import writeFileTool


def test_creates_new_file_without_read(tmp_path):
    accessed = []

    def observe(absolute):
        assert Path(absolute).read_text(encoding="utf-8") == "hello\nworld"
        accessed.append(absolute)

    ctx = ToolContext(str(tmp_path), onFileAccessed=observe)
    out = asyncio.run(writeFileTool.handler({"path": "new.txt", "content": "hello\nworld"}, ctx))
    assert "已写入" in out
    assert (tmp_path / "new.txt").read_text(encoding="utf-8") == "hello\nworld"
    assert accessed == [str(tmp_path / "new.txt")]


def write(ctx, path="exists.txt", content="new"):
    return asyncio.run(writeFileTool.handler({"path": path, "content": content}, ctx))


def test_creates_parents(tmp_path):
    write(ToolContext(str(tmp_path)), "a/b/c.txt", "x")
    assert (tmp_path / "a/b/c.txt").read_text(encoding="utf-8") == "x"


def test_requires_read_before_overwrite(tmp_path):
    (tmp_path / "exists.txt").write_text("old", encoding="utf-8", newline="")
    with pytest.raises(ValueError, match="先用 Read"):
        write(ToolContext(str(tmp_path)))


def test_overwrites_after_read(tmp_path):
    path = tmp_path / "exists.txt"
    path.write_text("old", encoding="utf-8", newline="")
    assert write(ToolContext(str(tmp_path), readFiles={str(path)}, lang="en")) == "Wrote exists.txt (1 lines)"
    assert path.read_text(encoding="utf-8") == "new"


def test_second_rewrite_without_execution_rejected(tmp_path):
    path = tmp_path / "compress.rs"
    path.write_text("old", encoding="utf-8", newline="")
    ctx = ToolContext(str(tmp_path), readFiles={str(path)})
    write(ctx, "compress.rs", "v1")
    assert str(path) in ctx.pendingUnverifiedWrites
    with pytest.raises(ValueError, match=r"拒绝写入.*compress\.rs.*未经命令验证"):
        write(ctx, "compress.rs", "v2 rewritten from scratch")
    assert path.read_text(encoding="utf-8") == "v1"


def test_execution_clear_allows_next_rewrite(tmp_path):
    path = tmp_path / "compress.rs"
    path.write_text("old", encoding="utf-8", newline="")
    ctx = ToolContext(str(tmp_path), readFiles={str(path)})
    write(ctx, "compress.rs", "v1")
    ctx.pendingUnverifiedWrites.clear()
    write(ctx, "compress.rs", "v2 rewritten after running v1")
    assert path.read_text(encoding="utf-8") == "v2 rewritten after running v1"


def test_external_write_with_explicit_authorization(tmp_path):
    # MVP用明确审批callback替代来源独立权限gate；批准后保持区外写能力。
    async def approve(path):
        return True
    ctx = ToolContext(str(tmp_path), approveExternalWrite=approve)
    write(ctx, "../outside-write.txt", "ok")
    assert (tmp_path.parent / "outside-write.txt").read_text(encoding="utf-8") == "ok"


def test_rejects_changed_read_meta(tmp_path):
    path = tmp_path / "exists.txt"
    path.write_text("old", encoding="utf-8", newline="")
    stat = path.stat()
    ctx = ToolContext(str(tmp_path), readFiles={str(path)}, readMeta={str(path): {
        "mtime": stat.st_mtime_ns / 1_000_000 - 1000, "size": 999,
    }})
    with pytest.raises(ValueError, match="已被外部改动"):
        write(ctx)


def test_matching_read_meta_allows_write(tmp_path):
    path = tmp_path / "exists.txt"
    path.write_text("old", encoding="utf-8", newline="")
    stat = path.stat()
    ctx = ToolContext(str(tmp_path), readFiles={str(path)}, readMeta={str(path): {
        "mtime": stat.st_mtime_ns / 1_000_000, "size": stat.st_size,
    }})
    write(ctx)
    assert path.read_text(encoding="utf-8") == "new"


def test_declares_write_required():
    assert (writeFileTool.name, writeFileTool.capability, writeFileTool.approval) == ("Write", "write", "required")
    expected = json.loads((Path(__file__).parent / "fixtures/n2-editjournal/descriptions.json").read_text(encoding="utf-8"))["Write"]
    registry = ToolRegistry()
    registry.register(writeFileTool)
    definition = registry.toApiTools()[0]["function"]
    assert definition["description"] != expected["description"]
    assert all(word in definition["description"] for word in ("完整内容", "Read", "Edit"))
    english = registry.toApiTools(lang="en")[0]["function"]["description"]
    assert english != expected["descriptionEn"]
    assert all(word in english for word in ("entire contents", "content", "Edit"))
    assert definition["parameters"] == {
        "type": "object", "required": ["path", "content"], "additionalProperties": False,
        "properties": {
            "path": {"type": "string", "description": "相对工作区根目录的文件路径"},
            "content": {"type": "string", "description": "文件的完整内容"},
        },
    }
