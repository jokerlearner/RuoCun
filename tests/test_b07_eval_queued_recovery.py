"""Resume a real accepted queue after its disk skill channel is disabled."""

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from importlib.resources import as_file, files
from pathlib import Path

from test_b07_platform_entry import _environment

import ruocun


def _exercise(workspace):
    from ruocun.agent import runtime
    from ruocun.client.resilient import ResilientResult
    from ruocun.platform.windows.durable_file import ensure_private_dir
    from ruocun.session.conversation import Conversation
    from ruocun.session.inputs import originalInput
    from ruocun.session.runtime import (
        verify_controlled_runtime,
        verify_official_archive,
    )
    from ruocun.session.session import Session

    native = Path.home() / ".ruocun"
    config = Path.home() / "config.json"
    secret, model = "synthetic-eval-queue-key", "synthetic-eval-queue-model"
    config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
        "provider": "deepseek", "model": model, "key": secret,
        "baseUrl": "http://127.0.0.1:1/v1"}}}), encoding="utf-8")
    disk_skill = native / "skills" / "synthetic-old-skill" / "SKILL.md"
    disk_skill.parent.mkdir(parents=True)
    body = "synthetic disk expansion that should never reach the resumed model"
    disk_skill.write_text(f"---\nname: synthetic-old-skill\ndescription: synthetic skill\n---\n{body}\n", encoding="utf-8")
    scope = hashlib.sha256(os.path.normcase(str(workspace)).encode("utf-8")).hexdigest()[:20]
    sessions = native / "sessions"
    ensure_private_dir(sessions)
    ensure_private_dir(sessions / scope)
    session_id = "synthetic-old-queued"
    directory = sessions / scope / session_id
    archive = files("ruocun").joinpath("resources/runtime/sqlite-dll-win-x64-3540100.zip")
    with as_file(archive) as archive_path:
        dll = verify_official_archive(archive_path, native / "runtime" / "sqlite-3.54.1")
    sqlite_runtime = verify_controlled_runtime(dll)
    original = "/synthetic-old-skill"

    async def prepare():
        session = Session("synthetic previous system", model, env={})
        session.addUser("synthetic retained user")
        session.messages.append({"role": "assistant", "content": "synthetic retained assistant"})
        conversation = await Conversation.open(directory, session_id, workspace, sqlite_runtime, session, secret, resume=False)
        try:
            assert conversation.foreground_state == "idle"
            return await conversation.queue_user(session, original, model_content=body)
        finally:
            await conversation.close()

    queued = asyncio.run(prepare())
    requests = []

    def request(options, **_):
        requests.append(options["messages"][-1]["content"])
        return ResilientResult("complete", [], {"role": "assistant", "content": "synthetic unexpected request"},
                               None, "stop", [], {})

    runtime.streamChatResilient = request
    code = runtime.run_cli(["--config", str(config), "--cwd", str(workspace), "--eval", "--continue", session_id])
    assert requests == [], requests
    assert code == 0, code

    async def verify():
        session = Session("unused", model, env={})
        conversation = await Conversation.open(directory, session_id, workspace, sqlite_runtime, session, secret, resume=True)
        try:
            checkpoint = (await conversation.worker.load_recovery_view()).checkpoint
            assert checkpoint is not None and len(checkpoint.accepted_inputs) == 1
            record = checkpoint.accepted_inputs[0]
            assert record.state == "discarded" and record.input_id == queued.input_id
            assert record.payload == queued.payload and originalInput(record.payload) == original
            assert [item["content"] for item in checkpoint.messages[1:]] == [
                "synthetic retained user", "synthetic retained assistant"]
        finally:
            await conversation.close()

    asyncio.run(verify())


def test_eval_discards_old_disk_skill_projection_without_model_request(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    package = Path(ruocun.__file__).resolve().parent.parent
    loader = """
import runpy, sys
from pathlib import Path
sys.path[:0] = [sys.argv[1], str(Path(sys.argv[2]).parent)]
runpy.run_path(sys.argv[2])["_exercise"](Path(sys.argv[3]).resolve())
"""
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", loader, str(package),
                             str(Path(__file__).resolve()), str(workspace)], cwd=workspace,
                            env=_environment(tmp_path), input="", capture_output=True,
                            text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[已跳过排队输入]" in result.stdout
