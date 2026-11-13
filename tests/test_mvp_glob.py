"""冻结 glob.test.ts / file_search.test.ts / walk.test.ts 的首版断言。"""

import asyncio
import os

from ruocun.tools.glob import globToRegExp, walkFiles
from ruocun.tools.glob_files import globFilesTool
from ruocun.tools.types import ToolContext


def test_star_matches_one_directory():
    regex = globToRegExp("*.ts")
    assert regex.search("a.ts")
    assert not regex.search("sub/a.ts")
    assert not regex.search("a.js")


def test_double_star_including_zero_directories():
    regex = globToRegExp("**/*.ts")
    assert regex.search("a.ts")
    assert regex.search("sub/a.ts")
    assert regex.search("a/b/c.ts")
    assert not regex.search("a.js")


def test_question_single_character():
    regex = globToRegExp("?.ts")
    assert regex.search("a.ts")
    assert not regex.search("ab.ts")


def test_directory_prefix_literal():
    regex = globToRegExp("src/*.ts")
    assert regex.search("src/a.ts")
    assert not regex.search("lib/a.ts")


def test_regex_characters_escaped():
    regex = globToRegExp("a.b+c.txt")
    assert regex.search("a.b+c.txt")
    assert not regex.search("aXbXc.txt")


def search(tmp_path, glob):
    return asyncio.run(globFilesTool.handler({"glob": glob}, ToolContext(str(tmp_path))))


def search_files(tmp_path):
    (tmp_path / "old.ts").write_bytes(b"x")
    (tmp_path / "new.ts").write_bytes(b"y")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub/deep.ts").write_bytes(b"z")
    (tmp_path / "note.md").write_bytes(b"m")
    os.utime(tmp_path / "old.ts", (1, 1))
    os.utime(tmp_path / "new.ts", (2, 2))


def test_glob_top_level_newest_first(tmp_path):
    search_files(tmp_path)
    assert search(tmp_path, "*.ts").split("\n") == ["new.ts", "old.ts"]


def test_glob_nested_double_star(tmp_path):
    search_files(tmp_path)
    out = search(tmp_path, "**/*.ts")
    assert "sub/deep.ts" in out and "new.ts" in out


def test_glob_no_matches(tmp_path):
    search_files(tmp_path)
    assert search(tmp_path, "*.json") == "(无匹配)"


def test_glob_declares_read_auto():
    assert (globFilesTool.name, globFilesTool.capability, globFilesTool.approval) == ("Glob", "read", "auto")


def walk_files(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"x")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub/b.txt").write_bytes(b"y")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules/skip.txt").write_bytes(b"z")


def test_walk_relative_paths(tmp_path):
    walk_files(tmp_path)
    paths = [relative for _, relative in walkFiles(str(tmp_path))]
    assert "a.txt" in paths and "sub/b.txt" in paths


def test_walk_skips_ignored_directory(tmp_path):
    walk_files(tmp_path)
    paths = [relative for _, relative in walkFiles(str(tmp_path))]
    assert not any("node_modules" in path for path in paths)


def test_walk_single_file(tmp_path):
    walk_files(tmp_path)
    assert [relative for _, relative in walkFiles(str(tmp_path / "a.txt"))] == ["a.txt"]
