"""Normal, resumed and headless session Hook boundaries."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ruocun
from ruocun.agent.runtime_context import isRuntimeContext


def test_ordinary_session_hooks_replace_start_context_and_gate_prompt(tmp_path):
    workspace = tmp_path / "workspace"
    home = tmp_path / "home"
    user_root = home / ".ruocun"
    workspace.mkdir()
    user_root.mkdir(parents=True)
    hooks_file = user_root / "hooks.json"

    def configure_start(label):
        hooks_file.write_text(json.dumps({
            "SessionStart": [{"command": f"echo synthetic-start-{label}"}],
            "UserPromptSubmit": [{"command": "echo synthetic-prompt-context"}],
            "SessionEnd": [{"command": "echo ended>>ends.txt"}],
        }), encoding="utf-8")

    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"role":"assistant","content":"synthetic reply"}}]}\n\n'
                             b'data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-lifecycle", "key": "synthetic-lifecycle-credential",
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = f"import os,runpy,sys;sys.path.insert(0,{str(package)!r})\n"
        loader += (
            "if os.environ.get('RUOCUN_SYNTHETIC_PREVIOUS_MARKER') == '1':\n"
            "    from ruocun.agent import runtime\n"
            "    runtime._SESSION_START_MARKER = '[[dao:session-start-hook]]'\n"
            "runpy.run_module('ruocun',run_name='__main__')"
        )
        command = [sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config),
                   "--cwd", str(workspace), "--no-memory", "--no-skills"]
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
               if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path))

        def run(*args, stdin=None, previous_marker=False):
            run_env = {**env, "RUOCUN_SYNTHETIC_PREVIOUS_MARKER": "1"} if previous_marker else env
            result = subprocess.run([*command, *args], cwd=workspace, env=run_env, input=stdin or "",
                                    capture_output=True, encoding="utf-8", timeout=35)
            assert result.returncode == 0, result.stdout + result.stderr
            return result.stdout

        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            configure_start("first")
            run("synthetic first prompt", previous_marker=True)
            saved_session = next((user_root / "sessions").glob("*/*/session.db")).parent.name
            configure_start("resumed")
            run("--continue", saved_session, "synthetic second prompt")
            rewind = run("--continue", saved_session, stdin="/rewind\n/exit\n")
            assert "1. synthetic first prompt" in rewind and "2. synthetic second prompt" in rewind
            assert "3." not in rewind and "<ruocun-runtime-context>" not in rewind
            command_line = "exit /b 2" if os.name == "nt" else "exit 2"
            hooks_file.write_text(json.dumps({"UserPromptSubmit": [{"command": command_line}]}), encoding="utf-8")
            assert "提交被 Hook 阻止" in run(stdin="synthetic blocked prompt\n/exit\n")
        finally:
            server.shutdown()
            serving.join(timeout=5)

    assert len(requests) == 2
    first, resumed = (request["messages"] for request in requests)
    assert first[1]["content"] == "[[dao:session-start-hook]]\nsynthetic-start-first"
    assert resumed[1]["content"] == "[[ruocun:session-start-hook]]\nsynthetic-start-resumed"
    assert sum("[[ruocun:session-start-hook]]" in message.get("content", "") for message in resumed) == 1
    assert all("[[dao:session-start-hook]]" not in message.get("content", "") for message in resumed)
    assert resumed[-2]["content"] == "synthetic second prompt"
    assert resumed[-1] == {"role": "system", "content": "[hook 注入的上下文]\nsynthetic-prompt-context"}
    assert str(workspace) not in first[0]["content"]
    assert sum(isRuntimeContext(message) for message in first) == sum(isRuntimeContext(message) for message in resumed) == 1
    assert (workspace / "ends.txt").read_text(encoding="utf-8").splitlines() == ["ended", "ended", "ended"]
