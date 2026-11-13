"""冻结 materialize-trace.mjs（MIT），接入 RuoCun 的权威会话。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ruocun.tools.execute import looksFailed

_AUDITS = ("tool-trace.jsonl", "perm-trace.jsonl", "memory-trace.jsonl", "skill-trace.jsonl", "cache.jsonl")
_ROLES = {"system", "user", "assistant", "tool"}


def findSessionDir(home: Path) -> Path | None:
    sessions = [path for path in (home / ".ruocun" / "sessions").glob("*/*/session.db") if path.is_file()]
    return max(sessions, key=lambda path: path.stat().st_mtime_ns).parent if sessions else None


def loadRuoCunState(session: Path) -> dict[str, Any]:
    from importlib.resources import as_file, files

    from ruocun.session.log import loadState
    from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive

    home = session.parents[3]
    archive = files("ruocun").joinpath("resources/runtime/sqlite-dll-win-x64-3540100.zip")
    with as_file(archive) as archive_file:
        dll = verify_official_archive(archive_file, home / ".ruocun" / "runtime" / "sqlite-3.54.1")
    state = loadState(session.parent, session.name, runtime=verify_controlled_runtime(dll))
    if state is None:
        raise ValueError("没有可读取的产品会话。")
    return state


def _read_jsonl(file: Path) -> list[dict[str, Any]]:
    if not file.is_file():
        return []
    rows = []
    for line in file.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def redact_data(value: Any, redact: Callable[[str], str]) -> Any:
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_data(item, redact) for item in value]
    if isinstance(value, dict):
        return {key: redact_data(item, redact) for key, item in value.items()}
    return value


def _display(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def materializeTrace(
    source: Path, output: Path, redact: Callable[[str], str] = str,
) -> dict[str, Any]:
    json_state = source / "state.json"
    state = loadRuoCunState(source) if (source / "session.db").is_file() else json.loads(json_state.read_text(encoding="utf-8"))
    state = redact_data(state, redact)
    messages = state.get("messages")
    if not isinstance(messages, list):
        raise ValueError("会话缺少有效消息。")
    message_dir = output / "messages"
    message_dir.mkdir(parents=True, exist_ok=False)
    (output / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audits = []
    for name in _AUDITS:
        audit = source / name
        if audit.is_file():
            rows = redact_data(_read_jsonl(audit), redact)
            (output / name).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
            audits.append(name)
    main_cache = sorted(
        (row for row in _read_jsonl(output / "cache.jsonl") if row.get("agent", "main") == "main" and row.get("depth", 0) == 0),
        key=lambda row: row.get("turn", 0),
    )
    turns: list[dict[str, Any]] = []
    calls_by_id: dict[str, dict[str, Any]] = {}
    for index, message in enumerate(messages):
        role = message.get("role")
        if role not in _ROLES:
            continue
        prefix = f"{index:03d}"
        content = _display(message.get("content"))
        heading = f"# [{prefix}] {role}"
        detail = content
        suffix = role
        if role == "assistant":
            calls = []
            for call in message.get("tool_calls") or []:
                if isinstance(call.get("function"), dict):
                    function = call["function"]
                    item = {"id": call["id"], "name": function["name"], "ok": None}
                    calls.append(item)
                    calls_by_id[call["id"]] = item
            turn: dict[str, Any] = {"turn": len(turns), "msgIndex": index, "hasText": bool(content),
                                   "hasReasoning": bool(message.get("reasoningContent")), "toolCalls": calls}
            if len(turns) < len(main_cache):
                cached = main_cache[len(turns)]
                turn["cache"] = {key: cached[key] for key in ("prompt", "hit", "miss", "completion", "ratio", "model") if key in cached}
            turns.append(turn)
            heading += f" · turn {turn['turn']}"
            if calls:
                detail += "\n\n## 工具调用\n" + "\n".join(
                    f"- {call['id']} → {call['function']['name']}({call['function'].get('arguments', '')})"
                    for call in message["tool_calls"] if isinstance(call.get("function"), dict)
                )
            if message.get("reasoningContent"):
                detail += "\n\n## 推理输出\n\n" + _display(message["reasoningContent"])
        elif role == "tool":
            call = calls_by_id.get(message.get("tool_call_id"))
            name = call["name"] if call else "unknown"
            failed = looksFailed(content)
            heading += f"_result — {name} ({message.get('tool_call_id', '')})"
            suffix += "-" + re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:60]
            detail = f"ok: {str(not failed).lower()}\n\n{content}"
            if call is not None:
                call.update(ok=not failed, msgIndex=index)
        (message_dir / f"{prefix}-{suffix}.md").write_text(f"{heading}\n\n{detail}\n", encoding="utf-8")

    (output / "turns.jsonl").write_text("".join(json.dumps(turn, ensure_ascii=False) + "\n" for turn in turns), encoding="utf-8")
    failed_turns = sum(any(call["ok"] is False for call in turn["toolCalls"]) for turn in turns)
    index_rows = [
        f"# Trace 索引 · {state.get('id', source.name)}", "",
        f"- 模型 {state.get('model', '?')} · 模式 {state.get('mode', '?')}",
        f"- 消息 {len(messages)} · 回合 {len(turns)} · 含失败工具的回合 {failed_turns}", "",
        "| 回合 | 有文本 | 工具 | Prompt tokens | 缓存命中率 |", "| --- | --- | --- | --- | --- |",
    ]
    for turn in turns:
        cache = turn.get("cache", {})
        ratio = f"{cache['ratio']:.0%}" if isinstance(cache.get("ratio"), (int, float)) else "-"
        tools = ", ".join(call["name"] + ("✗" if call["ok"] is False else "") for call in turn["toolCalls"]) or "-"
        index_rows.append(f"| {turn['turn']} | {turn['hasText']} | {tools} | {cache.get('prompt', '-')} | {ratio} |")
    index_rows += ["", "- messages/ · 逐条消息", "- turns.jsonl · 可分析回合", "- state.json · 会话投影"]
    index_rows.extend(f"- {name}" for name in audits)
    (output / "index.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
    return {"ok": True, "turns": len(turns), "messages": len(messages), "failedTurns": failed_turns,
            "tools": sum(len(turn["toolCalls"]) for turn in turns)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--redact-stdin", action="store_true")
    args = parser.parse_args()
    values = json.load(sys.stdin) if args.redact_stdin else []
    if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
        parser.error("脱敏输入必须是非空字符串列表。")
    pattern = re.compile("|".join(re.escape(value) for value in sorted(values, key=len, reverse=True))) if values else None

    def redact(value: str) -> str:
        return pattern.sub("[REDACTED]", value) if pattern is not None else value

    print(json.dumps(materializeTrace(args.source, args.output, redact), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
