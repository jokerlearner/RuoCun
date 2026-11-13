"""66必要普通入口接缝；复用原TTY/回环，合成账户且不访问系统钥匙串。"""
import asyncio
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from ruocun.agent import runtime
from ruocun.agent.input_broker import InputBroker
from ruocun.config.credential import MemoryKeychain
from ruocun.platform.file_contract import DurabilityUnconfirmedError
from ruocun.platform.windows.durable_file import ensure_private_dir
from ruocun.session.session import Session


def _exercise_account_runtime(tmp_path, monkeypatch, unknown_save, recover_rate_limit=False):
    captured, requests = [], []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            raw = json.dumps({"data": [{"id": "gpt-6-astra"}, {"id": "synthetic-custom-model"}]}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            captured.append((self.path, self.headers.get("Authorization"), body["model"]))
            if recover_rate_limit and len(captured) == 1:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":{"message":"synthetic rate limit"}}')
                return
            message = f"synthetic-account-reply-{len(captured)}"
            frames = [{"choices": [{"delta": {"content": message}}]},
                      {"choices": [{"delta": {}, "finish_reason": "stop"}]}]
            raw = ("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames) + "data: [DONE]\n\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    serving = threading.Thread(target=server.serve_forever)
    serving.start()

    class Output(DummyOutput):
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    async def scenario():
        home, workspace = tmp_path / "home", tmp_path / "workspace"
        ensure_private_dir(home)
        workspace.mkdir()
        for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            monkeypatch.setenv(key, str(home))
        monkeypatch.setenv("ProgramData", str(home / "program-data"))
        monkeypatch.setenv("RUOCUN_LANG", "zh")
        monkeypatch.setenv("RUOCUN_THEME", "dark")
        retained_system_secret = ("ruocun-api-key", "ruocun/personal")
        malformed_origin_secret = ("ruocun-api-key", "ruocun/invalid-metadata")
        keychain = MemoryKeychain({retained_system_secret: "synthetic-preserved-system-key",
                                   malformed_origin_secret: "synthetic-preserved-malformed-origin-key"})
        monkeypatch.setattr(runtime.credential, "createKeychain", lambda env: keychain)
        config = home / "config.json"
        base = f"http://127.0.0.1:{server.server_port}"
        cfg = {"version": 2, "activeProfile": "personal", "profiles": {
            "personal": {"provider": "deepseek", "baseUrl": base + "/a", "model": "deepseek-v4-pro", "key": "synthetic-account-key-a"},
            "work": {"provider": "openai", "baseUrl": base + "/b", "model": "gpt-6-astra",
                     "key": "synthetic-account-key-b", "keyRef": "keychain:ruocun/personal"},
            "invalid-metadata": {"provider": "openai", "baseUrl": base + "/b", "model": "gpt-6-astra",
                                 "keyRef": "keychain:ruocun/invalid-metadata"},
        }, "_ruocun": {"credentialOrigins": {
            "work": {"keyRef": "keychain:ruocun/personal", "service": "ruocun-api-key"},
            "invalid-metadata": [],
        }}}
        original_save = runtime.profiles_store.saveProfiles
        original_save(config, cfg)
        if unknown_save:
            def publish_unconfirmed(file, value):
                original_save(file, value)
                raise DurabilityUnconfirmedError("synthetic post-publication uncertainty")
            monkeypatch.setattr(runtime.profiles_store, "saveProfiles", publish_unconfirmed)
        original_request = runtime.streamChatResilient

        def request(options, **kwargs):
            requests.append((options["provider"], options["baseUrl"], options["apiKey"], options["model"]))
            return original_request(options, **kwargs)
        monkeypatch.setattr(runtime, "streamChatResilient", request)
        opened, output = {}, Output()
        original_open = runtime.Conversation.open

        async def open_conversation(*args, **kwargs):
            conversation = await original_open(*args, **kwargs)
            opened.update(conversation=conversation, session=args[4], runtime=args[3])
            return conversation
        monkeypatch.setattr(runtime.Conversation, "open", open_conversation)
        args = runtime._parser().parse_args(["--config", str(config), "--cwd", str(workspace), "--no-memory", "--no-skills"])
        with create_pipe_input() as pipe:
            def factory(pause):
                broker = InputBroker(on_pause=pause, input=pipe, output=output)
                opened["broker"] = broker
                return broker
            running = asyncio.create_task(runtime._run(args, broker_factory=factory))

            async def until(check):
                async with asyncio.timeout(12):
                    while not check():
                        assert not running.done(), "ordinary runtime exited before expected boundary"
                        await asyncio.sleep(.01)

            try:
                await until(lambda: "RuoCun ·" in "".join(output.parts))
                pipe.send_text("first synthetic input\r")
                broker = opened["broker"]
                if recover_rate_limit:
                    await until(lambda: broker._modal is not None and "切到账号「work」重试" in broker._dialog_text())
                    assert len(captured) == 1
                    pipe.send_text("2")
                    await until(lambda: "synthetic-account-reply-2" in "".join(output.parts))
                    assert captured == [("/a/chat/completions", "Bearer synthetic-account-key-a", "deepseek-v4-pro"),
                                        ("/b/chat/completions", "Bearer synthetic-account-key-b", "gpt-6-astra")]
                    assert len(requests) == 2 and not keychain.calls
                    assert json.loads(config.read_text("utf-8"))["activeProfile"] == "work"
                    pipe.send_text("/exit\r")
                    assert await asyncio.wait_for(running, 12) == 0
                    return
                await until(lambda: "synthetic-account-reply-1" in "".join(output.parts))
                pipe.send_text("/account\r")
                await until(lambda: broker._modal is not None and "work" in broker._dialog_text())
                pipe.send_text("\x1b[B\r")
                if unknown_save:
                    assert await asyncio.wait_for(running, 12) == 74
                    assert len(captured) == len(requests) == 1
                    assert opened["conversation"].blocked
                    assert json.loads(config.read_text("utf-8"))["activeProfile"] == "work"
                    saved = opened["conversation"]
                    restored = await original_open(saved.directory, saved.session_id, workspace, opened["runtime"],
                        Session("SYS", "deepseek-v4-pro", env={}), "synthetic-account-key-a", resume=True)
                    try:
                        assert restored.blocked
                    finally:
                        await restored.close()
                else:
                    await until(lambda: broker._modal is None and broker._status_info.get("model") == "gpt-6-astra")
                    pipe.send_text("after account switch\r")
                    await until(lambda: "synthetic-account-reply-2" in "".join(output.parts))
                    pipe.send_text("/model\r")
                    await until(lambda: broker._modal is not None and "synthetic-custom-model" in broker._dialog_text())
                    pipe.send_text("\x1b[B\r")
                    await until(lambda: broker._modal is None and "Model: synthetic-custom-model" in "".join(output.parts))
                    pipe.send_text("after model switch\r")
                    await until(lambda: "synthetic-account-reply-3" in "".join(output.parts))
                    pipe.send_text("/account rm work\r")
                    await until(lambda: "本进程沿用原连接" in "".join(output.parts))
                    removed = json.loads(config.read_text("utf-8"))
                    assert removed["activeProfile"] == "personal" and "work" not in removed["profiles"]
                    assert keychain.secrets[retained_system_secret] == "synthetic-preserved-system-key"
                    pipe.send_text("/account rm invalid-metadata\r")
                    await until(lambda: "invalid-metadata" not in json.loads(config.read_text("utf-8"))["profiles"])
                    assert keychain.secrets[malformed_origin_secret] == "synthetic-preserved-malformed-origin-key"
                    pipe.send_text("after active removal\r")
                    await until(lambda: "synthetic-account-reply-4" in "".join(output.parts))
                    pipe.send_text("/account switch personal\r")
                    await until(lambda: broker._status_info.get("model") == "deepseek-v4-pro")
                    pipe.send_text("after manual switch\r")
                    await until(lambda: "synthetic-account-reply-5" in "".join(output.parts))
                    pipe.send_text("/exit\r")
                    assert await asyncio.wait_for(running, 12) == 0
                    assert requests == [("deepseek", base + "/a", "synthetic-account-key-a", "deepseek-v4-pro"),
                                        ("openai", base + "/b", "synthetic-account-key-b", "gpt-6-astra"),
                                        ("openai", base + "/b", "synthetic-account-key-b", "synthetic-custom-model"),
                                        ("openai", base + "/b", "synthetic-account-key-b", "synthetic-custom-model"),
                                        ("deepseek", base + "/a", "synthetic-account-key-a", "deepseek-v4-pro")]
                    assert captured == [("/a/chat/completions", "Bearer synthetic-account-key-a", "deepseek-v4-pro"),
                                        ("/b/chat/completions", "Bearer synthetic-account-key-b", "gpt-6-astra"),
                                        ("/b/chat/completions", "Bearer synthetic-account-key-b", "synthetic-custom-model"),
                                        ("/b/chat/completions", "Bearer synthetic-account-key-b", "synthetic-custom-model"),
                                        ("/a/chat/completions", "Bearer synthetic-account-key-a", "deepseek-v4-pro")]
                    final = json.loads(config.read_text("utf-8"))
                    assert final["activeProfile"] == "personal" and "work" not in final["profiles"]
                assert not keychain.calls
                assert all(key not in "".join(output.parts) for key in ("synthetic-account-key-a", "synthetic-account-key-b"))
            finally:
                if "broker" in opened:
                    await opened["broker"].close()
                if not running.done():
                    await asyncio.wait_for(running, 12)
    try:
        asyncio.run(scenario())
    finally:
        server.shutdown()
        server.server_close()
        serving.join(timeout=5)
        assert not serving.is_alive()


@pytest.mark.parametrize(("unknown_save", "recover_rate_limit"), [(False, False), (True, False), (False, True)],
                         ids=["manual-switch", "save-unknown", "rate-limit-switch"])
def test_real_account_model_requests_and_unknown_save_preserves_scene(tmp_path, unknown_save, recover_rate_limit):
    source = Path(__file__).resolve().parents[1] / "src"
    entry = (f"import sys\nsys.path.insert(0,{str(source)!r})\nsys.path.insert(0,{str(Path(__file__).parent)!r})\n"
             "from pathlib import Path\nfrom pytest import MonkeyPatch\n"
             "from test_b02_account_runtime import _exercise_account_runtime\n"
             "with MonkeyPatch.context() as patch:\n"
             f" _exercise_account_runtime(Path(sys.argv[1]),patch,{unknown_save!r},{recover_rate_limit!r})")
    result = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", entry, str(tmp_path)],
                            capture_output=True, text=True, encoding="utf-8", timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr


def test_notify_user_consumes_frozen_execution_environment(monkeypatch):
    from ruocun.tools.notify_user import notifyUserTool
    from ruocun.tools.types import ToolContext
    monkeypatch.setenv("RUOCUN_NO_NOTIFY", "0")
    sent = []
    ctx = ToolContext("/synthetic", notifyUser=sent.append, notificationEnv={"RUOCUN_NO_NOTIFY": "1"})
    result = asyncio.run(notifyUserTool.handler({"message": "synthetic disabled notice"}, ctx))
    assert not sent and "终端提示未发送" in result and "未发送桌面" in result
