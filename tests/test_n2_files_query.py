"""冻结index.ts:2292–2296的/files纯查询文字适配，不需要模型或stdin。"""

from ruocun.agent.files import filesReport


def test_source_files_query_empty_paths_and_fifty_item_projection(tmp_path):
    assert filesReport(str(tmp_path), []) == "本会话尚未读取任何文件。"
    files = [str(tmp_path / "中文目录" / "已读.py"), str(tmp_path)]
    out = filesReport(str(tmp_path), files)
    assert out == f"上下文中读过的文件(2):\n  中文目录\\已读.py\n  {tmp_path}"
    assert files == [str(tmp_path / "中文目录" / "已读.py"), str(tmp_path)]
    many = [str(tmp_path / f"read-{index}.txt") for index in range(51)]
    out = filesReport(str(tmp_path), iter(many))
    assert out.startswith("上下文中读过的文件(51):\n  read-0.txt")
    assert "read-49.txt" in out and "read-50.txt" not in out
    assert out.endswith("\n  …等共 51 个")
