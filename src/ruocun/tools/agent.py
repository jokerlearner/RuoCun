"""把 Agent 工具参数转换成子代理请求，通过当前会话提供的运行入口派发。前台调用汇总结果，后台调用交回任务标识。"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Literal

from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT = json.loads(files("ruocun.tools").joinpath("resources/agent.json").read_text("utf-8"))


@dataclass(frozen=True)
class AgentRequest:
    task: str
    agent_type: str = "general-purpose"
    model: str | None = None
    mode: Literal["normal", "plan"] | None = None
    fork: bool = False
    isolation: Literal["worktree", "remote"] | None = None


class AgentFailure(ValueError):
    """表示可以确定失败或取消的子代理运行，父回合可以据此完成工具结果。"""


def normalizeModel(model: str | None) -> str | None:
    selected = (model or "").strip()
    return "inherit" if selected.lower() == "inherit" else selected or None


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.subagentDepth >= 1:
        return "子代理内不能再派子代理(不支持嵌套)。请自己完成这件事,或把它拆小后在结论里回报需要继续的部分。"
    runner = ctx.runAgent
    if runner is None:
        return "当前环境不支持子代理。"
    fork = args.get("fork") is True
    requested_isolation = args.get("isolation")
    isolation: Literal["worktree", "remote"] | None = None
    if requested_isolation == "remote":
        isolation = "remote"
    elif requested_isolation == "worktree" or args.get("isolate") is True:
        isolation = "worktree"
    # 分叉沿用父会话的运行边界，拒绝同时覆盖模型、权限模式或隔离方式。
    if fork and (args.get("model") or args.get("mode")):
        return "fork 与 model/mode 覆盖互斥。请保留继承设置，或关闭 fork 后按指定设置派发。"
    if fork and isolation is not None:
        return "fork 与 worktree/remote 隔离互斥。请明确选择要保留的派发方式。"
    agent_type = args.get("agent_type") or "general-purpose"
    if args.get("background") or (not fork and ctx.agentRunsInBackground is not None and ctx.agentRunsInBackground(agent_type)):
        if ctx.launchAgent is None:
            return "当前环境不支持后台子代理。"
        runner = ctx.launchAgent
    tasks = args.get("tasks") or ([args["task"]] if args.get("task") else [])
    if not tasks:
        return "请提供 task 或 tasks。"
    if ctx.signal.is_set():
        return "本轮已取消，未启动子代理。"

    def request(task: str) -> AgentRequest:
        return AgentRequest(task, agent_type, normalizeModel(args.get("model")), args.get("mode"), fork, isolation)

    if len(tasks) == 1:
        try:
            return await runner(request(tasks[0]))
        except AgentFailure as error:
            return f"Error: {error}"

    results = [""] * len(tasks)
    pending = iter(enumerate(tasks))
    stopped = False

    async def worker() -> None:
        nonlocal stopped
        while not stopped and not ctx.signal.is_set():
            entry = next(pending, None)
            if entry is None:
                return
            index, task = entry
            try:
                text = await runner(request(task))
            except AgentFailure as error:
                text = f"[失败] {error}"
            except BaseException:
                stopped = True
                raise
            results[index] = f"### 子代理 {index + 1}/{len(tasks)}\n任务:{task}\n\n{text}"

    outcomes = await asyncio.gather(*(worker() for _ in range(min(ctx.maxParallelAgents, len(tasks)))), return_exceptions=True)
    for outcome in outcomes:
        if isinstance(outcome, BaseException):
            raise outcome
    for index, task in enumerate(tasks):
        if not results[index]:
            results[index] = f"### 子代理 {index + 1}/{len(tasks)}\n任务:{task}\n\n[取消] 未启动。"
    return "\n\n---\n\n".join(results)


_PROPERTIES: dict[str, dict[str, Any]] = {
    "task": {"type": "string", "minLength": 1},
    "tasks": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1, "maxItems": 20},
    "background": {"type": "boolean"},
    "agent_type": {"type": "string"},
    "isolate": {"type": "boolean"},
    "isolation": {"type": "string", "enum": ["worktree", "remote"]},
    "fork": {"type": "boolean"},
    "model": {"type": "string"},
    "mode": {"type": "string", "enum": ["normal", "plan"]},
}
for _name, _property in _PROPERTIES.items():
    _property["description"] = _TEXT["properties"][_name]

agentTool = Tool(
    name="Agent",
    description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
    schema=objectSchema(_PROPERTIES, []), capability="plan", approval="auto", persistentEffect=True,
    handler=_handler,
)
