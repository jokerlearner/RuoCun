"""冻结 SWE-bench adapter.mjs（MIT）：从本地实例清单生成补丁，评分留给官方 harness。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from ..run import Settings, Task, runOnce

_COMPONENT = re.compile(r"[a-zA-Z0-9_.-]+")
_REPOSITORY = re.compile(r"[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+")
_COMMIT = re.compile(r"[0-9a-fA-F]{40}")


def _instances(path: Path, selected: list[str]) -> list[dict[str, Any]]:
    records = []
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = row.get("instance_id")
        if not isinstance(key, str) or key in (".", "..") or not _COMPONENT.fullmatch(key) or key in seen:
            raise ValueError("SWE 实例标识无效或重复。")
        seen.add(key)
        if selected and key not in selected:
            continue
        if (not isinstance(row.get("repo"), str) or not _REPOSITORY.fullmatch(row["repo"])
                or not isinstance(row.get("base_commit"), str) or not _COMMIT.fullmatch(row["base_commit"])
                or not isinstance(row.get("problem_statement"), str)):
            raise ValueError("SWE 实例缺少仓库、固定提交或问题描述。")
        records.append(row)
    if not records or set(selected).difference(row["instance_id"] for row in records):
        raise ValueError("SWE 清单中没有匹配实例。")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--timeout-ms", type=int, default=600_000)
    parser.add_argument("--git")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()
    if not args.instances.is_file():
        print(json.dumps({"status": "environment_unavailable", "reason": "缺少本地 SWE 实例清单。"}, ensure_ascii=False))
        return 2
    try:
        rows = _instances(args.instances, args.ids)
    except (OSError, ValueError):
        print(json.dumps({"status": "invalid_dataset", "reason": "SWE 清单缺失有效实例。"}, ensure_ascii=False))
        return 2
    if args.list:
        for row in rows:
            print(row["instance_id"])
        return 0
    if not args.allow_network or not args.config or not args.output or args.timeout_ms <= 0:
        parser.error("执行推理须提供配置、输出、正数超时并显式允许联网克隆。")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    settings = Settings(args.config.resolve(), args.timeout_ms / 1000, args.model, git=args.git,
                        network=True, live=args.allow_live, inference_only=True)
    predictions = []
    for row in rows:
        task_id = row["instance_id"]
        directory = root / task_id
        prompt = f"这是仓库 {row['repo']} 中的实际问题。请定位并修复，只改必要的源码。\n\n{row['problem_statement']}"
        task = Task(task_id, root, {"kind": "oss", "repo": f"https://github.com/{row['repo']}",
                                   "ref": row["base_commit"], "prompt": prompt})
        report = runOnce(task, settings, directory, 1)
        if report["status"] == "prediction_ready":
            patch = (directory / "agent.diff").read_text(encoding="utf-8")
            predictions.append({"instance_id": task_id, "model_name_or_path": args.model or "ruocun",
                                "model_patch": "" if patch == "(无改动)" else patch})
    (root / "predictions.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions),
                                           encoding="utf-8")
    print(json.dumps({"status": "predictions_only", "produced": len(predictions), "requested": len(rows)}))
    return 0 if len(predictions) == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
