"""冻结 skills/install.ts（MIT）的原生技能安装与目录发布。"""

from __future__ import annotations

import asyncio
import os
import shutil
import stat
import sys
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Literal, Protocol

from ..platform.file_contract import AtomicFileError
from ..platform.process_tree import ForegroundResult, run_foreground_argv
from ..platform.windows.durable_file import sync_directory
from ..tools.paths import fileLock
from .bundled import BUNDLED_SKILLS

InstallScope = Literal["user", "project"]


class GitRunner(Protocol):
    def __call__(
        self, argv: list[str], cwd: str, signal: Event, *, environ: Mapping[str, str] | None = None,
    ) -> ForegroundResult: ...


class InstallUnconfirmed(RuntimeError):
    """进程退出或目录发布未确认。保留本次现场，不得自动重放。"""


class _InstallFailure(ValueError):
    """失败边界已知，已发布目录另计。"""


@dataclass(frozen=True, slots=True)
class InstallResult:
    destination: Path
    scope: InstallScope
    installed: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    found: bool = False
    error: str | None = None

    def format(self, *, refreshing: bool = False) -> str:
        rows = [f"Error: {self.error}"] if self.error else []
        if self.found or self.installed:
            layer = "用户级,跨项目可用" if self.scope == "user" else "项目级,仅本项目"
            rows.append(f"✓ 安装 {len(self.installed)} 个技能 → {self.destination}({layer})")
        elif not self.error:
            rows.append("未找到任何含 SKILL.md 的技能。")
        if self.warnings:
            rows.append("注意:\n" + "\n".join(f"  - {item}" for item in self.warnings))
        bundled = {item["name"] for item in BUNDLED_SKILLS if item.get("core")}
        shadowed = [name for name in self.installed if name in bundled]
        if shadowed:
            names = "、".join(f"'{name}'" for name in shadowed)
            rows.append(f"提示:{names} 覆盖了内置同名技能。可在 /skills 管理开关。")
        if self.installed:
            availability = "工具结果保存后刷新本会话技能目录" if refreshing else "重启 RuoCun 生效"
            rows.append(f"({availability};启动只列 name+description,模型按需用 Skill 加载正文。"
                        "外来技能首次加载时自动按用途转换工具名并缓存。)")
        return "\n".join(rows)


def _check_cancel(signal: Event) -> None:
    if signal.is_set():
        raise _InstallFailure("技能安装已取消。")


