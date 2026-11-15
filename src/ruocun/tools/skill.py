"""从当前会话的技能清单查找并返回正文，在读取时记录实际使用的技能。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

_CAPABILITY_NOTE = (
    "\n[当前能力] 支持启动加载、动态发现、安装后调用、按需正文适配和完整终端交互。"
    "正文引用的其它工具仅在当前可用工具列表已提供时使用；"
    "需要给用户选项或确认时，通过当前文字交互入口进行。"
)

_FOLLOW = (
    "\n\n---\n[技能执行] 按加载出的步骤处理本任务，并遵守用户当下的指令、执行权限和证据要求。"
    "若存的模型选择与上下文规则仍适用。用 TodoWrite 记录技能明确要求执行的步骤。"
    "需要用户选择或确认时调用 AskUserQuestion，收到所需答复后再继续对应步骤。"
)


async def _skill(args: dict[str, Any], ctx: ToolContext) -> str:
    want = args["name"].strip().lower()
    skill = next((item for item in ctx.skills
                  if ((f"{item['namespace']}:" if item.get("namespace") else "")
                      + item.get("slug", "")).lower() == want), None)
    if skill is None:
        skill = next((item for item in ctx.skills if item["name"] == args["name"]), None)
    if skill is None:
        skill = next((item for item in ctx.skills if item["name"].lower() == want), None)
    if skill is None:
        skill = next((item for item in ctx.skills if item.get("slug", "").lower() == want), None)
    if skill is None:
        available = ", ".join(item["name"] for item in ctx.skills) or "(无)"
        return f"未找到 skill「{args['name']}」。可用:{available}。"
    if ctx.recordSkillUse:
        ctx.recordSkillUse(skill["name"])
    text = await ctx.adaptSkill(skill["body"]) if ctx.adaptSkill else skill["body"]
    location = (f"(目录:{skill['dir']},正文中引用的相对资源以此为根)\n"
                if skill.get("dir") else "")
    argsNote = f"\n(用户参数:{args['args']})\n" if args.get("args") else ""
    return f"# Skill: {skill['name']}\n{location}\n{argsNote}{text}{_FOLLOW}{_CAPABILITY_NOTE}"


skillTool = Tool(
    name="Skill",
    description=(
        "任务符合可用技能时，先按 name 加载完整步骤，再采取行动。遵循加载出的流程和用户要求，按需用 args "
        "传参。同一份已加载的技能可直接使用。技能指定需要用户决定时，在可用的问答工具中征询。"
    ) + _CAPABILITY_NOTE,
    descriptionEn=(
        "Load the full instructions by name before acting on a task that matches an "
        "available skill. Follow the procedure within the user’s instructions and pass args "
        "if needed. Reuse a skill that is already loaded. When its procedure calls for a "
        "user decision, use the available question tool."
    ),
    capability="read",
    approval="auto",
    schema=objectSchema({
        "name": {"type": "string", "minLength": 1, "description": "要加载的 skill 名"},
        "args": {"type": "string", "description": "传给技能的可选参数(如 '-m \"Fix bug\"' 或 '123')"},
    }, ["name"]),
    handler=_skill,
)
