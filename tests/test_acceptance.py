"""T-N2: the installed development driver calls installed product boundaries."""

import json
import subprocess
import sys

import pytest


def acceptance(tmp_path, *arguments):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {
        "SYSTEMROOT": "C:\\Windows", "WINDIR": "C:\\Windows",
        "HOME": str(home), "USERPROFILE": str(home),
        "APPDATA": str(home / "appdata"), "LOCALAPPDATA": str(home / "localappdata"),
        "TEMP": str(home), "TMP": str(home), "PYTHONUTF8": "1",
        "PYTHONNOUSERSITE": "1",
    }
    return subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-m", "ruocun_acceptance", *arguments],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


def test_offline_driver_runs_real_installed_cli_and_resource_cases(tmp_path):
    result = acceptance(tmp_path, "offline", "--output", str(tmp_path / "evidence"))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["suite"] == "offline"
    assert {case["id"] for case in report["cases"]} == {
        "ENT-01.version", "ENT-01.help", "ENT-01.resource", "ENT-01.missing-config",
    }
    assert all(case["status"] == "passed" for case in report["cases"])
    assert all(case["argv"] for case in report["cases"])


@pytest.mark.parametrize("suite", ["oracle", "runtime", "protocol", "live", "terminal", "install"])
def test_unimplemented_suites_are_explicitly_not_run(tmp_path, suite):
    result = acceptance(tmp_path, suite, "--output", str(tmp_path / "evidence"))
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert report["cases"][0]["status"] == "not-run"
    assert report["cases"][0]["reason"]


def test_missing_product_interpreter_failure_propagates(tmp_path):
    result = acceptance(
        tmp_path, "offline", "--python", str(tmp_path / "absent-python.exe"),
        "--output", str(tmp_path / "evidence"),
    )
    assert result.returncode != 0
    report = json.loads(result.stdout)
    assert all(case["status"] == "failed" for case in report["cases"])
    assert all(case["cleanup"]["command_joined"] for case in report["cases"])


@pytest.mark.parametrize("extra", [("--case", "no-such-case"), ()])
def test_empty_selection_and_unknown_suite_are_nonzero(tmp_path, extra):
    arguments = ("offline", *extra) if extra else ("unknown-suite",)
    result = acceptance(tmp_path, *arguments, "--output", str(tmp_path / "evidence"))
    assert result.returncode != 0
    if extra:
        assert json.loads(result.stdout)["cases"][0]["status"] == "not-run"
