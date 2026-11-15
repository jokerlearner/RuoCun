"""通过固定版本的 Codex CLI 创建 Windows MXC 沙箱执行计划。

提前准备私有临时目录，并把控制目录和解释器等可信资源排除在可写范围外。执行时沿用审批依据中的命令、工作目录和环境。
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

from ..file_contract import AtomicFileError
from ..process_tree import scrubbed_env
from ..shell_plan import ShellExecutionPlan
from .durable_file import (
    PrivateDirectory,
    atomic_publish,
    ensure_private_dir,
    verify_private_file,
)

CODEX_VERSION = "0.169.0"
CODEX_SHA256 = "ce1945eb440b5481ed1233ebaf32b7056ee7e4e452fa62ffe1cbfb26103cdee0"
_BASE_CONFIG = b"# RuoCun-owned sandbox configuration; no user profile.\n"
_BRIDGE = (
    "import base64,os,subprocess,sys;"
    "os.environ.update({key:sys.argv[3] for key in ('TEMP','TMP','TMPDIR')});"
    "raw=base64.b64decode(sys.argv[1]).decode('utf-8');"
    "raise SystemExit(subprocess.call(raw,executable=sys.argv[2],shell=False,"
    "stdin=sys.stdin,stdout=sys.stdout,stderr=sys.stderr,creationflags=subprocess.CREATE_NO_WINDOW))"
)
_MAX_COMMAND_UNITS = 32766


class WindowsSandboxError(RuntimeError):
    """Windows 沙箱无法在指定边界内准备，原命令尚未启动。"""


def _absolute(value: str) -> Path:
    path = Path(value)
    if (not path.is_absolute() or not re.fullmatch(r"[A-Za-z]:", path.drive)
            or any(ord(char) < 32 for char in value)):
        raise WindowsSandboxError("Windows沙箱要求固定本地卷上的绝对路径。")
    return path.resolve()


def _within(path: Path, root: Path) -> bool:
    return path.is_relative_to(root)


def _setenv(values: dict[str, str], name: str, value: str) -> None:
    for key in tuple(values):
        if key.casefold() == name.casefold():
            del values[key]
    values[name] = value


def windowsSandboxEnvironment(
    environ: Mapping[str, str], *, stateRoot: str, tempRoot: str, cacheRoot: str,
) -> dict[str, str]:
    """审批前准备沙箱子进程的环境，沿用 HOME 和 PATH。"""
    state, temporary, cache = map(_absolute, (stateRoot, tempRoot, cacheRoot))
    values = scrubbed_env(environ)
    system = next((value for key, value in values.items() if key.casefold() == "systemroot"), r"C:\Windows")
    _setenv(values, "SystemDrive", _absolute(system).drive)
    for name, value in (
        ("CODEX_HOME", state), ("TEMP", temporary), ("TMP", temporary), ("TMPDIR", temporary),
        ("PIP_CACHE_DIR", cache / "pip"), ("npm_config_cache", cache / "npm"),
        ("GRADLE_USER_HOME", cache / "gradle"),
    ):
        _setenv(values, name, str(value))
    maven = next((value for key, value in values.items() if key.casefold() == "maven_opts"), "")
    repository = f'-Dmaven.repo.local="{cache / "maven"}"'
    _setenv(values, "MAVEN_OPTS", maven if repository in maven else (maven + " " + repository).strip())
    # 先创建带私有权限的目录，再把 TEMP 指向它。
    # 进程身份查询等启动组件也会尝试创建 TEMP，
    # 如果在它们运行前目录不存在，就可能继承普通 ACL。
    try:
        for directory in (state, temporary, cache):
            _private_tree(directory)
    except (AtomicFileError, OSError) as error:
        raise WindowsSandboxError("Windows沙箱受控目录无法在启动前安全准备。") from error
    return values


def _private_tree(path: Path) -> None:
    missing: list[Path] = []
    ancestor = path
    while not ancestor.exists():
        missing.append(ancestor)
        ancestor = ancestor.parent
    for item in reversed(missing):
        ensure_private_dir(item)
    ensure_private_dir(path)


def _immutable(path: Path, content: bytes) -> None:
    if path.exists():
        verify_private_file(path)
        if path.read_bytes() != content:
            raise WindowsSandboxError("Windows沙箱受控配置已改变，拒绝覆盖或执行。")
    else:
        atomic_publish(path, content)


def _executable(value: str) -> Path:
    executable = _absolute(value)
    if executable.suffix.casefold() != ".exe" or not executable.is_file():
        raise WindowsSandboxError(f"缺少固定Codex CLI {CODEX_VERSION}，请配置官方独立可执行文件的绝对路径。")
    digest = hashlib.sha256()
    with executable.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != CODEX_SHA256:
        raise WindowsSandboxError(f"Codex CLI不是已核验的官方{CODEX_VERSION}构建或文件已改变，拒绝执行。")
    return executable


def validateWindowsSandbox(executable: str) -> None:
    """核对固定的本地 CLI 依赖，验证过程不启动命令。"""
    _executable(executable)


def _profile(writable: Sequence[Path], protected: Sequence[Path], no_net: bool) -> bytes:
    lines = [
        'default_permissions = "ruocun"', '[windows]', 'sandbox = "mxc"',
        '[features]', 'network_proxy = false', '[shell_environment_policy]', 'inherit = "all"',
        '[permissions.ruocun.filesystem]', '":root" = "read"',
    ]
    for paths, access in ((writable, "write"), (protected, "read")):
        lines.extend(f'{json.dumps(str(path), ensure_ascii=False)} = "{access}"' for path in paths)
    lines += ['[permissions.ruocun.network]', f'enabled = {str(not no_net).lower()}', '']
    return "\n".join(lines).encode("utf-8")


def windowsSandboxExecutionPlan(
    plan: ShellExecutionPlan, *, executable: str, stateRoot: str, writableRoots: Sequence[str],
    tempRoot: str, cacheRoot: str, protectedRoots: Sequence[str] = (), noNet: bool = False,
) -> ShellExecutionPlan:
    """将已获批准的环境和限制转为固定的 Codex CLI 调用。"""
    if sys.platform != "win32":
        raise WindowsSandboxError("Windows MXC后端仅支持原生Windows。")
    try:
        cli = _executable(executable)
        state, temporary, cache = map(_absolute, (stateRoot, tempRoot, cacheRoot))
        environment = dict(plan.environment)
        if windowsSandboxEnvironment(environment, stateRoot=stateRoot, tempRoot=tempRoot, cacheRoot=cacheRoot) != environment:
            raise WindowsSandboxError("沙箱环境尚未在审批前冻结，命令未执行。")
        python = _absolute(sys.executable)
        protected = sorted({state, cli.parent, *map(_absolute, protectedRoots),
                            _absolute(sys.prefix), _absolute(sys.base_prefix)})
        writable = sorted({_absolute(root) for root in writableRoots} | {temporary, cache})
        if not writableRoots or any(_within(root, blocked) for root in writable for blocked in protected):
            raise WindowsSandboxError("沙箱写目录与受保护控制文件或运行库冲突，命令未执行。")
        command = plan.commandLine
        expected = f'"{plan.argv[0]}" /d /s /c "{plan.command}"' if plan.argv else None
        if (plan.dialect != "cmd" or command is None or command != expected
                or plan.argv[1:] != ("/d", "/s", "/c", plan.command)
                or Path(plan.argv[0]).name.casefold() != "cmd.exe"):
            raise WindowsSandboxError("Windows沙箱不能保真执行该Shell计划，命令未执行。")
        content = _profile(writable, protected, noNet)
        name = "ruocun-" + hashlib.sha256(content).hexdigest()
        encoded = base64.b64encode(command.encode("utf-8")).decode("ascii")
        argv = (str(cli), "-c", 'windows.sandbox="mxc"', "sandbox", "--profile", name,
                "--permission-profile", "ruocun", "--cd", plan.cwd, "--",
                str(python), "-I", "-c", _BRIDGE, encoded, plan.argv[0], str(temporary))
        for text in (command, subprocess.list2cmdline(argv)):
            if len(text.encode("utf-16-le")) // 2 > _MAX_COMMAND_UNITS:
                raise WindowsSandboxError("Windows沙箱命令超过原生命令行长度限制，命令未执行。")
        for directory in (state, temporary, cache):
            _private_tree(directory)
        with PrivateDirectory(state):
            _immutable(state / "config.toml", _BASE_CONFIG)
            _immutable(state / (name + ".config.toml"), content)
        return replace(plan, argv=argv, commandLine=None)
    except WindowsSandboxError:
        raise
    except (AtomicFileError, OSError, ValueError) as error:
        raise WindowsSandboxError("Windows沙箱依赖或受控目录不可用，命令未执行。") from error
