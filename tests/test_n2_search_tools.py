"""冻结list_dir.test.ts原6例；既有Glob/Grep来源断言继续复用MVP文件。"""

import asyncio
import json
from copy import deepcopy
from pathlib import Path

import pytest

from ruocun.tools.glob_files import globFilesTool
from ruocun.tools.grep_files import grepFilesTool
from ruocun.tools.list_dir import listDirTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext


@pytest.fixture
def directory(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    return tmp_path


def test_listdir_entries_sorted_with_directory_slash(directory):
    out = asyncio.run(listDirTool.handler({}, ToolContext(str(directory))))
    assert out == "file.txt\nsub/"


def test_listdir_relative_subdirectory(directory):
    out = asyncio.run(listDirTool.handler({"path": "sub"}, ToolContext(str(directory))))
    assert out == "(空目录)"


def test_listdir_missing_directory_raises(directory):
    with pytest.raises(OSError):
        asyncio.run(listDirTool.handler({"path": "nope"}, ToolContext(str(directory))))


def test_listdir_declares_read_auto():
    assert (listDirTool.name, listDirTool.capability, listDirTool.approval) == ("ListDir", "read", "auto")


def test_listdir_external_denied_returns_error(directory):
    out = asyncio.run(listDirTool.handler({"path": ".."}, ToolContext(str(directory))))
    assert "工作区之外" in out


def test_listdir_external_approved_lists(directory):
    async def approve(path):
        return True

    out = asyncio.run(listDirTool.handler({"path": ".."}, ToolContext(
        str(directory), approveExternalRead=approve)))
    assert "工作区之外" not in out


def test_grep_python_offsets_render_source_utf16_columns_context_and_line_lengths(tmp_path):
    # 保留Python re，仅把其代码点位置转换为source的JS列号/显示字符计数。
    path = tmp_path / "中文.py"
    path.write_bytes("x🙂foo尾\n".encode("utf-8"))
    ctx = ToolContext(str(tmp_path))
    out = asyncio.run(grepFilesTool.handler({
        "pattern": "foo", "glob": "中文.py", "only_matching": True, "match_context": 2,
    }, ctx))
    assert out == "中文.py:1:4:…🙂<<foo>>尾"
    path.write_bytes(("🙂" * 151 + "foo\n").encode("utf-8"))
    out = asyncio.run(grepFilesTool.handler({"pattern": "foo", "glob": "中文.py"}, ctx))
    assert "该行共 305 字符,已截断" in out and "foo" not in out
    path.write_bytes(("before" + "m" * 500 + "after\n").encode("utf-8"))
    out = asyncio.run(grepFilesTool.handler({
        "pattern": "m+", "glob": "中文.py", "only_matching": True, "match_context": 3,
    }, ctx))
    assert out == "中文.py:1:7:…ore<<" + "m" * 500 + ">>…(上下文过长已截断)"


def test_native_search_descriptions_keep_source_api_shapes():
    # 期待值由独立冻结TS literal/Zod提取器生成，提取时不import产品。
    source = json.loads((Path(__file__).parent / "fixtures/n2-search-source-descriptors.json").read_text(encoding="utf-8"))
    for tool in (listDirTool, globFilesTool, grepFilesTool):
        expected = source["tools"][tool.name]
        if tool.name == "Grep":
            expected["parameters"]["properties"]["pattern"]["description"] = "正则表达式(Python标准语法)"
            old_matching_help = expected["parameters"]["properties"]["only_matching"].pop("description")
        registry = ToolRegistry()
        registry.register(tool)
        for lang, description in (("zh", "description"), ("en", "descriptionEn")):
            actual = registry.toApiTools(lang=lang)[0]["function"]
            assert actual["name"] == tool.name
            parameters = deepcopy(actual["parameters"])
            if tool.name == "Grep":
                matching_help = parameters["properties"]["only_matching"].pop("description")
                assert matching_help != old_matching_help and "<<...>>" in matching_help
            assert parameters == expected["parameters"]
            assert actual["description"] and actual["description"] != expected[description]
            if tool.name == "Grep":
                assert all(word in actual["description"] for word in ("Python", "only_matching", "match_context"))
