"""44 normal CLI: notes and goals reach the model, and /batch dispatches real children."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ruocun


def test_goal_notes_and_builtin_batch_through_ordinary_entry(tmp_path):
    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            messages = request["messages"]
            if (request["model"] == "synthetic-parent" and messages[-1]["role"] == "user"
                    and "synthetic batch target" in messages[-1]["content"]):
                tasks = ["synthetic part 1", "synthetic part 2"]
                delta = {"tool_calls": [{"index": 0, "id": "synthetic-batch", "type": "function", "function": {
                    "name": "Agent", "arguments": json.dumps({"tasks": tasks, "model": "synthetic-child"}),
                }}]}
                finish = "tool_calls"
            else:
                delta, finish = {"content": "synthetic done"}, "stop"
            frames = [{"choices": [{"delta": {"role": "assistant", **delta}}]},
                      {"choices": [{"delta": {}, "finish_reason": finish}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode())

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-parent", "key": "synthetic-b04-goal-key",
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
               if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = f"import runpy,sys;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
        command = [sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config), "--cwd", str(workspace),
                   "--no-memory", "--no-skills", "--permission-mode", "bypassPermissions"]
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            result = subprocess.run(command, input="/batch\n/btw synthetic note\n/coordinator\n/status\n/goal synthetic target\n"
                                    "/task\n/status\n/mode bypassPermissions\n/batch synthetic batch target\n/exit\n",
                                    cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=35)
            assert result.returncode == 0, result.stdout + result.stderr
            assert "用法:/batch" in result.stdout
            assert "长任务模式已关闭" in result.stdout
            assert "长任务模式：开启" in result.stdout and "长任务模式：关闭" in result.stdout
        finally:
            server.shutdown()
            serving.join(timeout=5)

    parent = [request["messages"] for request in requests if request["model"] == "synthetic-parent"]
    children = [request["messages"] for request in requests if request["model"] == "synthetic-child"]
    assert len(parent) == 3 and len(children) == 2
    assert parent[0][-1] == {"role": "user", "content": "synthetic target"}
    assert {message["content"] for message in parent[0] if message["role"] == "system" and
            message["content"].startswith("[用户备注]")} == {"[用户备注] synthetic note"}
    assert sum(message.get("content", "").startswith("[长任务自主模式已开启]") for message in parent[0]) == 1
    assert "tasks:[...]" in parent[1][-1]["content"]
    assert not any((message.get("content") or "").startswith("[长任务自主模式已开启]") for message in parent[1])
    assert {row[-1]["content"] for row in children} == {"synthetic part 1", "synthetic part 2"}
    batch_result = next(message["content"] for message in parent[2] if message.get("tool_call_id") == "synthetic-batch")
    assert batch_result.count("synthetic done") == 2
