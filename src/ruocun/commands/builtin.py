"""Expand standard RuoCun commands into model requests."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypedDict

from ..i18n.i18n import Lang
from ..skills.bundled import SIMPLIFY_BODY


class BuiltinResult(TypedDict, total=False):
    prompt: str
    output: str


@dataclass(frozen=True)
class BuiltinCommand:
    description: str
    descriptionEn: str
    buildPrompt: Callable[[str, Lang], str]
    argHint: str = ""
    argHintEn: str = ""


SIMPLIFY_BODY_EN = """Use this pass for quality cleanup that preserves current behavior.

Establish the requested scope. When the scope is the working tree, inspect git status and git diff. Follow affected callers to spot duplicate work, unnecessary branches and state, or logic owned by another module. Reuse existing implementations where they fit.

Use Edit for focused changes and give the reason for each one. Compare the original and revised public behavior, including errors and side effects. Run the relevant tests or build and report what they covered."""


def _simplify(_args: str, lang: Lang) -> str:
    return SIMPLIFY_BODY_EN if lang == "en" else SIMPLIFY_BODY


def _remember(args: str, lang: Lang) -> str:
    if not args:
        return ""
    if lang == "en":
        return (
            "Record the user-supplied fact below with MemoryWrite. Pick the storage scope and memory type "
            "that fit how it will be retrieved later: user for personal context, feedback for preferences, "
            "procedural for reusable methods, semantic for project knowledge, or episodic for work history.\n\n"
            + args
        )
    return (
        "用 MemoryWrite 保存下面这条事实。按今后的检索场景选择归属和类型。"
        "个人背景用 user，协作偏好用 feedback，通用方法用 procedural，项目知识用 semantic，工作经过用 episodic。\n\n"
        + args
    )


def _review(args: str, lang: Lang) -> str:
    pull_request = re.fullmatch(r"[0-9]+", args) is not None
    if lang == "en":
        scope = (f"Use Bash to load the proposed changes with gh pr diff {args} and obtain the PR context "
                 f"with gh pr view {args} if needed." if pull_request else
                 "Use git status and git diff to identify the local changes that are ready for review.")
        return (
            f"{scope}\n\n"
            "Trace the affected callers and examine boundaries, error handling, authorization, sensitive data, "
            "and maintenance risks. For each confirmed finding, state the file and line, a trigger, the impact, "
            "and a possible fix. Return a review report with an overall readiness judgment. Keep files unchanged."
        )
    scope = (f"用 Bash 执行 gh pr diff {args} 取得待审改动。如需补充 PR 背景，执行 gh pr view {args}。"
             if pull_request else "先用 git status / git diff 找出当前未提交改动。")
    return (
        f"{scope}\n\n"
        "追踪受影响的调用方，检查正确性、输入边界、错误处理、权限、敏感信息和维护风险。"
        "在报告中逐条写出文件与行号、触发条件、影响及建议修法，最后判断改动是否可交付。保持文件原样。"
    )


def _init(_args: str, lang: Lang) -> str:
    if lang == "en":
        return """Prepare RUOCUN.md for future sessions in this repository.

Gather the project purpose, stack, entry points, and directory layout from the README and build manifests. Check existing AGENTS.md or CLAUDE.md for applicable coding, naming, and testing conventions. Confirm how to build, run, test, and lint.

Use Write to create a concise RUOCUN.md with the verified conventions, commands, and repository-specific pitfalls. Tell the user where to edit the guidance."""
    return """为后续若存会话整理仓库指引。

从 README、构建清单和程序入口确认项目用途、技术栈与主要目录。核对 AGENTS.md 或 CLAUDE.md 中适用的编码、命名和测试约定，并查实构建、启动、测试和 lint 命令。

用 Write 写 RUOCUN.md，收录已核实的约定、命令和项目特有的注意事项。告知用户文件位置和调整方式。"""


def _batch(args: str, lang: Lang) -> str:
    if not args:
        return ""
    if lang == "en":
        return f"""Inspect this request and assign each file to a single owner. Group coupled work, with at most six independent assignments.

