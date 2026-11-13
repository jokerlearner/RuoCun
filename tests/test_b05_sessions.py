"""Frozen session/log.ts selection and Markdown export behavior."""

import subprocess
import sys
from pathlib import Path

import pytest

import ruocun


def test_source_first_user_excerpt_and_export_keep_unicode():
    from ruocun.session.log import exportSessionMarkdown, firstUserExcerpt

    messages = [{"role": "system", "content": "system"}, {"role": "user", "content": [{"type": "text", "text": "image"}]},
                {"role": "user", "content": "  任务🙂\n 继续  "}, {"role": "assistant", "content": "回答🙂"}]
    assert firstUserExcerpt(messages) == "任务🙂 继续"
    assert firstUserExcerpt([{"role": "user", "content": "x" * 61}]) == "x" * 60 + "…"
    assert firstUserExcerpt(messages[:2]) is None
    exported = exportSessionMarkdown({"messages": messages})
    assert "## user\n\n  任务🙂\n 继续  " in exported and "## assistant\n\n回答🙂" in exported


def test_streaming_full_export_rejects_a_scope_that_changes_during_read(tmp_path):
    from ruocun.platform.file_contract import AtomicFileError
    from ruocun.session.log import writeArchiveExport

    reads = []
    (tmp_path / ".ruocun").mkdir()
    def page(scope, offset):
        reads.append((scope, offset))
        return {"revision": 1 if len(reads) == 1 else 2, "messages": [{"role": "user", "content": "saved"}],
                "records": [], "derived": [], "attachments": [], "boundaries": [], "legacy_gap": False,
                "next_offset": None}
    with pytest.raises(AtomicFileError):
        writeArchiveExport(tmp_path, "one", ["main"], page, json_format=True)
    assert not list((tmp_path / ".ruocun" / "exports").glob("*.json"))
    assert reads


_SESSIONS = r'''
import asyncio,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[3])
from ruocun.session.log import findResumable,listSessions,loadState
from ruocun.session.prune import prune_durable_session
from ruocun.session.conversation import Conversation
from ruocun.session.runtime import verify_controlled_runtime,verify_official_archive
from ruocun.session.session import Session
root=Path(sys.argv[1]);runtime=verify_controlled_runtime(verify_official_archive(Path(sys.argv[2]),root/'dll'))

async def save(id,cwd,text,closed=False):
    session=Session('system','synthetic',env={})
    store=await Conversation.open(root/'sessions'/id,id,cwd,runtime,session,'synthetic-key',resume=False)
    try:
        if text:
            await store.accept_user(session,text)
        await store.set_foreground_state(session,'closed' if closed else 'paused')
    finally:await store.close()

async def scenario():
    (root/'sessions').mkdir()
    await save('old',root,'older question')
    await save('new',root,'newer question')
    await save('done',root,'done question',True)
    other=root/'other';other.mkdir()
    await save('other',other,'other cwd')
    await save('empty',root,'')
    metas=listSessions(root/'sessions',str(root),runtime=runtime)
    assert set(meta['id'] for meta in metas)=={'old','new','done','empty'}
    state=findResumable(root/'sessions',str(root),runtime=runtime)
    assert state['id']=='new'
    assert loadState(root/'sessions','new',runtime=runtime)['messages'][-1]['content']=='newer question'
    assert loadState(root/'sessions','../new',runtime=runtime) is None
    current=Session('system','synthetic',env={})
    store=await Conversation.open(root/'sessions'/'new','new',root,runtime,current,'synthetic-key',resume=True)
    try:
        await store.rename(current,'manual title')
        await store.replace_context(current,[current.messages[0],{'role':'user','content':'compacted task'}])
        state=loadState(root/'sessions','new',runtime=runtime)
        assert state['title']=='manual title' and state['taskTitle']=='newer question'
        await store.clear(current)
        assert loadState(root/'sessions','new',runtime=runtime)['taskTitle'] is None
        await store.accept_user(current,'next task')
        state=loadState(root/'sessions','new',runtime=runtime)
        assert state['title']=='manual title' and state['taskTitle']=='next task'
        import hashlib
        from ruocun.session.durable_store import inspect_durable_session
        attachment=root/'synthetic-attachment.bin';attachment.write_bytes(b'synthetic-image-bytes')
        digest=hashlib.sha256(attachment.read_bytes()).hexdigest()
        await store.register_background_attachment(str(attachment),digest)
        branch_id=await store.branch(current,root/'sessions',runtime,root,title='branch title')
        branch=inspect_durable_session(root/'sessions'/branch_id,runtime)
        assert branch['checkpoint']['title']=='branch title'
        assert branch['checkpoint']['task_title']=='next task'
        assert branch['checkpoint']['accepted_inputs']==[] and not branch['runs'] and not branch['tools'] and not branch['pending_events']
        # B branches carry only attachments reachable from the visible transcript.
        assert not branch['attachments']
    finally:await store.close()
    cutoff=int(time.time()*1000)+1000
    assert not prune_durable_session(root/'sessions'/'old',runtime,cutoff_ms=cutoff)
    assert prune_durable_session(root/'sessions'/'done',runtime,cutoff_ms=cutoff)
    assert not (root/'sessions'/'done').exists() and (root/'sessions'/'old'/'session.db').is_file()
asyncio.run(scenario())
'''


