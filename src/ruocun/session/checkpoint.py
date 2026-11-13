"""Frozen session/checkpoint.ts (MIT): private Git snapshots of workspace files."""

from __future__ import annotations

import json
import math
import os
import re
import stat
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from time import monotonic
from typing import TypedDict

from ..agent.worktree import (
    GitBoundaryError,
    GitCommand,
    GitMutationUnknown,
    directory_identity,
    private_git_directory,
)

PRE_RESTORE_LABEL = "回退前自动快照"
_BRANCH = "refs/heads/checkpoints"
_OID = re.compile(r"[0-9a-f]{40}\Z")
_SHADOW_CONFIG = b"[core]\n\trepositoryformatversion = 0\n\tbare = true\n\tprotectNTFS = true\n\tprotectHFS = true\n[user]\n\tname = RuoCun\n\temail = ruocun@local\n"
_EXCLUDES = (
    "node_modules/", ".git/", ".dao/", ".ruocun/", ".codeds/", "dist/", "dist-bin/", "build/", "out/", "target/", "obj/", "bin/",
    ".next/", ".nuxt/", ".svelte-kit/", ".turbo/", ".cache/", "coverage/", ".parcel-cache/",
    ".venv/", "venv/", "env/", "__pycache__/", ".mypy_cache/", ".pytest_cache/", ".tox/", ".ruff_cache/",
    "vendor/", ".gradle/", ".idea/", "Pods/", "DerivedData/", ".terraform/", "*.log", "*.tmp", ".DS_Store",
    "*.zip", "*.tar", "*.gz", "*.tgz", "*.mp4", "*.mov", "*.iso", "*.dmg", "*.bin", "*.sqlite", "",
)
_PATHS = tuple(f":(exclude,glob,icase,top)**/{name}/**" for name in (".git", ".ruocun", ".dao"))
_RESERVED = {".git", ".ruocun", ".dao"}
_DEVICES = {"con", "prn", "aux", "nul", *(f"{prefix}{number}" for prefix in ("com", "lpt") for number in "0123456789¹²³")}


class Checkpoint(TypedDict):
    ref: str
    label: str
    ts: str


def readCheckpointEnabled(user_file: Path, project_file: Path | None) -> bool:
    for file in (project_file, user_file):
        if file is None:
            continue
        try:
            document = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            continue
        checkpoint = document.get("checkpoint") if isinstance(document, dict) else None
        enabled = checkpoint.get("enabled") if isinstance(checkpoint, dict) else None
        if isinstance(enabled, bool):
            return enabled
    return False


def _option(environ: Mapping[str, str], name: str) -> str | None:
    return environ.get("RUOCUN_" + name)


def _limit(environ: Mapping[str, str], name: str, default: float) -> float:
    try:
        number = float(_option(environ, name) or "")
    except ValueError:
        return default
    return number / 1000 if math.isfinite(number) and number > 0 else default


def _plain(info: os.stat_result) -> bool:
    return not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _read_regular(path: Path) -> bytes:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or not _plain(info):
        raise GitBoundaryError("影子 Git 配置文件身份异常。")
    return path.read_bytes()


def _path_parts(raw: str) -> tuple[str, ...]:
    parts = tuple(raw.split("/"))
    for part in parts:
        if not part or part in {".", ".."} or part.casefold() in _RESERVED:
            raise GitBoundaryError("检查点含 Git 或私有目录路径，已拒绝回退。")
        if os.name == "nt" and (re.search(r'[\\:<>"|?*\x00-\x1f]', part) or part.endswith((".", " "))
                                or part.split(".", 1)[0].casefold() in _DEVICES):
            raise GitBoundaryError("检查点含当前平台无法安全还原的路径。")
    return parts


