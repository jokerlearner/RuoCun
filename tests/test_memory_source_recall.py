"""Reflection source labels survive a fresh process and ordinary startup recall."""

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from support.ruocun_acceptance.environment import isolated_env

import ruocun
from ruocun.memory.frontmatter import parseMemoryFile


def test_reflected_non_file_sources_are_recalled_in_a_new_cli_process(tmp_path):
    environment = isolated_env(tmp_path / "environment", Path(sys.executable))
    environment.update(RUOCUN_REFLECT_SYNC="1", RUOCUN_LANG="zh")
    home = Path(environment["HOME"])
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    preference = "用户希望每次答复先给出结论，再说明验证依据。"
    project_fact = "当前演示项目在任务完成后集中展示验证摘要。"
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            reflective = "mergeInto" in str(body["messages"][-1].get("content", ""))
            requests.append({"reflection": reflective, "request": body})
            if reflective:
                text = json.dumps({
                    "onTrack": True, "advisory": None, "memories": [
                        {"title": "回答顺序偏好", "text": preference, "type": "user",
                         "importance": 8, "source": "user_stated"},
                        {"title": "演示项目验证展示", "text": project_fact, "type": "semantic",
                         "importance": 7, "source": "inferred"},
                    ], "corrections": [], "confirmed": [],
                }, ensure_ascii=False)
            else:
                text = "合成请求已完成。"
            frames = [
                {"choices": [{"delta": {"role": "assistant", "content": text}}]},
                {"choices": [{"delta": {}, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 100, "completion_tokens": 10}},
            ]
            data = "".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write((data + "data: [DONE]\n\n").encode("utf-8"))

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {
            "synthetic": {"provider": "zhipu", "model": "synthetic-memory-source",
                          "key": "synthetic-memory-source-key",
                          "baseUrl": f"http://127.0.0.1:{server.server_port}/v1"},
        }}), encoding="utf-8")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = (f"import runpy,sys;sys.path.insert(0,{str(package)!r});"
                  "runpy.run_module('ruocun',run_name='__main__')")
        command = [sys.executable, "-I", "-B", "-X", "utf8", "-c", loader,
                   "--config", str(config), "--cwd", str(workspace),
                   "--no-skills", "--no-hooks", "--no-mcp"]

        def run(label, text, *arguments):
            result = subprocess.run(
                [*command, *arguments], input=text + "\n/exit\n", env=environment,
                cwd=workspace, capture_output=True, encoding="utf-8", timeout=45,
            )
            (tmp_path / f"{label}.stdout.txt").write_text(result.stdout, encoding="utf-8")
            (tmp_path / f"{label}.stderr.txt").write_text(result.stderr, encoding="utf-8")
            assert result.returncode == 0, (result.stdout, result.stderr)

        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            run("first", preference + "请确认已理解这项偏好。", "--reflect-memory")
            first_requests = len(requests)
            assert [item["reflection"] for item in requests] == [False, True]

            # The fixture does not create memory files: only ordinary reflection does.
            saved = {}
            for root in (home / ".ruocun" / "memory", workspace / ".ruocun" / "memory"):
                for file in root.glob("*.md"):
                    memory = parseMemoryFile(file.stem, file.read_text(encoding="utf-8"))
                    assert memory is not None
                    saved[memory.title] = (memory, root)
            assert set(saved) == {"回答顺序偏好", "演示项目验证展示"}
            assert saved["回答顺序偏好"][0].source == "user_stated"
            assert saved["回答顺序偏好"][0].text == preference
            assert saved["回答顺序偏好"][1] == home / ".ruocun" / "memory"
            assert saved["演示项目验证展示"][0].source == "inferred"
            assert saved["演示项目验证展示"][0].text == project_fact
            assert saved["演示项目验证展示"][1] == workspace / ".ruocun" / "memory"

            # No --continue and no reflection: this process must recall from disk.
            run("second", "请开始下一项合成任务。")
            fresh_requests = requests[first_requests:]
            assert len(fresh_requests) == 1 and not fresh_requests[0]["reflection"]
            messages = fresh_requests[0]["request"]["messages"]
            assert [message["role"] for message in messages] == ["system", "user"]
            system = messages[0]["content"]
            assert preference in system, "fresh startup omitted persisted user_stated preference"
            assert project_fact in system, "fresh startup omitted persisted inferred project fact"
        finally:
            (tmp_path / "requests.json").write_text(
                json.dumps(requests, ensure_ascii=False, indent=2), encoding="utf-8",
            )
            server.shutdown()
            serving.join(timeout=5)
