"""ADR-0003: real HTTP/SSE side effects survive a lost response without replay."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from support.mcp_http import HttpFixture

import ruocun


@pytest.mark.parametrize("transport,path", [("http", "/mcp"), ("sse", "/sse")])
def test_actual_cli_protocol_error_then_lost_effect_blocks_reopen_new_id_and_redacts_sdk(tmp_path, transport, path):
    source = Path(ruocun.__file__).resolve().parent.parent
    workspace, home = tmp_path / "workspace", tmp_path / "home"
    workspace.mkdir()
    (home / ".ruocun").mkdir(parents=True)
    effect_file, secret = tmp_path / "effect-count", "synthetic-mcp-diagnostic-credential"
    requests = []
    eval_reopen = transport == "http"
    old_instruction = "synthetic-project-instruction-for-ordinary-session"
    if eval_reopen:
        (workspace / "RUOCUN.md").write_text(old_instruction, encoding="utf-8")

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            user = next(row["content"] for row in reversed(body["messages"]) if row["role"] == "user")
            if user == "synthetic eval resume":
                delta, finish = {"content": "synthetic eval finished"}, "stop"
            elif any(row.get("tool_call_id") == "rejected" for row in body["messages"]) and user == "reject":
                delta, finish = {"content": "explicit rejection was confirmed"}, "stop"
            else:
                name, call_id = ("reject", "rejected") if user == "reject" else ("effect", "effect-new-id" if user == "alternate" else "effect-original")
                delta = {"tool_calls": [{"index": 0, "id": call_id, "type": "function", "function": {
                    "name": "mcp__fixture__" + name, "arguments": "{}"}}]}
                if user == "reject":
                    delta["tool_calls"].append({"index": 1, "id": "todo", "type": "function", "function": {
                        "name": "TodoWrite", "arguments": json.dumps({"todos": [{"content": "synthetic MCP", "status": "in_progress"}]})}})
                finish = "tool_calls"
            frames = [{"choices": [{"delta": {"role": "assistant", **delta}}]},
                      {"choices": [{"delta": {}, "finish_reason": finish}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode())

    with HttpFixture(effect_file=effect_file, diagnostic_secret=secret) as peer, ThreadingHTTPServer(("127.0.0.1", 0), Model) as model:
        worker = threading.Thread(target=model.serve_forever, daemon=True)
        worker.start()
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-mcp", "key": "synthetic-model-key",
            "baseUrl": f"http://127.0.0.1:{model.server_port}/v1"}}}), encoding="utf-8")
        (home / ".ruocun/mcp.json").write_text(json.dumps({"mcpServers": {"fixture": {
            "type": transport, "url": peer.url + path + "?access_token=" + secret,
            "headers": {"Authorization": "Bearer " + secret}}}}), encoding="utf-8")
        loader = f"import runpy,sys;sys.path.insert(0,{str(source)!r});runpy.run_module('ruocun',run_name='__main__')"
        command = [sys.executable, "-I", "-B", "-X", "utf8", "-c", loader, "--config", str(config), "--cwd", str(workspace),
                   "--no-memory", "--no-skills", "--permission-mode", "bypassPermissions"]
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT") if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh")

        def run(*args):
            return subprocess.run([*command, *args], cwd=workspace, env=env, stdin=subprocess.DEVNULL,
                                  capture_output=True, encoding="utf-8", timeout=25)

        try:
            rejected = run("reject")
            assert rejected.returncode == 0, rejected.stdout + rejected.stderr
            paired = next(row for row in requests[-1]["messages"] if row.get("tool_call_id") == "rejected")
            assert paired["content"].startswith("Error: MCP synthetic rejected ")
            assert secret not in paired["content"]
            database = next(home.rglob("session.db"))
            session_id = database.parent.name
            if eval_reopen:
                ordinary = requests[-1]
                assert ordinary["messages"][0]["role"] == "system" and old_instruction in ordinary["messages"][0]["content"]
                assert any(tool["function"]["name"].startswith("mcp__fixture__") for tool in ordinary["tools"])
                wire_count, request_count = len(peer.wire), len(requests)
                resumed = run("--eval", "--continue", session_id, "synthetic eval resume")
                assert len(peer.wire) == wire_count
                assert resumed.returncode == 0, resumed.stdout + resumed.stderr
                assert len(requests) == request_count + 1
                assert secret not in resumed.stdout + resumed.stderr
                evaluation = requests[-1]
                assert all(not tool["function"]["name"].startswith("mcp__") for tool in evaluation["tools"])
                assert evaluation["messages"][0]["role"] == "system"
                assert old_instruction not in evaluation["messages"][0]["content"]
                assert evaluation["messages"][1:] == [
                    *ordinary["messages"][1:],
                    {"role": "assistant", "content": "explicit rejection was confirmed"},
                    {"role": "user", "content": "synthetic eval resume"},
                ]
            count = len(requests)
            lost = run("--continue", session_id, "effect")
            assert lost.returncode == 74, lost.stdout + lost.stderr
            assert len(requests) == count + 1 and effect_file.read_text() == "1"
            calls = [row for row in peer.wire if row.get("body", {}).get("method") == "tools/call"]
            assert [row["body"]["params"]["name"] for row in calls] == ["reject", "effect"]
            reopened = run("--continue", session_id, "alternate")
            assert reopened.returncode == 74 and len(requests) == count + 1 and effect_file.read_text() == "1"
            with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as con:
                records = {row[0]: json.loads(row[1]) for row in con.execute("SELECT id,json FROM tools")}
            assert records["rejected"]["state"] == "result_committed"
            assert records["effect-original"]["state"] == "outcome_unknown" and "effect-new-id" not in records
            if eval_reopen:
                wire_count = len(peer.wire)
                eval_blocked = run("--eval", "--continue", session_id, "alternate")
                assert eval_blocked.returncode == 74, eval_blocked.stdout + eval_blocked.stderr
                assert len(peer.wire) == wire_count and len(requests) == count + 1 and effect_file.read_text() == "1"
                assert secret not in eval_blocked.stdout + eval_blocked.stderr
                with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as con:
                    assert {row[0]: json.loads(row[1]) for row in con.execute("SELECT id,json FROM tools")} == records
            assert secret not in rejected.stdout + rejected.stderr + lost.stdout + lost.stderr + reopened.stdout + reopened.stderr
        finally:
            model.shutdown()
            worker.join(3)
            assert not worker.is_alive()
