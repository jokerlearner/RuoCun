"""集中管理 Windows 沙箱的写入范围，供子进程和宿主侧文件工具共同判断。

检查前先规范化路径。受保护的控制目录优先拒绝，即使它同时位于可写范围内。
"""

from __future__ import annotations

import hashlib
import os
import sys
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ..config.compat import resolve_env


def canonical(path: str | Path) -> str:
    value = os.fspath(path)
    if (not value or not Path(value).is_absolute() or "\0" in value
            or unicodedata.normalize("NFKC", value) != value
            or any(unicodedata.category(char) in {"Cf", "Co", "Cn", "Cc"} for char in value)):
        raise ValueError("沙箱路径必须是无控制字符的绝对路径。")
    return os.path.normcase(os.path.realpath(os.path.abspath(value)))


def _under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


@dataclass(frozen=True)
class SandboxPolicy:
    executable: str
    stateRoot: str
    tempRoot: str
    cacheRoot: str
    writableRoots: tuple[str, ...]
    protectedRoots: tuple[str, ...]

    def isProtected(self, path: str) -> bool:
        try:
            target = canonical(path)
            return any(_under(target, canonical(root)) for root in self.protectedRoots)
        except ValueError:
            return True

    def allowsWrite(self, path: str) -> bool:
        if self.isProtected(path):
            return False
        try:
            target = canonical(path)
            return any(_under(target, canonical(root)) for root in (*self.writableRoots, self.tempRoot, self.cacheRoot))
        except ValueError:
            return False


def createSandboxPolicy(workspaceRoot: str | Path, environ: Mapping[str, str] | None = None) -> SandboxPolicy | None:
    values = os.environ if environ is None else environ
    if sys.platform != "win32" or resolve_env("SANDBOX", values) != "1":
        return None
    workspace = Path(canonical(workspaceRoot))
    if workspace.parent == workspace:
        raise ValueError("沙箱工作区不能是整个磁盘根目录。")
    lowered = {key.casefold(): value for key, value in values.items()}
    home = lowered.get("userprofile") or lowered.get("home") or str(Path.home())
    base = Path(canonical(home)) / ".ruocun" / "sandbox"
    executable = canonical(resolve_env("SANDBOX_CLI", values) or
                           str(base.parent / "dependencies/codex/0.169.0/bin/codex.exe"))
    package = Path(executable).parent
    if package.name.casefold() == "bin":
        package = package.parent
    key = hashlib.sha256(str(workspace).encode("utf-8")).hexdigest()[:16]
    work = base / "work" / key
    state = str(base / "control")
    user_root = base.parent
    protected = tuple(dict.fromkeys((state, str(user_root / "sessions"), str(user_root / "runtime"),
                                     str(package), canonical(sys.prefix), canonical(sys.base_prefix))))
    return SandboxPolicy(executable, state, str(work / "temp"), str(work / "cache"),
                         (str(workspace),), protected)


def sandboxEnvironment(environ: Mapping[str, str], policy: SandboxPolicy | None) -> dict[str, str]:
    if policy is None:
        return dict(environ)
    from .windows.sandbox import windowsSandboxEnvironment
    return windowsSandboxEnvironment(environ, stateRoot=policy.stateRoot,
                                     tempRoot=policy.tempRoot, cacheRoot=policy.cacheRoot)


def parseSandboxPolicy(value: dict[str, object]) -> SandboxPolicy:
    data = dict(value)
    for key in ("writableRoots", "protectedRoots"):
        roots = data.get(key)
        if not isinstance(roots, (list, tuple)) or not all(isinstance(root, str) for root in roots):
            raise ValueError("沙箱执行计划缺少冻结目录列表。")
        data[key] = tuple(roots)
    names = ("executable", "stateRoot", "tempRoot", "cacheRoot")
    if set(data) != {*names, "writableRoots", "protectedRoots"} or not all(isinstance(data.get(name), str) for name in names):
        raise ValueError("沙箱执行计划字段无效。")
    return SandboxPolicy(str(data["executable"]), str(data["stateRoot"]), str(data["tempRoot"]),
                         str(data["cacheRoot"]), cast(tuple[str, ...], data["writableRoots"]),
                         cast(tuple[str, ...], data["protectedRoots"]))
