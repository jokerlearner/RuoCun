"""把 Bash 工具请求转换为 Shell 执行计划，应用批准的沙箱边界后交给执行后端。

本模块还负责整理输出、创建备份和保存超长输出。宿主程序执行这些写入时也要核对路径策略。
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import uuid
from pathlib import Path
from typing import Any, Literal

from ..platform.process_tree import run_foreground_plan
from ..platform.sandbox import SandboxUnavailable, sandboxExecutionPlan
from ..platform.sandbox_policy import SandboxPolicy
from ..platform.shell_plan import buildShellPlan
from .paths import classifyPath
from .sandbox import prepareSandboxPlan
from .types import Tool, ToolContext, ToolRejected

_PYTHON_INLINE = re.compile(r"(?:^|[\s;&|])python3?\s+-c\b")
_DB_EXT = r"db|db3|sqlite3?|mdb|accdb|rdb|aof|fdb|gdb|kdbx|dbf"
_DB_BACKUP_SUFFIX = ".ruocun-backup"
_TEXT_EXT = r"jsonl?|md|txt|log|csv|ya?ml|toml|ini|tsv"
_CRASH = re.compile(
    r"Segmentation fault|core dumped|\bSIG(SEGV|ABRT|ILL|FPE|BUS)\b|"
    r"malloc\(\):\s*(corrupted|invalid)|free\(\):\s*(invalid|double free)|"
    r"double free or corruption|stack smashing detected|AddressSanitizer|^Aborted(?:\s*\(core dumped\))?\s*$",
    re.I | re.M,
)
_pythonInlineStreak = 0
_pythonInlineNudged = False


def _references(command: str, extensions: str) -> list[str]:
    # 按后缀提取可能出现在命令里的路径，匹配 Windows 盘符和带引号的空格路径。
    pattern = re.compile(
        rf"(['\"])([^'\"\r\n]+\.(?:{extensions})(?!\w))\1|"
        rf"((?:[A-Za-z]:[\\/]|[.\w/\\])[\w./\\:-]*\.(?:{extensions})(?!\w))", re.I
    )
    return [match.group(2) or match.group(3) for match in pattern.finditer(command)]


def _backup_databases(command: str, cwd: str, *, workspace_only: bool = False, policy: SandboxPolicy | None = None) -> str | None:
    targets: dict[Path, str] = {}
    for name in _references(command, _DB_EXT):
        for suffix in ("", "-wal", "-shm", "-journal"):
            path = Path(cwd) / (name + suffix)
            targets[path] = name + suffix
    backed: list[str] = []
    for path, name in targets.items():
        backup = Path(str(path) + _DB_BACKUP_SUFFIX)
        try:
            if policy is not None and not policy.allowsWrite(str(backup.absolute())):
                continue
            if workspace_only and any(classifyPath(cwd, str(candidate)).external for candidate in (path, backup)):
                continue
            if path.is_file() and not backup.exists():
                # 只在备份尚不存在时创建一份，保留最早的备份。
                with path.open("rb") as source, backup.open("xb") as dest:
                    shutil.copyfileobj(source, dest)
                backed.append(name)
        except OSError:
            continue
    if not backed:
        return None
    return (
        f"[自动备份] 检测到命令涉及数据库文件，已在执行前备份到同名 + {_DB_BACKUP_SUFFIX} 后缀"
        f"（{'、'.join(backed)}）；数据库查询也可能自动修复或重写原始文件。"
        "首版退出时保留这些备份；请确认无需恢复后手动清理。"
    )


async def cleanupDbBackups(workspaceRoot: str) -> int:
    """保留已创建的数据库备份。

    仅凭路径无法确认同名文件仍属于这次运行，自动清理会误删用户后来放入的文件。
    创建回执会给出备份位置。
    """
    return 0


def _spill_output(content: str, cwd: str, *, workspace_only: bool = False, policy: SandboxPolicy | None = None) -> str:
    if len(content) <= 16000:
        return content
    pointer = ""
    try:
        path = Path(cwd) / ".ruocun" / "spill" / (uuid.uuid4().hex + ".txt")
        if ((not workspace_only or not classifyPath(cwd, str(path)).external)
                and (policy is None or policy.allowsWrite(str(path.absolute())))):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            pointer = f"\n[完整输出 {len(content)} 字符已落盘:{path}；需要完整内容时用Read读取]"
    except OSError:
        pass
    return (
        content[:9600] + f"\n…(已省略中间 {len(content) - 16000} 字符,共 {len(content)} 字符)…\n"
        + content[-6400:] + pointer
    )


def _check(raw: str) -> Literal["ask"] | None:
    try:
        args = json.loads(raw)
    except ValueError:
        return None
    return "ask" if isinstance(args, dict) and args.get("dangerouslyDisableSandbox") is True else None


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    global _pythonInlineStreak, _pythonInlineNudged
    background = bool(args.get("background"))
    unsupported = set(args) - {"command", "description", "background", "dangerouslyDisableSandbox", "additionalWriteDirectories"}
    if unsupported:
        return "首版不支持这些Bash参数；命令未执行：" + ", ".join(sorted(unsupported))
    command = args["command"]
    execution_signal = ctx.signal
    if execution_signal.is_set():
        return "[已中断,运行 0s]"
    sleep = re.match(r"^\s*sleep\s+(\d+(?:\.\d+)?)\s*(?:&&|;|\||$)", command)
    if sleep and float(sleep.group(1)) >= 2 and not background:
        return (
            "不要用 sleep 阻塞等待。等待当前会话已登记的后台任务时，单独调用TaskWait；"
            "请直接运行需要完成的前台命令，或将可拆分的工作分步执行。命令未执行。"
        )
    cwd = ctx.cwd or ctx.workspaceRoot
    inline = bool(_PYTHON_INLINE.search(command))
    if inline:
        for name in _references(command, _TEXT_EXT):
            try:
                path = Path(cwd) / name
                if path.is_file() and path.stat().st_size <= 200 * 1024:
                    return (
                        f"不用写 python 脚本——{name} 只有 {path.stat().st_size / 1024:.1f}KB，"
                        "一次Read就能读完，或用Grep定位关键字。命令未执行；复杂处理请先说明理由。"
                    )
            except OSError:
                continue
        _pythonInlineStreak += 1
    else:
        _pythonInlineStreak, _pythonInlineNudged = 0, False
    plan = ctx.getShellPlan(command, cwd) if ctx.getShellPlan is not None else buildShellPlan(command, cwd, analyze=False)
    plan = await prepareSandboxPlan(plan, ctx, args.get("additionalWriteDirectories"))
    if plan.sandbox is not None and args.get("dangerouslyDisableSandbox") is True:
        raise ToolRejected("Windows 沙箱已开启，不能整次绕过；请请求本次额外可写目录。")
    # 单次绕过仅限前台命令，后台继续按既定执行边界运行。
    disable_sandbox = not background and args.get("dangerouslyDisableSandbox") is True
    try:
        execution_plan = sandboxExecutionPlan(plan, disable_sandbox)
    except SandboxUnavailable as error:
        raise ToolRejected(str(error)) from error
    if background and ctx.managedShell is None:
        return "首版不支持 background=true；命令未执行。请使用前台执行。"
    if background and os.name != "nt":
        raise ToolRejected("当前环境未提供可恢复Shell执行后端，命令未执行。")
    sandboxed = execution_plan is not plan
    # 备份由宿主程序写入，子进程沙箱的路径限制在此处也需显式检查。
    backup_notice = _backup_databases(command, plan.cwd, workspace_only=sandboxed, policy=plan.sandbox)
    output_callback = ctx.onShellOutput
    if ctx.managedShell is not None and (os.name == "nt" or background):
        managed = await ctx.managedShell.execute(plan, execution_signal, background=background,
                                                 onOutput=output_callback, disableSandbox=disable_sandbox)
        if isinstance(managed, str):
            return (backup_notice + "\n" if backup_notice else "") + managed
        result = managed
    else:
        result = None
    loop = asyncio.get_running_loop()
    observer_error: str | None = None

    def deliver(stream: Literal["stdout", "stderr"], text: str) -> None:
        nonlocal observer_error
        if output_callback is not None and observer_error is None and not execution_signal.is_set():
            try:
                output_callback(stream, text)
            except Exception as error:
                observer_error = type(error).__name__

    def enqueue(stream: Literal["stdout", "stderr"], text: str) -> None:
        loop.call_soon_threadsafe(deliver, stream, text)

    if result is None:
        execution = asyncio.create_task(asyncio.to_thread(
            run_foreground_plan, execution_plan, execution_signal, onOutput=enqueue if output_callback is not None else None,
        ))
        try:
            result = await asyncio.shield(execution)
        except asyncio.CancelledError:
            execution_signal.set()
            await execution  # 等待真正的进程树退出后，再结束本地等待。
            raise
        except FileNotFoundError as error:
            if execution_plan is plan:
                raise
            raise ToolRejected("沙箱启动文件或工作目录不可用，命令未执行。") from error
    ctx.pendingUnverifiedWrites.clear()
    if ctx.headless and ctx.todoWriteRequired is not None and (
        result.code in {132, 134, 135, 136, 139}
        or _CRASH.search(result.stdout + result.stderr)
    ):
        ctx.todoWriteRequired["done"] = False
    parts: list[str] = []
    if observer_error is not None:
        parts.append(f"[实时输出不可用（{observer_error}）；完整工具结果保留如下]")
    if backup_notice:
        parts.append(backup_notice)
    if result.stdout.strip():
        parts.append(result.stdout.rstrip())
    if result.stderr.strip():
        parts.append("[stderr]\n" + result.stderr.rstrip())
    status = "已中断" if result.aborted else f"exit {result.code}"
    parts.append(f"[{status},运行 {round(result.elapsedMs / 1000)}s]")
    if inline and _pythonInlineStreak >= 3 and not _pythonInlineNudged:
        _pythonInlineNudged = True
        parts.append(
            f"[提示] 连续 {_pythonInlineStreak} 次用 python3 -c 内联脚本做一次性分析；"
            "简单搜索优先用Grep，通读文件用Read；复杂解析请用Write保存为.py文件后执行。"
        )
    if result.aborted and re.search(r"(?:^|[\s;&|])(apt-get|apt|dpkg|aptitude)(?=\s|$|;|&|\|)", command):
        # 恢复包管理器会再次写入系统，先提示用户单独批准恢复命令。
        parts.append("[需恢复] 包管理器命令被中断；继续前请审批并执行 dpkg --configure -a 检查修复状态。")
    return _spill_output("\n".join(parts), plan.cwd, workspace_only=sandboxed, policy=plan.sandbox)


execShellTool = Tool(
    name="Bash",
    description=(
        "在工作区前台执行Shell命令，返回stdout/stderr和退出码。Windows默认使用cmd语法；"
        "PowerShell/pwsh/Bash须显式调用，按实际方言审批；非Windows使用/bin/sh。"
        "没有超时，Ctrl+C停止当前前台受管树；已绑定可恢复后端时支持background=true及同run转后台。"
        "Shell退出后遗留的受管子孙也会停止。查询内容用Grep、查路径用Glob、读文件用Read。"
        "系统沙箱默认关闭；RUOCUN_SANDBOX=1 时Windows使用固定独立Codex CLI/MXC，macOS/Linux沿用原生后端。"
        "Windows开启后失败即报错且不能整次绕过；additionalWriteDirectories仅请求本次目录，仍需用户明确批准。"
    ),
    schema={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的Shell命令；Windows默认cmd，其他解释器显式调用"},
            "description": {"type": "string", "description": "命令的语义描述（用于审计日志）"},
            "background": {"type": "boolean", "description": "true启动为可重连后台Shell，默认false"},
            "dangerouslyDisableSandbox": {"type": "boolean", "description": "Windows沙箱开启时禁止；其它后端仅本次前台绕过并强制审批"},
            "additionalWriteDirectories": {"type": "array", "items": {"type": "string", "minLength": 1}, "maxItems": 8,
                                           "description": "请求本次额外可写的绝对目录；需逐次用户批准，不代表已获授权"},
        },
        "required": ["command"],
        "additionalProperties": False,
    },
    capability="exec", approval="required", checkPermissions=_check, handler=_handler,
)