@pytest.mark.skipif(sys.platform != "win32", reason="uses controlled Windows SQLite")
def test_source_session_selection_uses_saved_cwd_done_and_real_user_turns(tmp_path):
    source = Path(ruocun.__file__).resolve().parents[1]
    archive = Path(__file__).parent / "fixtures/sqlite-dll-win-x64-3540100.zip"
    result = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", _SESSIONS,
                             str(tmp_path), str(archive.resolve()), str(source)],
                            capture_output=True, text=True, encoding="utf-8", timeout=35)
    assert result.returncode == 0, result.stderr + result.stdout


def test_source_session_commands_switch_branch_and_continue_through_normal_entry(tmp_path):
    import json
    import os
    import re
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    home, workspace = tmp_path / "home", tmp_path / "workspace"
    home.mkdir()
    workspace.mkdir()
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            frames = [{"choices": [{"delta": {"role": "assistant", "content": "synthetic done"}}]},
                      {"choices": [{"delta": {}, "finish_reason": "stop"}]}]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(("".join("data: " + json.dumps(frame) + "\n\n" for frame in frames)
                              + "data: [DONE]\n\n").encode())

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        config = home / "config.json"
        config.write_text(json.dumps({"version": 2, "activeProfile": "synthetic", "profiles": {"synthetic": {
            "provider": "deepseek", "model": "synthetic-parent", "key": "synthetic-b05-session-key",
            "baseUrl": f"http://127.0.0.1:{server.server_port}/v1",
        }}}), encoding="utf-8")
        env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT")
               if key in os.environ}
        env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home), LOCALAPPDATA=str(home),
                   ProgramData=str(home / "program-data"), TEMP=str(tmp_path), TMP=str(tmp_path), RUOCUN_LANG="zh")
        package = Path(ruocun.__file__).resolve().parent.parent
        loader = f"import runpy,sys;sys.path.insert(0,{str(package)!r});runpy.run_module('ruocun',run_name='__main__')"
        command = [sys.executable, "-I", "-X", "utf8", "-c", loader, "--config", str(config), "--cwd", str(workspace),
                   "--no-memory", "--no-skills", "--no-hooks", "--no-mcp", "--permission-mode", "bypassPermissions"]
        serving = threading.Thread(target=server.serve_forever, daemon=True)
        serving.start()
        try:
            first = subprocess.run(command, input="first task\n/rename manual\n/session\n/branch fork\n"
                                   "/clear\nsecond task\n/export\n/export --context --format json\n/archive list --limit 1\n/exit\n", cwd=workspace, env=env,
                                   capture_output=True, encoding="utf-8", timeout=35)
            assert first.returncode == 0, first.stdout + first.stderr
            assert "会话已命名:manual" in first.stdout
            original_id = re.search(r"当前会话:([\w-]+)", first.stdout)[1]
            branch_id = re.search(r"快照分支为 ([\w-]+)", first.stdout)[1]
            exports = list((workspace / ".ruocun" / "exports").glob("*.md"))
            assert len(exports) == 1 and "second task" in exports[0].read_text("utf-8")
            assert "first task" in exports[0].read_text("utf-8")
            assert "clear" in exports[0].read_text("utf-8")
            context_exports = list((workspace / ".ruocun" / "exports").glob("*.json"))
            assert len(context_exports) == 1
            context = json.loads(context_exports[0].read_text("utf-8"))
            assert [m["content"] for m in context["messages"] if m["role"] == "user"] == ["second task"]
            assert '"next_offset": 1' in first.stdout
            archive_id = re.search(r'"id": "([A-Za-z0-9_-]+)"', first.stdout)[1]
            resumed = subprocess.run(command, input=f"/resume {branch_id}\nresumed task\n/session\n/exit\n",
                                     cwd=workspace, env=env, capture_output=True, encoding="utf-8", timeout=35)
            assert resumed.returncode == 0, resumed.stdout + resumed.stderr
            assert f"当前会话:{branch_id}" in resumed.stdout
            explicit = subprocess.run([*command, "--continue", original_id, "/session"], cwd=workspace, env=env,
                                      capture_output=True, encoding="utf-8", timeout=20)
            assert explicit.returncode == 0 and f"当前会话:{original_id}" in explicit.stdout, explicit.stdout + explicit.stderr
            read = subprocess.run([*command, "--continue", original_id, "/archive", "read", archive_id,
                                   "--offset", "1", "--limit", "3"], cwd=workspace, env=env,
                                  capture_output=True, encoding="utf-8", timeout=20)
            assert read.returncode == 0 and '"next_offset": 4' in read.stdout, read.stdout + read.stderr
            latest = subprocess.run([*command, "--continue", "--", "/session"], cwd=workspace, env=env,
                                    capture_output=True, encoding="utf-8", timeout=20)
            assert latest.returncode == 0 and f"当前会话:{original_id}" not in latest.stdout
        finally:
            server.shutdown()
            serving.join(timeout=5)
    assert len(requests) == 3
    assert [message["content"] for message in requests[-1]["messages"] if message["role"] == "user"] == ["first task", "resumed task"]


