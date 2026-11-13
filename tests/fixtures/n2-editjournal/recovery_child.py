"""Run real Read/Edit/Write through the foreground loop at REC-05 boundaries."""

import asyncio
import json
import sys
import threading
from pathlib import Path
from unittest.mock import patch

from ruocun.agent.loop import run_turn
from ruocun.client.resilient import ResilientResult
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.conversation import Conversation
from ruocun.session.durable_store import DurableStore
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive
from ruocun.session.session import Session
from ruocun.tools import edit_file, write_file
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import ToolContext

CALL_ID = "change"
PATH = "target.txt"
OLD = "before\n"
NEW = "after\n"


def call(call_id, name, raw):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": raw}}


def reply(content, tool_call=None):
    message = {"role": "assistant", "content": content}
    if tool_call is not None:
        message["tool_calls"] = [tool_call]
    return ResilientResult(status="complete", deltas=[], message=message, usage=None,
                           finish_reason="stop", attempts=[], request_body={}, error=None)


class CutJournal:
    def __init__(self, conversation, park):
        self.conversation, self.park = conversation, park

    async def save(self, session):
        await self.conversation.save(session)

    async def intent(self, call_id, name, args, effect):
        if call_id == CALL_ID:
            self.park("before-intent")
        result = await self.conversation.intent(call_id, name, args, effect)
        if call_id == CALL_ID:
            self.park("after-intent")
        return result

    async def result(self, call_id, text, image_data=None):
        if call_id == CALL_ID:
            self.park("before-result")
        await self.conversation.result(call_id, text, image_data)
        if call_id == CALL_ID:
            self.park("after-result")


