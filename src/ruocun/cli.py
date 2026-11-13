"""Lightweight composition-root entry; business runtime is implemented by later tasks.

Version flag intent: frozen reference src/index.ts:216-220 (MIT).

任务04 扩展：``--chat-demo <合成配置目录> [--model <id>] [prompt...]`` 走
一次性 prompt 产品路径（合成账户配置 + 本地合成 SSE 服务）。这是显式演示/验收
入口；既有 ``--version`` / ``--help`` / 包资源 / 普通 Agent 退出码 69 行为不变，
完整 Agent 运行路径仍由后续任务实现，未实现处不返回占位成功。

任务05 扩展：``--responses-demo <合成配置目录> [--model <id>] [prompt...]`` 走
Responses 路由的同一对话/工具回合（合成账户配置 + 本地合成 HTTP/SSE 服务 +
注入式 transport 重写端点）。同样是显式演示入口，不改变任何既有行为。
"""

from __future__ import annotations

import asyncio
import json
import sys
import threading
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from .chat_demo import ChatConfigError, run_chat_demo
from .responses_demo import ResponsesDemoError, run_responses_demo
from .version import __version__


def _error(message: str) -> None:
    print(message, file=sys.stderr)


def _chat_demo(arguments: list[str]) -> int:
    index = arguments.index("--chat-demo")
    tail = arguments[index + 1:]
    if not tail:
        _error("RuoCun：--chat-demo 需要合成配置目录。")
        return 71
    config_dir = Path(tail[0])
    rest = tail[1:]
    model_override: str | None = None
    prompt_tokens: list[str] = []
    i = 0
    while i < len(rest):
        if rest[i] == "--model" and i + 1 < len(rest):
            model_override = rest[i + 1]
            i += 2
        else:
            prompt_tokens.append(rest[i])
            i += 1
    prompt = " ".join(prompt_tokens) or "你好"
    try:
        report = run_chat_demo(config_dir, prompt, model_override=model_override)
    except (ChatConfigError, OSError, ValueError, UnicodeError) as exc:
        _error(f"RuoCun：一次性对话失败（{type(exc).__name__}）：{exc}")
        return 71
    print(json.dumps(report, ensure_ascii=False))
    return 0


def _responses_demo(arguments: list[str]) -> int:
    index = arguments.index("--responses-demo")
    tail = arguments[index + 1:]
    if not tail:
        _error("RuoCun：--responses-demo 需要合成配置目录。")
        return 71
    config_dir = Path(tail[0])
    rest = tail[1:]
    model_override: str | None = None
    prompt_tokens: list[str] = []
    i = 0
    while i < len(rest):
        if rest[i] == "--model" and i + 1 < len(rest):
            model_override = rest[i + 1]
            i += 2
        else:
            prompt_tokens.append(rest[i])
            i += 1
    prompt = " ".join(prompt_tokens) or "看图并读文件"
    try:
        report = run_responses_demo(config_dir, prompt, model_override=model_override)
    except (ResponsesDemoError, OSError, ValueError, UnicodeError, RuntimeError) as exc:
        _error(f"RuoCun：Responses 演示失败（{type(exc).__name__}）：{exc}")
        return 71
    print(json.dumps(report, ensure_ascii=False))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    options = arguments[:arguments.index("--")] if "--" in arguments else arguments
    if arguments == ["--ruocun-ipc-helper"]:
        from .platform.windows.ipc import helper_main

        return helper_main()
    if len(arguments) == 2 and arguments[0] == "--ruocun-shell-runner":
        from .tools.shell_runner import main as runner_main

        return runner_main(Path(arguments[1]))
    if "--version" in options or "-v" in options:
        print(f"RuoCun v{__version__}")
        return 0
    if arguments and arguments[0] == "Schedule":
        from .schedule import ScheduleService

        service = ScheduleService()
        def write(text: str) -> None:
            sys.stdout.write(text)
        action = arguments[1] if len(arguments) > 1 else ""
        try:
            if action == "add" and len(arguments) > 3:
                ok = asyncio.run(service.add(arguments[2], " ".join(arguments[3:]), str(Path.cwd()), write))
            elif action == "list":
                ok = asyncio.run(service.list(write))
            elif action == "remove" and len(arguments) > 2:
                ok = asyncio.run(service.remove(int(arguments[2]), write))
            else:
                _error('用法: ruocun Schedule add "<cron>" "<prompt>" | list | remove <n>')
                return 1
            return 0 if ok else 1
        except Exception as exc:
            _error(f"系统定时未完成（{type(exc).__name__}），请核对现有任务；未自动重试。")
            return 1
    if len(arguments) >= 2 and arguments[:2] == ["Skill", "add"]:
        from .skills.install import installSkills

        source = next((item for item in arguments[2:] if not item.startswith("--")), None)
        if source is None:
            _error("用法: ruocun Skill add <git-url|本地路径> [--user|--project]")
            return 1
        try:
            installed = asyncio.run(installSkills(source, "project" if "--project" in arguments[2:] else "user",
                Path.cwd(), Path.home() / ".ruocun", threading.Event()))
            print(installed.format())
            return 1 if installed.error else 0
        except Exception as exc:
            _error(f"技能安装未确认（{type(exc).__name__}），保留现场，未自动重试。")
            return 1
    if "--help" in options or "-h" in options:
        try:
            help_text = files("ruocun").joinpath("resources/help.zh-CN.txt").read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeError) as exc:
            _error(f"RuoCun：无法读取帮助资源（{type(exc).__name__}）。")
            return 70
        print(help_text, end="")
        return 0
    if "--chat-demo" in options:
        return _chat_demo(arguments)
    if "--responses-demo" in options:
        return _responses_demo(arguments)
    from .agent.runtime import run_cli

    return run_cli(arguments)
