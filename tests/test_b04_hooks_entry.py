"""48 ordinary CLI wiring for the frozen tool Hook and trust paths."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ruocun


def test_ordinary_cli_loads_only_trusted_hooks_and_executes_rewritten_input(tmp_path):
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    user_root = home / ".ruocun"
    project_root = workspace / ".ruocun"
    user_root.mkdir(parents=True)
    project_root.mkdir(parents=True)

    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    write_json(user_root / "hooks.json", {"PreToolUse": [
        {"matcher": "Write", "command": "echo synthetic-user-hook"},
    ]})
    write_json(project_root / "hooks.json", {"hooks": {"PreToolUse": [
        {"matcher": "Write", "command": 'echo {"updatedInput":{"path":"rewritten.txt","content":"synthetic"}}'},
    ]}})
    seen_results = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            results = [message for message in request["messages"] if message["role"] == "tool"]
            if results:
                seen_results.extend(results)
                delta = {"content": "synthetic hook turn complete"}
                reason = "stop"
            else:
                calls = [
                    ("todo", "TodoWrite", {"todos": [
                        {"content": "Write one synthetic file", "status": "in_progress"},
                    ]}),
                    ("write", "Write", {"path": "original.txt", "content": "unmodified"}),
                ]
                delta = {"tool_calls": [
                    {"index": i, "id": call_id, "type": "function", "function": {
                        "name": name, "arguments": json.dumps(arguments),
                    }}
                    for i, (call_id, name, arguments) in enumerate(calls)
                ]}
                reason = "tool_calls"
            frames = [{"choices": [{"delta": {"role": "assistant", **delta}}]},
                      {"choices": [{"delta": {}, "finish_reason": reason}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode("utf-8"))

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = home / "config.json"
        write_json(config, {"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-hook", "key": "synthetic-hook-credential",
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}})
        package_root = Path(ruocun.__file__).resolve().parent.parent
        loader = f"import runpy,sys;sys.path.insert(0,{str(package_root)!r});runpy.run_module('ruocun',run_name='__main__')"
        command = [sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config),
                   "--cwd", str(workspace), "--no-memory", "--no-skills", "--permission-mode", "bypassPermissions"]
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
               if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path))

        def run(*args, trusted=False):
            result = subprocess.run(
                [*command, *args], cwd=workspace, env={**env, "RUOCUN_TRUST": "1" if trusted else "0"},
                stdin=subprocess.DEVNULL, capture_output=True, encoding="utf-8", timeout=30,
            )
            assert result.returncode == 0, result.stdout + result.stderr
            return result.stdout

        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            untrusted = run("/hooks")
            assert "synthetic-user-hook" in untrusted and "rewritten.txt" not in untrusted
            disabled = run("--no-hooks", "/hooks", trusted=True)
            assert "synthetic-user-hook" not in disabled and "rewritten.txt" not in disabled
            assert "synthetic hook turn complete" in run("synthetic request", trusted=True)
        finally:
            server.shutdown()
            serving.join(timeout=5)

    assert (workspace / "rewritten.txt").read_text(encoding="utf-8") == "synthetic"
    assert not (workspace / "original.txt").exists()
    assert [message["tool_call_id"] for message in seen_results] == ["todo", "write"]
