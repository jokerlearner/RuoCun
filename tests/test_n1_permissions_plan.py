"""DAO plan_mode.test.ts and native tools_for_mode cases (MIT)."""
import asyncio

from ruocun.tools.plan_mode import enterPlanModeTool, exitPlanModeTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.schema import objectSchema
from ruocun.tools.tools_for_mode import apiToolsForMode
from ruocun.tools.types import Tool, ToolContext


def test_enter(tmp_path):
    mode = []
    ctx = ToolContext(str(tmp_path), setMode=mode.append)
    assert "规划模式" in asyncio.run(enterPlanModeTool.handler({}, ctx))
    assert mode == ["plan"]
    mode.clear()
    ctx.headless = True
    assert "无人值守" in asyncio.run(enterPlanModeTool.handler({}, ctx))
    assert mode == []
    assert "不支持模式切换" in asyncio.run(enterPlanModeTool.handler({}, ToolContext(str(tmp_path))))


def test_exit(tmp_path):
    mode, asked = [], []
    async def approve(question, options, multi=False):
        asked.append(question)
        return "批准,开始实现"
    ctx = ToolContext(str(tmp_path), setMode=mode.append, askChoice=approve)
    assert "已退出规划模式" in asyncio.run(exitPlanModeTool.handler({}, ctx))
    assert mode == ["normal"] and "批准" in asked[0]
    async def reject(question, options, multi=False):
        return "不批准,继续讨论"
    ctx.askChoice = reject
    mode.clear()
    assert "未批准" in asyncio.run(exitPlanModeTool.handler({}, ctx))
    assert mode == []
    ctx.askChoice, ctx.headless = None, True
    assert "已退出规划模式" in asyncio.run(exitPlanModeTool.handler({}, ctx))
    assert mode == ["normal"]
    assert "不支持模式切换" in asyncio.run(exitPlanModeTool.handler({}, ToolContext(str(tmp_path))))


def test_native_mode_catalog():
    registry = ToolRegistry()
    async def handler(args, ctx):
        return ""
    for name, cap, approval in [("Read", "read", "auto"), ("Write", "write", "required"), ("Bash", "exec", "required")]:
        registry.register(Tool(name, "", objectSchema({}, []), cap, approval, handler))
    assert [t["function"]["name"] for t in apiToolsForMode(registry, "normal")] == ["Read", "Write", "Bash"]
    assert [t["function"]["name"] for t in apiToolsForMode(registry, "plan")] == ["Read"]
    registry.register(Tool("CronCreate", "创建定时任务。", objectSchema({"x": {"type": "string"}}, ["x"]), "read", "auto", handler, shouldDefer=True))
    assert "CronCreate" not in [t["function"]["name"] for t in apiToolsForMode(registry, "normal")]
    registry.searchAndActivateDeferred("cron")
    result = apiToolsForMode(registry, "normal")[-1]
    assert result["function"]["name"] == "CronCreate"
    assert "x" in result["function"]["parameters"]["properties"]
