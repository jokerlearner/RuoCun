"""ENT-01: observe an installed package through the real CLI boundary."""

import subprocess
import sys
from pathlib import Path

import pytest


def cli(tmp_path, *arguments):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        "SYSTEMROOT": "C:\\Windows",
        "WINDIR": "C:\\Windows",
        "PATH": str(Path(sys.executable).parent),
        "HOME": str(home),
        "USERPROFILE": str(home),
        "APPDATA": str(home / "appdata"),
        "LOCALAPPDATA": str(home / "localappdata"),
        "TEMP": str(home),
        "TMP": str(home),
        "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
    }
    assert "PYTHONPATH" not in env
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-m", "ruocun", *arguments],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )


@pytest.mark.parametrize("arguments", [("--version",), ("-v",), ("synthetic", "--version")])
def test_installed_version_does_not_start_an_agent(tmp_path, arguments):
    """Frozen index.ts:216-220; RuoCun own development version, ENT-01."""
    result = cli(tmp_path, *arguments)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "RuoCun v0.1.0.dev0\n"
    assert result.stderr == ""


def test_help_reads_the_installed_chinese_resource_without_an_agent(tmp_path):
    """Spec ENT-01/R-15 explicitly requires an actual installed help resource."""
    result = cli(tmp_path, "--help")
    assert result.returncode == 0, result.stderr
    assert "用法：ruocun [选项] [提示词]" in result.stdout
    assert "--version, -v" in result.stdout
    assert "TodoWrite、Skill" in result.stdout  # ADR-0012：普通入口已增加静态Skill
    assert result.stderr == ""
