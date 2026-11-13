"""冻结 src/tools/registry.test.ts / schema.test.ts 的首版语义迁移。"""

import asyncio

import pytest

from ruocun.tools.registry import ToolRegistry
from ruocun.tools.schema import toJsonSchema
from ruocun.tools.types import Tool, ToolContext


def run(coro):
    return asyncio.run(coro)


async def echo(args, ctx):
    return f"echo:{args['text']}"


def make_echo():
    return Tool("echo", "echoes the text", {
        "type": "object", "properties": {"text": {"type": "string"}},
        "required": ["text"], "additionalProperties": False,
    }, "read", "auto", echo)


def test_registers_and_dispatches_validated_args(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    assert run(reg.dispatch("echo", '{"text":"hi"}', ToolContext(str(tmp_path)))) == "echo:hi"


def test_api_tools_registration_order():
    reg = ToolRegistry()
    reg.register(make_echo())
    api = reg.toApiTools()
    assert len(api) == 1
    assert api[0]["type"] == "function"
    assert api[0]["function"]["name"] == "echo"
    assert api[0]["function"]["description"] == "echoes the text"
    assert api[0]["function"]["parameters"]["type"] == "object"


def test_unknown_tool(tmp_path):
    with pytest.raises(ValueError, match="unknown tool: nope"):
        run(ToolRegistry().dispatch("nope", "{}", ToolContext(str(tmp_path))))


def test_invalid_json(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    with pytest.raises(ValueError, match="invalid JSON arguments for echo"):
        run(reg.dispatch("echo", "{not json", ToolContext(str(tmp_path))))


def test_truncated_json_diagnosed_never_executed(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    truncated = '{"text": "这是一段很长的文本,写到一半就断掉了没有收尾'
    with pytest.raises(ValueError, match=r"invalid JSON arguments for echo.*被截断.*text\(\d+ 字符.*拆成更小的几次调用"):
        run(reg.dispatch("echo", truncated, ToolContext(str(tmp_path))))


def test_malformed_json_short_error(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    with pytest.raises(ValueError) as info:
        run(reg.dispatch("echo", "{not json", ToolContext(str(tmp_path))))
    assert str(info.value) == "invalid JSON arguments for echo"


def test_schema_failure(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    with pytest.raises(ValueError):
        run(reg.dispatch("echo", '{"text":123}', ToolContext(str(tmp_path))))


def tool(name, fields):
    return Tool(name, "search", {"type": "object", "properties": fields,
                                "required": [next(iter(fields))], "additionalProperties": False},
                "read", "auto", echo)


def test_wrong_parameter_name_diagnostic(tmp_path):
    reg = ToolRegistry()
    reg.register(tool("Glob", {"glob": {"type": "string"}, "path": {"type": "string"}}))
    with pytest.raises(ValueError, match=r"Glob 缺少必填参数「glob」.*你传了 \[pattern\].*参数名可能写错了.*Glob 接受的参数.*glob\(string, 必填"):
        run(reg.dispatch("Glob", '{"pattern":"**/*.ts"}', ToolContext(str(tmp_path))))


def test_single_required_minimal_example(tmp_path):
    reg = ToolRegistry()
    reg.register(tool("Grep", {"pattern": {"type": "string"}, "path": {"type": "string"}}))
    with pytest.raises(ValueError, match=r'Grep 缺少必填参数「pattern」.*最小调用示例:Grep\(\{"pattern": "<值>"\}\)'):
        run(reg.dispatch("Grep", '{"path":"src"}', ToolContext(str(tmp_path))))


def test_multiple_required_no_minimal_example(tmp_path):
    reg = ToolRegistry()
    multi = Tool("Multi", "multi required", {"type": "object", "properties": {
        "a": {"type": "string"}, "b": {"type": "string"}}, "required": ["a", "b"]}, "read", "auto", echo)
    reg.register(multi)
    with pytest.raises(ValueError) as info:
        run(reg.dispatch("Multi", '{"a":"x"}', ToolContext(str(tmp_path))))
    assert "最小调用示例" not in str(info.value)


def test_missing_all_params_diagnostic(tmp_path):
    reg = ToolRegistry()
    reg.register(tool("Read", {"path": {"type": "string"}}))
    with pytest.raises(ValueError, match=r"Read 缺少必填参数「path」.*Read 需要参数「path」.*但你没传任何参数.*Read 接受的参数.*path\(string, 必填"):
        run(reg.dispatch("Read", "{}", ToolContext(str(tmp_path))))


def test_wrong_type_diagnostic(tmp_path):
    reg = ToolRegistry()
    reg.register(make_echo())
    with pytest.raises(ValueError, match=r"echo 参数「text」需要 string,收到 number.*echo 接受的参数.*text\(string, 必填"):
        run(reg.dispatch("echo", '{"text":123}', ToolContext(str(tmp_path))))


def test_clean_schema_without_dialect_key():
    schema = {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
              "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}
    result = toJsonSchema(schema)
    assert "$schema" not in result
    assert result["type"] == "object"
    assert result["properties"]["path"]["type"] == "string"
    assert "path" in result["required"] and "limit" not in result["required"]
