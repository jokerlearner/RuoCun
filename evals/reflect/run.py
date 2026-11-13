"""Frozen reflect run.ts (MIT): six controls and explicit invalid/failed cases."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from statistics import fmean
from typing import Any

from ruocun.memory.distill import ModelCall

from ..memory.lib.creds import EvalConfig, InvalidEvaluation, loadEvalConfig
from ..memory.lib.metrics import precisionRecall
from ..memory.lib.redact import redactText
from ..run import EnvironmentIssue
from .grade import runReflectCase

FIXTURES = Path(__file__).parent / "fixtures"


async def runCases(directories: list[Path], call: ModelCall, config: EvalConfig) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for directory in directories:
        try:
            score = await runReflectCase(directory, call, config)
        except (InvalidEvaluation, ValueError, OSError):
            rows.append({"case": directory.name, "status": "invalid"})
            continue
        except Exception:
            rows.append({"case": directory.name, "status": "environment_unavailable"})
            continue
        advisory = score.pop("advisory")
        if isinstance(advisory, str):
            score["advisory"] = redactText(advisory, known_secret=config.options.get("apiKey", ""))
        status = "passed" if score["onTrackMatch"] and score["advisoryOnPoint"] != 0 else "failed"
        rows.append({"case": directory.name, "status": status, **score})
    graded = [row for row in rows if row["status"] in ("passed", "failed")]
    predicted = {row["case"] for row in graded if not row["gotOnTrack"]}
    gold = {row["case"] for row in graded if not row["expectedOnTrack"]}
    points = [float(row["advisoryOnPoint"]) for row in graded if row["advisoryOnPoint"] is not None]
    has_controls = bool(gold) and len(gold) < len(graded)
    return {"mode": config.mode, "rows": rows, "scored": len(graded), "balancedControls": has_controls,
            "alarmPR": precisionRecall(predicted, gold) if has_controls else None,
            "advisoryOnPoint": fmean(points) if points else None}


def formatReport(report: dict[str, Any]) -> str:
    lines = ["# 反思评估", "", f"运行模式 {report['mode']}。已评分 {report['scored']} 项。",
             "", "| 用例 | 期望在轨 | 实得在轨 | advisory 点中 | 结果 |",
             "| --- | --- | --- | --- | --- |"]
    for row in report["rows"]:
        lines.append(f"| {row['case']} | {row.get('expectedOnTrack', '—')} | {row.get('gotOnTrack', '—')} "
                     f"| {row.get('advisoryOnPoint', '—')} | {row['status']} |")
    pr = report["alarmPR"]
    lines.extend(("", f"报警 P/R/F1 {pr['p']:.2f}/{pr['r']:.2f}/{pr['f1']:.2f}" if pr is not None else
                  "报警 P/R/F1 待有效的报警与正控样本同时齐备。",
                  f"Advisory 点中率 {report['advisoryOnPoint'] if report['advisoryOnPoint'] is not None else 'N/A'}。"))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--judge-k", type=int, default=3)
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    directories = sorted(path for path in args.fixtures.iterdir() if path.is_dir())
    if not directories:
        parser.error("缺少反思评估用例。")
    try:
        config = loadEvalConfig(args.config, live=args.allow_live, judge_k=args.judge_k)
    except (EnvironmentIssue, OSError, ValueError):
        parser.error("评估模型配置不可用。")
    report = asyncio.run(runCases(directories, config.call, config))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "report.md").write_text(formatReport(report), encoding="utf-8")
    return 0 if report["balancedControls"] and all(row["status"] == "passed" for row in report["rows"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
