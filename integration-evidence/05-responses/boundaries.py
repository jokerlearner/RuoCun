"""独立 merger 复核：任务 05 失败 / 取消 / 资源退出边界。

复核者自写，不修改产品代码、不放宽测试。分三部分：
  A. 协议与流失败：注入 transport 直接调用 client.streamChat，独立构造
     错误事件、无完成事件断流、中途断流/取消、坏参数等，核实明确失败或
     标 partial、不伪报成功。
  B. CLI 坏配置 / 非法参数：真实 ``-m ruocun --responses-demo`` 子进程，
     合成配置，核实退出码、具体诊断、无 secret 泄漏、无伪成功。
  C. 资源退出独立证实：复核者自己持有本地 loopback HTTP/SSE 服务对象，
     在成功与失败路径下真实 HTTP POST，finally 中 shutdown()/server_close()/
     thread.join()，再独立用 socket.create_connection 探测端口、检查
     server.socket.fileno()、thread.is_alive()、threading.enumerate()。
     另对产品 run_responses_demo 的报告 port 做独立端口探测。

用法（经 tools/run.py 白名单启动）：
  python -I -X utf8 boundaries.py --output integration-evidence/05-responses/raw/boundaries.json
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SYNTHETIC_KEY = "sk-synthetic-NOT-A-REAL-KEY"
SECRET_RE = re.compile(r"sk-[A-Za-z0-9_-]{6,}|Bearer |Authorization|api_key|SECRET|PASSWORD|TOKEN")

OPTS: dict[str, Any] = {
    "baseUrl": "https://api.openai.com/v1", "apiKey": SYNTHETIC_KEY,
    "model": "gpt-6.1-sol", "messages": [{"role": "user", "content": "你好"}],
}

USAGE = {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
         "input_tokens_details": {"cached_tokens": 80}}
ANSWER = {"type": "message", "content": [{"type": "output_text", "text": "完成"}]}


def responses_sse(events: list[Any]) -> list[bytes]:
    parts: list[str] = []
    for event in events:
        if isinstance(event, str):
            parts.append("data: " + event + "\r\n\r\n")
        elif isinstance(event, bytes):
            parts.append(event.decode("latin-1"))
        else:
            parts.append("event: " + str(event["type"]) + "\r\ndata: "
                         + json.dumps(event, ensure_ascii=False) + "\r\n\r\n")
    raw = "".join(parts).encode("utf-8")
    return [raw[i:i + 17] for i in range(0, len(raw), 17)]


def completed(output: list[dict[str, Any]]) -> list[Any]:
    return [{"type": "response.completed", "response": {"output": output, "usage": USAGE}}]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    from ruocun.client import client, responses

    results: dict[str, Any] = {"role": "independent merger (task 05)"}

    # ===================== A. 协议 / 流失败（注入 transport） =====================
    stream_cases: dict[str, Any] = {}

    def stream_case(name: str, chunks: Any) -> None:
        def transport(url: str, headers: dict[str, str], body: bytes):
            return client.HttpResponse(200, {}, iter(chunks))
        entry: dict[str, Any] = {}
        try:
            r = client.streamChat(OPTS, transport=transport)
            entry["outcome"] = "returned"
            entry["status"] = r.status
            entry["answer"] = r.message.get("content")
            entry["finish_reason"] = r.finish_reason
            entry["error"] = None
            entry["fake_success"] = (
                r.status == "complete" and not r.message.get("content")
            )
        except Exception as exc:  # 明确失败
            entry["outcome"] = "error"
            entry["status"] = None
            entry["answer"] = None
            entry["error_type"] = type(exc).__name__
            entry["error"] = str(exc)
            entry["fake_success"] = False
        stream_cases[name] = entry

    stream_case("protocol_failed_event", responses_sse([
        {"type": "response.failed", "response": {"error": {"message": "bad request"}}},
    ]))
    stream_case("protocol_error_event", responses_sse([
        {"type": "error", "error": {"message": "boom"}},
    ]))
    stream_case("no_completed_event_clean_eof", responses_sse([
        {"type": "response.output_text.delta", "delta": "部分"},
    ]))
    stream_case("empty_stream", responses_sse([]))
    stream_case("arguments_delta_without_call", responses_sse([
        {"type": "response.function_call_arguments.delta", "output_index": 1, "delta": "{}"},
    ]))
    stream_case("output_item_done_then_eof", responses_sse([
        {"type": "response.output_item.done", "output_index": 0, "item": ANSWER},
    ]))
    stream_case("malformed_json_event", responses_sse([
        b"data: {not-json}\r\n\r\n",
    ]))
    stream_case("incomplete_terminal", responses_sse([
        {"type": "response.incomplete", "response": {"output": [ANSWER], "usage": USAGE}},
    ]))

    def non_2xx(url: str, headers: dict[str, str], body: bytes):
        return client.HttpResponse(401, {}, iter([]))
    try:
        client.streamChat(OPTS, transport=non_2xx)
        stream_cases["non_2xx_401"] = {"outcome": "returned", "fake_success": True}
    except Exception as exc:
        stream_cases["non_2xx_401"] = {
            "outcome": "error", "error_type": type(exc).__name__,
            "error": str(exc), "fake_success": False,
        }

    # 中途断流 / 取消：chunks 生成器抛 StreamDisconnected
    def disconnecting(before: list[Any]):
        def gen():
            for c in responses_sse(before):
                yield c
            raise client.StreamDisconnected("user cancelled mid-stream")
        return gen()

    stream_case("cancel_before_any_output", disconnecting([]))
    stream_case("cancel_after_partial_output", disconnecting([
        {"type": "response.output_text.delta", "delta": "部分"},
    ]))
    results["stream_cases"] = stream_cases

    # ===================== B. CLI 坏配置 / 非法参数 =====================
    tmp_root = pathlib.Path(tempfile.mkdtemp(prefix="m05r2-boundaries-"))
    home = tmp_root / "home"
    home.mkdir(exist_ok=True)
    base_env = {
        "SYSTEMROOT": "C:\\Windows", "WINDIR": "C:\\Windows",
        "PATH": str(pathlib.Path(sys.executable).parent),
        "HOME": str(home), "USERPROFILE": str(home),
        "APPDATA": str(home / "appdata"), "LOCALAPPDATA": str(home / "localappdata"),
        "TEMP": str(home), "TMP": str(home),
        "PYTHONUTF8": "1", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PIP_CONFIG_FILE": os.devnull,
    }

    def make_cfg(name: str, *, key: bool = True, bad_json: bool = False,
                 model: str = "gpt-6.1-sol") -> pathlib.Path:
        cfg = tmp_root / name
        cfg.mkdir(exist_ok=True)
        profile: dict[str, Any] = {
            "provider": "openai", "baseUrl": "https://api.openai.com/v1", "model": model,
        }
        if key:
            profile["key"] = SYNTHETIC_KEY
        payload = {"version": 2, "activeProfile": "synthetic",
                   "profiles": {"synthetic": profile}, "theme": "dark"}
        (cfg / "config.json").write_text(
            "{ broken" if bad_json else json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        (cfg / ".env").write_text(
            "RUOCUN_MAX_OUTPUT_TOKENS=50000\nRUOCUN_REASONING_EFFORT=none\n",
            encoding="utf-8")
        return cfg

    good_cfg = make_cfg("cfg-good")

    def cli_case(name: str, argv: list[str], extra_env: dict[str, str] | None = None) -> None:
        env = dict(base_env)
        if extra_env:
            env.update(extra_env)
        proc = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", "-m", "ruocun", *argv],
            cwd=tmp_root, env=env, capture_output=True, text=True,
            encoding="utf-8", timeout=30,
        )
        stderr = proc.stderr or ""
        stream_case_entry = {
            "argv_tail": argv,
            "exit": proc.returncode,
            "stderr": stderr.strip(),
            "stdout_tail": (proc.stdout or "")[-200:],
            "secret_leak": bool(SECRET_RE.search(stderr + (proc.stdout or ""))),
            "fake_success": proc.returncode == 0,
            "diag_hit": any(k in stderr for k in ("失败", "缺少", "判据", "需要")),
        }
        cli_cases[name] = stream_case_entry

    cli_cases: dict[str, Any] = {}
    cli_case("missing_config_dir",
             ["--responses-demo", str(tmp_root / "absent"), "你好"])
    cli_case("bad_json_config",
             ["--responses-demo", str(make_cfg("cfg-bad", bad_json=True)), "你好"])
    cli_case("missing_key_generic_env_ignored",
             ["--responses-demo", str(make_cfg("cfg-nokey", key=False)), "你好"],
             extra_env={"OPENAI_API_KEY": "sk-env-NOT-REAL-M05R2"})
    cli_case("route_not_matched_gpt5",
             ["--responses-demo", str(good_cfg), "--model", "gpt-5", "你好"])
    cli_case("no_config_dir_argument", ["--responses-demo"])
    compat_bad = make_cfg("cfg-compat-bad")
    (compat_bad / "compatibility.json").write_text("{ broken", encoding="utf-8")
    cli_case("bad_compatibility_json",
             ["--responses-demo", str(compat_bad), "你好"])
    results["cli_cases"] = cli_cases

    # ===================== C. 资源退出独立证实 =====================
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length) if length else None
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            payload: bytes = self.server.payload  # type: ignore[attr-defined]
            for i in range(0, len(payload), 17):
                self.wfile.write(payload[i:i + 17])
                self.wfile.flush()

        def log_message(self, format: str, *a: Any) -> None:
            return

    class _Server(ThreadingHTTPServer):
        daemon_threads = True

        def __init__(self, payload: bytes) -> None:
            super().__init__(("127.0.0.1", 0), _Handler)
            self.payload = payload

    def port_listening(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            return False

    def resource_case(name: str, payload: bytes) -> dict[str, Any]:
        server = _Server(payload)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = int(server.server_address[1])
        before = port_listening(port)

        def http_transport(url: str, headers: dict[str, str], body: bytes):
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/responses", data=body,
                headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                status = int(resp.status)
            return client.HttpResponse(
                status, {}, [raw[i:i + 17] for i in range(0, len(raw), 17)])

        error: str | None = None
        answer: str | None = None
        try:
            r = client.streamChat(OPTS, transport=http_transport)
            answer = r.message.get("content")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        after = port_listening(port)
        try:
            fileno = server.socket.fileno()
        except OSError:
            fileno = -1
        alive = thread.is_alive()
        still = any(t is thread for t in threading.enumerate())
        return {
            "port": port,
            "listening_before": before,
            "listening_after": after,
            "server_socket_fileno_after_close": fileno,
            "thread_alive_after_join": alive,
            "owned_thread_still_enumerated": still,
            "error": error,
            "answer": answer,
            "shutdown_server_close_join_performed": True,
        }

    ok_sse = "".join(
        "event: " + e["type"] + "\r\ndata: " + json.dumps(e, ensure_ascii=False) + "\r\n\r\n"
        for e in completed([ANSWER])
    ).encode("utf-8")
    resources: dict[str, Any] = {
        "success_real_http": resource_case("success", ok_sse),
        "failure_invalid_utf8": resource_case(
            "failure", b"data: \xff\xfe bad\r\n\r\n"),
    }

    # 产品 run_responses_demo 成功报告 + 独立端口探测
    from ruocun.responses_demo import run_responses_demo
    report = run_responses_demo(good_cfg, "看图并读文件")
    prod_port = int(report["port"])
    resources["product_demo_success"] = {
        "port": prod_port,
        "selfreported_server_closed": report["server_closed"],
        "selfreported_socket_fileno": report["server_socket_fileno"],
        "selfreported_port_not_listening": report["port_not_listening"],
        "independent_port_listening": port_listening(prod_port),
        "wire_request_validated": report["wire_request_validated"],
        "answer": report["answer"],
    }
    results["resources"] = resources
    results["thread_summary"] = {"alive_threads": [t.name for t in threading.enumerate()]}

    # 汇总：边界检查通过一个独立判定（不依赖产品自报字段）
    failures: list[str] = []
    for name, e in stream_cases.items():
        if e.get("fake_success"):
            failures.append("stream:" + name + " fake success")
        if name.startswith(("protocol_", "no_completed", "empty_stream", "arguments_delta",
                            "output_item_done", "malformed_json", "non_2xx", "cancel_before")) \
                and e["outcome"] != "error":
            failures.append("stream:" + name + " expected explicit error")
    if stream_cases["cancel_after_partial_output"]["status"] != "partial":
        failures.append("stream:cancel_after_partial_output expected partial")
    for name, e in cli_cases.items():
        if e["fake_success"] or e["exit"] == 0:
            failures.append("cli:" + name + " unexpected success")
        if e["secret_leak"]:
            failures.append("cli:" + name + " secret leak")
    for name, e in resources.items():
        if name == "product_demo_success":
            if e["independent_port_listening"]:
                failures.append("resources:product_demo port still listening")
            continue
        if not e["listening_before"] or e["listening_after"]:
            failures.append("resources:" + name + " port lifecycle")
        if e["server_socket_fileno_after_close"] != -1:
            failures.append("resources:" + name + " socket_fileno != -1")
        if e["thread_alive_after_join"] or e["owned_thread_still_enumerated"]:
            failures.append("resources:" + name + " thread leak")
    results["summary"] = {"failures": failures, "passed": not failures}
    pathlib.Path(args.output).write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results["summary"], ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
