"""Pinned backend preparation, frozen profiles and raw Windows command contract."""

from __future__ import annotations

import base64
import hashlib
import os
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from ruocun.platform.shell_plan import buildShellPlan
from ruocun.platform.windows import sandbox

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows paths and private files")


@pytest.fixture
def backend(tmp_path, monkeypatch):
    cli = tmp_path / "dependency" / "codex.exe"
    cli.parent.mkdir()
    cli.write_bytes(b"synthetic CLI identity; never executed")
    monkeypatch.setattr(sandbox, "CODEX_SHA256", hashlib.sha256(cli.read_bytes()).hexdigest())
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    options = dict(executable=str(cli), stateRoot=str(tmp_path / "control"),
                   writableRoots=(str(workspace),), tempRoot=str(tmp_path / "temp"), cacheRoot=str(tmp_path / "cache"))
    env = sandbox.windowsSandboxEnvironment(
        {"SystemRoot": r"C:\Windows", "COMSPEC": r"C:\Windows\System32\cmd.exe",
         "PATH": str(tmp_path / "synthetic-bin"), "HOME": str(tmp_path / "existing-home"),
         "USERPROFILE": str(tmp_path / "existing-home"), "APPDATA": str(tmp_path / "existing-appdata"),
         "MAVEN_OPTS": "-Xmx128m", "SYNTHETIC_NORMAL": "retained", "SYNTHETIC_API_KEY": "removed"},
        stateRoot=options["stateRoot"], tempRoot=options["tempRoot"], cacheRoot=options["cacheRoot"])
    plan = buildShellPlan('echo "中文 空格 & argument"', str(workspace), environ=env, analyze=False)
    return options, plan


def test_environment_is_prepared_once_and_preserves_home_and_existing_options(backend):
    options, plan = backend
    env = dict(plan.environment)
    again = sandbox.windowsSandboxEnvironment(env, stateRoot=options["stateRoot"],
        tempRoot=options["tempRoot"], cacheRoot=options["cacheRoot"])
    assert again == env and env["HOME"].endswith("existing-home")
    assert env["USERPROFILE"] == env["HOME"] and env["APPDATA"].endswith("existing-appdata")
    assert env["MAVEN_OPTS"].startswith("-Xmx128m ") and env["MAVEN_OPTS"].count("-Dmaven.repo.local=") == 1
    assert env["SystemDrive"] == "C:" and env["SYNTHETIC_NORMAL"] == "retained"
    assert "SYNTHETIC_API_KEY" not in env
    for name in ("stateRoot", "tempRoot", "cacheRoot"):
        assert Path(options[name]).is_dir()
        sandbox.ensure_private_dir(Path(options[name]))


def test_environment_refuses_existing_public_temp_without_changing_acl(tmp_path):
    from ruocun.platform.windows.durable_file import _read_acl_sddl

    temporary = tmp_path / "ordinary-temp"
    temporary.mkdir()
    before = _read_acl_sddl(temporary)
    with pytest.raises(sandbox.WindowsSandboxError, match="启动前安全准备"):
        sandbox.windowsSandboxEnvironment({"SystemRoot": r"C:\Windows"},
            stateRoot=str(tmp_path / "control"), tempRoot=str(temporary), cacheRoot=str(tmp_path / "cache"))
    assert _read_acl_sddl(temporary) == before


def test_snapshot_keeps_raw_command_and_environment_and_freezes_each_grant(backend, tmp_path):
    options, plan = backend
    wrapped = sandbox.windowsSandboxExecutionPlan(plan, **options)
    assert wrapped.environment == plan.environment and wrapped.command == plan.command and wrapped.commandLine is None
    assert base64.b64decode(wrapped.argv[-3]).decode("utf-8") == plan.commandLine
    assert wrapped.argv[-2] == plan.argv[0] and wrapped.argv[-1] == options["tempRoot"]
    assert "stdin=sys.stdin,stdout=sys.stdout,stderr=sys.stderr" in wrapped.argv[-4]
    assert wrapped.argv[3:5] == ("sandbox", "--profile") and "windows" not in wrapped.argv
    profile_path = Path(options["stateRoot"]) / (wrapped.argv[5] + ".config.toml")
    original = profile_path.read_bytes()
    profile = tomllib.loads(original.decode("utf-8"))
    assert profile["windows"]["sandbox"] == "mxc" and not profile["features"]["network_proxy"]
    rules = profile["permissions"]["ruocun"]["filesystem"]
    assert rules[":root"] == "read" and rules[options["writableRoots"][0]] == "write"
    assert rules[options["stateRoot"]] == "read" and rules[str(Path(options["executable"]).parent)] == "read"
    extra = tmp_path / "approved-once"
    extra.mkdir()
    expanded = sandbox.windowsSandboxExecutionPlan(plan, **{**options, "writableRoots": (*options["writableRoots"], str(extra))})
    assert expanded.argv[5] != wrapped.argv[5] and profile_path.read_bytes() == original
    restored = sandbox.windowsSandboxExecutionPlan(plan, **options)
    assert restored == wrapped
    no_net = sandbox.windowsSandboxExecutionPlan(plan, **options, noNet=True)
    no_net_file = Path(options["stateRoot"]) / (no_net.argv[5] + ".config.toml")
    assert not tomllib.loads(no_net_file.read_text(encoding="utf-8"))["permissions"]["ruocun"]["network"]["enabled"]


