"""The seven confirmed acceptance suite names, with honest per-case evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal

from .environment import isolated_env

Status = Literal["passed", "failed", "not-run", "cancelled", "cleanup-failed"]
SUITES = ("oracle", "offline", "runtime", "protocol", "live", "terminal", "install")


@dataclass(frozen=True)
class Case:
    id: str
    arguments: tuple[str, ...]
    exit: int
    contains: str
    source: str
    stderr: bool = False


def offline_cases(expected_version: str) -> list[Case]:
    return [
        Case("ENT-01.version", ("-m", "ruocun", "--version"), 0,
             f"RuoCun v{expected_version}\n",
             "frozen src/index.ts:216-220; installed distribution metadata; R-02"),
        Case("ENT-01.help", ("-m", "ruocun", "--help"), 0,
             "用法：ruocun [选项] [提示词]", "ENT-01/R-15 help resource requirement"),
        Case("ENT-01.resource", ("-c",
             "from importlib.resources import files; "
             "print(files('ruocun').joinpath('resources/help.zh-CN.txt').read_text(encoding='utf-8'))"),
             0, "--version, -v", "R-15/importlib.resources installed package boundary"),
        Case("ENT-01.missing-config", ("-m", "ruocun", "合成提示词"), 71,
             "缺少可用账户", "ADR-0011: actual agent rejects missing synthetic config", True),
    ]


def diagnostic(operation: str, error: BaseException) -> dict[str, object]:
    """Keep actionable operation/error codes without copying arbitrary exception text."""
    result: dict[str, object] = {"operation": operation, "exception": type(error).__name__}
    for name in ("errno", "winerror"):
        value = getattr(error, name, None)
        if isinstance(value, int):
            result[name] = value
    return result


def finish_owned_child(
    process: subprocess.Popen[bytes], abort: bool,
) -> tuple[int | None, dict[str, object]]:
    """Resolve only this Popen-owned process and pipes, using its process handle.

    A stop request is not an exit observation. Observation or pipe-close failures
    remain explicit; a caller must not run another case after incomplete cleanup.
    """
    errors: list[dict[str, object]] = []
    stop_requested = False
    if abort:
        try:
            running = process.poll() is None
        except BaseException as exc:
            errors.append(diagnostic("poll", exc))
            running = True
        if running:
            stop_requested = True
            try:
                process.kill()
            except BaseException as exc:
                errors.append(diagnostic("kill", exc))
    code: int | None = None
    try:
        code = process.wait(timeout=5)
    except BaseException as exc:
        errors.append(diagnostic("wait", exc))
        try:
            code = process.poll()
        except BaseException as poll_error:
            errors.append(diagnostic("poll", poll_error))
    streams_closed = True
    for name, stream in (("stdout", process.stdout), ("stderr", process.stderr)):
        if stream is not None:
            try:
                stream.close()
            except BaseException as exc:
                errors.append(diagnostic(f"close-{name}", exc))
            streams_closed = streams_closed and stream.closed
    return code, {
        "process_started": True, "command_joined": code is not None,
        "streams_closed": streams_closed, "stop_requested": stop_requested,
        "errors": errors, "workspace_retained": True,
    }


def execute(case: Case, python: Path, output: Path) -> dict[str, object]:
    workspace = output / case.id
    workspace.mkdir()
    argv = [str(python), "-I", "-X", "utf8", *case.arguments]
    evidence: dict[str, object] = {
        "id": case.id, "argv": argv, "cwd": str(workspace),
        "expected": {"exit": case.exit, "contains": case.contains, "stderr": case.stderr},
        "expected_source": case.source,
        "environment": "explicit allowlist; synthetic home/config/temp; no PYTHONPATH",
    }
    stdout, stderr = b"", b""
    process: subprocess.Popen[bytes] | None = None
    completed = False
    abort = True
    cleanup: dict[str, object] = {
        "process_started": False, "command_joined": True, "streams_closed": True,
        "stop_requested": False, "errors": [], "workspace_retained": True,
    }
    try:
        started = time.monotonic_ns()
        process = subprocess.Popen(argv, cwd=workspace,
                                   env=isolated_env(workspace, python),
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        evidence["process"] = {
            "pid": process.pid, "executable": str(python),
            "spawn_observed_monotonic_ns": started,
            "identity": "owned subprocess.Popen process/handle; no PID-based reacquisition",
        }
        stdout, stderr = process.communicate(timeout=15)
        completed = True
        actual = (stderr if case.stderr else stdout).decode(
            "utf-8", errors="replace"
        ).replace("\r\n", "\n")
        passed = process.returncode == case.exit and case.contains in actual
        if not case.stderr:
            passed = passed and not stderr
        evidence.update(status="passed" if passed else "failed", logical_exit=0 if passed else 1)
        abort = False
    except BaseException as exc:
        cancelled = isinstance(exc, KeyboardInterrupt)
        reason = "interrupted" if cancelled else type(exc).__name__
        if isinstance(exc, subprocess.TimeoutExpired):
            reason = "15 second command deadline"
            stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
            stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
        evidence.update(status="cancelled" if cancelled else "failed",
                        logical_exit=130 if cancelled else 1, reason=reason,
                        failure=diagnostic("spawn-or-communicate", exc))
    finally:
        code = None
        if process is not None:
            code, cleanup = finish_owned_child(process, abort=abort)
        evidence["exit"] = code
        evidence["output_complete"] = completed
        evidence["cleanup"] = cleanup
        errors = cleanup["errors"]
        if isinstance(errors, list) and any(
            isinstance(error, dict) and error.get("exception") == "KeyboardInterrupt"
            for error in errors
        ):
            evidence.update(status="cancelled", logical_exit=130, reason="interrupted during cleanup")
        if not cleanup["command_joined"] or not cleanup["streams_closed"]:
            evidence["status"] = "cleanup-failed"
            if evidence.get("logical_exit") != 130:
                evidence["logical_exit"] = 1
    for name, data in (("stdout", stdout), ("stderr", stderr)):
        (workspace / f"{name}.bin").write_bytes(data)
        evidence[name + "_sha256"] = hashlib.sha256(data).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=SUITES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--case", action="append", dest="case_ids")
    args = parser.parse_args()
    output = (args.output or Path.cwd() / ".ruocun-acceptance" / uuid.uuid4().hex[:8]).resolve()
    # Existing evidence must never be silently overwritten.
    output.mkdir(parents=True, exist_ok=False)
    cases: list[dict[str, object]]
    if args.suite != "offline":
        cases = [{"id": f"{args.suite}.availability", "status": "not-run",
                  "reason": "suite has no implemented product cases in task 03; "
                            "source oracle remains separately runnable with explicit frozen inputs"}]
    else:
        try:
            expected_version = version("ruocun")
        except PackageNotFoundError:
            cases = [{"id": "offline.prerequisites", "status": "not-run",
                      "reason": "ruocun distribution is not installed"}]
        else:
            selected = [case for case in offline_cases(expected_version)
                        if args.case_ids is None or case.id in args.case_ids]
            cases = []
            halted: str | None = None
            for case in selected:
                if halted:
                    cases.append({"id": case.id, "status": "not-run", "reason": halted})
                else:
                    outcome = execute(case, args.python.resolve(), output)
                    cases.append(outcome)
                    if outcome["status"] in ("cancelled", "cleanup-failed"):
                        halted = str(outcome["status"])
            if not cases:
                cases = [{"id": "offline.selection", "status": "not-run",
                          "reason": "no cases selected"}]
    success = bool(cases) and all(case["status"] == "passed" for case in cases)
    cleanups = [case["cleanup"] for case in cases if "cleanup" in case]
    joined = all(isinstance(item, dict) and item.get("command_joined") is True for item in cleanups)
    closed = all(isinstance(item, dict) and item.get("streams_closed") is True for item in cleanups)
    logical_exit = 130 if any(case.get("logical_exit") == 130 for case in cases) else (0 if success else 1)
    report = {"schema_version": 1, "suite": args.suite, "scope": "task03 implemented subset",
              "cases": cases, "status": "cleanup-failed" if not joined or not closed else
              ("passed" if success else "not-passed"), "logical_exit": logical_exit,
              "cleanup": {"commands_joined": joined, "streams_closed": closed, "workspace_retained": True}}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (output / "summary.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return logical_exit
