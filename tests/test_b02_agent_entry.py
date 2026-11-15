"""Synchronous Agent on the ordinary command with a synthetic loopback provider."""

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from test_b02_worktree import repo as repo

import ruocun
from ruocun.agent.runtime_context import isRuntimeContext


@pytest.mark.parametrize("case", ["builtin", "custom", "worktree", "worktree-unavailable"])
def test_agent_in_normal_cli_dispatches_isolated_child_session(tmp_path, case, request):
    requests = []
    custom = case == "custom"
    unavailable = case == "worktree-unavailable"
    agent_args = {"task": "synthetic child prompt"}
    if custom:
        definitions = tmp_path / ".ruocun" / "agents"
        definitions.mkdir(parents=True)
        (definitions / "entry-reader.md").write_text(
            "---\nname: entry-reader\ndescription: synthetic discovery marker\n"
            "model: synthetic-child-model\ntools: Read\n---\nsynthetic custom prompt\n", encoding="utf-8")
        agent_args["agent_type"] = "entry-reader"
    else:
        agent_args["model"] = "synthetic-child-model"
    if case.startswith("worktree"):
        tmp_path, git = request.getfixturevalue("repo")
        agent_args["isolation"] = "remote"
        if unavailable:
            git("symbolic-ref", "HEAD", "refs/heads/synthetic-unborn")

    def tool(index, name, arguments):
        return {"index": index, "id": f"parent-{index}", "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)}}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            if len(requests) == 1:
                calls = [tool(0, "TodoWrite", {"todos": [{"content": "synthetic task", "status": "in_progress"}]}),
                         tool(1, "Agent", agent_args)]
                delta, reason = {"role": "assistant", "tool_calls": calls}, "tool_calls"
            elif body["model"] == "synthetic-child-model":
                delta, reason = {"role": "assistant", "content": "synthetic child result"}, "stop"
            else:
                delta, reason = {"role": "assistant", "content": "synthetic parent complete"}, "stop"
            frames = [{"choices": [{"delta": delta}]}, {"choices": [{"delta": {}, "finish_reason": reason}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"version": 2, "activeProfile": "default", "profiles": {"default": {
        "provider": "deepseek", "model": "synthetic-parent-model", "key": "synthetic-agent-entry-key",
        "baseUrl": f"http://127.0.0.1:{server.server_port}/v1"}}}), encoding="utf-8")
    package = Path(ruocun.__file__).resolve().parent.parent
    loader = f"import sys,runpy;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
    try:
        skills = [] if custom else ["--no-skills"]
        result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config),
                                 "--cwd", str(tmp_path), "--no-memory", *skills, "--permission-mode", "default",
                                 "synthetic parent prompt"],
                                cwd=tmp_path, capture_output=True, encoding="utf-8", timeout=30)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)

    assert result.returncode == 0 and "synthetic parent complete" in result.stdout, result.stdout + result.stderr
    if unavailable:
        assert [body["model"] for body in requests] == ["synthetic-parent-model"] * 2
        assert any("隔离工作树未创建，子代理未派发" in item["content"] for item in requests[-1]["messages"]
                   if item.get("tool_call_id") == "parent-1")
        return
    assert [body["model"] for body in requests] == ["synthetic-parent-model", "synthetic-child-model", "synthetic-parent-model"]
    assert "Agent" in {tool["function"]["name"] for tool in requests[0]["tools"]}
    assert "Agent" not in {tool["function"]["name"] for tool in requests[1]["tools"]}
    child_messages = [message for message in requests[1]["messages"] if not isRuntimeContext(message)]
    assert isRuntimeContext(requests[1]["messages"][-1])
    assert len(child_messages) == 2 and child_messages[1] == {"role": "user", "content": "synthetic child prompt"}
    if custom:
        assert "entry-reader" in requests[0]["messages"][0]["content"]
        assert "synthetic discovery marker" in requests[0]["messages"][0]["content"]
        assert "synthetic custom prompt" in child_messages[0]["content"]
        assert {tool["function"]["name"] for tool in requests[1]["tools"]} == {"Read"}
    parent_messages = requests[-1]["messages"]
    results = [item["content"] for item in parent_messages if item.get("tool_call_id") == "parent-1"]
    if case == "worktree":
        snapshot = requests[1]["messages"][-1]["content"]
        assert ".ruocun" in snapshot and "worktrees" in snapshot
        assert git("worktree", "list", "--porcelain").count(b"worktree ") == 1
        assert results == ["synthetic child result\n[remote 在同机 Git 工作树执行。]"]
    else:
        assert results == ["synthetic child result"]
    assert not any(item["role"] == "user" and item["content"] == "synthetic child prompt" for item in parent_messages)
