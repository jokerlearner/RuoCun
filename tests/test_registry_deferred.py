"""冻结 registry.test.ts 的原生deferred/toApiTools语义；53其余能力另验。"""

from dataclasses import replace

import pytest

from ruocun.tools.registry import ToolRegistry
from ruocun.tools.tool_search import toolSearchTool
from ruocun.tools.types import Tool


async def handler(args, ctx):
    return ""


def registry():
    reg = ToolRegistry()
    reg.register(Tool("Read", "读取", {"type": "object", "properties": {}}, "read", "auto", handler))
    reg.register(Tool("CronCreate", "创建定时任务。支持循环和一次性。", {
        "type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"],
    }, "read", "auto", handler, shouldDefer=True))
    return reg


def test_unactivated_deferred_has_short_description_and_empty_schema():
    api = registry().toApiTools()
    assert [item["function"]["name"] for item in api] == ["Read", "CronCreate"]
    assert api[1]["function"]["description"] == "创建定时任务"
    assert api[1]["function"]["parameters"]["properties"] == {}


def test_search_activates_full_schema_for_remaining_session():
    reg = registry()
    assert "已激活" in reg.searchAndActivateDeferred("CRON")
    assert "x" in reg.toApiTools()[1]["function"]["parameters"]["properties"]
    assert "没有延迟加载工具匹配" in reg.searchAndActivateDeferred("cron")


@pytest.mark.parametrize(("query", "expected"), [
    ("不存在的xyz", "没有延迟加载工具匹配"), ("  ", "请提供搜索关键词"),
    ("循环", "CronCreate"),
])
def test_search_messages_and_description_match(query, expected):
    assert expected in registry().searchAndActivateDeferred(query)


@pytest.mark.parametrize("activated", [False, True])
def test_schema_error_guides_unactivated_tool_to_search(activated):
    reg = registry()
    if activated:
        reg.searchAndActivateDeferred("cron")
    with pytest.raises(ValueError) as error:
        reg.validate("CronCreate", "{}")
    assert ("ToolSearch" in str(error.value)) is not activated


@pytest.mark.parametrize("hide", [False, True])
def test_api_hide_flag_and_activation(hide):
    reg = registry()
    assert len(reg.toApiTools(hideUnactivatedDeferred=hide)) == (1 if hide else 2)
    reg.searchAndActivateDeferred("cron")
    api = reg.toApiTools(hideUnactivatedDeferred=hide)
    assert len(api) == 2
    assert "x" in api[1]["function"]["parameters"]["properties"]


def test_predicate_and_english_description():
    reg = registry()
    tool = reg.get("Read")
    reg.register(replace(tool, descriptionEn="Read a file"))
    api = reg.toApiTools(lambda item: item.name == "Read", "en")
    assert len(api) == 1
    assert api[0]["function"]["description"] == "Read a file"


def test_tool_search_rejects_empty_query_before_callback():
    # 冻结tool_search.ts query:z.string().min(1)，必要原生工具接线确认。
    reg = ToolRegistry()
    reg.register(toolSearchTool)
    with pytest.raises(ValueError):
        reg.validate("ToolSearch", '{"query":""}')


def test_source_mcp_registration_search_and_server_removal():
    reg = registry()
    for index in range(7):
        reg.register(Tool(f"mcp__sample__tool{index}", f"sample operation {index}",
                          {"type": "object", "properties": {}}, "exec", "required", handler))
    assert reg.countMcpTools() == reg.countByPrefix("mcp__sample__") == 7
    assert [reg.isMcpVisible(f"mcp__sample__tool{i}") for i in range(7)] == [True] * 5 + [False] * 2
    reg.restoreMcpVisibility(["mcp__sample__tool5", "mcp__missing__tool", "Read"])
    assert reg.isMcpVisible("mcp__sample__tool5") and not reg.isMcpVisible("mcp__missing__tool")
    assert "tool6" in reg.searchAndActivateMcp("operation 6")
    assert reg.isMcpVisible("mcp__sample__tool6")
    assert "没有 MCP" in reg.searchAndActivateMcp("missing")
    assert len(reg.unregisterByPrefix("mcp__sample__")) == 7
    assert reg.countMcpTools() == 0 and reg.get("Read") is not None
    reg.register(Tool("mcp__next__read", "next read", {"type": "object"}, "read", "auto", handler))
    assert reg.isMcpVisible("mcp__next__read")