If the assignments are independent, send one Agent call with tasks:[...] and isolate:true so each implementation has its own Git worktree and branch. Give each agent enough background to start without this conversation. Include the goal, owned files, deliverable, constraints, and RuoCun tools to use. If the work shares files or depends on unfinished changes, handle the coupled work in the main thread and explain the dependency.

Report the branch changes, review and merge steps, and any conflicts or unfinished work.

Requested change
{args}"""
    return f"""先调查变更范围，为每个文件指定唯一负责人。相互依赖的部分放在一起，最多分成六个独立子任务。

能独立完成的子任务用一次 Agent 调用提交 tasks:[...] 和 isolate:true，让每项实现使用独立 Git worktree 和分支。每份任务说明应包含背景、目标、文件范围、交付物、限制和会用到的若存工具。共用文件或彼此等待的工作由主会话推进，并说明依赖。

汇总各分支的变化、复核和合并方式，以及冲突或遗漏。

用户的改动要求
{args}"""


def _skillify(args: str, lang: Lang) -> str:
    if lang == "en":
        return f"""Extract a procedure that would help in a future session. Leave one-time details out. Record repository conventions in RUOCUN.md.

Write .ruocun/skills/<kebab-name>/SKILL.md. Choose an action-oriented name and put name and description in the front matter. Use up to 60 characters for the trigger description. Put the procedure in the body and aim to stay under 500 characters. Use RuoCun tool names such as Read, Edit, Bash, Grep, Glob and Agent. For a procedure that tends to be skipped under pressure, include signs of drift and the action to take.

Ask whether the user wants to spend resources on subagent checks. With their agreement, use Agent to check correct discovery, false triggers, and whether instructions hold up under pressure. Report the skill as untested if the checks are skipped.

{f"Suggested skill name: {args}" if args else "Choose a name for the procedure."}"""
    return f"""从本次工作中挑出下次还会用的操作方法。仓库约定记入 RUOCUN.md，一次性信息省略。

写入 .ruocun/skills/<kebab-name>/SKILL.md。用动词短横线命名，frontmatter 里填写 name 和 description。描述用不超过 60 字说明触发场景，操作步骤放入正文，尽量控制在 500 字内。使用 Read、Edit、Bash、Grep、Glob、Agent 等若存工具名。容易在压力下省略的步骤，要写清触发信号和应做的动作。

子代理测试会耗用资源，先确认用户是否要跑。获同意后用 Agent 检查正确触发、误触发及压力下的遵循情况。未运行就标记未测。

{f"建议技能名:{args}" if args else "按流程用途拟定技能名。"}"""


BUILTIN_COMMANDS: dict[str, BuiltinCommand] = {
    "simplify": BuiltinCommand(
        "精简当前改动并保持已有行为", "Reduce complexity in current changes while preserving behavior", _simplify,
    ),
    "remember": BuiltinCommand(
        "保存一条今后可检索的记忆", "Save a fact for retrieval in future sessions", _remember,
        "<要记住的事实>", "<fact to remember>",
    ),
    "review": BuiltinCommand(
        "审查本地改动或 PR，报告有证据的发现", "Report review findings for local changes or a GitHub pull request",
        _review, "[PR号]", "[PR number]",
    ),
    "init": BuiltinCommand(
        "查明仓库入口与约定，生成 RUOCUN.md", "Generate RUOCUN.md with verified repository guidance", _init,
    ),
    "batch": BuiltinCommand(
        "把独立子任务派到各自的工作树", "Run independent changes in their own worktrees", _batch,
        "<大改动指令>", "<change request>",
    ),
    "skillify": BuiltinCommand(
        "将可复用流程保存为项目技能", "Save a reusable procedure as a project skill", _skillify,
        "[技能名]", "[skill name]",
    ),
}


def runBuiltinCommand(name: str, args: str, *, lang: Lang = "zh") -> BuiltinResult | None:
    command = BUILTIN_COMMANDS.get(name)
    if command is None:
        return None
    prompt = command.buildPrompt(args.strip(), lang)
    if prompt:
        return {"prompt": prompt}
    usage = f"Usage: /{name} {command.argHintEn}" if lang == "en" else f"用法:/{name} {command.argHint}"
    return {"output": usage.rstrip()}
