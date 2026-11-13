"""Frozen DAO deck_cli.integration.test.ts through the normal RuoCun executable entry."""

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

import ruocun


def test_deck_managed_cli_question_approval_and_reconnect(tmp_path):
    home, work, discovery = (tmp_path / name for name in ("home", "workspace", "deck"))
    home.mkdir()
    work.mkdir()
    requests = []
    check = "if exist smoke-result.txt (exit /b 0) else (exit /b 1)" if sys.platform == "win32" else "test -f smoke-result.txt"

    def tool(call_id, name, arguments):
        return {"tool_calls": [{"index": 0, "id": call_id, "type": "function", "function": {
            "name": name, "arguments": json.dumps(arguments, ensure_ascii=False),
        }}]}

    class Model(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            results = {row["tool_call_id"]: row["content"] for row in request["messages"] if row["role"] == "tool"}
            if "question" not in results:
                delta = tool("question", "AskUserQuestion", {"question": "选一个方案", "options": ["方案 A", "方案 B"]})
            elif "write" not in results:
                delta = tool("write", "Write", {"path": "smoke-result.txt", "content": "已批准"})
            elif "verify" not in results:
                delta = tool("verify", "Bash", {"command": check})
            else:
                delta = {"content": "流程完成"}
            finish = "tool_calls" if "tool_calls" in delta else "stop"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            frames = [{"choices": [{"delta": {"role": "assistant", **delta}}]},
                      {"choices": [{"delta": {}, "finish_reason": finish}]}]
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode("utf-8"))

    with ThreadingHTTPServer(("127.0.0.1", 0), Model) as server:
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-deck", "key": "synthetic-b08-deck-key",
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
               if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh", RUOCUN_DECK="1", RUOCUN_DECK_MANAGED="1",
                   AGENT_DECK_HOME=str(discovery), RUOCUN_REPO_MAP_TOKENS="0", RUOCUN_REFLECT="0")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = f"import runpy,sys;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
        argv = [sys.executable, "-I", "-B", "-X", "utf8", "-c", loader,
                "--cwd", str(work), "--config", str(config), "--model", "synthetic-deck",
                "--no-memory", "--no-skills", "--no-hooks", "--no-mcp", "--no-web", "--no-project-instructions"]
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        log = tmp_path / "child.log"
        with log.open("w", encoding="utf-8") as output:
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=output, stderr=output, cwd=work, env=env)
            try:
                def wait_for(check):
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        assert child.poll() is None, log.read_text(encoding="utf-8")
                        result = check()
                        if result is not None:
                            return result
                        time.sleep(0.03)
                    raise AssertionError("未收到预期的 Deck 状态\n" + log.read_text(encoding="utf-8"))

                def read_record():
                    file = next((discovery / "agents").glob("*.json"), None)
                    return json.loads(file.read_text(encoding="utf-8")) if file else None

                record = wait_for(read_record)
                url = f"http://127.0.0.1:{record['port']}"
                auth = {"Authorization": "Bearer " + record["token"]}

                def command(client, kind, **fields):
                    data = {"id": str(uuid.uuid4()), "type": kind, "sessionId": record["sessionId"], **fields}
                    response = client.post("/command", json=data, headers=auth)
                    assert response.status_code == 200, response.json()
                    return response.json()

                with httpx.Client(base_url=url, trust_env=False) as client:
                    def snapshot():
                        response = client.get("/snapshot", headers=auth)
                        assert response.status_code == 200
                        return response.json()

                    assert snapshot()["capabilities"]["message"]
                    assert command(client, "message", text="执行测试流程")["status"] == "queued"
                    kinds = set()

                    def finished():
                        current = snapshot()
                        if (prompt := current.get("attention")) is not None and prompt.get("replyable"):
                            kinds.add(prompt["kind"])
                            if prompt["kind"] == "question":
                                assert "方案 A" in prompt["text"]
                                command(client, "answer", promptId=prompt["id"], text="1")
                            else:
                                command(client, "answer", promptId=prompt["id"], decision="allow")
                        if current["state"] == "idle" and any(row["content"] == "流程完成" for row in current["messages"]):
                            return current
                        return None

                    assert wait_for(finished)["sessionId"] == record["sessionId"]
                    assert kinds == {"question", "approval"}
                    assert (work / "smoke-result.txt").read_text(encoding="utf-8") == "已批准"

                # Release every HTTP client connection and create a new client for the same Agent.
                with httpx.Client(base_url=url, trust_env=False) as reconnected:
                    assert command(reconnected, "message", text="面板重连后继续")["status"] == "queued"

                    def resumed():
                        current = reconnected.get("/snapshot", headers=auth).json()
                        if current["state"] == "idle" and any(
                            row["text"] == "面板重连后继续" and row["status"] == "consumed"
                            for row in current["receipts"]
                        ):
                            return current
                        return None

                    assert wait_for(resumed)["instanceId"] == record["instanceId"]
                    assert command(reconnected, "pause")["status"] == "paused"
                    assert reconnected.get("/snapshot", headers=auth).json()["state"] == "paused"
            finally:
                if child.poll() is None:
                    child.terminate()
                    child.wait(timeout=5)
                server.shutdown()
                server_thread.join(timeout=5)

    model_results = [row for request in requests for row in request["messages"] if row["role"] == "tool"]
    assert any(row["tool_call_id"] == "question" and row["content"] == "方案 A" for row in model_results)
    assert any(row["tool_call_id"] == "verify" for row in model_results)