class Checkpointer:
    def __init__(self, root: Path | None = None, git_dir: Path | None = None, git: GitCommand | None = None, *,
                 max_seconds: float = 2.5) -> None:
        self.enabled = root is not None and git_dir is not None and git is not None
        self._root, self._directory, self._git = root, git_dir, git
        self._max_seconds = max_seconds
        self._too_slow = False
        self._root_identity = directory_identity(root) if root is not None else None
        self._identity = directory_identity(git_dir) if git_dir is not None else None

    def _paths(self) -> tuple[Path, Path, GitCommand]:
        if self._root is None or self._directory is None or self._git is None:
            raise GitBoundaryError("影子 Git 未启用。")
        return self._root, self._directory, self._git

    def _verify(self) -> None:
        root, directory, _ = self._paths()
        if directory_identity(root) != self._root_identity:
            raise GitBoundaryError("影子 Git 对应的工作区身份已变化。")
        directory_identity(directory.parent)
        if directory_identity(directory) != self._identity:
            raise GitBoundaryError("影子 Git 目录身份已变化。")
        if _read_regular(directory / "ruocun-root") != os.fsencode(root) or _read_regular(directory / "config") != _SHADOW_CONFIG:
            raise GitBoundaryError("影子 Git 配置与原工作区不匹配。")
        for child in ("objects", "objects/info", "objects/pack", "refs", "refs/heads", "info"):
            directory_identity(directory / child)
        for entry in (directory / "objects").iterdir():
            if not _plain(entry.lstat()):
                raise GitBoundaryError("影子 Git 的对象路径被重定向。")
        if any(os.path.lexists(directory / child) for child in ("objects/info/alternates", "objects/info/http-alternates", "commondir")):
            raise GitBoundaryError("影子 Git 的对象或引用被重定向。")
        if _read_regular(directory / "HEAD").strip() != f"ref: {_BRANCH}".encode():
            raise GitBoundaryError("影子 Git HEAD 指向非预期分支。")
        for child in ("index", "packed-refs", _BRANCH):
            path = directory / child
            if os.path.lexists(path):
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or not _plain(info):
                    raise GitBoundaryError("影子 Git 索引或引用不是普通文件。")

    @contextmanager
    def _operation(self, *, initializing: bool = False) -> Iterator[None]:
        _, directory, _ = self._paths()
        lock = directory / "ruocun-operation.lock"
        if not initializing:
            self._verify()
        try:
            stream = lock.open("xb")
        except FileExistsError as exc:
            raise GitBoundaryError("另一个检查点操作正在执行，或前次结果待确认。") from exc
        preserve = False
        identity = os.fstat(stream.fileno())
        try:
            if not initializing:
                self._verify()
            yield
        except GitMutationUnknown:
            preserve = True
            raise
        finally:
            stream.close()
            if not preserve:
                try:
                    found = lock.lstat()
                    if (found.st_dev, found.st_ino) != (identity.st_dev, identity.st_ino):
                        raise GitMutationUnknown("检查点操作锁身份已改变。")
                    lock.unlink()
                except OSError as exc:
                    raise GitMutationUnknown("无法确认检查点操作锁已释放。") from exc

    def _run(self, *args: str, allow: tuple[int, ...] = (0,), mutation: bool = False) -> bytes:
        root, directory, git = self._paths()
        result = git.run(root, ["--git-dir", str(directory), "--work-tree", str(root), *args], allow=allow, mutation=mutation)
        return result.stdout

    def _snapshot(self, label: str) -> str:
        start = monotonic()
        self._run("add", "-A", "--", *_PATHS, mutation=True)
        self._run("commit", "--allow-empty", "--no-verify", "--no-gpg-sign", "-m", label, mutation=True)
        try:
            ref = self._run("rev-parse", "--verify", "HEAD").decode("ascii").strip()
            if _OID.fullmatch(ref) is None:
                raise GitBoundaryError("无法确认检查点的完整提交标识。")
        except (GitBoundaryError, UnicodeError) as exc:
            raise GitMutationUnknown("检查点写入后未能确认引用，保留现场。") from exc
        if monotonic() - start > self._max_seconds:
            self._too_slow = True
        return ref

    def snapshot(self, label: str) -> str | None:
        if not self.enabled or self._too_slow:
            return None
        try:
            with self._operation():
                return self._snapshot(label)
        except (GitBoundaryError, OSError, UnicodeError):
            return None
        except GitMutationUnknown:
            self._too_slow = True
            return None  # 自动快照可降级，操作锁保留以禁止不明写入后的重复提交。

    def _entries(self, ref: str) -> dict[tuple[str, ...], bytes]:
        values: dict[tuple[str, ...], bytes] = {}
        folded: dict[tuple[str, ...], tuple[str, ...]] = {}
        for entry in self._run("ls-tree", "-r", "-z", "--full-tree", ref).split(b"\0"):
            if not entry:
                continue
            header, path = entry.split(b"\t", 1)
            parts = _path_parts(path.decode("utf-8"))
            if os.name == "nt":
                for index in range(1, len(parts) + 1):
                    component = parts[:index]
                    key = tuple(value.casefold() for value in component)
                    if folded.setdefault(key, component) != component:
                        raise GitBoundaryError("检查点含大小写冲突的路径，已拒绝回退。")
            values[parts] = header
        return values

    def _restore_guard(self, current: dict[tuple[str, ...], bytes], target: dict[tuple[str, ...], bytes]) -> None:
        root, _, _ = self._paths()
        changed = {parts for parts in current.keys() | target.keys() if current.get(parts) != target.get(parts)}
        if os.name == "nt":
            original = {tuple(value.casefold() for value in path): path for path in current}
            if any(original.get(tuple(value.casefold() for value in path), path) != path for path in target):
                raise GitBoundaryError("回退路径发生大小写冲突。")
        for parts in changed:
            for header in (current.get(parts), target.get(parts)):
                if header is not None and header.split(b" ", 1)[0] not in {b"100644", b"100755"}:
                    raise GitBoundaryError("回退将改变链接或嵌套仓库，已保留现场。")
            for size in range(1, len(parts) + 1):
                prefix = parts[:size]
                path = root.joinpath(*prefix)
                try:
                    info = path.lstat()
                except (FileNotFoundError, NotADirectoryError):
                    break
                if not _plain(info):
                    raise GitBoundaryError("回退路径包含链接或重解析点。")
                if stat.S_ISDIR(info.st_mode):
                    if prefix == parts and parts in target:
                        # A target file can replace only a directory whose every
                        # existing entry belongs to the current shadow snapshot.
                        self._check_replaced_directory(path, parts, current)
                elif not stat.S_ISREG(info.st_mode) or prefix not in current:
                    raise GitBoundaryError("回退会覆盖未纳入检查点的现有文件。")

    def _check_replaced_directory(self, path: Path, parts: tuple[str, ...], current: dict[tuple[str, ...], bytes]) -> None:
        for child in path.iterdir():
            child_parts = (*parts, child.name)
            info = child.lstat()
            if not _plain(info):
                raise GitBoundaryError("回退会覆盖包含链接的目录。")
            if stat.S_ISDIR(info.st_mode):
                self._check_replaced_directory(child, child_parts, current)
            elif not stat.S_ISREG(info.st_mode) or child_parts not in current:
                raise GitBoundaryError("回退会覆盖未纳入检查点的目录内容。")

    def restore(self, ref: str) -> bool:
        if not self.enabled or _OID.fullmatch(ref) is None:
            return False
        try:
            with self._operation():
                target = self._entries(ref)
                self._run("merge-base", "--is-ancestor", ref, "HEAD")
                before = self._snapshot(PRE_RESTORE_LABEL)
                self._restore_guard(self._entries(before), target)
                # Two-tree update checks the current index and workspace; keep HEAD
                # at the pre-restore snapshot so its data stays directly listable.
                self._run("read-tree", "-m", "-u", before, ref, mutation=True)
                try:
                    self._run("diff", "--quiet", "--no-ext-diff", "--no-textconv")
                    self._run("diff", "--cached", "--quiet", "--no-ext-diff", "--no-textconv", ref)
                except GitBoundaryError as exc:
                    raise GitMutationUnknown("回退已执行，未能确认文件与目标检查点一致。") from exc
        except (GitBoundaryError, OSError, ValueError, UnicodeError):
            return False
        return True

    def list(self, limit: int = 30) -> list[Checkpoint]:
        if not self.enabled or limit <= 0:
            return []
        try:
            self._verify()
            raw = self._run("log", "-z", "--format=%H%x00%s%x00%cI", f"-{limit}").decode("utf-8")
            values = raw.rstrip("\0").split("\0")
            return [{"ref": ref, "label": label, "ts": timestamp}
                    for ref, label, timestamp in zip(values[::3], values[1::3], values[2::3], strict=True)]
        except (GitBoundaryError, OSError, ValueError, UnicodeError):
            return []


