"""冻结 src/tools/paths.test.ts；Windows用junction承载目录软链语义。"""

import os

import pytest

from ruocun.tools.paths import resolveInWorkspace


def test_relative_inside_workspace(tmp_path):
    assert resolveInWorkspace(str(tmp_path), "a.txt") == str(tmp_path / "a.txt")
    assert resolveInWorkspace(str(tmp_path), "sub/b.txt") == str(tmp_path / "sub/b.txt")


def test_workspace_itself(tmp_path):
    assert resolveInWorkspace(str(tmp_path), ".") == str(tmp_path)


def test_harmless_parent(tmp_path):
    assert resolveInWorkspace(str(tmp_path), "sub/../a.txt") == str(tmp_path / "a.txt")


def test_rejects_escaping_traversal(tmp_path):
    for path in ("../etc/passwd", "sub/../../x"):
        with pytest.raises(ValueError, match="越界"):
            resolveInWorkspace(str(tmp_path), path)


def test_rejects_absolute_outside(tmp_path):
    with pytest.raises(ValueError, match="越界"):
        resolveInWorkspace(str(tmp_path), str(tmp_path.parent / "etc/passwd"))


def test_rejects_directory_link_escape(tmp_path):
    workspace = tmp_path / "ws"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"x")
    link = workspace / "link"
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(outside), str(link))
    else:
        link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="逃逸|越界"):
        resolveInWorkspace(str(workspace), "link/secret.txt")
