"""按实际平台封装命令计划，应用可选的文件和网络沙箱。

开启后按环境选择 Windows MXC、macOS sandbox-exec 或 Linux bwrap。启动准备失败会返回明确错误，避免命令落到普通 Shell 执行。
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, TypedDict

from ..config.compat import resolve_env

if TYPE_CHECKING:
    from .shell_plan import ShellExecutionPlan

_BINARY_DIRS = ("/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin")


class SandboxUnavailable(RuntimeError):
    """请求的操作系统沙箱无法准备，命令未启动。"""


class SpawnSpec(TypedDict):
    file: str
    args: list[str]


class SandboxError(TypedDict):
    error: str


def sandboxActive(environ: Mapping[str, str] | None = None) -> bool:
    return resolve_env("SANDBOX", os.environ if environ is None else environ) == "1"


def sandboxNoNet(environ: Mapping[str, str] | None = None) -> bool:
    return resolve_env("SANDBOX_NO_NET", os.environ if environ is None else environ) == "1"


def _binary(name: str, exists: Callable[[str], bool]) -> str | None:
    return next((f"{directory}/{name}" for directory in _BINARY_DIRS if exists(f"{directory}/{name}")), None)


def _seatbelt(cwd: str, no_net: bool) -> str:
    workspace = cwd.replace("\\", "\\\\").replace('"', '\\"')
    return (
        '(version 1) (allow default) (deny file-write*) '
        f'(allow file-write* (subpath "{workspace}") (subpath "/tmp") (subpath "/private/tmp") '
        '(subpath "/private/var/folders") (literal "/dev/null") (literal "/dev/stdout") '
        '(literal "/dev/stderr") (literal "/dev/dtracehelper"))'
        + (" (deny network*)" if no_net else "")
    )


def sandboxSpawn(command: str, cwd: str, disableSandbox: bool = False, *,
                 environ: Mapping[str, str] | None = None, platform: str | None = None,
                 exists: Callable[[str], bool] = os.path.exists) -> SpawnSpec | SandboxError | None:
    if not sandboxActive(environ) or disableSandbox:
        return None
    current = sys.platform if platform is None else platform
    shell = ["/bin/sh", "-c", command]
    no_net = sandboxNoNet(environ)
    if current == "darwin":
        binary = _binary("sandbox-exec", exists)
        if binary is None:
            return {"error": "RUOCUN_SANDBOX=1 但找不到 sandbox-exec"}
        return {"file": binary, "args": ["-p", _seatbelt(cwd, no_net), *shell]}
    if current == "linux":
        binary = _binary("bwrap", exists)
        if binary is None:
            return {"error": "RUOCUN_SANDBOX=1 但找不到 bwrap(请装 bubblewrap)"}
        args = ["--ro-bind", "/", "/", "--bind", cwd, cwd, "--tmpfs", "/tmp",
                "--proc", "/proc", "--dev", "/dev", "--die-with-parent"]
        if no_net:
            args.append("--unshare-net")
        return {"file": binary, "args": [*args, *shell]}
    return {"error": "当前平台不支持沙箱(仅 macOS/Linux)"}


def sandboxExecutionPlan(plan: ShellExecutionPlan, disableSandbox: bool = False) -> ShellExecutionPlan:
    """用本平台的沙箱包装已审批命令，保留计划中的原命令与工作目录。"""
    if sys.platform == "win32" and (plan.sandbox is not None or sandboxActive(dict(plan.environment))):
        if disableSandbox:
            raise SandboxUnavailable("Windows 沙箱已开启，不能整次绕过；请请求本次额外可写目录。")
        from .sandbox_policy import canonical, createSandboxPolicy, sandboxEnvironment
        from .windows.sandbox import (
            WindowsSandboxError,
            validateWindowsSandbox,
            windowsSandboxExecutionPlan,
        )
        policy = plan.sandbox or createSandboxPolicy(plan.cwd, dict(plan.environment))
        assert policy is not None
        try:
            if canonical(plan.argv[0]) == canonical(policy.executable) and plan.commandLine is None:
                validateWindowsSandbox(policy.executable)
                return plan
            environment = sandboxEnvironment(dict(plan.environment), policy)
            frozen = replace(plan, environment=tuple(sorted(environment.items())), sandbox=policy)
            return windowsSandboxExecutionPlan(
                frozen, executable=policy.executable, stateRoot=policy.stateRoot,
                writableRoots=policy.writableRoots, tempRoot=policy.tempRoot, cacheRoot=policy.cacheRoot,
                protectedRoots=policy.protectedRoots, noNet=sandboxNoNet(environment),
            )
        except (OSError, ValueError, WindowsSandboxError) as error:
            raise SandboxUnavailable(f"Windows MXC 沙箱启动准备失败，命令未执行：{error}") from error
    spec = sandboxSpawn(plan.command, plan.cwd, disableSandbox, environ=dict(plan.environment))
    if spec is None:
        return plan
    if "error" in spec:
        raise SandboxUnavailable(str(spec.get("error")))
    return replace(plan, argv=(spec["file"], *spec["args"]), commandLine=None)
