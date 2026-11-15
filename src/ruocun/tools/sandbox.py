"""执行 Shell 前为调用绑定当前项目的写入策略。额外写入目录经审批后才加入该次执行计划。"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..platform.file_contract import AtomicFileError
from ..platform.sandbox_policy import createSandboxPolicy, sandboxEnvironment
from ..platform.shell_plan import ShellExecutionPlan
from ..platform.windows.sandbox import WindowsSandboxError
from .types import ToolContext, ToolRejected


async def prepareSandboxPlan(plan: ShellExecutionPlan, ctx: ToolContext, requested: Any = None) -> ShellExecutionPlan:
    roots = [] if requested is None else requested
    if not isinstance(roots, list) or len(roots) > 8 or not all(isinstance(root, str) and root for root in roots):
        raise ToolRejected("additionalWriteDirectories 必须是最多8个绝对目录的列表。")
    try:
        policy = plan.sandbox or ctx.sandboxPolicy or createSandboxPolicy(ctx.workspaceRoot, dict(plan.environment))
        environment = tuple(sorted(sandboxEnvironment(dict(plan.environment), policy).items()))
    except (OSError, ValueError, AtomicFileError, WindowsSandboxError) as error:
        raise ToolRejected(f"沙箱环境准备失败，命令未执行：{error}") from error
    if policy is None:
        if roots:
            raise ToolRejected("本次额外目录参数仅用于已开启的 Windows 沙箱。")
        return plan
    if plan.sandbox != policy or plan.environment != environment:
        plan = replace(plan, sandbox=policy, environment=environment)
    if roots:
        if ctx.authorizeSandboxShell is None:
            raise ToolRejected("未绑定本次额外目录的用户审批入口，命令未执行。")
        plan = await ctx.authorizeSandboxShell(plan, roots)
    return plan
