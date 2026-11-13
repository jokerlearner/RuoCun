"""独立 merger：核实 wheel-only 安装下 --responses-demo 的结构化输出。

不只看产品自报字段：额外做独立端口探测（socket.create_connection），
并对复核者自己生成的 clean-demo 输出与实现者 raw/demo-output.json 做 secret 扫描。
复核者自写，不改产品。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import socket

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{6,}",
    r"Bearer ",
    r"Authorization",
    r"api_key",
    r"SECRET",
    r"PASSWORD",
    r"TOKEN",
]

REASONING = {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext"}
CALL_ARGUMENTS = '{"path":"中文.ts"}'
SECOND_INPUT_TAIL = [
    REASONING,
    {"type": "function_call", "call_id": "call_1", "name": "Read", "arguments": CALL_ARGUMENTS},
    {"type": "function_call_output", "call_id": "call_1", "output": "文件内容"},
]


def scan(text: str) -> dict[str, int]:
    return {p: len(re.findall(p, text)) for p in SECRET_PATTERNS}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean-demo", required=True, help="复核者 run.py raw stdout.bin")
    ap.add_argument("--impl-demo", required=True, help="实现者 raw/demo-output.json")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    clean_text = pathlib.Path(args.clean_demo).read_bytes().decode("utf-8")
    report = json.loads(clean_text)
    impl_text = pathlib.Path(args.impl_demo).read_text(encoding="utf-8")

    port = int(report["port"])
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            independent_listening = True
    except OSError:
        independent_listening = False

    checks: dict[str, dict[str, object]] = {}

    def ck(name: str, cond: object, detail: object = "") -> None:
        checks[name] = {"pass": bool(cond), "detail": detail}

    ck("status_complete", report.get("status") == "complete", report.get("status"))
    ck("route_responses", report.get("route") == "responses", report.get("route"))
    ck("answer", report.get("answer") == "完成", report.get("answer"))
    ck("wire_request_validated", report.get("wire_request_validated") is True)
    ck("server_closed_selfreported", report.get("server_closed") is True)
    ck("server_socket_fileno_selfreported", report.get("server_socket_fileno") == -1,
       report.get("server_socket_fileno"))
    ck("port_not_listening_selfreported", report.get("port_not_listening") is True)
    ck("port_NOT_LISTENING_independent_probe", independent_listening is False,
       {"port": port, "independent_listening": independent_listening})
    ck("request_golden_len_2", len(report.get("request_golden", [])) == 2)
    ck("responses_events_golden_len_2", len(report.get("responses_events_golden", [])) == 2)
    ck("event_golden_len_2", len(report.get("event_golden", [])) == 2)
    ck("server_captured_paths_are_responses",
       [c.get("path") for c in report.get("server_captured", [])] == ["/responses", "/responses"],
       [c.get("path") for c in report.get("server_captured", [])])

    first = report["request_golden"][0]
    ck("first_store_include",
       first.get("store") is False and first.get("include") == ["reasoning.encrypted_content"])
    ck("first_max_output_tokens_dotenv_50000", first.get("max_output_tokens") == 50000,
       first.get("max_output_tokens"))
    ck("first_effort_low", first.get("reasoning") == {"effort": "low"}, first.get("reasoning"))
    ck("first_has_no_chat_only_fields",
       "messages" not in first and "max_tokens" not in first and "max_completion_tokens" not in first)
    ck("first_input_image",
       first["input"][1]["content"][1]
       == {"type": "input_image", "image_url": "data:image/png;base64,test"})
    ck("second_input_slice2_frozen",
       report["request_golden"][1]["input"][2:] == SECOND_INPUT_TAIL,
       json.dumps(report["request_golden"][1]["input"][2:], ensure_ascii=False))

    ev0 = report["event_golden"][0]
    ck("first_finish_reason_tool_calls", ev0.get("finish_reason") == "tool_calls")
    ck("first_usage_cache_hit80_miss20",
       ev0["usage"].get("prompt_cache_hit_tokens") == 80
       and ev0["usage"].get("prompt_cache_miss_tokens") == 20)
    ck("first_tool_call_and_responseItems_present",
       len(ev0["message"].get("tool_calls", [])) == 1
       and len(ev0["message"].get("responseItems", [])) == 1)
    ev1 = report["event_golden"][1]
    ck("second_answer", ev1["message"].get("content") == "完成")
    ck("second_single_content_delta",
       [d["text"] for d in ev1["deltas"] if d["kind"] == "content"] == ["完成"])
    ck("local_endpoint_is_loopback_responses",
       str(report.get("local_endpoint", "")).startswith("http://127.0.0.1:")
       and str(report.get("local_endpoint", "")).endswith("/responses"),
       report.get("local_endpoint"))
    ck("configured_base_url_official_not_public_network",
       report.get("configured_base_url") == "https://api.openai.com/v1")
    ck("route_criteria_uses_responses_true",
       report.get("route_criteria", {}).get("uses_responses") is True)

    clean_hits = scan(clean_text)
    impl_hits = scan(impl_text)
    ck("secret_scan_clean_demo_zero", all(v == 0 for v in clean_hits.values()), clean_hits)
    ck("secret_scan_implementer_demo_zero", all(v == 0 for v in impl_hits.values()), impl_hits)

    summary = {
        "total": len(checks),
        "passed": sum(1 for c in checks.values() if c["pass"]),
        "failed": [k for k, c in checks.items() if not c["pass"]],
    }
    out = {
        "role": "independent merger (task 05)",
        "clean_demo_stdout_bytes": len(clean_text.encode("utf-8")),
        "implementer_demo_bytes": len(impl_text.encode("utf-8")),
        "independent_port_probe": {"port": port, "listening": independent_listening},
        "checks": checks,
        "summary": summary,
    }
    pathlib.Path(args.output).write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
