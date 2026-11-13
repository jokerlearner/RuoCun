"""冻结bash_ast.test.ts已有命令在叶子语法树的可消费结构，非3449 golden。"""

import pytest

from ruocun.permissions.bash.bash_parser import parseSource


def commands(node):
    if node.type == "command":
        return [node.text]
    return [text for child in node.children for text in commands(child)]


@pytest.mark.parametrize(("source", "expected"), [
    ("npm test", ["npm test"]),
    ("npm i && git status", ["npm i", "git status"]),
    ("echo hello | grep foo", ["echo hello", "grep foo"]),
    ("echo hello > /tmp/out", ["echo hello"]),
    ("NODE_ENV=prod npm test", ["NODE_ENV=prod npm test"]),
    ("if true; then echo yes; fi", ["true", "echo yes"]),
])
def test_frozen_simple_command_nodes(source, expected):
    root = parseSource(source, float("inf"))
    assert root is not None and root.type == "program"
    assert commands(root) == expected


def test_utf8_byte_offsets_and_quoted_newline_gap_remain_consumable():
    # Python代码点游标的必要适配；source string_content故意在换行处留字节gap。
    source = 'echo "中文🙂\n${x}" && pwd'
    root = parseSource(source, float("inf"))
    assert root is not None
    data = source.encode("utf-8")

    def walk(node):
        assert data[node.startIndex:node.endIndex].decode("utf-8") == node.text
        return [node, *(item for child in node.children for item in walk(child))]

    nodes = walk(root)
    content = next(node for node in nodes if node.type == "string_content")
    expansion = next(node for node in nodes if node.type == "expansion")
    assert (content.text, content.startIndex, content.endIndex) == ("中文🙂", 6, 16)
    assert expansion.startIndex == 17 and content.endIndex + 1 == expansion.startIndex


def test_source_time_and_node_caps_return_none_without_fallback_tree():
    # 源每128节点查时钟、5万节点硬帽；只确认这两个既有预算，不扩压力矩阵。
    assert parseSource("echo " + "x " * 130, -1) is None
    assert parseSource("echo " + "x " * 130, float("inf")) is not None
    assert parseSource("echo " + "x " * 50_001, float("inf")) is None
