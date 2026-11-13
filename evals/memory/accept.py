"""Run the frozen memory and cache acceptance sequences through the ordinary CLI."""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from ruocun.platform.process_tree import ForegroundResult

from ..run import EnvironmentIssue, OutcomeUnknown, _isolated_env, _profile, _run, agent_command, privateProfile
from .cache import gradeCache
from .lib.creds import InvalidEvaluation
from .lib.transcript import parseJsonl

_MEMORY_FIRST = "我在 macOS 上用 pnpm 管理依赖,平时在学习 AI agent 的实现原理。先随便回我一句就行。"
_MEMORY_SECOND = "我平时用什么包管理器?直接告诉我。"
_CACHE_PROMPTS = ("你好,用一句话介绍你自己就好", "/cost", "用一句话讲讲什么是闭包",
                  "再用一句话讲讲什么是递归", "/cost", "/exit")


def _run_agent(config: Path, workspace: Path, env: dict[str, str], lines: tuple[str, ...],
               *, local_only: bool, reflect: bool = False) -> ForegroundResult:
    args = agent_command(config, workspace, None, None, evaluation=False, local_only=local_only)
    if reflect:
        args.append("--reflect-memory")
    result = _run(args, workspace, env, 45, ("\n".join(lines) + "\n").encode())
    if result.aborted or result.outputCapped or result.code:
        raise EnvironmentIssue("产品 CLI 退出或输出不满足评估条件。")
    return result


def _trace_files(home: Path, filename: str) -> dict[str, Path]:
    return {path.parent.name: path for path in (home / ".ruocun" / "sessions").glob(f"*/*/{filename}")}


def _memory(config: Path, home: Path, workspace: Path, env: dict[str, str], *, local_only: bool) -> dict[str, Any]:
    _run_agent(config, workspace, env, (_MEMORY_FIRST, "/exit"), local_only=local_only, reflect=True)
    first_trace = _trace_files(home, "memory-trace.jsonl")
    first = [row for path in first_trace.values() for row in parseJsonl(path.read_text(encoding="utf-8"))]
    memory_dirs = (workspace / ".ruocun" / "memory", home / ".ruocun" / "memory", home / ".ruocun" / "knowledge")
    files = [file for directory in memory_dirs for file in directory.glob("*.md")]
    stored = any("pnpm" in file.read_text(encoding="utf-8").casefold() for file in files)
    second = _run_agent(config, workspace, env, (_MEMORY_SECOND, "/exit"), local_only=local_only)
    second_trace = _trace_files(home, "memory-trace.jsonl")
    recall = [row for session, path in second_trace.items() if session not in first_trace
              for row in parseJsonl(path.read_text(encoding="utf-8")) if row.get("kind") == "recalled"]
    reflected = sum(int(row.get("memAdded", 0)) for row in first if row.get("kind") == "reflected" and row.get("ran"))
    recalled = sum(int(row.get("injected", 0)) for row in recall)
    recalled_answer = "pnpm" in second.stdout.casefold()
    tools = second.stdout.count("→ ")
    status = "observed" if stored and reflected and recalled and recalled_answer and not tools else "not_observed"
    return {"status": status, "persistedCount": len(files), "reflectedAdded": reflected,
            "recallInjected": recalled, "answerMentionsPnpm": recalled_answer, "visibleToolMarkers": tools}


def runAcceptance(which: str, config: Path, *, live: bool) -> dict[str, Any]:
    report: dict[str, Any] = {"kind": which, "mode": "live" if live else "offline"}
    root = Path(tempfile.mkdtemp(prefix="rc-m-"))
    try:
        profile, _ = _profile(config, live=live)
        home, workspace = root / "h", root / "w"
        workspace.mkdir()
        env = _isolated_env(home)
        env.update(RUOCUN_LANG="zh", RUOCUN_REFLECT_SYNC="1", RUOCUN_REASONING_EFFORT="low")
        with privateProfile(profile) as private:
            if which == "memory":
                report.update(_memory(private, home, workspace, env, local_only=not live))
            else:
                _run_agent(private, workspace, env, _CACHE_PROMPTS, local_only=not live)
                paths = list(_trace_files(home, "cache.jsonl").values())
                if len(paths) != 1:
                    raise InvalidEvaluation("缺少唯一缓存审计。")
                report.update(gradeCache(paths[0]))
    except OutcomeUnknown:
        report.update(status="outcome_unknown", workspaceRetained=str(root))
    except (InvalidEvaluation, OSError, ValueError):
        report.update(status="invalid")
    except EnvironmentIssue:
        report.update(status="environment_unavailable")
    finally:
        if report.get("status") != "outcome_unknown":
            try:
                shutil.rmtree(root)
            except OSError:
                report.update(status="outcome_unknown", workspaceRetained=str(root))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("which", choices=("memory", "cache"))
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    report = runAcceptance(args.which, args.config, live=args.allow_live)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["status"] in ("observed", "measured") else 1


if __name__ == "__main__":
    raise SystemExit(main())
