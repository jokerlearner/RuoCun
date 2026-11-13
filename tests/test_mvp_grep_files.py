"""冻结 src/tools/grep_files.test.ts 的首版语义断言。"""

import asyncio

import pytest

from ruocun.tools.grep_files import grepFilesTool
from ruocun.tools.types import ToolContext


@pytest.fixture(autouse=True)
def files(tmp_path):
    (tmp_path / "a.ts").write_bytes(b"const foo = 1;\nconst bar = 2;\n")
    (tmp_path / "b.md").write_bytes(b"foo appears here\n")


def call(tmp_path, **args):
    return asyncio.run(grepFilesTool.handler(args, ToolContext(str(tmp_path))))


def test_returns_path_line_content(tmp_path):
    (tmp_path / "a.ts").write_text("const foo = 1;\nconst bar = 2;\n", encoding="utf-8", newline="")
    (tmp_path / "b.md").write_text("foo appears here\n", encoding="utf-8", newline="")
    out = asyncio.run(grepFilesTool.handler({"pattern": "foo"}, ToolContext(str(tmp_path))))
    assert "a.ts:1:const foo = 1;" in out
    assert "b.md:1:foo appears here" in out


def test_files_mode(tmp_path):
    out = call(tmp_path, pattern="foo", mode="files")
    assert "a.ts" in out and "b.md" in out
    assert ":1:" not in out


def test_filename_glob(tmp_path):
    out = call(tmp_path, pattern="foo", glob="*.ts")
    assert "a.ts" in out and "b.md" not in out


def test_ignore_case(tmp_path):
    assert "a.ts:1:" in call(tmp_path, pattern="FOO", ignore_case=True)


def test_no_match_echoes_scope(tmp_path):
    out = call(tmp_path, pattern="zzz-nope", path="sub")
    assert "无匹配" in out and "zzz-nope" in out and "sub" in out


def test_declares_read_auto():
    assert (grepFilesTool.name, grepFilesTool.capability, grepFilesTool.approval) == ("Grep", "read", "auto")


def test_before_after_context_markers(tmp_path):
    (tmp_path / "ctx.ts").write_bytes(b"line0\nline1\nfoo\nline3\nline4\n")
    out = call(tmp_path, pattern="foo", before=1, after=1)
    assert "ctx.ts:2:- line1" in out
    assert "ctx.ts:3:> foo" in out
    assert "ctx.ts:4:- line3" in out


def test_context_both_sides(tmp_path):
    (tmp_path / "ctx2.ts").write_bytes(b"a\nb\nfoo\nc\nd\n")
    out = call(tmp_path, pattern="foo", context=1)
    assert "ctx2.ts:2:- b" in out
    assert "ctx2.ts:3:> foo" in out
    assert "ctx2.ts:4:- c" in out


def test_head_limit(tmp_path):
    (tmp_path / "multi.ts").write_bytes(b"foo\nfoo\nfoo\nfoo\nfoo\n")
    (tmp_path / "a.ts").unlink()
    (tmp_path / "b.md").unlink()
    out = call(tmp_path, pattern="foo", head_limit=2)
    assert len([line for line in out.split("\n") if "multi.ts:" in line and "截断" not in line]) == 2
    assert "截断" in out


def test_offset(tmp_path):
    (tmp_path / "skip.ts").write_bytes(b"foo\nfoo\nfoo\n")
    (tmp_path / "a.ts").unlink()
    (tmp_path / "b.md").unlink()
    out = call(tmp_path, pattern="foo", offset=1)
    assert len([line for line in out.split("\n") if "skip.ts:" in line and "跳过" not in line]) == 2
    assert "跳过前 1 条" in out


def test_type_filter(tmp_path):
    out = call(tmp_path, pattern="foo", type="ts")
    assert "a.ts" in out and "b.md" not in out


def test_multiline_single_line_pattern(tmp_path):
    (tmp_path / "ml.ts").write_bytes(b"const x = {\n  val: 42,\n};\n")
    assert "ml.ts:2:" in call(tmp_path, pattern=r"val:\s*42", multiline=True)


def test_multiline_cross_line_pattern(tmp_path):
    (tmp_path / "ml2.rs").write_bytes(b"struct Foo {\n    field: u32,\n}\n")
    assert "ml2.rs:1:" in call(tmp_path, pattern=r"struct Foo \{[\s\S]*?field", multiline=True)


def test_long_line_explicit_truncation(tmp_path):
    line = "x" * 400 + "foo" + "y" * 400
    (tmp_path / "long.ts").write_bytes((line + "\n").encode())
    out = call(tmp_path, pattern="foo", glob="long.ts")
    assert "共 803 字符,已截断" in out
    assert "y" * 400 not in out


def test_only_matching_exact_boundaries_on_long_line(tmp_path):
    filler = "-" * 320
    synthetic = "hf_REDACTEDTESTFIXTUREPLACEHOLDERVALUE"
    line = '{"diff": "' + filler + synthetic + filler + '"}'
    (tmp_path / "big.json").write_bytes((line + "\n").encode())
    plain = call(tmp_path, pattern=r"hf_[A-Za-z0-9]{29,}", glob="big.json")
    assert synthetic not in plain
    precise = call(tmp_path, pattern=r"hf_[A-Za-z0-9]{29,}", glob="big.json", only_matching=True)
    assert f"<<{synthetic}>>" in precise


def test_path_points_at_single_file(tmp_path):
    (tmp_path / "single.json").write_bytes(b'{"k": "hf_abcdefghijklmnopqrstuvwxyz123456"}\n')
    out = call(tmp_path, pattern=r"hf_[a-zA-Z0-9]{20,}", path="single.json")
    assert "single.json:1:" in out
    assert "hf_abcdefghijklmnopqrstuvwxyz123456" in out


def test_match_context_characters(tmp_path):
    (tmp_path / "mc.ts").write_bytes(b"prefix_here foo_needle suffix_here\n")
    out = call(tmp_path, pattern="foo_needle", glob="mc.ts", only_matching=True, match_context=7)
    assert "_here <<foo_needle>> suffi" in out
