"""普通runtime的必要受控TTY接线；无模型费用，不代替Windows Terminal/resize。"""

import asyncio
import copy
import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

import ruocun
from ruocun.agent import input_broker, runtime
from ruocun.agent.input_broker import InputBroker
from ruocun.client.resilient import ResilientResult
from ruocun.commands.builtin import SIMPLIFY_BODY_EN
from ruocun.permissions.settings import extractCliPermissions
from ruocun.session.inputs import modelInput, originalInput


class Output(DummyOutput):
    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)

    def text(self):
        return "".join(self.parts)


def _exercise_tty(tmp_path, monkeypatch):
    monkeypatch.setenv("RUOCUN_LANG", "zh")
    monkeypatch.setenv("RUOCUN_OWNED_TERMINAL", "1")
    async def scenario():
        home, workspace = tmp_path / "home", tmp_path / "workspace"
        home.mkdir()
        workspace.mkdir()
        native = home / ".ruocun"
        native.mkdir()
        nested = workspace / "src" / ".ruocun" / "skills" / "runtime-nested"
        nested.mkdir(parents=True)
        (workspace / "src" / "main.py").write_bytes(b"synthetic-main\n")
        (nested / "SKILL.md").write_text(
            "---\nname: runtime-nested\ndescription: synthetic nested skill\n---\nbody-from-nested-skill",
            encoding="utf-8",
        )
        vendor = workspace / "vendor" / "install-demo"
        vendor.mkdir(parents=True)
        original_skill = b"---\nname: install-demo\ndescription: synthetic install\n---\nUse `ForeignRead` from assets."
        (vendor / "SKILL.md").write_bytes(original_skill)
        (vendor / "asset data.txt").write_bytes(b"synthetic resource\r\n")
        (workspace / ".env").write_text(f"ProgramData={workspace / 'untrusted-managed'}\n", encoding="utf-8")
        for name, body in (("queued-skill", "queued-body-at-ack"), ("simplify", "shadow-simplify-body")):
            folder = native / "skills" / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: synthetic {name}\n---\n{body}", encoding="utf-8")
        (native / "skills-disabled.json").write_text('["simplify"]', encoding="utf-8")
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "openai", "baseUrl": "http://127.0.0.1:1/v1",
            "model": "glm-5.3-flash", "key": "synthetic-runtime-key",
        }}}), encoding="utf-8")
        first_started, release = threading.Event(), threading.Event()
        captured, contexts, opened, conversions = [], [], {}, []
        sigint_handlers = []
        output = Output()
        original_signal = runtime.signal.signal

        def register_signal(signum, handler):
            if signum == runtime.signal.SIGINT:
                sigint_handlers.append(handler)
            return original_signal(signum, handler)

        monkeypatch.setattr(runtime.signal, "signal", register_signal)

        def tool(call_id, name, args):
            return {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}

        def request(options, *, env, context):
            if not options.get("tools"):
                conversions.append(copy.deepcopy(options))
                return ResilientResult("complete", [], {"role": "assistant", "content": "adapted installed body"},
                                       None, "stop", [], {})
            captured.append(copy.deepcopy(options))
            contexts.append(context)
            number = len(captured)
            if number == 1:
                first_started.set()
                assert release.wait(8)
                if context.on_delta:
                    context.on_delta({"kind": "content", "text": "obsolete-delta-must-not-show"})
                message = {"role": "assistant", "content": "interrupted-old-response"}
            elif number == 2:
                message = {"role": "assistant", "content": "", "tool_calls": [
                    tool("read-main", "Read", {"path": "src/main.py"}),
                    tool("write-approved", "Write", {"path": "approved.txt", "content": "approved"}),
                    tool("install-demo", "SkillInstall", {"source": "vendor/install-demo", "scope": "user"}),
                ]}
            elif number == 5:
                message = {"role": "assistant", "content": "", "tool_calls": [
                    tool("plan-write", "Write", {"path": "plan-denied.txt", "content": "forbidden"}),
                    tool("load-nested", "Skill", {"name": "runtime-nested"}),
                    tool("load-installed", "Skill", {"name": "install-demo"}),
                    tool("write-memory", "MemoryWrite", {
                        "title": "synthetic-note", "text": "Prefer short synthetic summaries.", "type": "feedback",
                    }),
                    tool("read-memory", "MemoryRead", {"query": "synthetic-note"}),
                ]}
            elif number == 7:
                message = {"role": "assistant", "content": "", "tool_calls": [
                    tool("close-write", "Write", {"path": "close-denied.txt", "content": "forbidden"}),
                ]}
            else:
                suffix = " 若存🙂" if number == 4 else ""
                message = {"role": "assistant", "content": f"tty-complete-{number}{suffix}"}
                if context.on_delta:
                    context.on_delta({"kind": "content", "text": message["content"]})
            return ResilientResult("complete", [], message, {"prompt_tokens": 11, "completion_tokens": 5},
                                   "tool_calls" if message.get("tool_calls") else "stop", [], {})

        monkeypatch.setattr(runtime, "streamChatResilient", request)
        clipboard = []
        monkeypatch.setattr(runtime, "_copy_to_clipboard", clipboard.append)
        original_open = runtime.Conversation.open

        async def open_conversation(*args, **kwargs):
            journal = await original_open(*args, **kwargs)
            opened.update(journal=journal, session=args[4])
            return journal

        monkeypatch.setattr(runtime.Conversation, "open", open_conversation)
        arguments = runtime._parser().parse_args(["--config", str(config), "--cwd", str(workspace)])
        arguments.permissions = extractCliPermissions(["--permission-mode", "default"])["config"]
        with create_pipe_input() as pipe:
            monkeypatch.setattr(input_broker, "create_input", lambda: pipe)

            def factory(pause):
                opened["broker"] = InputBroker(on_pause=pause, output=output)
                return opened["broker"]

            running = asyncio.create_task(runtime._run(arguments, broker_factory=factory))

            async def until(predicate):
                async with asyncio.timeout(8):
                    while not predicate():
                        if running.done():
                            raise AssertionError(f"入口在预期状态出现前退出，返回码 {running.result()}")
                        await asyncio.sleep(0.01)

            try:
                await until(lambda: "RuoCun ·" in output.text())
                broker = opened["broker"]
                assert broker._owned_viewport, "The ordinary entry must opt in for an explicitly owned viewport."
                pipe.send_text("/copy\r")
                await until(lambda: "没有可复制的回答。" in output.text())
                assert not clipboard and not captured
                pipe.send_text("开始TTY\r")
                await until(first_started.is_set)
                assert "推理正文始终使用简体中文" in captured[0]["messages"][0]["content"]
                pipe.send_text("\x1b[Z")
                await until(lambda: "本轮结束后可切换" in output.text())
                assert broker._status_info["permMode"] == "default"
                pipe.send_text("/status\r/memory\r/queued-skill\r排队-乙\r/effort invalid\r/context-window broken\r"
                               "/permissions add\r/memory delete ../outside\r正在编辑🙂")
                await until(lambda: broker._queued == 2 and broker.buffer.text == "正在编辑🙂")
                assert len(captured) == 1 and not contexts[0].cancel()
                assert "执行状态：running" in output.text()
                await until(lambda: "记忆为空" in output.text() and "用法:/memory delete" in output.text())
                assert not contexts[0].cancel()
                view = await opened["journal"].worker.load_recovery_view()
                queued = [item for item in view.checkpoint.accepted_inputs if item.state == "queued"]
                assert [originalInput(item.payload) for item in queued] == ["/queued-skill", "排队-乙"]
                assert modelInput(queued[0].payload) == "queued-body-at-ack"
                (native / "skills/queued-skill/SKILL.md").write_text("changed-after-ack", encoding="utf-8")
                cursor = broker.buffer.cursor_position
                try:
                    sigint_handlers[-1](runtime.signal.SIGINT, None)
                except KeyboardInterrupt as exc:
                    raise AssertionError("readonly查询覆盖了飞行run状态，SIGINT未取消当前Event") from exc
                assert contexts[0].cancel()
                release.set()
                await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
                assert contexts[0].cancel() and not contexts[1].cancel()
                assert "obsolete-delta-must-not-show" not in output.text()
                assert broker.buffer.text == "正在编辑🙂" and broker.buffer.cursor_position == cursor
                pipe.send_text("y\r")
                await until(lambda: "安装技能 vendor/install-demo → 用户技能目录" in broker._approval_prompt)
                pipe.send_text("y\r")
                await until(lambda: "tty-complete-3" in output.text() and broker._state == "idle")
                assert broker._status_info["permMode"] == "default"
                assert "输入已保存" not in output.text() and "已保存 ·" not in output.text()
                assert (workspace / "approved.txt").read_text(encoding="utf-8") == "approved"
                installed = native / "skills" / "install-demo"
                assert (installed / "SKILL.md").read_bytes() == (vendor / "SKILL.md").read_bytes() == original_skill
                assert (installed / "asset data.txt").read_bytes() == b"synthetic resource\r\n"
                wire = captured[2]["messages"]
                assert wire[0] == captured[1]["messages"][0]
                catalogs = [m["content"] for m in wire[1:] if m["role"] == "system"]
                assert any("runtime-nested" in text for text in catalogs)
                assert wire[-1]["role"] == "system" and "install-demo" in wire[-1]["content"]
                assert [m["tool_call_id"] for m in wire if m["role"] == "tool"] == [
                    "read-main", "write-approved", "install-demo",
                ]
                users = [message["content"] for message in captured[1]["messages"] if message["role"] == "user"]
                assert users == ["开始TTY", "queued-body-at-ack", "排队-乙"]
                assert broker.buffer.text == "正在编辑🙂" and broker.buffer.cursor_position == cursor
                pipe.send_text("\x05\x15/files\r/skills\r")
                await until(lambda: broker.app.layout.current_buffer is not broker.buffer)
                assert "main.py" in output.text()
                pipe.send_text("\x1b")
                await until(lambda: broker.app.layout.current_buffer is broker.buffer)
                assert json.loads((native / "skills-disabled.json").read_text(encoding="utf-8")) == ["simplify"]
                pipe.send_text("/lang en\r/simplify\r")
                await until(lambda: "tty-complete-4" in output.text() and broker._state == "idle")
                assert "中文终端思考语言" not in captured[3]["messages"][0]["content"]
                assert captured[3]["messages"][-1]["content"] == SIMPLIFY_BODY_EN
                pipe.send_text("/lang zh\r/copy\r")
                await until(lambda: "已复制最后一条回答" in output.text())
                assert clipboard == ["tty-complete-4 若存🙂"] and len(captured) == 4
                unaccepted = "包含synthetic-runtime-key的输入"
                pipe.send_text(unaccepted + "\r")
                await until(lambda: "输入未接纳" in output.text() and broker.buffer.text == unaccepted)
                view = await opened["journal"].worker.load_recovery_view()
                assert len(view.checkpoint.accepted_inputs) == 4 and len(captured) == 4
                assert all(originalInput(item.payload) != unaccepted for item in view.checkpoint.accepted_inputs)
                pipe.send_text("\x05\x15/plan\r规划调用\r")
                await until(lambda: "tty-complete-6" in output.text() and broker._state == "idle")
                assert "推理正文始终使用简体中文" in captured[4]["messages"][0]["content"]
                pipe.send_text("\x1b[Z")
                await until(lambda: "退出只读规划后可切换权限" in output.text())
                assert broker._status_info["permMode"] == "plan"
                names = {item["function"]["name"] for item in captured[4]["tools"]}
                assert {"Write", "Bash", "SkillInstall"}.isdisjoint(names)
                assert {"MemoryRead", "MemoryWrite"} <= names
                assert not (workspace / "plan-denied.txt").exists()
                refused = [message for message in captured[5]["messages"] if message.get("tool_call_id") == "plan-write"]
                assert len(refused) == 1 and "只读规划" in refused[0]["content"]
                memory = [m["content"] for m in captured[5]["messages"] if m.get("tool_call_id") == "read-memory"]
                assert memory and "Prefer short synthetic summaries." in memory[0]
                memory_path = native / "memory" / "synthetic-note.md"
                assert memory_path.is_file()
                view = await opened["journal"].worker.load_recovery_view()
                assert all(item.intent is not None and item.intent.policy_version == "permissions-v1"
                           and item.intent.approval_ref == "gate-approved" for item in view.tool_records)
                memory_record = next(item for item in view.tool_records if item.tool_ref.tool_call_id == "write-memory")
                assert memory_record.intent is not None and memory_record.intent.side_effect
                pipe.send_text("/memory\r")
                await until(lambda: "记忆审核(共 1 条)" in output.text() and "synthetic-note" in output.text())
                pipe.send_text("/memory delete synthetic-note\r")
                await until(lambda: not memory_path.exists() and "已删除" in output.text())
                pipe.send_text("/plan\r")
                await until(lambda: broker._status_info["permMode"] == "default")
                async def reject_mode_save(self, session):
                    raise OSError("synthetic checkpoint save failure")

                with monkeypatch.context() as patch:
                    patch.setattr(runtime.Conversation, "save", reject_mode_save)
                    pipe.send_text("\x1b[Z")
                    await until(lambda: "权限切换保存失败" in output.text())
                    assert broker._status_info["permMode"] == "default"
                for mode, label in (("auto", "智能批准"), ("bypassPermissions", "全权放行"), ("auto", "智能批准")):
                    notice = f"已切换到{label}"
                    count = output.text().count(notice)
                    pipe.send_text("\x1b[Z")
                    await until(lambda: output.text().count(notice) > count)
                    assert broker._status_info["permMode"] == mode
                    assert broker._status_bar()[0] == ("class:permission-status", f"{label} 『 Shift+Tab 切换 』")
                pipe.send_text("/mode default\r")
                await until(lambda: broker._status_info["permMode"] == "default")
                pipe.send_text("/runtime-nested\r")
                await until(lambda: len(captured) == 7 and broker.app.layout.current_buffer is not broker.buffer)
                assert captured[6]["messages"][-1]["content"] == "body-from-nested-skill"
                await broker.close()
                assert await asyncio.wait_for(running, 8) == 0
                assert pipe.closed and not broker.app.is_running
                assert not (workspace / "close-denied.txt").exists()
                closed_pair = [message for message in opened["session"].messages if message.get("tool_call_id") == "close-write"]
                assert len(closed_pair) == 1
                assert opened["session"].usage["promptTokens"] == 77
                loaded = [m["content"] for m in opened["session"].messages if m.get("tool_call_id") == "load-nested"]
                assert len(loaded) == 1 and "body-from-nested-skill" in loaded[0]
                adapted = [m["content"] for m in opened["session"].messages if m.get("tool_call_id") == "load-installed"]
                assert len(adapted) == 1 and "adapted installed body" in adapted[0]
                assert len(conversions) == 1 and "`ForeignRead`" in conversions[0]["messages"][-1]["content"]
                assert conversions[0]["model"] == "glm-5.3-flash"
                cache = list((native / "skill-adapted").glob("*.md"))
                assert len(cache) == 1 and cache[0].read_text(encoding="utf-8") == "adapted installed body"
                skill_usage = json.loads((native / "skill-state" / "skill-usage.json").read_text(encoding="utf-8"))
                assert skill_usage["runtime-nested"]["count"] == skill_usage["install-demo"]["count"] == 1
                trace = next((native / "sessions").glob("*/*/skill-trace.jsonl"))
                events = [json.loads(line) for line in trace.read_text(encoding="utf-8").split("\n") if line]
                assert sorted((e["kind"], e["round"], e["name"]) for e in events) == [
                    ("loaded", 5, "install-demo"), ("loaded", 5, "runtime-nested"),
                ]
            finally:
                release.set()
                if "broker" in opened:
                    await opened["broker"].close()
                if not running.done():
                    await asyncio.wait_for(running, 8)
    asyncio.run(scenario())


def test_runtime_single_tty_owner_queue_approval_draft_snapshot_plan_and_close(tmp_path):
    # 普通入口须在首次导入sqlite3前绑定受控DLL。pytest收集其它测试时可能已导入它。
    # 子进程使用父测试实际载入的包根，源码定向和固定wheel验证走同一条接线。
    package_root = Path(ruocun.__file__).resolve().parent.parent
    home = tmp_path / "home"
    env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
           if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
               ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path))
    entry = """
import runpy
import sys
from pathlib import Path
from pytest import MonkeyPatch

sys.path.insert(0, sys.argv[1])
exercise = runpy.run_path(sys.argv[2])["_exercise_tty"]
with MonkeyPatch.context() as patch:
    exercise(Path(sys.argv[3]), patch)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", entry,
         str(package_root), str(Path(__file__).resolve()), str(tmp_path)],
        cwd=tmp_path, env=env, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
