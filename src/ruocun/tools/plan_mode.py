"""Tool entry points for planning and plan approval."""
from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext


async def _enter(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.setMode is None:
        return "当前环境不支持模式切换。"
    if ctx.headless:
        return "无人值守（headless）会话无法接收退出规划所需的用户确认。本次未切换模式，请在已有授权内推进并说明结果。"
    ctx.setMode("plan")
    return "已进入规划模式(只读)。探索代码库、设计方案,完成后用 ExitPlanMode 退出。"


async def _exit(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.setMode is None:
        return "当前环境不支持模式切换。"
    if ctx.askChoice is not None:
        answer = await ctx.askChoice("已设计好方案,是否批准并退出规划模式开始实现?", ["批准,开始实现", "不批准,继续讨论"])
        if not answer.startswith("批准"):
            return f"用户未批准方案(回应:{answer})。仍在规划模式,根据反馈调整方案后再试。"
    ctx.setMode("normal")
    return "已退出规划模式,切回 normal。可以开始实现方案。"


enterPlanModeTool = Tool(
    name="EnterPlanMode",
    description=(
        "进入只读规划模式，先了解项目、确定改动范围并写好可验收的方案。方案完成时用 ExitPlanMode 提交给用户，获准后开始实现。"
    ),
    descriptionEn=(
        "Start read-only planning. Inspect the project and prepare an actionable plan with "
        "verification steps. Submit it with ExitPlanMode and wait for approval before "
        "implementation."
    ),
    capability="plan", approval="auto", shouldDefer=True,
    schema=objectSchema({}, []), handler=_enter,
)

exitPlanModeTool = Tool(
    name="ExitPlanMode",
    description=(
        "提交当前规划并等待用户批准后退出规划模式。用 allowedPrompts 列出方案确实需要预授权的 Bash 操作，按用途描述。"
    ),
    descriptionEn=(
        "Submit the current plan and leave planning mode after approval. In allowedPrompts, "
        "list only the Bash operations needed to carry out the plan and describe their "
        "purpose."
    ),
    capability="plan", approval="auto", shouldDefer=True,
    schema=objectSchema({"allowedPrompts": {
        "type": "array", "description": "实现方案需要的权限预声明",
        "items": objectSchema({
            "tool": {"type": "string", "enum": ["Bash"], "description": "要预授权的工具(目前只支持 Bash)"},
            "prompt": {"type": "string", "description": "语义化描述,如 'run tests'、'install dependencies'"},
        }, ["tool", "prompt"]),
    }}, []), handler=_exit,
)
