"""Frozen worktree/Enter/Exit semantics using only newly created Git repos."""

import asyncio
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

_WINDOWS_GIT = Path("D:/study_software/Git/cmd/git.exe")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    if os.name == "nt" and _WINDOWS_GIT.is_file():
        monkeypatch.setenv("PATH", str(_WINDOWS_GIT.parent) + os.pathsep + os.environ["PATH"])
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git unavailable")
    root = tmp_path / "synthetic repo"
    root.mkdir()

    def run(*args, cwd=root):
        return subprocess.run([git, *args], cwd=cwd, check=True, capture_output=True).stdout

    run("init", "-q")
    run("config", "user.name", "Synthetic")
    run("config", "user.email", "synthetic@example.invalid")
    (root / "a.txt").write_text("base", encoding="utf-8")
    (root / ".gitignore").write_bytes(b"*.tmp\r\n")
    run("add", ".")
    run("commit", "-qm", "base")
    return root, run


def test_source_worktree_create_dirty_unique_commits_and_cleanup(repo):
    from ruocun.agent.worktree import WorktreeChanges, createWorktree

    root, git = repo
    tree = createWorktree(root, "source-1")
    assert tree is not None
    checkout = Path(tree.root)
    assert (checkout / "a.txt").read_text("utf-8") == "base"
    assert not tree.hasChanges() and not tree.hasUnpushedCommits()
    assert (root / ".gitignore").read_bytes() == b"*.tmp\r\n"
    assert git("status", "--porcelain") == b""
    (checkout / "b.txt").write_text("new", encoding="utf-8")
    assert tree.hasChanges()
    with pytest.raises(WorktreeChanges):
        tree.cleanup()
    assert (checkout / "b.txt").exists()
    git("add", ".", cwd=checkout)
    git("commit", "-qm", "worktree commit", cwd=checkout)
    assert not tree.hasChanges() and tree.hasUnpushedCommits()
    with pytest.raises(WorktreeChanges):
        tree.cleanup()
    tree.cleanup(discard_changes=True)
    assert not checkout.exists()
    assert tree.branch.encode() not in git("branch", "--list")
    assert (root / "a.txt").read_text("utf-8") == "base"


def test_source_tools_keep_reject_nested_and_remove_with_explicit_discard(repo):
    from ruocun.agent.worktree import createWorktree
    from ruocun.tools.enter_worktree import enterWorktreeTool
    from ruocun.tools.exit_worktree import exitWorktreeTool

    root, git = repo

    async def scenario():
        ctx = SimpleNamespace(workspaceRoot=str(root), cwd=None, activeWorktree=None,
                              createWorktree=lambda name: createWorktree(root, name))
        assert "不在 worktree" in await exitWorktreeTool.handler({"action": "keep"}, ctx)
        assert "已进入" in await enterWorktreeTool.handler({"name": "keep"}, ctx)
        assert ctx.workspaceRoot == str(root) and ctx.cwd != str(root)
        kept = Path(ctx.cwd)
        assert "已经在" in await enterWorktreeTool.handler({"name": "nested"}, ctx)
        assert "保留" in await exitWorktreeTool.handler({"action": "keep"}, ctx)
        assert kept.is_dir() and ctx.cwd is None and ctx.activeWorktree is None
        ctx.cwd = str(root)
        await enterWorktreeTool.handler({"name": "remove"}, ctx)
        removed = Path(ctx.cwd)
        (removed / "ignored.tmp").write_text("keep unless discard", encoding="utf-8")
        assert "discard_changes" in await exitWorktreeTool.handler({"action": "remove"}, ctx)
        assert removed.exists() and ctx.activeWorktree is not None
        assert "已移除" in await exitWorktreeTool.handler({"action": "remove", "discard_changes": True}, ctx)
        assert not removed.exists() and ctx.cwd == str(root) and ctx.activeWorktree is None

    asyncio.run(scenario())
    assert b"ruocun-wt-keep" in git("branch", "--list") and b"ruocun-wt-remove" not in git("branch", "--list")


