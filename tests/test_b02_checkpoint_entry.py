"""27 ordinary terminal commands against a synthetic Git workspace."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from test_b02_worktree import repo as repo

import ruocun


def _exercise(home, workspace, patch):
    from prompt_toolkit.input import create_pipe_input
    from prompt_toolkit.output import DummyOutput

    from ruocun.agent import runtime
    from ruocun.agent.input_broker import InputBroker
    from ruocun.agent.runtime_context import isRuntimeContext
    from ruocun.client.resilient import ResilientResult

    class Output(DummyOutput):
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    native = home / ".ruocun"
    native.mkdir(parents=True)
    (native / "settings.json").write_text('{"checkpoint":{"enabled":true}}', encoding="utf-8")
    config = home / "config.json"
    config.write_text(json.dumps({"version": 2, "activeProfile": "default", "profiles": {"default": {
        "provider": "deepseek", "model": "synthetic-checkpoint-model", "key": "synthetic-checkpoint-key",
        "baseUrl": "http://127.0.0.1:1/v1"}}}), encoding="utf-8")
    for variable in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "ProgramData"):
        patch.setenv(variable, str(home))
    patch.setenv("RUOCUN_THEME", "dark")
    requests = []

    def request(options, *, env, context):
        messages = options["messages"]
        requests.append(messages)
        task_messages = [item for item in messages if not isRuntimeContext(item)]
        users = [item["content"] for item in task_messages if item["role"] == "user"]
        if task_messages[-1]["role"] == "user":
            name = "Write" if len(users) == 1 else "Edit"
            arguments = {"path": "a.txt", "content": users[-1]} if name == "Write" else {
                "path": "a.txt", "old_string": users[-2], "new_string": users[-1]}
            call = {"id": "write-" + users[-1], "type": "function", "function": {"name": name,
                    "arguments": json.dumps(arguments)}}
            read = {"id": "read-" + users[-1], "type": "function", "function": {"name": "Read",
                    "arguments": '{"path":"a.txt"}'}}
            message, finish = {"role": "assistant", "content": "", "tool_calls": [read, call]}, "tool_calls"
        else:
            message, finish = {"role": "assistant", "content": "finished-" + users[-1]}, "stop"
        return ResilientResult("complete", [], message, None, finish, [], {})

    patch.setattr(runtime, "streamChatResilient", request)
    args = runtime._parser().parse_args(["--config", str(config), "--cwd", str(workspace),
                                        "--no-memory", "--no-skills", "--yolo"])

    async def scenario():
        output, owners = Output(), []
        with create_pipe_input() as pipe:
            def factory(pause):
                broker = InputBroker(on_pause=pause, input=pipe, output=output)
                owners.append(broker)
                return broker

            task = asyncio.create_task(runtime._run(args, broker_factory=factory))

            async def until(expected):
                async with asyncio.timeout(12):
                    while expected not in "".join(output.parts):
                        if task.done():
                            raise AssertionError(f"startup exited before {expected!r}, code {task.result()}")
                        await asyncio.sleep(.01)

            try:
                await until("RuoCun ·")
                pipe.send_text("synthetic-first\r")
                await until("finished-synthetic-first")
                pipe.send_text("synthetic-second\r")
                await until("finished-synthetic-second")
                assert (workspace / "a.txt").read_text("utf-8") == "synthetic-second"
                pipe.send_text("/rewind 2 code\r")
                await until("已回退到第 2 条用户消息之前")
                assert (workspace / "a.txt").read_text("utf-8") == "synthetic-first"
                pipe.send_text("/restore\r")
                await until("工作区已恢复到")
                assert (workspace / "a.txt").read_text("utf-8") == "synthetic-second"
                pipe.send_text("/diff\r")
                await until("变更文件")
                pipe.send_text("/exit\r")
                assert await asyncio.wait_for(task, 12) == 0
                assert len(requests) == 4
            finally:
                if not task.done():
                    for owner in owners:
                        await owner.close()
                    await asyncio.wait_for(task, 12)

    asyncio.run(scenario())


def test_rewind_code_and_restore_preserve_real_git_history(repo, tmp_path):
    workspace, git = repo
    head, index = git("rev-parse", "HEAD"), (workspace / ".git/index").read_bytes()
    package = Path(ruocun.__file__).resolve().parent.parent
    entry = (f"import sys\nsys.path[:0]=[{str(package)!r}, {str(Path(__file__).parent)!r}]\n"
             "from pathlib import Path\nfrom pytest import MonkeyPatch\n"
             "from test_b02_checkpoint_entry import _exercise\n"
             "with MonkeyPatch.context() as patch:\n _exercise(Path(sys.argv[1]), Path(sys.argv[2]), patch)")
    child = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "-c", entry, str(tmp_path / "home"), str(workspace)],
                           env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                           capture_output=True, text=True, encoding="utf-8", timeout=55)
    assert child.returncode == 0, child.stdout + child.stderr
    assert git("rev-parse", "HEAD") == head and (workspace / ".git/index").read_bytes() == index
