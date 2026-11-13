"""Frozen agent/cleanup.ts (MIT), with durable session and attachment protection."""

from __future__ import annotations

import asyncio
import math
import stat
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..config.compat import resolve_env
from ..platform.file_contract import AtomicFileError
from ..platform.windows.durable_file import atomic_publish, ensure_private_dir
from ..session.contract import RuntimeRecord, StoreError
from ..session.durable_store import inspect_durable_session
from ..session.prune import prune_durable_session
from .worktree import (
    GitBoundaryError,
    GitCommand,
    directory_identity,
    verifyAgentWorktree,
)

DAY = 86_400_000


@dataclass
class CleanupResult:
    spill: int = 0
    subagents: int = 0
    sessions: int = 0
    worktreesPruned: bool = False
    worktreesReclaimed: int = 0


def _plain(path: Path, directory: bool) -> bool:
    info = path.lstat()
    return (not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)))


def _remove_old_files(directory: Path, cutoff: int, protected: set[Path]) -> int:
    if not directory.exists() or not _plain(directory, True):
        return 0
    removed = 0
    for file in directory.iterdir():
        try:
            if _plain(file, False) and file.stat().st_mtime_ns // 1_000_000 < cutoff and file.resolve() not in protected:
                file.unlink()
                removed += 1
        except OSError:
            continue
    return removed


def _reclaim_worktrees(workspace: Path, cutoff: int, env: Mapping[str, str], protected: set[Path]) -> int:
    private = workspace / ".ruocun" / "worktrees"
    if not private.exists() or not _plain(private, True):
        return 0
    git, reclaimed = GitCommand(env), 0
    for tree in private.iterdir():
        try:
            if not _plain(tree, True) or tree.resolve() in protected or tree.stat().st_mtime_ns // 1_000_000 >= cutoff:
                continue
            verifyAgentWorktree(workspace, tree, environ=env)
            branch = "refs/heads/ruocun-wt-" + tree.name
            head = git.read(tree, "rev-parse", "--verify", "HEAD")
            if (git.run(tree, ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=matching"]).stdout
                    or git.run(workspace, ["merge-base", "--is-ancestor", head, "HEAD"], allow=(0, 1)).returncode):
                continue
            verifyAgentWorktree(workspace, tree, environ=env)
            if git.read(tree, "rev-parse", "--verify", "HEAD") != head:
                continue
            git.run(workspace, ["worktree", "remove", "--", str(tree)], allow=(0, 128))
            if tree.exists():
                continue
            # A concurrent ref update preserves the branch instead of deleting the new head.
            if git.read(workspace, "rev-parse", "--verify", branch) == head:
                git.run(workspace, ["update-ref", "-d", branch, head], allow=(0, 1))
            reclaimed += 1
        except (OSError, GitBoundaryError):
            continue
    return reclaimed


def cleanup(workspaceRoot: Path, days: float, now: int, *, sessions_dir: Path,
            runtime: RuntimeRecord, environ: Mapping[str, str], protection_root: Path | None = None) -> CleanupResult:
    if not math.isfinite(days) or days <= 0:
        raise ValueError("清理保留天数须为正数。")
    workspace = Path(workspaceRoot).absolute()
    directory_identity(workspace)
    cutoff = now - int(days * DAY)
    result = CleanupResult()
    protected: set[Path] = set()
    protected_worktrees: set[Path] = set()
    inspect_complete = True
    candidates: list[Path] = []
    dependencies: dict[Path, set[Path]] = {}

    def collect_worktrees(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"worktree", "cwd"} and isinstance(child, str):
                    protected_worktrees.add(Path(child).resolve())
                else:
                    collect_worktrees(child)
        elif isinstance(value, list):
            for child in value:
                collect_worktrees(child)

    roots = [sessions_dir]
    if protection_root is not None and protection_root.exists():
        roots = [root for root in protection_root.iterdir() if not root.name.startswith(".")]
    for session_root in roots:
        if not session_root.exists():
            continue
        if not _plain(session_root, True):
            inspect_complete = False
            continue
        for directory in session_root.iterdir():
            if directory.name.startswith("."):
                continue
            try:
                if not _plain(directory, True) or not (directory / "session.db").is_file():
                    inspect_complete = False
                    continue
                view = inspect_durable_session(directory, runtime)
                dependencies[directory] = {Path(file).resolve() for file in (view.get("attachments") or {})}
                protected.update(dependencies[directory])
                for run in view["runs"]:
                    collect_worktrees(run.get("snapshot", {}))
                # Spill pointers are display strings in legacy paired transcripts. Protect
                # their exact files too, even if that old producer had no attachment ledger.
                transcript = str(view["checkpoint"].get("messages", []))
                for private_name in ("spill", "subagents"):
                    private_dir = workspace / ".ruocun" / private_name
                    if private_dir.exists() and _plain(private_dir, True):
                        for file in private_dir.iterdir():
                            if file.name in transcript:
                                protected.add(file.resolve())
                if (session_root == sessions_dir and not view["owner_alive"] and view["done"]
                        and view["updated_at"] < cutoff):
                    candidates.append(directory)
            except (StoreError, OSError):
                inspect_complete = False
    for directory in candidates if inspect_complete else ():
        try:
            other_paths = {str(file) for other, files in dependencies.items() if other != directory for file in files}
            result.sessions += int(prune_durable_session(directory, runtime, cutoff_ms=cutoff,
                                                        protected_paths=tuple(sorted(other_paths))))
        except (StoreError, OSError):
            inspect_complete = False
    if inspect_complete:
        result.spill = _remove_old_files(workspace / ".ruocun" / "spill", cutoff, protected)
        result.subagents = _remove_old_files(workspace / ".ruocun" / "subagents", cutoff, protected)
        result.worktreesReclaimed = _reclaim_worktrees(workspace, cutoff, environ, protected_worktrees)
        result.worktreesPruned = result.worktreesReclaimed > 0
    return result


async def maybeCleanup(workspaceRoot: Path, *, sessions_dir: Path, runtime: RuntimeRecord,
                       environ: Mapping[str, str], now: int | None = None,
                       protection_root: Path | None = None) -> CleanupResult | None:
    if resolve_env("NO_CLEANUP", environ) == "1":
        return None
    now = time.time_ns() // 1_000_000 if now is None else now
    stamp = Path(workspaceRoot) / ".ruocun" / ".last-cleanup"
    try:
        try:
            previous = int(stamp.read_text("utf-8"))
        except (FileNotFoundError, ValueError):
            previous = 0
        if now - previous < DAY:
            return None
        configured = float(resolve_env("CLEANUP_DAYS", environ) or "30")
        days = configured if math.isfinite(configured) and configured > 0 else 30
        ensure_private_dir(stamp.parent)
        result = await asyncio.to_thread(cleanup, Path(workspaceRoot), days, now,
                                          sessions_dir=sessions_dir, runtime=runtime, environ=environ,
                                          protection_root=protection_root)
        atomic_publish(stamp, str(now).encode("ascii"))
        return result
    except (StoreError, OSError, ValueError, AtomicFileError):
        return None
