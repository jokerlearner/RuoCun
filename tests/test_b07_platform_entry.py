"""59/62 ordinary entry boundaries; synthetic commands and wake processes only."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun


def _environment(tmp_path):
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
           if key in os.environ}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
               ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh")
    return env


@pytest.mark.skipif(sys.platform != "win32", reason="approved Windows unsupported boundary")
def test_schedule_cli_without_account_explicitly_rejects_windows(tmp_path):
    package = Path(ruocun.__file__).resolve().parent.parent
    loader = f"import runpy,sys;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", loader, "Schedule", "list"],
                            cwd=tmp_path, env=_environment(tmp_path), stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Windows" in result.stdout and "不支持" in result.stdout
    assert not (tmp_path / "home" / ".ruocun" / "config.json").exists()


def test_ordinary_registry_exports_four_schedule_tools():
    from ruocun.agent.runtime import _registry

    registry = _registry(web=False)
    assert [registry.get(name).name for name in ("Schedule", "CronCreate", "CronDelete", "CronList")] == [
        "Schedule", "CronCreate", "CronDelete", "CronList"]


def _exercise_turn_locks(tmp_path, patch):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent import runtime
    from ruocun.agent.input_broker import InputBroker
    from ruocun.agent.loop import TurnResult
    from ruocun.tui import wakelock

    home, workspace = tmp_path / "home", tmp_path / "workspace"
    workspace.mkdir()
    for variable, value in _environment(tmp_path).items():
        patch.setenv(variable, value)
    patch.setenv("RUOCUN_THEME", "dark")
    config = home / "config.json"
    config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
        "provider": "deepseek", "model": "synthetic-power-model", "key": "synthetic-power-key",
        "baseUrl": "http://127.0.0.1:1/v1"}}}), encoding="utf-8")
    locks, entered = [], []

    class Lock:
        status = "requested"
        reason = "synthetic wake lock"

        def __init__(self):
            self.releases = 0

        def __call__(self):
            self.releases += 1
            self.status = "released"

    def acquire(**_):
        lock = Lock()
        locks.append(lock)
        return lock

    async def run_turn(_session, _options, _registry, ctx, **_):
        index = len(entered)
        entered.append(index)
        assert len(locks) == index + 1 and locks[index].releases == 0
        assert all(lock.releases == 1 for lock in locks[:index])
        if index == 1:
            while not ctx.signal.is_set():
                await asyncio.sleep(.01)
            return TurnResult("cancelled")
        if index == 2:
            raise RuntimeError("synthetic turn exception")
        return TurnResult("complete")

    patch.setattr(wakelock, "acquireWakeLock", acquire)
    patch.setattr(runtime, "run_turn", run_turn)
    args = runtime._parser().parse_args(["--config", str(config), "--cwd", str(workspace),
                                        "--no-memory", "--no-skills", "--no-mcp", "--no-hooks"])

    class Output(DummyOutput):
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    async def scenario():
        output, owners = Output(), []
        with create_pipe_input() as pipe:
            def factory(pause):
                broker = InputBroker(on_pause=pause, input=pipe, output=output)
                owners.append(broker)
                return broker

            task = asyncio.create_task(runtime._run(args, broker_factory=factory))

            async def until(condition):
                async with asyncio.timeout(12):
                    while not condition():
                        if task.done():
                            raise AssertionError(f"entry exited early: {task.result()}")
                        await asyncio.sleep(.01)

            try:
                await until(lambda: "RuoCun ·" in "".join(output.parts))
                assert not locks  # Idle REPL must not acquire a session-long lock.
                for index in range(3):
                    pipe.send_text(f"synthetic-turn-{index}\r")
                    await until(lambda: len(entered) == index + 1)
                    if index == 1:
                        await owners[0]._pause()
                    await until(lambda: locks[index].releases == 1 and owners[0]._state != "running")
                    assert len(locks) == index + 1
                await until(lambda: "会话已暂停" in "".join(output.parts))
            finally:
                pipe.send_text("/exit\r")
                assert await asyncio.wait_for(task, 12) == 0
            assert [lock.releases for lock in locks] == [1, 1, 1]
            print(json.dumps({"outcomes": ["complete", "cancelled", "exception"],
                              "acquired": len(locks), "released": [lock.releases for lock in locks]}))

    asyncio.run(scenario())


def test_turn_wake_lock_released_after_complete_cancel_and_exception(tmp_path):
    package = Path(ruocun.__file__).resolve().parent.parent
    loader = """
import runpy,sys
from pathlib import Path
from pytest import MonkeyPatch
sys.path.insert(0,sys.argv[1])
exercise=runpy.run_path(sys.argv[2])["_exercise_turn_locks"]
with MonkeyPatch.context() as patch:
    exercise(Path(sys.argv[3]),patch)
"""
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", loader, str(package),
                             str(Path(__file__).resolve()), str(tmp_path)], cwd=tmp_path,
                            env=_environment(tmp_path), stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, encoding="utf-8", timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"acquired": 3, "released": [1, 1, 1]' in result.stdout
