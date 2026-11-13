"""Frozen reference tools/sandbox.ts file and network sandbox routing (MIT)."""

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
    """The requested OS sandbox cannot start, so the command is not run."""


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
    """Wrap the approved command and frozen environment without changing its identity."""
    spec = sandboxSpawn(plan.command, plan.cwd, disableSandbox, environ=dict(plan.environment))
    if spec is None:
        return plan
    if "error" in spec:
        raise SandboxUnavailable(str(spec.get("error")))
    return replace(plan, argv=(spec["file"], *spec["args"]), commandLine=None)
