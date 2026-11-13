"""Frozen memory run.ts (MIT): explicit report outputs for extraction and recall."""

import argparse
import asyncio
import json
from functools import partial
from pathlib import Path
from typing import Any

from ..materialize_trace import redact_data
from ..run import EnvironmentIssue
from .extract import runExtractCase
from .injection_ab import runInjectionABCase
from .lib.creds import EvalConfig, InvalidEvaluation, loadEvalConfig
from .lib.redact import redactText
from .recall import runRecallCase
from .report import formatReport

FIXTURES = Path(__file__).parent / "fixtures"


async def runCases(fixture_root: Path, which: str, cfg: EvalConfig) -> dict[str, Any]:
    modes = {"extract": runExtractCase, "recall": runRecallCase, "injection-ab": runInjectionABCase}
    selected = ("extract", "recall") if which == "both" else (which,)
    rows: list[dict[str, Any]] = []
    redact = partial(redactText, known_secret=cfg.options["apiKey"])
    for kind in selected:
        directory = fixture_root / ("recall" if kind == "injection-ab" else kind)
        cases = sorted(path for path in directory.iterdir() if path.is_dir() and not path.is_symlink()) if directory.is_dir() else []
        if not cases:
            rows.append({"case": "fixtures", "kind": kind, "status": "invalid"})
            continue
        for case in cases:
            name = redact(case.name)
            try:
                score = await modes[kind](case, cfg.call, cfg)
            except (InvalidEvaluation, ValueError, OSError):
                rows.append({"case": name, "kind": kind, "status": "invalid"})
                continue
            except EnvironmentIssue:
                rows.append({"case": name, "kind": kind, "status": "environment_unavailable"})
                continue
            status = "failed" if score.get("staleLeak", 0) else "scored"
            rows.append({"case": name, "kind": kind, "status": status, **redact_data(score, redact)})
    return {"mode": cfg.mode, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("which", nargs="?", choices=("extract", "recall", "injection-ab", "both"), default="both")
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--judge-k", type=int, default=3)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    try:
        cfg = loadEvalConfig(args.config, live=args.allow_live, judge_k=args.judge_k)
    except (EnvironmentIssue, ValueError, OSError):
        parser.error("评估模型配置不可用。")
    report = asyncio.run(runCases(args.fixtures, args.which, cfg))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "report.md").write_text(formatReport(report), encoding="utf-8")
    return 0 if report["rows"] and all(row["status"] == "scored" for row in report["rows"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