def createCheckpointer(workspaceRoot: str | Path, *, enabled: bool | None = None,
                       environ: Mapping[str, str] | None = None) -> Checkpointer:
    env = os.environ if environ is None else environ
    if _option(env, "NO_CHECKPOINT") or not (enabled if enabled is not None else
                                             (_option(env, "CHECKPOINT") or "").lower() in {"1", "true", "yes", "on"}):
        return Checkpointer()
    git = GitCommand(env, isolated=True, timeout=_limit(env, "CHECKPOINT_TIMEOUT_MS", 10))
    if git.executable is None:
        return Checkpointer()
    try:
        root = Path(workspaceRoot).resolve(strict=True)
        directory = root / ".ruocun" / "shadow.git"
        if os.path.lexists(directory) and not os.path.lexists(directory / "ruocun-root"):
            return Checkpointer()  # Preserve unknown pre-existing directories.
        if git.run(root, ["ls-files", "-z", "--", str(directory)], allow=(0, 128)).stdout:
            return Checkpointer()
        directory = private_git_directory(root, "shadow.git")
        cp = Checkpointer(root, directory, git, max_seconds=_limit(env, "CHECKPOINT_MAX_MS", 2.5))
        if not os.path.lexists(directory / "ruocun-root"):
            with cp._operation(initializing=True):
                if not os.path.lexists(directory / "ruocun-root"):
                    if any(entry.name not in {".gitignore", "ruocun-operation.lock"} for entry in directory.iterdir()):
                        raise GitBoundaryError("影子 Git 目录已有未确认内容。")
                    git.run(root, ["init", "--bare", "--template=", "--initial-branch=checkpoints",
                                   "--object-format=sha1", str(directory)], mutation=True)
                    (directory / "config").write_bytes(_SHADOW_CONFIG)
                    directory_identity(directory / "info", create=True)
                    (directory / "info" / "exclude").write_text("\n".join(_EXCLUDES), encoding="utf-8", newline="\n")
                    with (directory / "ruocun-root").open("xb") as marker:
                        marker.write(os.fsencode(root))
        cp._verify()
        return cp
    except (GitBoundaryError, GitMutationUnknown, OSError, ValueError, UnicodeError):
        return Checkpointer()