async def exercise(root, archive, cut, tool_name, reopen_number):
    reopening = reopen_number > 0
    workspace = root / "workspace"
    target = workspace / PATH
    runtime = verify_controlled_runtime(verify_official_archive(archive, root / "dll"))
    expected_args = {"path": PATH}
    if tool_name == "Write":
        expected_args["content"] = NEW
    else:
        expected_args.update(old_string=OLD, new_string=NEW)
    raw = json.dumps(expected_args, separators=(",", ":"))

    def park(at):
        if reopening or cut != at:
            return
        pending = root / "ready.tmp"
        pending.write_text(at, encoding="utf-8")
        pending.replace(root / "ready")
        threading.Event().wait(25)
        raise RuntimeError("owned probe process did not receive termination at the requested boundary")

    target_module = write_file if tool_name == "Write" else edit_file
    real_atomic = target_module.atomicWrite

    def observed_atomic(path, text):
        real_atomic(path, text)
        with (root / "effects.log").open("a", encoding="utf-8", newline="\n") as log:
            log.write(tool_name + "\n")
        park("after-effect")

    target_module.atomicWrite = observed_atomic

    class ObservedRegistry(ToolRegistry):
        async def dispatch(self, name, raw_args, ctx):
            if name == tool_name:
                with (root / "dispatch.log").open("a", encoding="utf-8", newline="\n") as log:
                    log.write(name + "\n")
            return await super().dispatch(name, raw_args, ctx)

    registry = ObservedRegistry()
    for tool in (readFileTool, edit_file.editFileTool, write_file.writeFileTool):
        registry.register(tool)
    session = Session("SYS", "synthetic", env={})
    conversation = await Conversation.open(root / "session", "editjournal", workspace, runtime,
                                           session, "", resume=reopening)
    try:
        async def ask(_text):
            raise AssertionError("fixture permissions already allow the tools")

        async def legacy_approval(_name, _args):
            raise AssertionError("ordinary permission runtime must decide")

        rules = emptyPermissions()
        rules["allow"] = ["Read", "Edit", "Write"]
        permissions = await createPermissionRuntime(
            workspace, root / "native-user", Compatibility(1, ()), session, rules, ask,
            interactive=False, env={"ProgramData": str(root / "program-data")},
        )

        async def turn(replies, journal, ctx=None):
            scripted = iter(replies)
            return await run_turn(
                session, {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic", "model": session.model},
                registry, ctx if ctx is not None else ToolContext(str(workspace)),
                approve=legacy_approval, authorize=permissions.authorize,
                permission_mode=permissions.getMode, request=lambda _opts, _ctx: next(scripted), journal=journal,
            )

        if not reopening:
            await conversation.accept_user(session, "合成文件编辑恢复验证")
            await turn([
                reply("", call("read", "Read", json.dumps({"path": PATH}))),
                reply("", call(CALL_ID, tool_name, raw)),
                reply("完成"),
            ], CutJournal(conversation, park))
            raise AssertionError("requested cut was not reached")

        view = await conversation.worker.load_recovery_view()
        records = {record.tool_ref.tool_call_id: record for record in view.tool_records}
        assert records["read"].state == "result_committed"
        pairs = [m["content"] for m in session.messages if m.get("tool_call_id") == CALL_ID]
        checked = "reopened"
        if cut == "before-intent":
            assert CALL_ID not in records and not conversation.blocked
            assert len(pairs) == 1 and "未执行" in pairs[0]
            state = "not_started"
            if reopen_number == 3:
                # Same source execute_durable case: the real intent transaction
                # hits SQLite query_only and the tool handler never starts.
                import sqlite3

                failure_id = "failed-intent"
                commit_intent = DurableStore.commit_intent

                def reject_intent(store, owner, intent):
                    assert intent.tool_ref.tool_call_id == failure_id
                    connection = store._con
                    assert connection is not None
                    connection.execute("PRAGMA query_only=ON")
                    try:
                        return commit_intent(store, owner, intent)
                    finally:
                        connection.execute("PRAGMA query_only=OFF")

                ctx = ToolContext(str(workspace))
                await readFileTool.handler({"path": PATH}, ctx)
                with patch.object(DurableStore, "commit_intent", reject_intent):
                    try:
                        await turn([reply("", call(failure_id, tool_name, raw))], conversation, ctx)
                    except sqlite3.OperationalError as exc:
                        assert "readonly" in str(exc)
                    else:
                        raise AssertionError("read-only SQLite did not reject the real intent transaction")
                failed_view = await conversation.worker.load_recovery_view()
                assert all(record.tool_ref.tool_call_id != failure_id for record in failed_view.tool_records)
                checked = "failed-intent-before-dispatch"
        elif cut == "after-result":
            assert not conversation.blocked
            record = records[CALL_ID]
            assert record.state == "result_committed"
            assert pairs == [record.result]
            assert await conversation.intent(CALL_ID, tool_name, raw, True) == record.result
            state = record.state
            if reopen_number == 3:
                # Repeat the same source tool ID through the real foreground
                # loop after observing the single recovered pair.
                completed = await turn([reply("", call(CALL_ID, tool_name, raw)), reply("完成")], conversation)
                assert completed.status == "complete"
                assert session.messages[-2]["content"] == record.result
                checked = "cached-foreground-result"
        else:
            assert conversation.blocked and not pairs
            record = records[CALL_ID]
            assert record.state == "outcome_unknown" and record.result is None
            try:
                await conversation.intent("different-id", tool_name, raw, True)
            except RuntimeError as exc:
                assert "未确认" in str(exc)
            else:
                raise AssertionError("unknown side effect did not block a new call ID")
            state = record.state

        # Load the persisted record and check real bytes independently on each process reopen.
        effect_happened = cut in {"after-effect", "before-result", "after-result"}
        assert target.read_bytes() == (NEW if effect_happened else OLD).encode()
        print(json.dumps({"cut": cut, "state": state, "blocked": conversation.blocked,
                          "pairs": len(pairs), "changed": effect_happened, "checked": checked}), flush=True)
    finally:
        await conversation.close()


if __name__ == "__main__":
    asyncio.run(exercise(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5])))