@pytest.mark.parametrize("target", ["base", "profile"])
def test_changed_configuration_is_rejected_without_overwriting(backend, target):
    options, plan = backend
    wrapped = sandbox.windowsSandboxExecutionPlan(plan, **options)
    name = "config.toml" if target == "base" else wrapped.argv[5] + ".config.toml"
    selected = Path(options["stateRoot"]) / name
    selected.write_text("# synthetic changed configuration\n", encoding="utf-8")
    with pytest.raises(sandbox.WindowsSandboxError, match="配置已改变"):
        sandbox.windowsSandboxExecutionPlan(plan, **options)
    assert selected.read_text(encoding="utf-8") == "# synthetic changed configuration\n"


def test_bridge_restores_only_frozen_temp_after_mxc_environment_rewrite(backend, monkeypatch):
    options, plan = backend
    wrapped = sandbox.windowsSandboxExecutionPlan(plan, **options)
    inherited = {"TEMP": "synthetic-mxc-temp", "TMP": "synthetic-mxc-tmp", "TMPDIR": "synthetic-mxc-tempdir",
                 "HOME": "synthetic-home", "USERPROFILE": "synthetic-profile", "LOCALAPPDATA": "synthetic-sdk-appdata",
                 "PIP_CACHE_DIR": "synthetic-pip-cache", "SYNTHETIC_SDK_STATE": "retained"}
    actual = dict(inherited)
    monkeypatch.setattr(os, "environ", actual)
    monkeypatch.setattr(sys, "argv", ["-c", *wrapped.argv[-3:]])

    def launch(raw, **kwargs):
        assert raw == plan.commandLine and kwargs["executable"] == plan.argv[0] and kwargs["shell"] is False
        assert kwargs["stdin"] is sys.stdin and kwargs["stdout"] is sys.stdout and kwargs["stderr"] is sys.stderr
        expected = {**inherited, **dict.fromkeys(("TEMP", "TMP", "TMPDIR"), options["tempRoot"])}
        assert actual == expected
        return 7

    monkeypatch.setattr(subprocess, "call", launch)
    with pytest.raises(SystemExit) as stopped:
        exec(sandbox._BRIDGE, {"__name__": "__main__"})
    assert stopped.value.code == 7


def test_pin_missing_dependency_unfrozen_env_and_protected_grants_fail_closed(backend, tmp_path):
    options, plan = backend
    with pytest.raises(sandbox.WindowsSandboxError, match="缺少固定"):
        sandbox.windowsSandboxExecutionPlan(plan, **{**options, "executable": str(tmp_path / "missing.exe")})
    cli = Path(options["executable"])
    cli.write_bytes(b"synthetic different build")
    with pytest.raises(sandbox.WindowsSandboxError, match="构建或文件已改变"):
        sandbox.windowsSandboxExecutionPlan(plan, **options)
    cli.write_bytes(b"synthetic CLI identity; never executed")
    with pytest.raises(sandbox.WindowsSandboxError, match="审批前冻结"):
        sandbox.windowsSandboxExecutionPlan(replace(plan, environment=tuple((k, v) for k, v in plan.environment if k != "TEMP")), **options)
    for protected in (options["stateRoot"], str(cli.parent)):
        with pytest.raises(sandbox.WindowsSandboxError, match="受保护"):
            sandbox.windowsSandboxExecutionPlan(plan, **{**options, "writableRoots": (protected,)})
    with pytest.raises(sandbox.WindowsSandboxError, match="保真"):
        sandbox.windowsSandboxExecutionPlan(replace(plan, commandLine="synthetic different raw line"), **options)
    assert not (Path(options["stateRoot"]) / "config.toml").exists()


def test_excessive_command_is_rejected_before_control_files(backend):
    options, plan = backend
    command = "echo " + "长" * 12000
    oversized = buildShellPlan(command, plan.cwd, environ=dict(plan.environment), analyze=False)
    with pytest.raises(sandbox.WindowsSandboxError, match="长度限制"):
        sandbox.windowsSandboxExecutionPlan(oversized, **options)
    assert not (Path(options["stateRoot"]) / "config.toml").exists()
