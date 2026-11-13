"""40 ordinary CLI: Agent launch, durable TaskWait and one background delivery."""

import json
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

import ruocun


@pytest.mark.parametrize(("by_definition", "recover", "fork", "synchronous", "relay"), [
    (False, False, False, False, False), (True, False, False, False, False),
    (False, True, False, False, False), (False, True, True, False, False),
    (False, True, False, True, False), (False, False, False, False, True),
])
def test_background_agent_reads_then_wakes_waiting_main_session(tmp_path, by_definition, recover, fork, synchronous, relay):
    waiting = threading.Event()
    checkpoint_reached = threading.Event()
    release_old_request = threading.Event()
    requests = []
    task_ids = []
    (tmp_path / "task-data.txt").write_text("synthetic child read content", encoding="utf-8")
    agent_args = {"task": "synthetic background prompt", "model": "synthetic-background-agent"}
    if by_definition:
        definitions = tmp_path / ".ruocun" / "agents"
        definitions.mkdir(parents=True)
        (definitions / "background-reader.md").write_text(
            "---\nname: background-reader\nbackground: true\ntools: Read\n---\nsynthetic reader\n", encoding="utf-8")
        agent_args["agent_type"] = "background-reader"
    elif not synchronous:
        agent_args["background"] = True
    if fork:
        del agent_args["model"]
        agent_args["fork"] = True

    def is_child(body):
        if fork:
            return any(message["role"] == "user" and "<fork-boilerplate>" in json.dumps(message["content"])
                       for message in body["messages"])
        return body["model"] == "synthetic-background-agent"

    def tool(index, identity, name, arguments):
        return {"index": index, "id": identity, "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)}}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            messages = body["messages"]
            results = {msg["tool_call_id"]: msg["content"] for msg in messages if msg["role"] == "tool"}
            calls = None
            finish = None
            waiting_request = False
            if is_child(body):
                if "child-read" not in results:
                    if not synchronous:
                        waiting.wait(8)
                        time.sleep(.6)  # Permit the actual foreground wait to settle first.
                    calls = [tool(0, "child-read", "Read", {"path": "task-data.txt"})]
                elif recover and messages[-1] == {"role": "user", "content": "synthetic resume instruction"}:
                    finish = "synthetic child finished from checkpoint"
                elif relay and messages[-1] == {"role": "user", "content": "synthetic TaskSend follow-up"}:
                    finish = "synthetic child finished the follow-up"
                elif recover:
                    checkpoint_reached.set()
                    release_old_request.wait(20)
                    return
                else:
                    finish = "synthetic child finished after reading"
            elif "start" not in results:
                calls = [tool(0, "todo", "TodoWrite", {"todos": [{"content": "synthetic task", "status": "in_progress"}]}),
                         tool(1, "start", "Agent", agent_args)]
            elif "wait" not in results:
                match = re.search(r"\(([A-Za-z0-9_-]{4,})\)", results["start"])
                if match is None:
                    finish = "background launch did not return a task identity"
                else:
                    task_ids.append(match[1])
                    calls = [tool(0, "wait", "TaskWait", {"ids": [match[1]], "mode": "all"})]
                    waiting_request = True
            elif relay and "send" not in results:
                calls = [tool(0, "send", "TaskSend", {"id": task_ids[0], "message": "synthetic TaskSend follow-up"})]
            elif relay and "wait-follow-up" not in results:
                calls = [tool(0, "wait-follow-up", "TaskWait", {"ids": [task_ids[0]], "mode": "all"})]
            else:
                finish = "synthetic foreground completed after wait"
            delta = {"role": "assistant", "tool_calls": calls} if calls else {"role": "assistant", "content": finish}
            frames = [{"choices": [{"delta": delta}]},
                      {"choices": [{"delta": {}, "finish_reason": "tool_calls" if calls else "stop"}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode())
            self.wfile.flush()
            if waiting_request:
                waiting.set()

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"version": 2, "activeProfile": "default", "profiles": {"default": {
        "provider": "deepseek", "model": "synthetic-foreground-agent", "key": "synthetic-background-test-key",
        "baseUrl": f"http://127.0.0.1:{server.server_port}/v1"}}}), encoding="utf-8")
    package = Path(ruocun.__file__).resolve().parent.parent
    loader = f"import sys,runpy;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
    try:
        skills = [] if by_definition else ["--no-skills"]
        command = [sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config),
                   "--cwd", str(tmp_path), "--no-memory", *skills, "--permission-mode", "bypassPermissions"]
        if recover:
            with subprocess.Popen([*command, "synthetic foreground prompt"], cwd=tmp_path,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE) as original:
                try:
                    assert checkpoint_reached.wait(25), "child never reached its committed checkpoint"
                finally:
                    if original.poll() is None:
                        original.kill()
                    original.communicate(timeout=5)
                    release_old_request.set()
            if synchronous:
                opened = [*command, "--continue=latest"]
                report = subprocess.run([*opened, "/recovery"], cwd=tmp_path, capture_output=True,
                                        encoding="utf-8", timeout=40)
                assert report.returncode == 0, report.stdout + report.stderr
                view, _ = json.JSONDecoder().raw_decode(report.stdout[report.stdout.index("{\n"):])
                task_ids.extend(task["taskId"] for task in view["tasks"]
                                if task["kind"] == "agent" and task["status"] == "interrupted")
                assert any(item["scope"] == "main" and item["id"] == "start" for item in view["unresolved"])
                resolved = subprocess.run([*opened, "/recovery resolve main start synthetic checked old Agent"],
                                          cwd=tmp_path, capture_output=True, encoding="utf-8", timeout=40)
                assert resolved.returncode == 0, resolved.stdout + resolved.stderr
            assert len(task_ids) == 1
            resume = f"/recovery continue {task_ids[0]} synthetic resume instruction"
            count = len(requests)
            recovered = subprocess.run([*command, "--continue=latest", resume], cwd=tmp_path,
                                       capture_output=True, encoding="utf-8", timeout=40)
            if fork:
                assert recovered.returncode == 2 and "fork缺少" in recovered.stdout, recovered.stdout + recovered.stderr
                children = [row for row in requests if is_child(row)]
                assert len(requests) == count and len(children) == 2
                assert children[0]["model"] == requests[0]["model"] and children[0]["tools"] == requests[0]["tools"]
                assert children[0]["messages"][0] == requests[0]["messages"][0]
                assert children[0]["messages"][-1]["content"][0]["text"] == "Fork 已启动 - 后台处理中"
                assert any("synthetic child read content" in item["content"] for item in children[-1]["messages"]
                           if item.get("tool_call_id") == "child-read")
                return
            assert recovered.returncode == 0 and "completed" in recovered.stdout, recovered.stdout + recovered.stderr
            children = [row for row in requests if row["model"] == "synthetic-background-agent"]
            assert len(children) == 3 and children[-1]["messages"][:-1] == children[-2]["messages"]
            assert children[-1]["tools"] == children[-2]["tools"]
            assert children[-1]["messages"][-1] == {"role": "user", "content": "synthetic resume instruction"}
            count = len(requests)
            saved_session = re.search(r"会话：([A-Za-z0-9_-]+)", recovered.stdout).group(1)
            repeated = subprocess.run([*command, "--continue", saved_session, resume], cwd=tmp_path,
                                      capture_output=True, encoding="utf-8", timeout=40)
            assert repeated.returncode == 0 and repeated.stdout == recovered.stdout
            assert len(requests) == count
            return
        result = subprocess.run([*command, "synthetic foreground prompt"], cwd=tmp_path,
                                capture_output=True, encoding="utf-8", timeout=40)
    finally:
        waiting.set()
        release_old_request.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)

    assert result.returncode == 0 and "synthetic foreground completed after wait" in result.stdout, result.stdout + result.stderr
    parents = [row for row in requests if row["model"] == "synthetic-foreground-agent"]
    children = [row for row in requests if row["model"] == "synthetic-background-agent"]
    if relay:
        assert len(task_ids) == 1 and len(children) == 3
        resumed = children[-1]["messages"]
        assert resumed[-1] == {"role": "user", "content": "synthetic TaskSend follow-up"}
        assert sum(message.get("tool_call_id") == "child-read" for message in resumed) == 1
        assert any("已恢复" in message["content"] or "resumed" in message["content"]
                   for message in parents[-1]["messages"] if message.get("tool_call_id") == "send")
        return
    assert len(task_ids) == 1 and len(parents) == 3 and len(children) == 2
    if by_definition:
        assert "background-reader" in parents[0]["messages"][0]["content"]
        assert {tool["function"]["name"] for tool in children[0]["tools"]} == {"Read"}
    assert any("synthetic child read content" in msg["content"] for msg in children[-1]["messages"]
               if msg.get("tool_call_id") == "child-read")
    messages = parents[-1]["messages"]
    assert any(json.loads(msg["content"])["status"] == "waiting" for msg in messages if msg.get("tool_call_id") == "wait")
    deliveries = [msg["content"] for msg in messages if msg["role"] == "user" and isinstance(msg["content"], str)
                  and "synthetic child finished after reading" in msg["content"]]
    assert len(deliveries) == 1 and task_ids[0] in deliveries[0]
