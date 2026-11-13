"""ADR-0011必要接线确认：DAO工具回合/拒绝语义+07正常双进程保存重开。

合成HTTP端点，无真实模型费用。不扩建压力/故障矩阵。
"""

import asyncio
import base64
import json
import os
import struct
import subprocess
import sys
import threading
import time
import zlib
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ruocun
from ruocun.config.compat import DEFAULT_COMPATIBILITY
from ruocun.memory.distill import distill
from ruocun.memory.store import MemoryStore, routeScope
from ruocun.platform.windows.durable_file import ensure_private_dir


def test_seven_tools_approval_and_normal_reopen(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "main.py").write_text("print('old')\n", encoding="utf-8")
    memory_path = workspace / ".ruocun" / "memory" / "startup.md"
    memory_path.parent.parent.mkdir()
    ensure_private_dir(memory_path.parent)
    memory_record = b"---\nname: startup\ntype: semantic\nstatus: active\n---\n"
    memory_path.write_bytes(memory_record + b"synthetic-startup-memory\n")
    expired = memory_path.with_name("synthetic-expired.md")
    old_day = (datetime.now(UTC) - timedelta(days=8)).date().isoformat()
    expired.write_bytes(
        ("---\nname: synthetic-expired\ntype: semantic\nstatus: active\n"
         f"created: {old_day}\nlastUsed: {old_day}\nimportance: 2\nconfidence: 0.6\n---\nsynthetic-expired-body\n")
        .encode("utf-8"),
    )

    def png_chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
           + png_chunk(b"IDAT", zlib.compress(b"\0\xff\xff\xff\xff")) + png_chunk(b"IEND", b""))
    (workspace / "diagram.png").write_bytes(png)
    image_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    home = tmp_path / "home"
    home.mkdir()
    native = home / ".ruocun"
    native.mkdir()
    user_memory = native / "memory"
    ensure_private_dir(user_memory)
    for number in range(12):
        (user_memory / f"m{number}.md").write_text(
            f"---\nname: m{number}\ntitle: M{number}\ntype: user\nstatus: active\n---\n"
            f"synthetic-pref-{number}\n", encoding="utf-8",
        )
    marker = user_memory / ".last-consolidation"
    managed = home / "program-data/RuoCun/managed-settings.json"
    managed.parent.mkdir(parents=True)
    managed.write_text(json.dumps({"permissions": {"deny": ["Write(denied.txt)"]}}), encoding="utf-8")
    (workspace / ".env").write_text(
        f"ProgramData={workspace / 'untrusted-managed'}\nRUOCUN_PROVISIONAL_DAYS=50000\n", encoding="utf-8",
    )
    (native / "RUOCUN.md").write_text("synthetic-user-instruction", encoding="utf-8")
    (workspace / "RUOCUN.md").write_text("synthetic-project-instruction", encoding="utf-8")
    (workspace / "AGENTS.md").write_text("engineering-marker-must-stay-out", encoding="utf-8")
    skill = native / "skills" / "synthetic-demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: synthetic-demo\ndescription: synthetic skill catalog" + "a" * 196 + "😀\n---\n"
        "synthetic-private-skill-body", encoding="utf-8")
    legacy_skills = home / "legacy-skills"
    legacy_skills.mkdir()
    (legacy_skills / "legacy.md").write_text(
        "---\nname: synthetic-demo\n---\ncompat-body-overridden", encoding="utf-8")
    legacy_profile = home / "legacy-config.json"
    legacy_profile.write_text("{}", encoding="utf-8")
    (native / "compatibility.json").write_text(json.dumps({"version": 1, "sources": [{
        "id": "missing-instructions", "scope": "user", "resource": "instructions",
        "path": str(home / "missing.txt"),
    }, {
        "id": "legacy-profiles", "scope": "user", "resource": "profiles", "path": str(legacy_profile),
    }, {
        "id": "legacy-skills", "scope": "user", "resource": "skills", "path": str(legacy_skills),
    }]}), encoding="utf-8")
    config = home / "config.json"
    captured = []
    maintenance_requests = []
    maintenance_started = threading.Event()
    release_maintenance = threading.Event()
    foreground_during_maintenance = threading.Event()

    def call(i, name, args):
        return {"index": i, "id": f"call-product-{i}", "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)}}

    calls = [
        call(0, "TodoWrite", {"todos": [{"content": "修改并验证", "status": "in_progress"}]}),
        call(1, "Glob", {"glob": "*.py"}),
        call(2, "Grep", {"pattern": "old", "path": "main.py"}),
        call(3, "Read", {"path": "main.py"}),
        call(4, "Write", {"path": "created.txt", "content": "created\n"}),
        call(5, "Edit", {"path": "main.py", "old_string": "old", "new_string": "new"}),
        call(6, "Bash", {"command": f'"{sys.executable}" "main.py"', "description": "运行修改后的合成程序"}),
        call(7, "Write", {"path": "denied.txt", "content": "must not exist"}),
        call(8, "Skill", {"name": "synthetic-demo", "args": "synthetic-args"}),
        call(9, "Read", {"path": "diagram.png"}),
        call(10, "ListDir", {}),
    ]

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            last = body["messages"][-1]["content"]
            if isinstance(last, str) and "记忆提出合并计划" in last:
                maintenance_requests.append(body)
                maintenance_started.set()
                assert release_maintenance.wait(12)
                plan = {"groups": [{
                    "canonical": {"title": "M0", "text": "synthetic-merged-preference", "type": "user"},
                    "supersede": ["m1"], "reason": "synthetic duplicate preference",
                }]}
                self.respond({"content": json.dumps(plan)}, "stop")
                return
            captured.append(body)
            if last == "维护并行验证":
                foreground_during_maintenance.set()
            if len(captured) == 1:
                memory_path.write_bytes(memory_record + b"synthetic-reopened-memory\n")
                delta = {"role": "assistant", "tool_calls": [
                    {**call(90, "Read", {"path": "main.py"}), "index": 0, "id": "before-plan"},
                ]}
            elif len(captured) == 2:
                delta = {"role": "assistant", "tool_calls": calls}
            else:
                delta = {"content": "first complete" if len(captured) == 3 else "reopen complete"}
            if not body.get("tools"):
                delta = {"content": "<摘要>synthetic-compacted-summary</摘要>"}
            self.respond(delta, "tool_calls" if len(captured) in (1, 2) else "stop")

        def respond(self, delta, finish):
            frames = [
                {"choices": [{"delta": delta}]},
                {"choices": [{"delta": {}, "finish_reason": finish}]},
                {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 5,
                                          "prompt_tokens_details": {"cached_tokens": 2}}},
            ]
            data = "".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
            data += "data: [DONE]\n\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(data.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
        "provider": "openai", "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        "model": "glm-5.3-flash", "key": "synthetic-key",
    }}}), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k in {
        "SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
    }}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
               ProgramData=str(home / "program-data"), PYTHONNOUSERSITE="1", PIP_CONFIG_FILE="NUL",
               RUOCUN_LANG="zh")
    # 源定向与最终安装均绑定父进程实际载入的目标包，不借旧installed包假验新入口。
    package_root = Path(ruocun.__file__).resolve().parent.parent
    entry = f"import sys\nsys.path.insert(0, {str(package_root)!r})\n"
    if package_root.name == "src":
        # 源码检查显式选择同一checkout的内部角色，安装检查走默认同包-m入口。
        role_loader = (f"import sys, runpy\nsys.path.insert(0, {str(package_root)!r})\n"
                       "runpy.run_module('ruocun', run_name='__main__')")
        role_command = [sys.executable, "-I", "-X", "utf8", "-c", role_loader]
        entry += (
            "from functools import partial\n"
            "from ruocun.agent import runtime\n"
            "from ruocun.tools.managed_shell import ManagedShellManager\n"
            "runtime.ManagedShellManager = partial(ManagedShellManager, "
            f"runner_command={role_command + ['--ruocun-shell-runner']!r}, "
            f"helper_command={role_command + ['--ruocun-ipc-helper']!r})\n"
        )
    entry += "from ruocun.cli import main\nraise SystemExit(main())"
    command = [sys.executable, "-I", "-X", "utf8", "-c", entry,
               "--config", str(config), "--cwd", str(workspace),
               "--permission-mode", "bypassPermissions", "--deny", "Write(denied.txt)"]
    try:
        first = subprocess.run(command + ["合成修改任务"], env=env, cwd=home,
                               input="", text=True, encoding="utf-8",
                               capture_output=True, timeout=40)
        assert first.returncode == 0, first.stdout + first.stderr
        assert "first complete" in first.stdout
        assert not expired.exists()
        assert captured[0]["parallel_tool_calls"] is True
        assert (workspace / "created.txt").read_text(encoding="utf-8") == "created\n"
        assert (workspace / "main.py").read_text(encoding="utf-8") == "print('new')\n"
        assert not (workspace / "denied.txt").exists()
        first_rejection = [m for m in captured[1]["messages"] if m["role"] == "tool"]
        assert len(first_rejection) == 1 and "[操作被拒绝]" in first_rejection[0]["content"]
        assert "TodoWrite" in first_rejection[0]["content"] and "print('old')" not in first_rejection[0]["content"]
        results = {m["tool_call_id"]: m["content"] for m in captured[2]["messages"] if m["role"] == "tool"}
        assert len(results) == 12
        assert list(results)[1:] == [f"call-product-{i}" for i in range(11)]
        assert "new" in results["call-product-6"] and "exit 0" in results["call-product-6"], results["call-product-6"]
        assert "拒绝" in results["call-product-7"]
        assert "synthetic-private-skill-body" in results["call-product-8"]
        assert "synthetic-args" in results["call-product-8"]
        assert "已读取图片" in results["call-product-9"]
        assert "main.py" in results["call-product-10"]
        assert captured[2]["messages"][-1]["role"] == "user"
        assert captured[2]["messages"][-1]["content"][0]["image_url"]["url"] == image_url
        assert all("imageData" not in m and "imageDelivered" not in m for m in captured[2]["messages"])
        prefix = captured[0]["messages"][0]["content"]
        assert "synthetic-user-instruction" in prefix
        assert "synthetic-project-instruction" in prefix
        assert "engineering-marker-must-stay-out" not in prefix
        assert "synthetic skill catalog" in prefix
        assert "synthetic-private-skill-body" not in prefix
        for request in captured[:3]:
            system = request["messages"][0]["content"]
            assert "synthetic-startup-memory" in system and "synthetic-reopened-memory" not in system
        assert "compat-body-overridden" not in results["call-product-8"]
        assert all(source not in first.stdout for source in ("missing-instructions", "legacy-profiles", "legacy-skills"))
        saved_session = next((native / "sessions").glob("*/*/session.db")).parent.name
        second = subprocess.run(command + ["--continue", saved_session, "继续合成任务"], env=env, cwd=home,
                                input="", text=True, encoding="utf-8", capture_output=True, timeout=20)
        assert second.returncode == 0, second.stdout + second.stderr
        assert "reopen complete" in second.stdout
        assert "历史费用不完整" in second.stdout
        assert len(captured) == 4
        cache_file, = (native / "sessions").glob("*/*/cache.jsonl")
        cache_before_query = cache_file.read_bytes()
        main_events = [event for line in cache_before_query.splitlines()
                       if (event := json.loads(line))["agent"] == "main"]
        assert len(main_events) == 4
        assert [(e["prompt"], e["completion"], e["hit"], e["miss"]) for e in main_events] == [(10, 5, 2, 8)] * 4
        assert main_events[-1]["changed"] == []  # Reopened process starts with fresh prefix diagnostics.
        query = subprocess.run(command + ["--continue", saved_session, "/status"], cwd=home,
                               env={**env, "RUOCUN_MAX_BUDGET": "0.02", "RUOCUN_MAX_BUDGET_HARD": "1"},
                               input="", text=True, encoding="utf-8", capture_output=True, timeout=20)
        assert query.returncode == 0, query.stdout + query.stderr
        assert "模式 bypassPermissions · 开关 免审批" in query.stdout
        assert "输入 40 tok(cache 命中 8,命中率 20.0%)· 输出 20 tok" in query.stdout
        assert "本次进程费用:约 ￥0.0000（历史费用不完整）" in query.stdout
        assert "本次进程预算:提醒阈值 ￥0.020 · 达到预算硬停" in query.stdout
        assert "上下文 0%" in query.stdout and len(captured) == 4
        assert cache_file.read_bytes() == cache_before_query
        assert "synthetic-reopened-memory" in captured[3]["messages"][0]["content"]
        assert "synthetic-startup-memory" not in captured[3]["messages"][0]["content"]
        assert any(m.get("content") == "first complete" for m in captured[3]["messages"])
        assert captured[3]["messages"][-1]["content"] == "继续合成任务"
        images = [p for m in captured[3]["messages"] if isinstance(m.get("content"), list)
                  for p in m["content"] if p.get("type") == "image_url"]
        assert [p["image_url"]["url"] for p in images] == [image_url]
        # 复用刚从真实SQLite会话恢复的工具轨迹，抽取响应固定在模型边界。
        async def distill_saved_trace():
            store = MemoryStore(workspace, native, DEFAULT_COMPATIBILITY)

            async def fixed_distillation(options):
                transcript = options["messages"][-1]["content"]
                assert isinstance(transcript, str) and "tool:" in transcript and "exit 0" in transcript
                assert not options.get("tools")
                return json.dumps([{
                    "type": "semantic", "text": "synthetic-maintenance-fact", "importance": 7, "source": "main.py",
                }])

            records = await distill(captured[3]["messages"], today=store.today(), options={
                "baseUrl": "http://127.0.0.1:1/v1", "apiKey": "synthetic-key", "model": "glm-5.3-flash", "messages": [],
            }, call=fixed_distillation)
            assert len(records) == 1
            for memory in records:
                assert (await store.upsert(routeScope(memory.type), memory)).action == "added"
            reopened = MemoryStore(workspace, native, DEFAULT_COMPATIBILITY)
            assert any(entry.memory.text == "synthetic-maintenance-fact" and entry.memory.source == "main.py"
                       for entry in await reopened.load(("project",)))
            assert b"synthetic-reopened-memory" in memory_path.read_bytes()

        asyncio.run(distill_saved_trace())
        # 同一既有入口确认逐轮文字交互；管道输入不能冒充真实Terminal体验。
        early_input = "交互第一轮" + "x" * 1200
        interactive = subprocess.run(command + ["--no-memory"], env={**env, "RUOCUN_COMPACT_RETAIN_TOKENS": "20"}, cwd=home,
                                     input=("/skills\n/permissions list\n/cost\n/context-window 128k\n/context\n"
                                            f"/status\n/effort low\n{early_input}\n交互第二轮\n"
                                            "/synthetic-demo\n/compact\n压缩后继续\n/exit\n"), text=True,
                                     encoding="utf-8", capture_output=True, timeout=20)
        assert interactive.returncode == 0, interactive.stdout + interactive.stderr
        assert len(captured) == 9, interactive.stdout + interactive.stderr
        assert "synthetic-reopened-memory" not in captured[4]["messages"][0]["content"]
        assert {"MemoryRead", "MemoryWrite"} <= {tool["function"]["name"] for tool in captured[4]["tools"]}
        assert captured[4]["messages"][-1]["content"] == early_input
        assert captured[4]["reasoning_effort"] == "low"
        assert captured[5]["messages"][-1]["content"] == "交互第二轮"
        assert any(m.get("content") == early_input for m in captured[5]["messages"])
        assert captured[6]["messages"][-1]["content"] == "synthetic-private-skill-body"
        assert not captured[7].get("tools")
        assert "reasoning_effort" not in captured[7]
        assert captured[8]["messages"][-1]["content"] == "压缩后继续"
        assert any("synthetic-compacted-summary" in str(m.get("content", ""))
                   for m in captured[8]["messages"])
        assert "/synthetic-demo" in interactive.stdout
        assert str(managed) in interactive.stdout
        assert not maintenance_requests

        process = subprocess.Popen(command, env=env, cwd=home, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            assert maintenance_started.wait(8)
            assert process.stdin is not None
            process.stdin.write("维护并行验证\n")
            process.stdin.flush()
            assert foreground_during_maintenance.wait(8)
            release_maintenance.set()
            deadline = time.monotonic() + 8
            while not marker.is_file() and process.poll() is None and time.monotonic() < deadline:
                time.sleep(0.02)
            stdout, stderr = process.communicate("/exit\n", timeout=20)
            assert process.returncode == 0, stdout + stderr
            assert marker.is_file() and len(maintenance_requests) == 1
            assert "synthetic-merged-preference" in (user_memory / "m0.md").read_text(encoding="utf-8")
            assert "status: superseded" in (user_memory / "m1.md").read_text(encoding="utf-8")
            assert not list(user_memory.glob(".*.bak"))
            assert "synthetic-pref-0" in captured[-1]["messages"][0]["content"]
            assert "synthetic-maintenance-fact" in captured[-1]["messages"][0]["content"]
            assert "synthetic-merged-preference" not in captured[-1]["messages"][0]["content"]
            trace = [event for file in (native / "sessions").glob("*/*/memory-trace.jsonl")
                     for event in map(json.loads, file.read_text(encoding="utf-8").splitlines())]
            assert any(event["kind"] == "consolidated" and event["scope"] == "user"
                       and event["groups"] == 1 and event["superseded"] == 1 for event in trace)
        finally:
            release_maintenance.set()
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
