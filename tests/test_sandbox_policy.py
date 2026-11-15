"""Frozen write scopes and the ordinary disabled path."""

import sys
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from ruocun.platform.sandbox_policy import (
    SandboxPolicy,
    createSandboxPolicy,
    parseSandboxPolicy,
)
from ruocun.platform.shell_plan import buildShellPlan
from ruocun.tools.exec_shell import _backup_databases, _spill_output
from ruocun.tools.shell_runner import parse_plan, plan_payload


def test_policy_disabled_keeps_old_plan(tmp_path):
    assert createSandboxPolicy(tmp_path, {}) is None
    plan = buildShellPlan("echo ordinary", str(tmp_path), environ={}, analyze=False)
    payload = plan_payload(plan)
    payload.pop("sandbox")
    assert parse_plan(payload) == plan


def test_shell_host_backups_and_spill_obey_the_same_write_policy(tmp_path):
    protected = tmp_path / "protected"
    protected.mkdir()
    database = protected / "one.db"
    database.write_text("synthetic-original", encoding="utf-8")
    policy = SandboxPolicy("unused", "unused", str(tmp_path / "temp"), str(tmp_path / "cache"),
                           (str(tmp_path),), (str(protected), str(tmp_path / ".ruocun")))
    assert _backup_databases('type "protected/one.db"', str(tmp_path), policy=policy) is None
    assert not Path(str(database) + ".ruocun-backup").exists()
    assert "已落盘" not in _spill_output("x" * 17000, str(tmp_path), policy=policy)
    assert not (tmp_path / ".ruocun").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows MXC policy")
def test_policy_freezes_project_and_protects_trusted_state(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    env = {"RUOCUN_SANDBOX": "1", "USERPROFILE": str(home),
           "RUOCUN_SANDBOX_CLI": str(tmp_path / "dependency/bin/codex.exe")}
    policy = createSandboxPolicy(project, env)
    assert policy is not None
    assert policy.allowsWrite(str(project / "new.py"))
    assert policy.allowsWrite(str(Path(policy.cacheRoot) / "file"))
    assert not policy.allowsWrite(str(tmp_path / "other/new.py"))
    assert policy.isProtected(str(home / ".ruocun/sessions/one/capability"))
    assert policy.isProtected(str(home / ".ruocun/runtime/sqlite3.dll"))
    assert not policy.allowsWrite(str(home / ".ruocun/sandbox/control/config.toml"))
    assert parseSandboxPolicy(asdict(policy)) == policy
    plan = replace(buildShellPlan("echo frozen", str(project), environ=env, analyze=False), sandbox=policy)
    assert parse_plan(plan_payload(plan)) == plan
    with pytest.raises(ValueError):
        parseSandboxPolicy({**asdict(policy), "writableRoots": [3]})
