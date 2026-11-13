"""Ordinary child runs use their own durable compaction and archive scope."""

import json
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from support.ruocun_acceptance.environment import isolated_env

import ruocun

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="controlled Windows SQLite entry")


def run_child_entry(tmp_path, respond, *, stdin=None, files=None, settings=None, reopen=None):
    requests = []
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for name, text in (files or {}).items():
        (workspace / name).write_text(text, encoding="utf-8")
    environment = isolated_env(tmp_path / "e", Path(sys.executable))
    environment.update(RUOCUN_CONTEXT_WINDOW="64000", RUOCUN_LANG="zh", RUOCUN_NO_CLEANUP="1")
    environment.update(settings or {})

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body)
            delta, reason = respond(body, requests)
            frames = [{"choices": [{"delta": {"role": "assistant", **delta}}]},
                      {"choices": [{"delta": {}, "finish_reason": reason}],
                       "usage": {"prompt_tokens": 100, "completion_tokens": 10}}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode("utf-8"))

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = Path(environment["HOME"]) / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {
            "synthetic": {"provider": "deepseek", "model": "synthetic-parent-model",
                          "key": "synthetic-child-entry-key",
                          "baseUrl": f"http://127.0.0.1:{server.server_port}/v1"},
        }}), encoding="utf-8")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = (f"import runpy,sys;sys.path.insert(0,{str(package)!r});"
                  "runpy.run_module('ruocun',run_name='__main__')")
        command = [sys.executable, "-I", "-B", "-X", "utf8", "-c", loader,
                   "--config", str(config), "--cwd", str(workspace), "--no-memory", "--no-skills",
                   "--no-hooks", "--no-mcp", "--no-progress-advice"]
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            result = subprocess.run(
                command if stdin is not None else [*command, "synthetic parent input"],
                input=stdin or "", env=environment, cwd=workspace,
                capture_output=True, encoding="utf-8", timeout=60,
            )
            if reopen is not None:
                saved_session = re.search(r"会话：([a-f0-9-]+)", result.stdout)
                assert saved_session is not None, result.stdout + result.stderr
                resumed = subprocess.run([*command, "--continue", saved_session[1], reopen], input="",
                    env=environment, cwd=workspace, capture_output=True, encoding="utf-8", timeout=60)
                (tmp_path / "reopened-stdout.txt").write_text(resumed.stdout, encoding="utf-8")
                (tmp_path / "reopened-stderr.txt").write_text(resumed.stderr, encoding="utf-8")
                assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        finally:
            server.shutdown()
            serving.join(timeout=5)
    (tmp_path / "requests.json").write_text(json.dumps(requests, ensure_ascii=False, indent=2), encoding="utf-8")
    (tmp_path / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (tmp_path / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    return requests, result


def parent_dispatch(background=False, fork=False):
    agent = {"task": "synthetic child task", "background": background}
    agent.update({"fork": True} if fork else {"model": "synthetic-child-model"})
    return {"tool_calls": [
        {"index": 0, "id": "todo", "type": "function", "function": {
            "name": "TodoWrite", "arguments": json.dumps({"todos": [{
                "content": "synthetic delegated work", "status": "in_progress",
            }]})}},
        {"index": 1, "id": "agent", "type": "function", "function": {
            "name": "Agent", "arguments": json.dumps(agent)}},
    ]}, "tool_calls"


def test_ordinary_child_applies_the_actual_window_sized_default_output_limit(tmp_path):
    def respond(body, requests):
        if len(requests) == 1:
            return parent_dispatch()
        return {"content": "CHILD-DONE" if body["model"] == "synthetic-child-model" else "MAIN-DONE"}, "stop"

    requests, result = run_child_entry(tmp_path, respond)
    child, = [body for body in requests if body["model"] == "synthetic-child-model"]
    assert child.get("max_tokens", child.get("max_completion_tokens")) == 16000
    assert "MAIN-DONE" in result.stdout


@pytest.mark.parametrize("background", [False, True])
def test_fork_can_read_only_the_archive_closure_of_its_inherited_visible_prefix(tmp_path, background):
    original = []
    first_steps = []

    def respond(body, requests):
        if body["model"] == "synthetic-summary-model":
            return {"content": "<摘要>此前已完成两次读取，旧细节按归档查询。</摘要>"}, "stop"
        messages = body["messages"]
        if any("<fork-boilerplate>" in str(item.get("content")) for item in messages):
            pages = [json.loads(item["content"]) for item in messages
                     if str(item.get("tool_call_id", "")).startswith("fork-original")]
            if pages:
                # B 契约将完整 system 纳入摘要来源；旧细节可能位于首个 4096 字符页之后。
                text = "".join(page["text"] for page in pages)
                page = pages[-1]
                if "INHERITED-FIRST-DETAIL" in text or page["next_offset"] is None:
                    original.append(text)
                    return {"content": "FORK-DONE"}, "stop"
                return {"tool_calls": [{"index": 0, "id": f"fork-original-{page['next_offset']}",
                    "type": "function", "function": {
                        "name": "ArchiveRead", "arguments": json.dumps({
                            "id": page["id"], "offset": page["next_offset"], "limit": 4096,
                        }),
                    }}]}, "tool_calls"
            summary = next((item["content"] for item in messages
                            if item["role"] == "system" and "原文归档:" in str(item.get("content"))), "")
            match = re.search(r"原文归档:([A-Za-z0-9:_-]+)", summary)
            if match is None:
                return {"content": "NO-INHERITED-SUMMARY"}, "stop"
            return {"tool_calls": [{"index": 0, "id": "fork-original", "type": "function", "function": {
                "name": "ArchiveRead", "arguments": json.dumps({"id": match[1], "limit": 4096}),
            }}]}, "tool_calls"
        if any(item["role"] == "user" and item.get("content") == "synthetic second" for item in messages):
            if any(item.get("tool_call_id") == "agent" for item in messages):
                if background and not any(item.get("tool_call_id") == "fork-wait" for item in messages):
                    agent = next(item["content"] for item in messages if item.get("tool_call_id") == "agent")
                    match = re.search(r"\(([A-Za-z0-9_-]{4,})\)", agent)
                    return {"tool_calls": [{"index": 0, "id": "fork-wait", "type": "function", "function": {
                        "name": "TaskWait", "arguments": json.dumps({"ids": [match[1]]}),
                    }}]}, "tool_calls"
                return {"content": "MAIN-DONE"}, "stop"
            return parent_dispatch(background, fork=True)
        first_steps.append(body)
        if len(first_steps) <= 2:
            step = len(first_steps)
            return {"content": ("INHERITED-FIRST-DETAIL-" if step == 1 else "later-") + "X" * 30000,
                    "tool_calls": [{"index": 0, "id": f"parent-read-{step}", "type": "function", "function": {
                        "name": "Read", "arguments": json.dumps({"path": "small.txt"}),
                    }}]}, "tool_calls"
        return {"content": "FIRST-DONE"}, "stop"

    _, result = run_child_entry(tmp_path, respond, stdin="synthetic first\n/compact\nsynthetic second\n/exit\n",
                                files={"small.txt": "synthetic file"},
                                settings={"RUOCUN_SUMMARY_MODEL": "synthetic-summary-model"})
    assert original and "INHERITED-FIRST-DETAIL" in original[0]
    assert "MAIN-DONE" in result.stdout


def test_background_task_output_keeps_earlier_original_activity_after_summary_and_reopen(tmp_path):
    outputs = []
    summaries = []

    def respond(body, requests):
        if body["model"] == "synthetic-summary-model":
            summaries.append(body)
            return {"content": "<摘要>早期读取已经完成，继续完成当前合成子任务。</摘要>"}, "stop"
        if body["model"] == "synthetic-child-model":
            step = sum(item["model"] == "synthetic-child-model" for item in requests)
            if step <= 5:
                text = ("EARLY-ORIGINAL-RESPONSE-" if step == 1 else f"later-{step}-") + "X" * 30000
                return {"content": text, "tool_calls": [{"index": 0, "id": f"read-{step}", "type": "function",
                    "function": {"name": "Read", "arguments": json.dumps({"path": "small.txt"})}}]}, "tool_calls"
            return {"content": "CHILD-DONE"}, "stop"
        results = {item["tool_call_id"]: item["content"] for item in body["messages"] if item["role"] == "tool"}
        if "agent" not in results:
            return parent_dispatch(True)
        match = re.search(r"\(([A-Za-z0-9_-]{4,})\)", results["agent"])
        if match is None:
            return {"content": "LAUNCH-FAILED"}, "stop"
        if any(item.get("content") == "inspect persisted child" for item in body["messages"]):
            if "out-reopen" in results:
                outputs.append(results["out-reopen"])
                return {"content": "REOPEN-DONE"}, "stop"
            return {"tool_calls": [{"index": 0, "id": "out-reopen", "type": "function", "function": {
                "name": "TaskOutput", "arguments": json.dumps({"id": match[1]}),
            }}]}, "tool_calls"
        name, identity = ("TaskWait", "wait") if "wait" not in results else ("TaskOutput", "out")
        if "out" in results:
            outputs.append(results["out"])
            return {"content": "MAIN-DONE"}, "stop"
        args = {"ids": [match[1]]} if name == "TaskWait" else {"id": match[1]}
        return {"tool_calls": [{"index": 0, "id": identity, "type": "function", "function": {
            "name": name, "arguments": json.dumps(args),
        }}]}, "tool_calls"

    _, result = run_child_entry(tmp_path, respond, files={"small.txt": "small synthetic file"},
                                settings={"RUOCUN_SUMMARY_MODEL": "synthetic-summary-model"},
                                reopen="inspect persisted child")
    assert summaries, "the model-visible projection must actually have been summarized"
    assert len(outputs) >= 2
    assert all("EARLY-ORIGINAL-RESPONSE" in output and "CHILD-DONE" in output for output in outputs)
    assert "MAIN-DONE" in result.stdout


@pytest.mark.parametrize("background", [False, True])
def test_child_prunes_durably_and_reads_its_original_through_the_bound_archive_scope(tmp_path, background):
    recovered = []
    text = "\n".join(("MIDDLE-ORIGINAL-FACT-" if number == 8 else "line-") + "X" * 995
                     for number in range(150))

    def respond(body, requests):
        if len(requests) == 1:
            return parent_dispatch(background)
        if body["model"] != "synthetic-child-model":
            results = {item["tool_call_id"]: item["content"] for item in body["messages"] if item["role"] == "tool"}
            if background and "wait" not in results:
                match = re.search(r"\(([A-Za-z0-9_-]{4,})\)", results.get("agent", ""))
                if match is not None:
                    return {"tool_calls": [{"index": 0, "id": "wait", "type": "function", "function": {
                        "name": "TaskWait", "arguments": json.dumps({"ids": [match[1]]}),
                    }}]}, "tool_calls"
            return {"content": "MAIN-DONE"}, "stop"
        children = [item for item in requests if item["model"] == "synthetic-child-model"]
        if len(children) == 1:
            name, identity, args = "Read", "child-read", {"path": "large.txt"}
        elif len(children) == 2:
            result = next(item["content"] for item in body["messages"] if item.get("tool_call_id") == "child-read")
            match = re.search(r"原文归档:([A-Za-z0-9:_-]+)", result)
            if match is None:
                return {"content": "MISSING-ARCHIVE-REFERENCE"}, "stop"
            name, identity, args = "ArchiveRead", "child-archive", {"id": match[1], "offset": 4000, "limit": 12000}
        else:
            recovered.extend(item["content"] for item in body["messages"] if item.get("tool_call_id") == "child-archive")
            return {"content": "CHILD-DONE"}, "stop"
        return {"tool_calls": [{"index": 0, "id": identity, "type": "function", "function": {
            "name": name, "arguments": json.dumps(args),
        }}]}, "tool_calls"

    requests, result = run_child_entry(tmp_path, respond, files={"large.txt": text})
    children = [body for body in requests if body["model"] == "synthetic-child-model"]
    assert len(children) == 3, "child must continue after a confirmed archived reduction"
    assert recovered and "MIDDLE-ORIGINAL-FACT" in recovered[0]
    assert "未绑定归档读取权限" not in recovered[0]
    assert all("synthetic parent input" not in str(body["messages"]) for body in children)
    assert "MAIN-DONE" in result.stdout


def test_explicit_task_continuation_imports_the_original_child_scope_before_archive_read(tmp_path):
    resumed = []
    text = "\n".join(("CONTINUED-ORIGINAL-FACT-" if number == 8 else "line-") + "X" * 995
                     for number in range(150))

    def call(identity, name, args):
        return {"tool_calls": [{"index": 0, "id": identity, "type": "function", "function": {
            "name": name, "arguments": json.dumps(args),
        }}]}, "tool_calls"

    def respond(body, requests):
        results = {item["tool_call_id"]: item["content"] for item in body["messages"] if item["role"] == "tool"}
        if body["model"] == "synthetic-child-model":
            continuing = any(item["role"] == "user" and item.get("content") == "continue from archive"
                             for item in body["messages"])
            if continuing and "resume-read" in results:
                resumed.append(results["resume-read"])
                return {"content": "RESUMED-DONE"}, "stop"
            if "child-read" not in results:
                return call("child-read", "Read", {"path": "large.txt"})
            if continuing:
                match = re.search(r"原文归档:([A-Za-z0-9:_-]+)", results["child-read"])
                return call("resume-read", "ArchiveRead", {"id": match[1], "offset": 4000, "limit": 12000})
            return {"content": "CHILD-DONE"}, "stop"
        if "agent" not in results:
            return parent_dispatch(True)
        match = re.search(r"\(([A-Za-z0-9_-]{4,})\)", results["agent"])
        if match is None:
            return {"content": "LAUNCH-FAILED"}, "stop"
        if "wait" not in results:
            return call("wait", "TaskWait", {"ids": [match[1]]})
        if "send" not in results:
            return call("send", "TaskSend", {"id": match[1], "message": "continue from archive"})
        if "wait2" not in results:
            return call("wait2", "TaskWait", {"ids": [match[1]]})
        return {"content": "MAIN-DONE"}, "stop"

    _, result = run_child_entry(tmp_path, respond, files={"large.txt": text})
    assert resumed and "CONTINUED-ORIGINAL-FACT" in resumed[0]
    assert "MAIN-DONE" in result.stdout