def _linked(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _plain(path: Path) -> os.stat_result:
    info = path.lstat()
    if _linked(info):
        raise _InstallFailure("技能目录包含链接或重解析点，无法安全复制完整资源。")
    return info


def _directory(path: Path) -> None:
    if not stat.S_ISDIR(_plain(path).st_mode):
        raise _InstallFailure("技能目录位置不是普通目录。")


def _git_admin(path: Path) -> bool:
    return os.path.normcase(path.name) == os.path.normcase(".git")


def _local_source(workspace: Path, source: str) -> Path:
    path = Path(os.path.abspath(workspace / source))
    try:
        _plain(path)
    except FileNotFoundError:
        return path
    if path.resolve(strict=True) != path:
        raise _InstallFailure("本地技能源路径经过链接或重解析点。")
    return path


def _find(root: Path, signal: Event) -> Iterator[Path]:
    _check_cancel(signal)
    try:
        marker = _plain(root / "SKILL.md")
    except FileNotFoundError:
        pass
    else:
        if stat.S_ISREG(marker.st_mode):
            yield root
            return
    for child in sorted(root.iterdir()):
        info = child.lstat()
        if not _git_admin(child) and not _linked(info) and stat.S_ISDIR(info.st_mode):
            yield from _find(child, signal)


def _copy(source: Path, target: Path, signal: Event, *, omit_git: bool = False) -> None:
    _check_cancel(signal)
    mode = _plain(source).st_mode
    if stat.S_ISDIR(mode):
        target.mkdir(exist_ok=True)
        for item in source.iterdir():
            if not omit_git or not _git_admin(item):  # 导入时不复制可能含远程地址的 Git 元数据。
                _copy(item, target / item.name, signal, omit_git=omit_git)
        if sys.platform == "win32":
            sync_directory(target)
    elif stat.S_ISREG(mode):
        with source.open("rb") as src, target.open("wb") as dst:
            while chunk := src.read(1024 * 1024):
                _check_cancel(signal)
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
    else:
        raise _InstallFailure("技能目录包含无法复制的非普通资源。")


def _present(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _move(source: Path, target: Path) -> bool:
    """返回成功或原路径仍在、目标仍缺失的可确认失败。"""
    try:
        source.rename(target)
    except OSError as exc:
        try:
            if _present(source) and not _present(target):
                return False
        except OSError:
            pass
        raise InstallUnconfirmed("技能目录移动结果未确认。") from exc
    return True


def _sync_names(target: Path, stage: Path) -> None:
    if sys.platform != "win32":
        return  # Windows 为当前验收平台，其余保留目录交换语义。
    try:
        sync_directory(target.parent)
        sync_directory(stage)
    except (OSError, AtomicFileError) as exc:
        raise InstallUnconfirmed("技能目录发布持久确认未完成。") from exc


def _publish(candidate: Path, target: Path, backup: Path, *, existing: bool) -> None:
    if existing and not _move(target, backup):
        raise _InstallFailure("原技能目录未能移入备份，保留原安装。")
    if not _move(candidate, target):
        if existing:
            if not _move(backup, target):
                raise InstallUnconfirmed("原技能目录恢复未确认。")
            _sync_names(target, backup.parent)
        raise _InstallFailure("技能目录发布失败，原安装已保留。")
    _sync_names(target, candidate.parent)


def _clone(source: str, temporary: Path, workspace: Path, signal: Event, run_git: GitRunner) -> Path:
    git = shutil.which("git")
    if git is None:
        raise _InstallFailure("找不到 Git，无法拉取技能仓库。")
    argv = [str(Path(git).resolve()), "clone", "--depth", "1", "--", source, str(temporary)]
    environ = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    try:
        result = run_git(argv, str(workspace), signal, environ=environ)
    except (OSError, RuntimeError) as exc:
        raise InstallUnconfirmed("Git 拉取进程退出未确认。") from exc
    _check_cancel(signal)
    if result.aborted:
        raise _InstallFailure("技能安装已取消。")
    if result.code != 0:
        raise _InstallFailure(f"Git 拉取技能仓库失败（退出码 {result.code}）。")
    skills = temporary / "skills"
    if _present(skills):
        _directory(skills)
        return skills
    return temporary


def _remove_owned(directory: Path, warnings: list[str]) -> None:
    try:
        _directory(directory)
        if directory.resolve() != directory.absolute():
            raise _InstallFailure("暂存目录路径已变更。")
        shutil.rmtree(directory)
    except (OSError, _InstallFailure):
        warnings.append("本次技能暂存目录清理未确认。")


def _install(
    source: str, scope: InstallScope, workspace: Path, user_root: Path, signal: Event, run_git: GitRunner,
) -> InstallResult:
    workspace = workspace.resolve()
    native = (user_root.parent.resolve() / user_root.name) if scope == "user" else workspace / ".ruocun"
    destination = native / "skills"
    installed: list[str] = []
    warnings: list[str] = []
    checkout = stage = None
    found = False
    keep = False
    error = None
    try:
        _check_cancel(signal)
        if source.startswith(("http:", "https:", "git@")):
            checkout = Path(tempfile.mkdtemp(prefix="ruocun-skill-"))
            source_root = _clone(source, checkout, workspace, signal, run_git)
        else:
            source_root = _local_source(workspace, source)
        source_dirs = list(_find(source_root, signal)) if source_root.is_dir() else []
        found = bool(source_dirs)
        valid = []
        for skill in source_dirs:
            _check_cancel(signal)
            if skill.is_relative_to(destination) or destination.is_relative_to(skill):
                raise _InstallFailure("技能源与安装目标重叠，保留源目录。")
            body = (skill / "SKILL.md").read_text(encoding="utf-8", errors="replace")
            if body.lstrip().startswith("---"):
                valid.append(skill)
            else:
                warnings.append(f"{skill.name}:缺 frontmatter,跳过")
        if valid:
            with fileLock(str(destination)):
                _check_cancel(signal)
                native.mkdir(parents=True, exist_ok=True)
                _directory(native)
                destination.mkdir(exist_ok=True)
                _directory(destination)
                stage = Path(tempfile.mkdtemp(prefix=".skill-stage-", dir=native))
                for index, skill in enumerate(valid):
                    target = destination / skill.name
                    area = stage / str(index)
                    area.mkdir()
                    candidate, backup = area / "candidate", area / "original"
                    existing = _present(target)
                    if existing:
                        _directory(target)
                        _copy(target, candidate, signal)
                    _copy(skill, candidate, signal, omit_git=True)
                    _check_cancel(signal)
                    _publish(candidate, target, backup, existing=existing)
                    installed.append(skill.name)
    except InstallUnconfirmed:
        keep = True
        raise
    except _InstallFailure as exc:
        error = str(exc)
    except (OSError, RuntimeError, ValueError) as exc:
        error = f"无法准备完整技能资源（{type(exc).__name__}）。"
    finally:
        if not keep:
            for directory in (stage, checkout):
                if directory is not None:
                    _remove_owned(directory, warnings)
    return InstallResult(destination, scope, tuple(installed), tuple(warnings), found, error)


async def installSkills(
    source: str, scope: InstallScope, workspace_root: Path, user_root: Path, signal: Event, *,
    run_git: GitRunner | None = None,
) -> InstallResult:
    return await asyncio.to_thread(_install, source, scope, workspace_root, user_root, signal,
                                   run_git if run_git is not None else run_foreground_argv)
