"""冻结 src/tools/edit_file.test.ts 的首版语义断言。"""

import asyncio
import json
from pathlib import Path

import pytest

from ruocun.tools.edit_file import editFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext


def test_replaces_unique_occurrence(tmp_path):
    path = tmp_path / "f.txt"
    path.write_text("alpha beta gamma", encoding="utf-8", newline="")
    accessed = []

    def observe(absolute):
        assert Path(absolute).read_text(encoding="utf-8") == "alpha BETA gamma"
        accessed.append(absolute)

    ctx = ToolContext(str(tmp_path), readFiles={str(path)}, lang="en", onFileAccessed=observe)
    out = asyncio.run(editFileTool.handler({"path": "f.txt", "old_string": "beta", "new_string": "BETA"}, ctx))
    assert out.startswith("Edited f.txt (1 replacement(s), line 1)\n```diff\n")
    assert path.read_text(encoding="utf-8") == "alpha BETA gamma"
    assert accessed == [str(path)]


def edit(tmp_path, raw, old, new, **extra):
    path = tmp_path / "f.txt"
    path.write_text(raw, encoding="utf-8", newline="")
    ctx = ToolContext(str(tmp_path), readFiles={str(path)})
    return asyncio.run(editFileTool.handler({"path": "f.txt", "old_string": old, "new_string": new, **extra}, ctx))


def test_parallel_edits_same_file_serialize(tmp_path):
    path = tmp_path / "f.txt"
    path.write_text("A\nB", encoding="utf-8", newline="")
    ctx = ToolContext(str(tmp_path), readFiles={str(path)})
    async def parallel():
        await asyncio.gather(
            editFileTool.handler({"path": "f.txt", "old_string": "A", "new_string": "X"}, ctx),
            editFileTool.handler({"path": "f.txt", "old_string": "B", "new_string": "Y"}, ctx),
        )
    asyncio.run(parallel())
    assert path.read_text(encoding="utf-8") == "X\nY"


def test_replace_all(tmp_path):
    edit(tmp_path, "x x x", "x", "y", replace_all=True)
    assert (tmp_path / "f.txt").read_text(encoding="utf-8") == "y y y"


def test_missing_old_throws(tmp_path):
    with pytest.raises(ValueError):
        edit(tmp_path, "hello", "nope", "x")


def test_normalizes_lookalike_punctuation(tmp_path):
    out = edit(tmp_path, "免一次审批——下一步", "免一次审批--下一步", "done")
    assert "done" in out
    assert (tmp_path / "f.txt").read_text(encoding="utf-8") == "done"


def test_multiple_occurrences_require_replace_all(tmp_path):
    with pytest.raises(ValueError):
        edit(tmp_path, "x x", "x", "y")


def test_requires_read(tmp_path):
    (tmp_path / "f.txt").write_text("hello", encoding="utf-8", newline="")
    with pytest.raises(ValueError):
        asyncio.run(editFileTool.handler({"path": "f.txt", "old_string": "hello", "new_string": "hi"}, ToolContext(str(tmp_path))))


def test_dollars_are_literal(tmp_path):
    edit(tmp_path, "price PLACEHOLDER end", "PLACEHOLDER", "$100 & $& and $1")
    assert (tmp_path / "f.txt").read_text(encoding="utf-8") == "price $100 & $& and $1 end"


def test_declares_write_required():
    assert (editFileTool.name, editFileTool.capability, editFileTool.approval) == ("Edit", "write", "required")
    expected = json.loads((Path(__file__).parent / "fixtures/n2-editjournal/descriptions.json").read_text(encoding="utf-8"))["Edit"]
    registry = ToolRegistry()
    registry.register(editFileTool)
    definition = registry.toApiTools()[0]["function"]
    assert definition["description"] != expected["description"]
    assert all(word in definition["description"] for word in ("Read", "old_string", "replace_all"))
    english = registry.toApiTools(lang="en")[0]["function"]["description"]
    assert english != expected["descriptionEn"]
    assert all(word in english for word in ("exact match", "old_string", "replace_all"))
    assert definition["parameters"] == {
        "type": "object", "required": ["path", "old_string", "new_string"], "additionalProperties": False,
        "properties": {
            "path": {"type": "string", "description": "相对工作区根目录的文件路径"},
            "old_string": {"type": "string", "description": "要被替换的原文(需唯一)"},
            "new_string": {"type": "string", "description": "替换成的新文本"},
            "replace_all": {"type": "boolean", "description": "是否替换全部出现"},
        },
    }