def test_source_non_repo_and_owned_checkout_identity(repo, tmp_path):
    from ruocun.agent.worktree import GitBoundaryError, createWorktree

    root, git = repo
    outside = tmp_path
    while True:
        discovered = subprocess.run([shutil.which("git"), "rev-parse", "--show-toplevel"], cwd=outside, capture_output=True)
        if discovered.returncode != 0:
            break
        parent = Path(discovered.stdout.decode("utf-8").strip()).parent
        assert parent != outside and outside.is_relative_to(parent)
        outside = parent
    with tempfile.TemporaryDirectory(prefix="ruocun-source-nogit-", dir=outside) as directory:
        proof = subprocess.run([shutil.which("git"), "rev-parse", "--show-toplevel"], cwd=directory, capture_output=True)
        assert proof.returncode != 0
        assert createWorktree(directory, "nonrepo") is None
    with pytest.raises(GitBoundaryError):
        createWorktree(root, "..")
    nested = root / "nested"
    nested.mkdir()
    tree = createWorktree(nested, "identity")
    assert tree is not None
    assert Path(tree.root).is_relative_to(nested / ".ruocun" / "worktrees")
    git("switch", "--detach", cwd=tree.root)
    with pytest.raises(GitBoundaryError):
        tree.cleanup(discard_changes=True)
    assert Path(tree.root).is_dir()
    assert tree.branch.encode() in git("branch", "--list")


def test_source_isolated_agent_preserves_changes_and_cleans_only_clean_tree(repo):
    from ruocun.agent.worktree import (
        GitBoundaryError,
        createWorktree,
        finishAgentWorktree,
        openAgentWorktree,
        verifyAgentWorktree,
    )
    from ruocun.tools.agent import agentTool
    from ruocun.tools.types import ToolContext

    root, git = repo

    async def scenario():
        created, requests = [], []
        ctx = ToolContext(str(root), createWorktree=lambda name: createWorktree(root, name))

        async def run(request):
            requests.append(request)
            tree = await openAgentWorktree(ctx, request.isolation)
            created.append(tree)
            checkout = Path(tree.root)
            if request.task in {"dirty", "committed"}:
                (checkout / "agent.txt").write_text(request.task, encoding="utf-8")
            if request.task == "committed":
                git("add", ".", cwd=checkout)
                git("commit", "-qm", "child result", cwd=checkout)
            return await finishAgentWorktree(tree, "done")

        ctx.runAgent = run
        dirty = await agentTool.handler({"task": "dirty", "isolate": True}, ctx)
        committed = await agentTool.handler({"task": "committed", "isolation": "remote", "isolate": True}, ctx)
        clean = await agentTool.handler({"task": "clean", "isolation": "worktree"}, ctx)
        assert [request.isolation for request in requests] == ["worktree", "remote", "worktree"]
        assert created[0].branch in dirty and Path(created[0].root).is_dir()
        assert created[1].branch in committed and Path(created[1].root).is_dir()
        assert clean == "done" and not Path(created[2].root).exists()
        assert created[2].branch.encode() not in git("branch", "--list")
        verifyAgentWorktree(root, Path(created[1].root), environ=os.environ)
        git("switch", "--detach", cwd=created[1].root)
        with pytest.raises(GitBoundaryError):
            verifyAgentWorktree(root, Path(created[1].root), environ=os.environ)
        assert not (root / "agent.txt").exists() and ctx.cwd is None

    asyncio.run(scenario())


def test_source_agent_dispatch_and_git_failure_boundary():
    from ruocun.agent.worktree import (
        GitBoundaryError,
        GitMutationUnknown,
        openAgentWorktree,
    )
    from ruocun.tools.agent import agentTool
    from ruocun.tools.types import ToolContext

    async def scenario():
        calls = []

        async def run(request):
            calls.append(request)
            return "child"

        ctx = ToolContext("/synthetic", runAgent=run, agentRunsInBackground=lambda name: name == "verify")
        assert "互斥" in await agentTool.handler({"task": "x", "fork": True, "model": "other"}, ctx)
        assert "互斥" in await agentTool.handler({"task": "x", "fork": True, "isolation": "remote"}, ctx)
        assert not calls
        assert await agentTool.handler({"task": "fork", "fork": True, "agent_type": "verify"}, ctx) == "child"
        assert calls[0].fork is True and calls[0].isolation is None
        with pytest.raises(GitBoundaryError):
            await openAgentWorktree(ctx, "worktree")
        ctx.createWorktree = lambda _: None
        with pytest.raises(GitBoundaryError):
            await openAgentWorktree(ctx, "remote")

        def unconfirmed(_):
            raise GitMutationUnknown("synthetic Git response lost")

        ctx.createWorktree = unconfirmed
        with pytest.raises(GitMutationUnknown, match="response lost"):
            await openAgentWorktree(ctx, "remote")

    asyncio.run(scenario())