def test_cleanup_retains_clean_owned_worktree_named_by_retained_agent(tmp_path, monkeypatch):
    import os
    import shutil

    from ruocun.agent import cleanup as cleanup_module
    from ruocun.agent.worktree import createWorktree

    git = Path("D:/study_software/Git/cmd/git.exe")
    if git.is_file():
        monkeypatch.setenv("PATH", str(git.parent) + os.pathsep + os.environ["PATH"])
    elif not shutil.which("git"):
        pytest.skip("Git unavailable")
    root = tmp_path / "synthetic repo"
    root.mkdir()
    for arguments in (["init", "-q"], ["config", "user.name", "Synthetic"],
                      ["config", "user.email", "synthetic@example.invalid"]):
        subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)
    (root / "a.txt").write_text("base", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True, capture_output=True)
    tree = createWorktree(root, "protected")
    assert tree is not None
    os.utime(tree.root, (1, 1))
    sessions = tmp_path / "sessions"
    kept = sessions / "retained"
    kept.mkdir(parents=True)
    (kept / "session.db").write_text("synthetic inspection port", encoding="utf-8")
    monkeypatch.setattr(cleanup_module, "inspect_durable_session", lambda *_args: {
        "checkpoint": {"messages": []}, "attachments": {}, "owner_alive": False, "done": False,
        "updated_at": 1, "runs": [{"snapshot": {"recovery_material": {"worktree": str(tree.root)}}}],
    })
    result = cleanup_module.cleanup(root, 1, 10 * cleanup_module.DAY,
                                    sessions_dir=sessions, runtime=None, environ=dict(os.environ))
    assert Path(tree.root).is_dir() and result.worktreesReclaimed == 0
    tree.cleanup()
