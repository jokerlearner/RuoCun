"""The frozen 01 parse-query evaluator runs through real RuoCun with a local model fixture."""

import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import ruocun


@pytest.mark.oracle
def test_frozen_eval_runner_executes_scores_and_materializes(tmp_path):
    node = os.environ.get("RUOCUN_ORACLE_NODE") or shutil.which("node")
    if node is None:
        pytest.skip("显式提供 Node 才运行冻结的 JavaScript 验证器")
    repo = Path(__file__).resolve().parents[1]
    fixture = repo / "evals" / "tasks" / "01-parse-query" / "workspace" / "qs.mjs"
    patch = fixture.read_text(encoding="utf-8").replace(
        "    out[k] = v;",
        "    if (!Object.hasOwn(out, k)) out[k] = v;\n"
        "    else if (Array.isArray(out[k])) out[k].push(v);\n"
        "    else out[k] = [out[k], v];",
    )
    key = "synthetic-eval-credential"
    calls_seen = []

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            rows = payload["messages"]
            calls_seen.append(rows)
            observed = {row["tool_call_id"] for row in rows if row["role"] == "tool"}
            if not observed:
                calls = (
                    ("todo", "TodoWrite", {"todos": [{"content": "修复查询串解析", "status": "in_progress"}]}),
                    ("read", "Read", {"path": "qs.mjs"}),
                )
            elif "write" not in observed:
                calls = (("write", "Write", {"path": "qs.mjs", "content": patch}),)
            else:
                calls = ()
            if calls:
                delta = {"tool_calls": [
                    {"index": index, "id": call_id, "type": "function",
                     "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}
                    for index, (call_id, name, args) in enumerate(calls)
                ]}
                finish = "tool_calls"
            else:
                # The synthetic credential and HTML metacharacters must be safe in all emitted traces.
                delta, finish = {"content": f"合成修复完成 {key} </script><script>unsafe</script>"}, "stop"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            frames = [{"choices": [{"delta": delta}]}, {"choices": [{"delta": {}, "finish_reason": finish}]}]
            self.wfile.write(("".join(f"data: {json.dumps(frame)}\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode("utf-8"))

    config, output = tmp_path / "config.json", tmp_path / "output"
    home = tmp_path / "outer-home"
    home.mkdir()
    env = {name: os.environ[name] for name in ("SYSTEMROOT", "WINDIR", "PATH", "COMSPEC", "PATHEXT")
           if name in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
               TMP=str(home), TEMP=str(home), PYTHONUTF8="1")
    package = Path(ruocun.__file__).resolve().parent.parent
    launch = (f"import runpy,sys;sys.path[:0]=[{str(repo)!r},{str(package)!r}];"
              "runpy.run_module('evals.run',run_name='__main__')")
    with ThreadingHTTPServer(("127.0.0.1", 0), Model) as server:
        config.write_text(json.dumps({"version": 2, "activeProfile": "fixture", "profiles": {"fixture": {
            "provider": "deepseek", "model": "synthetic-eval", "key": key,
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            command = [sys.executable, "-I", "-B", "-X", "utf8", "-c", launch]
            listed = subprocess.run([*command, "--list"], cwd=repo, env=env, text=True,
                                    encoding="utf-8", capture_output=True, timeout=12, check=True)
            assert len(listed.stdout.splitlines()) == 16
            run = subprocess.run([*command, "--config", str(config), "--output", str(output),
                                  "--node", str(node), "--runs", "1", "--timeout-ms", "30000",
                                  "01-parse-query", "t1-valibot-mastercard"],
                                 cwd=repo, env=env, text=True, encoding="utf-8", capture_output=True, timeout=55)
            assert run.returncode == 1, run.stdout + run.stderr  # OSS remained unavailable; the local task still ran.

            mixed = tmp_path / "mixed.json"
            mixed.write_text(json.dumps({
                "apiKey": "synthetic-legacy-key", "baseUrl": "https://outside.invalid/v1",
                "activeProfile": "fixture", "profiles": json.loads(config.read_text(encoding="utf-8"))["profiles"],
            }), encoding="utf-8")
            refused = tmp_path / "refused"
            declined = subprocess.run([*command, "--config", str(mixed), "--output", str(refused),
                                       "--node", str(node), "--runs", "1", "--timeout-ms", "8000", "01-parse-query"],
                                      cwd=repo, env=env, text=True, encoding="utf-8", capture_output=True, timeout=20)
            assert declined.returncode == 1
            refused_meta = json.loads((refused / "01-parse-query/run-1/meta.json").read_text(encoding="utf-8"))
            assert refused_meta["status"] == "environment_unavailable" and "agentExit" not in refused_meta

            referenced = json.loads(config.read_text(encoding="utf-8"))
            selected = referenced["profiles"]["fixture"]
            selected.pop("key")
            selected["keyRef"] = "keychain:ruocun/synthetic-eval-only"
            mixed.write_text(json.dumps(referenced), encoding="utf-8")
            no_key = tmp_path / "no-key"
            blocked = subprocess.run([*command, "--config", str(mixed), "--output", str(no_key),
                                      "--node", str(node), "--runs", "1", "--timeout-ms", "8000", "01-parse-query"],
                                     cwd=repo, env=env, text=True, encoding="utf-8", capture_output=True, timeout=20)
            assert blocked.returncode == 1
            blocked_meta = json.loads((no_key / "01-parse-query/run-1/meta.json").read_text(encoding="utf-8"))
            assert blocked_meta["status"] == "environment_unavailable" and "agentExit" not in blocked_meta
        finally:
            server.shutdown()
            worker.join(timeout=5)

    attempt = output / "01-parse-query" / "run-1"
    report = json.loads((attempt / "meta.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed" and report["pass"], (report, (attempt / "agent.log").read_text(encoding="utf-8"))
    assert report["baselineFail2passExit"] == 1
    assert report["completion"] == 1 and report["traceStatus"] == "materialized", report
    assert "fail2pass OK" in (attempt / "fail2pass.log").read_text(encoding="utf-8")
    assert "pass2pass OK" in (attempt / "pass2pass.log").read_text(encoding="utf-8")
    assert "Object.hasOwn" in (attempt / "agent.diff").read_text(encoding="utf-8")
    trace = attempt / "trace"
    html = (trace / "trace.html").read_text(encoding="utf-8")
    assert "\\u003c/script>" in html and "__TRACE_DATA__" not in html
    assert any((trace / "messages").glob("*-tool-Write.md"))
    for file in attempt.rglob("*"):
        if file.is_file():
            assert key not in file.read_text(encoding="utf-8")
    unavailable = json.loads((output / "t1-valibot-mastercard" / "run-1" / "meta.json").read_text(encoding="utf-8"))
    assert unavailable["status"] == "environment_unavailable" and not unavailable["pass"]
    assert len(calls_seen) == 3 and not list(home.glob("rc-*"))
