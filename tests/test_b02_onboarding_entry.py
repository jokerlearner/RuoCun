"""ENT-02 through the ordinary startup with one InputBroker and a loopback key probe."""

import asyncio
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ruocun


def _exercise(tmp_path, patch):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent import runtime
    from ruocun.agent.input_broker import InputBroker
    from ruocun.config.credential import UnavailableKeychain

    probes = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            probes.append((self.path, self.headers.get("Authorization")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"data":[]}')

        def log_message(self, *args):
            pass

    class Output(DummyOutput):
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    root = tmp_path / "home"
    work = tmp_path / "project"
    root.mkdir()
    (work / ".ruocun").mkdir(parents=True)
    (work / ".ruocun/settings.json").write_text('{"permissions":{"defaultMode":"plan"}}', encoding="utf-8")
    (work / ".env").write_text("RUOCUN_OWNED_TERMINAL=1\n", encoding="utf-8")
    patch.delenv("RUOCUN_OWNED_TERMINAL", raising=False)
    patch.delenv("DAO_OWNED_TERMINAL", raising=False)
    for var in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "ProgramData"):
        patch.setenv(var, str(root))
    patch.setenv("RUOCUN_THEME", "dark")
    patch.setenv("LANG", "en_US")
    patch.setattr(runtime.credential, "createKeychain", lambda env: UnavailableKeychain())
    config = root / ".ruocun/config.json"
    settings = config.with_name("settings.json")
    trusted = config.with_name("trusted.json")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}/v1"
    patch.setitem(runtime.DEFAULTS, "deepseek", {**runtime.DEFAULTS["deepseek"], "baseUrl": base})
    args = runtime._parser().parse_args(["--cwd", str(work), "--no-memory", "--no-skills"])

    async def launch(*, first):
        output, owners = Output(), []
        with create_pipe_input() as pipe:
            def factory(pause):
                broker = InputBroker(on_pause=pause, input=pipe, output=output)
                owners.append(broker)
                return broker

            task = asyncio.create_task(runtime._run(args, broker_factory=factory))

            async def until(predicate):
                async with asyncio.timeout(10):
                    while not predicate():
                        if task.done():
                            raise AssertionError(f"startup returned {task.result()} before expected state")
                        await asyncio.sleep(.01)

            def modal_text():
                return owners[0]._dialog_text() if owners and owners[0]._approval is not None else ""

            try:
                if first:
                    await until(lambda: "Select language" in modal_text())
                    pipe.send_text("\x1b[A\r")
                    await until(lambda: "DeepSeek" in modal_text())
                    pipe.send_text("\r")
                    await until(lambda: owners[0]._secret_answer)
                    assert not config.exists() and not settings.exists() and not trusted.exists()
                    pipe.send_text("synthetic-b02-onboarding-key\r")
                    await until(lambda: "hooks.json" in modal_text())
                    assert config.is_file() and not settings.exists() and not trusted.exists()
                    pipe.send_text("y")
                await until(lambda: bool(owners and owners[0]._status_info.get("model")))
                assert len(owners) == 1 and owners[0]._status_info["permMode"] == "plan"
                assert not owners[0]._owned_viewport, "A project file cannot claim a shared terminal viewport."
                assert runtime.getLang() == "zh"
                pipe.send_text("/exit\r")
                assert await asyncio.wait_for(task, 10) == 0
                assert not owners[0].app.is_running
                assert "synthetic-b02-onboarding-key" not in "".join(output.parts)
            finally:
                if not task.done():
                    for owner in owners:
                        await owner.close()
                    await asyncio.wait_for(task, 10)

    async def scenario():
        await launch(first=True)
        saved = json.loads(config.read_text(encoding="utf-8"))
        assert saved["onboardingComplete"] and saved["profiles"]["default"]["baseUrl"] == base
        assert json.loads(settings.read_text(encoding="utf-8"))["lang"] == "zh"
        assert json.loads(trusted.read_text(encoding="utf-8")) == [str(work.resolve())]
        await launch(first=False)
        assert probes == [("/v1/models", "Bearer synthetic-b02-onboarding-key")]

    try:
        asyncio.run(scenario())
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_ent02_onboarding_saves_then_reuses_account_language_and_trust(tmp_path):
    package = Path(ruocun.__file__).resolve().parent.parent
    entry = (f"import sys\nsys.path[:0]=[{str(package)!r}, {str(Path(__file__).parent)!r}]\n"
             "from pathlib import Path\nfrom pytest import MonkeyPatch\n"
             "from test_b02_onboarding_entry import _exercise\n"
             "with MonkeyPatch.context() as patch:\n _exercise(Path(sys.argv[1]), patch)")
    child = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", entry, str(tmp_path)],
                           capture_output=True, text=True, encoding="utf-8", timeout=45)
    assert child.returncode == 0, child.stdout + child.stderr
