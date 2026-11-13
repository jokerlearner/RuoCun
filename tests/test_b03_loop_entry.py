"""Frozen App.tsx /loop on the ordinary input owner with a synthetic model."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

import ruocun
from ruocun.agent import runtime
from ruocun.agent.input_broker import InputBroker
from ruocun.client.resilient import ResilientResult


def _exercise_loop(tmp_path, monkeypatch):
    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "ProgramData"):
        monkeypatch.setenv(name, str(home))
    monkeypatch.setenv("RUOCUN_THEME", "dark")
    monkeypatch.setenv("RUOCUN_LANG", "zh")
    config = home / "config.json"
    config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
        "provider": "deepseek", "model": "synthetic-loop-model", "key": "synthetic-loop-key",
        "baseUrl": "http://127.0.0.1:1/v1"}}}), encoding="utf-8")
    requests = []

    def request(options, **_):
        requests.append(options["messages"][-1]["content"])
        return ResilientResult("complete", [], {"role": "assistant", "content": "synthetic loop answer"},
                               None, "stop", [], {})

    monkeypatch.setattr(runtime, "streamChatResilient", request)
    args = runtime._parser().parse_args(["--config", str(config), "--cwd", str(workspace), "--no-memory", "--no-skills"])

    class Output(DummyOutput):
        parts: list[str]

        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    async def scenario():
        output = Output()
        with create_pipe_input() as pipe:
            def factory(pause):
                return InputBroker(on_pause=pause, input=pipe, output=output)

            task = asyncio.create_task(runtime._run(args, broker_factory=factory))

            async def until(text):
                async with asyncio.timeout(10):
                    while text not in "".join(output.parts):
                        if task.done():
                            raise AssertionError(f"ordinary entry exited before {text!r}: {task.result()}")
                        await asyncio.sleep(.01)

            try:
                await until("RuoCun ·")
                pipe.send_text("/loop 1s synthetic   periodic input\r")
                await until("已开启循环")
                assert not requests
                await until("synthetic loop answer")
                pipe.send_text("/loop off\r")
                await until("已停止循环")
                await asyncio.sleep(1.1)
                assert requests == ["synthetic periodic input"]
            finally:
                pipe.send_text("/exit\r")
                assert await asyncio.wait_for(task, 10) == 0

    asyncio.run(scenario())


def test_loop_ordinary_entry_stops_future_requests(tmp_path):
    # Bind the controlled SQLite DLL before other tests import the system SQLite.
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
exercise = runpy.run_path(sys.argv[2])["_exercise_loop"]
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
