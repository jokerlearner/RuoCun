"""委托技能安装模块处理安装请求，成功后触发技能清单刷新。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from ..skills.install import GitRunner, InstallScope, installSkills
from .schema import objectSchema
from .types import Tool, ToolContext


def makeSkillInstallTool(user_root: Path, *, run_git: GitRunner | None = None) -> Tool:
    async def handler(args: dict[str, Any], ctx: ToolContext) -> str:
        scope = cast(InstallScope, args.get("scope", "user"))
        result = await installSkills(args["source"], scope, Path(ctx.workspaceRoot), user_root, ctx.signal, run_git=run_git)
        refresh = ctx.onSkillsInstalled
        if result.installed and refresh is not None:
            refresh(scope)
        return result.format(refreshing=refresh is not None)

    return Tool(
        name="SkillInstall",
        description=(
            "安装可复用的技能。选择用户范围或项目范围，保留技能正文。运行时会按可用工具适配受支持的工具引用。安装前核对来源和用户授权。"
        ),
        descriptionEn=(
            "Install a reusable skill at user or project scope. Installation preserves its "
            "content, and loading can adapt supported references to available tools. Confirm "
            "the source and user authorization before installing."
        ),
        schema=objectSchema({
            "source": {"type": "string", "minLength": 1, "description": "git URL(如 https://github.com/obra/superpowers-skills)或本地路径"},
            "scope": {"type": "string", "enum": ["user", "project"],
                      "description": "user=~/.ruocun/skills(跨项目,默认);project=当前项目 .ruocun/skills"},
        }, ["source"]),
        capability="exec", approval="required", shouldDefer=True, handler=handler,
    )
