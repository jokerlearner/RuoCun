"""冻结 src/tools/read_file.test.ts 的文本首版断言。"""

import asyncio
import threading

import pytest

from ruocun.tools.read_file import readFileTool
from ruocun.tools.types import ToolContext


def call(tmp_path, **args):
    return asyncio.run(readFileTool.handler(args, ToolContext(str(tmp_path))))


@pytest.fixture(autouse=True)
def files(tmp_path):
    (tmp_path / "a.txt").write_text("line1\nline2\nline3\n", encoding="utf-8", newline="")
    (tmp_path / "big.txt").write_text("\n".join(f"L{i + 1}" for i in range(2500)), encoding="utf-8", newline="")


def test_returns_file_content_with_line_numbers(tmp_path):
    (tmp_path / "a.txt").write_text("line1\nline2\nline3\n", encoding="utf-8", newline="")
    out = call(tmp_path, path="a.txt")
    assert "1\tline1" in out
    assert "2\tline2" in out
    assert "3\tline3" in out


def test_honors_offset_limit(tmp_path):
    assert call(tmp_path, path="a.txt", offset=2, limit=1) == "2\tline2"


def test_throws_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        call(tmp_path, path="nope.txt")


def test_declares_read_auto():
    assert (readFileTool.name, readFileTool.capability, readFileTool.approval) == ("Read", "read", "auto")


def test_denies_external_read_without_authorization(tmp_path):
    assert "工作区之外" in call(tmp_path, path="../escape.txt")


def test_authorized_external_read(tmp_path, monkeypatch):
    from ruocun.tools import paths

    outside = tmp_path.parent / "outside-read.txt"
    outside.write_text("外部内容", encoding="utf-8", newline="")
    approved = []
    async def approve(path):
        approved.append(path)
        return True
    ctx = ToolContext(str(tmp_path), approveExternalRead=approve)
    out = asyncio.run(readFileTool.handler({"path": "../outside-read.txt"}, ctx))
    assert "外部内容" in out
    assert approved == [str(outside)]

    classify = paths.classifyPath
    def pause_during_classification(root, path):
        result = classify(root, path)
        ctx.signal.set()
        return result

    monkeypatch.setattr(paths, "classifyPath", pause_during_classification)
    approved.clear()
    with pytest.raises(InterruptedError, match="取消"):
        asyncio.run(readFileTool.handler({"path": "../outside-read.txt"}, ctx))
    assert approved == []


def test_records_absolute_read_path(tmp_path):
    ctx = ToolContext(str(tmp_path))
    owner = threading.get_ident()

    class LoopReadFiles(set):
        def add(self, value):
            assert threading.get_ident() == owner, "业务读取状态不能在线程内修改"
            super().add(value)

    class LoopReadMeta(dict):
        def __setitem__(self, key, value):
            assert threading.get_ident() == owner, "业务读取基线不能在线程内修改"
            super().__setitem__(key, value)

    accessed = []

    def file_accessed(path):
        assert threading.get_ident() == owner
        accessed.append(path)

    ctx.readFiles, ctx.readMeta = LoopReadFiles(), LoopReadMeta()
    ctx.onFileAccessed = file_accessed
    asyncio.run(readFileTool.handler({"path": "a.txt"}, ctx))
    assert str(tmp_path / "a.txt") in ctx.readFiles
    assert str(tmp_path / "a.txt") in ctx.readMeta
    assert accessed == [str(tmp_path / "a.txt")]
    asyncio.run(readFileTool.handler({"path": "a.txt", "offset": 999}, ctx))
    assert accessed == [str(tmp_path / "a.txt")]


def test_binary_returns_error(tmp_path):
    (tmp_path / "bin.dat").write_bytes(b"A\x00B")
    assert "二进制" in call(tmp_path, path="bin.dat")


def test_offset_beyond_lines_is_explicit(tmp_path):
    assert "超过文件总行数" in call(tmp_path, path="a.txt", offset=999)


def test_default_cap_and_continue_notice(tmp_path):
    out = call(tmp_path, path="big.txt")
    assert "2000\tL2000" in out
    assert "2001\tL2001" not in out
    assert "文件共 2500 行" in out
    assert "offset=2001" in out


def test_explicit_limit_can_exceed_default(tmp_path):
    out = call(tmp_path, path="big.txt", limit=2300)
    assert "2300\tL2300" in out
    assert "文件共 2500 行" not in out


def test_small_file_hint_with_limit(tmp_path):
    out = call(tmp_path, path="a.txt", limit=20)
    assert "1\tline1" in out and "3\tline3" in out
    assert "文件共 4 行,已全部读取" in out
    assert "可不传 limit" in out


def test_no_small_hint_for_partial_read(tmp_path):
    out = call(tmp_path, path="big.txt", limit=100)
    assert "100\tL100" in out
    assert "已全部读取" not in out


def test_no_small_hint_without_limit(tmp_path):
    assert "已全部读取" not in call(tmp_path, path="a.txt")
