"""Frozen agent/worktree.ts (MIT), with exact ownership checks before removal."""

from __future__ import annotations

import asyncio
import os
import re
import secrets
import stat
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from ..tools.types import ToolContext

NAME_PATTERN = r"^[A-Za-z0-9._-]{1,64}$"
_OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_DEVICE = re.compile(r"(?:con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?\Z", re.IGNORECASE)


class GitBoundaryError(ValueError):
    """Operation was rejected before the requested Git mutation."""


class GitMutationUnknown(RuntimeError):
    """A Git mutation may have happened. Preserve the observed state."""


class WorktreeChanges(GitBoundaryError):
    def __init__(self, dirty: bool, commits: bool) -> None:
        reasons = []
        if dirty:
            reasons.append("有未提交的改动")
        if commits:
            reasons.append("有已提交但不在创建基线上的提交")
        super().__init__(f"工作树清理已暂停：{'、'.join(reasons)}。\n"
                         "可用 action=keep 保留现场。用户确认丢弃后，再传 discard_changes=true 清理。")


class GitCommand:
    """Local argv-only Git. Inherited GIT_* values cannot redirect repository I/O."""

    def __init__(self, environ: Mapping[str, str] | None = None, *, isolated: bool = False, timeout: float = 10) -> None:
        self.environment = {key: value for key, value in (os.environ if environ is None else environ).items()
                            if not key.upper().startswith("GIT_")}
        self.environment.update(GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0", GCM_INTERACTIVE="never", LC_ALL="C")
        if isolated:
            self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM="1")
        filename = "git.exe" if os.name == "nt" else "git"
        search = next((value for key, value in self.environment.items() if key.upper() == "PATH"), os.defpath)
        self.executable = next((str(directory / filename) for part in search.split(os.pathsep)
                                if (directory := Path(part)).is_absolute() and (directory / filename).is_file()), None)
        self.timeout = timeout

    def run(self, cwd: Path, args: Sequence[str], *, allow: tuple[int, ...] = (0,),
            mutation: bool = False) -> subprocess.CompletedProcess[bytes]:
        if self.executable is None:
            raise GitBoundaryError("未找到可用的 Git。")
        argv = [self.executable, "-c", f"core.hooksPath={os.devnull}", "-c", "core.fsmonitor=false", "-c", "gc.auto=0", *args]
        try:
            result = subprocess.run(argv, cwd=cwd, env=self.environment, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=self.timeout,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        except (OSError, subprocess.TimeoutExpired) as exc:
            if mutation:
                raise GitMutationUnknown("Git 写操作未得到可确认的结果。请保留现场并检查 Git 状态。") from exc
            raise GitBoundaryError("无法读取 Git 状态。") from exc
        if result.returncode not in allow:
            if mutation:
                raise GitMutationUnknown("Git 写操作未得到可确认的结果。请保留现场并检查 Git 状态。")
            raise GitBoundaryError("Git 状态检查失败，操作已停止。")
        return result

    def read(self, cwd: Path, *args: str) -> str:
        return self.run(cwd, args).stdout.decode("utf-8").rstrip("\r\n")


def directory_identity(path: Path, *, create: bool = False) -> tuple[int, int]:
    if create:
        path.mkdir(exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise GitBoundaryError("Git 工作目录不能是符号链接、重解析点或普通文件。")
    return info.st_dev, info.st_ino


def private_git_directory(repo: Path, name: str) -> Path:
    """Create only the private child and its own ignore file."""
    private = repo / ".ruocun"
    directory_identity(private, create=True)
    root = private / name
    directory_identity(root, create=True)
    ignore = root / ".gitignore"
    try:
        with ignore.open("xb") as target:
            target.write(b"*\n")
    except FileExistsError:
        info = ignore.lstat()
        if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise GitBoundaryError("私有目录的忽略文件不是普通文件。")
    return root


def validateWorktreeName(name: str) -> None:
    if not re.fullmatch(NAME_PATTERN, name) or name in {".", ".."} or name.endswith(".") or _DEVICE.fullmatch(name):
        raise GitBoundaryError("worktree 名称必须是可安全创建的目录和分支后缀。")


def _oid(value: str) -> str:
    if _OID.fullmatch(value) is None:
        raise GitBoundaryError("无法确认 Git 提交标识。")
    return value


def _git_dir(git: GitCommand, cwd: Path, flag: str) -> Path:
    return Path(git.read(cwd, "rev-parse", "--path-format=absolute", flag)).resolve(strict=True)


def _repository_root(git: GitCommand, path: Path) -> Path | None:
    result = git.run(path, ["rev-parse", "--show-toplevel"], allow=(0, 128))
    if result.returncode:
        return None
    top = Path(result.stdout.decode("utf-8").rstrip("\r\n"))
    if not top.is_absolute() or not path.is_relative_to(top):
        raise GitBoundaryError("Git 返回的仓库顶层与当前目录不匹配。")
    return top


def gitDiff(root: str | Path, *, environ: Mapping[str, str] | None = None) -> str | None:
    """Frozen /diff summary for a verified project or linked checkout root."""
    git = GitCommand(environ)
    if git.executable is None:
        return None
    path = Path(root).resolve(strict=True)
    if _repository_root(git, path) is None:
        return None
    status = git.read(path, "status", "--short")
    summary = git.read(path, "diff", "--stat", "--no-ext-diff", "--no-textconv")
    return "\n".join(part for part in (status, summary) if part)


def _registered(git: GitCommand, repo: Path, root: Path, branch: str, head: str) -> bool:
    raw = git.run(repo, ["worktree", "list", "--porcelain", "-z"]).stdout.decode("utf-8")
    for record in raw.split("\0\0"):
        fields = record.split("\0")
        if fields and fields[0].startswith("worktree ") and Path(fields[0][9:]) == root:
            locked = any(field == "locked" or field.startswith("locked ") for field in fields)
            return not locked and f"branch refs/heads/{branch}" in fields and f"HEAD {head}" in fields
    return False


@dataclass(frozen=True)
class Worktree:
    root: str
    branch: str
    _repository: Path = field(repr=False)
    _top: Path = field(repr=False)
    _common: Path = field(repr=False)
    _admin: Path = field(repr=False)
    _base: str = field(repr=False)
    _root_identity: tuple[int, int] = field(repr=False)
    _admin_identity: tuple[int, int] = field(repr=False)
    _git: GitCommand = field(repr=False)

    def _checked_head(self) -> str:
        root = Path(self.root)
        try:
            directory_identity(self._repository)
            directory_identity(self._repository / ".ruocun")
            directory_identity(root.parent)
            if directory_identity(root) != self._root_identity or directory_identity(self._admin) != self._admin_identity:
                raise GitBoundaryError("worktree 目录身份已改变，保留现场。")
            marker = (root / ".git").lstat()
            if not stat.S_ISREG(marker.st_mode) or getattr(marker, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise GitBoundaryError("worktree 的 Git 标记不是普通文件。")
            if (_repository_root(self._git, root) != root or _repository_root(self._git, self._repository) != self._top
                or _git_dir(self._git, root, "--absolute-git-dir") != self._admin
                or _git_dir(self._git, root, "--git-common-dir") != self._common
                or _git_dir(self._git, self._repository, "--git-common-dir") != self._common):
                raise GitBoundaryError("worktree 已脱离原 Git 仓库，保留现场。")
            head = _oid(self._git.read(root, "rev-parse", "--verify", "HEAD"))
            branch_ref = f"refs/heads/{self.branch}"
            if (self._git.read(root, "symbolic-ref", "HEAD") != branch_ref
                or self._git.read(self._repository, "rev-parse", "--verify", branch_ref) != head
                or not _registered(self._git, self._repository, root, self.branch, head)):
                raise GitBoundaryError("worktree 与原分支不再匹配，保留现场。")
            return head
        except (OSError, UnicodeError) as exc:
            raise GitBoundaryError("无法核实 worktree 身份，保留现场。") from exc

    def _dirty(self, *, ignored: bool = False) -> bool:
        args = ["status", "--porcelain=v1", "-z", "--untracked-files=all"]
        if ignored:
            args.append("--ignored=matching")
        return bool(self._git.run(Path(self.root), args).stdout)

    def _commits(self, head: str) -> bool:
        # Without `--`, Git may stat the long revision range as a filename.
        return bool(self._git.read(Path(self.root), "rev-list", "-1", f"{self._base}..{head}", "--"))

    def hasChanges(self) -> bool:
        self._checked_head()
        return self._dirty()

    def verify(self) -> None:
        """Check that this live ownership handle still names the same checkout."""
        self._checked_head()

    def hasUnpushedCommits(self) -> bool:
        return self._commits(self._checked_head())

    def cleanup(self, *, discard_changes: bool = False) -> None:
        head = self._checked_head()
        if not discard_changes:
            dirty, commits = self._dirty(ignored=True), self._commits(head)
            if dirty or commits:
                raise WorktreeChanges(dirty, commits)
        if self._checked_head() != head:
            raise GitBoundaryError("删除前 worktree 提交发生变化，请检查现场。")
        args = ["worktree", "remove", *(["--force"] if discard_changes else []), "--", self.root]
        self._git.run(self._repository, args, mutation=True)
        branch_ref = f"refs/heads/{self.branch}"
        try:
            if os.path.lexists(self.root) or os.path.lexists(self._admin):
                raise GitMutationUnknown("目录或 Git 工作树记录仍存在，保留分支。")
            if self._git.read(self._repository, "rev-parse", "--verify", branch_ref) != head:
                raise GitMutationUnknown("工作树已移除，分支状态发生变化并已保留。")
            # branch -D retains Git's guard against deleting a checked-out branch.
            self._git.run(self._repository, ["branch", "-D", "--", self.branch], mutation=True)
            present = self._git.run(self._repository, ["show-ref", "--verify", "--quiet", branch_ref], allow=(0, 1))
            if present.returncode == 0:
                raise GitMutationUnknown("工作树已移除，未能确认分支删除。")
        except (GitBoundaryError, OSError, UnicodeError) as exc:
            raise GitMutationUnknown("工作树已移除，分支删除结果未确认。请检查 Git 状态。") from exc


@dataclass(frozen=True)
class ActiveWorktree:
    worktree: Worktree
    previousCwd: str | None


def createWorktree(repoRoot: str | Path, id: str, *, environ: Mapping[str, str] | None = None) -> Worktree | None:
    validateWorktreeName(id)
    git = GitCommand(environ)
    if git.executable is None:
        return None
    try:
        repo = Path(repoRoot).resolve(strict=True)
        top = _repository_root(git, repo)
        if top is None:
            return None
        head = git.run(repo, ["rev-parse", "--verify", "HEAD"], allow=(0, 128))
        if head.returncode:
            return None
        base = _oid(head.stdout.decode("ascii").strip())
        common = _git_dir(git, repo, "--git-common-dir")
        branch = f"ruocun-wt-{id}"
        ref = f"refs/heads/{branch}"
        git.run(repo, ["check-ref-format", ref])
        if git.run(repo, ["show-ref", "--verify", "--quiet", ref], allow=(0, 1)).returncode == 0:
            raise GitBoundaryError("同名 worktree 分支已经存在。")
        private = repo / ".ruocun" / "worktrees"
        if git.run(repo, ["ls-files", "-z", "--", str(private)]).stdout:
            raise GitBoundaryError("私有 worktree 目录含项目已跟踪文件，创建已停止。")
        root = private_git_directory(repo, "worktrees") / id
        if os.path.lexists(root):
            raise GitBoundaryError("同名 worktree 目录已经存在。")
        if git.run(repo, ["check-ignore", "--no-index", "-q", "--", str(root)], allow=(0, 1)).returncode:
            raise GitBoundaryError("项目没有忽略私有 worktree 目录，创建已停止。")
    except (OSError, UnicodeError) as exc:
        raise GitBoundaryError("无法核实 worktree 创建位置。") from exc
    git.run(repo, ["worktree", "add", "-b", branch, "--", str(root), base], mutation=True)
    try:
        admin = _git_dir(git, root, "--absolute-git-dir")
        if admin.parent != common / "worktrees" or not _registered(git, repo, root, branch, base):
            raise GitBoundaryError("Git 未登记预期的 worktree 身份。")
        created = Worktree(str(root), branch, repo, top, common, admin, base, directory_identity(root), directory_identity(admin), git)
        if created._checked_head() != base:
            raise GitBoundaryError("创建后的 worktree HEAD 不是预期基线。")
        return created
    except (GitBoundaryError, OSError, UnicodeError) as exc:
        raise GitMutationUnknown("Git 创建已调用，无法确认 worktree 身份。保留现场供检查。") from exc


async def openAgentWorktree(ctx: ToolContext, mode: Literal["worktree", "remote"]) -> Worktree:
    """Create a local Git checkout for either isolation spelling."""
    create = ctx.createWorktree
    if create is None or ctx.signal.is_set():
        raise GitBoundaryError(f"当前无法创建 {mode} 隔离工作树。")
    worktree_id = "a" + secrets.token_hex(8)
    tree = await asyncio.to_thread(create, worktree_id)
    if tree is None:
        raise GitBoundaryError(f"无法创建 {mode} 隔离工作树，请检查 Git、仓库和 HEAD。")
    return tree


def verifyAgentWorktree(repo_root: Path, worktree_root: Path, *, environ: Mapping[str, str]) -> None:
    """Verify persisted isolation without granting ownership for deletion."""
    try:
        repo = repo_root.resolve(strict=True)
        private = repo / ".ruocun" / "worktrees"
        root = worktree_root.absolute()
        if root.parent != private:
            raise GitBoundaryError("隔离目录不在原项目私有工作树目录内。")
        validateWorktreeName(root.name)
        for path in (repo, private.parent, private, root):
            directory_identity(path)
        marker = (root / ".git").lstat()
        if not stat.S_ISREG(marker.st_mode) or getattr(marker, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise GitBoundaryError("隔离工作树的 Git 标记不是普通文件。")
        git = GitCommand(environ)
        if _repository_root(git, repo) is None or _repository_root(git, root) != root:
            raise GitBoundaryError("无法核实原项目与隔离树的 Git 根。")
        common = _git_dir(git, repo, "--git-common-dir")
        admin = _git_dir(git, root, "--absolute-git-dir")
        if admin.parent != common / "worktrees" or _git_dir(git, root, "--git-common-dir") != common:
            raise GitBoundaryError("隔离工作树不属于原 Git 仓库。")
        directory_identity(admin)
        branch = "ruocun-wt-" + root.name
        ref = "refs/heads/" + branch
        head = _oid(git.read(root, "rev-parse", "--verify", "HEAD"))
        if (git.read(root, "symbolic-ref", "HEAD") != ref or git.read(repo, "rev-parse", "--verify", ref) != head
                or not _registered(git, repo, root, branch, head)):
            raise GitBoundaryError("隔离工作树与已登记分支或提交不匹配。")
    except (OSError, UnicodeError) as exc:
        raise GitBoundaryError("无法核实原隔离工作树，保留现场。") from exc


async def finishAgentWorktree(worktree: Worktree, text: str) -> str:
    """Keep changes and clean only the exact checkout owned by this run."""
    location = f"分支 {worktree.branch}，目录 {worktree.root}"
    try:
        await asyncio.to_thread(worktree.cleanup, discard_changes=False)
    except WorktreeChanges:
        return f"{text}\n[隔离:改动已保留在{location}，可检查后合并。]"
    except GitBoundaryError as error:
        return f"{text}\n[隔离:未自动清理，请检查{location}。{error}]"
    except GitMutationUnknown as error:
        raise GitMutationUnknown(f"{error} 请检查隔离{location}。") from error
    return text
