"""冻结 render-trace.mjs（MIT），生成自包含的 HTML。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def renderTraceHtml(
    trace: Path, *, passed: bool | None = None, task_id: str | None = None, source_hint: str | None = None,
) -> str:
    state = json.loads((trace / "state.json").read_text(encoding="utf-8"))
    turns_raw = [
        json.loads(line) for line in (trace / "turns.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if not turns_raw:
        raise ValueError("轨迹没有已保存的 assistant 回合。")
    messages = state["messages"]
    results = {row["tool_call_id"]: row.get("content") for row in messages if row.get("role") == "tool"}
    turns = []
    for row in turns_raw:
        message = messages[row["msgIndex"]]
        args = {call["id"]: call["function"].get("arguments") for call in message.get("tool_calls") or []}
        turns.append({
            "turn": row["turn"], "text": message.get("content"), "reasoning": message.get("reasoningContent"),
            "cache": row.get("cache"), "toolCalls": [
                {"name": call["name"], "args": args.get(call["id"]), "ok": call["ok"], "result": results.get(call["id"])}
                for call in row["toolCalls"]
            ],
        })
    data: dict[str, Any] = {
        "taskId": task_id or state.get("id"), "pass": passed, "model": state.get("model"), "mode": state.get("mode"),
        "sessionId": state.get("id"), "usage": state.get("usage"), "sourceHint": source_hint or trace.name, "turns": turns,
    }
    template = (Path(__file__).parent / "trace-viewer-template.html").read_text(encoding="utf-8")
    embedded = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    return template.replace("__TRACE_DATA__", embedded, 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    trace = args.directory if (args.directory / "state.json").is_file() else args.directory / "trace"
    meta_path = trace.parent / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {}
    result = trace / "trace.html"
    result.write_text(renderTraceHtml(trace, passed=meta.get("pass"), task_id=meta.get("id")), encoding="utf-8")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
