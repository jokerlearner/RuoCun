"""DAO deck_messages.test.ts and deck_bridge.test.ts, using the public loopback protocol."""

import asyncio
import json
import threading
from dataclasses import dataclass
from pathlib import Path

import httpx

from ruocun.agent.background_runtime import BackgroundRuntime
from ruocun.agent.deck_bridge import DeckBridge, DeckOptions
from ruocun.agent.deck_messages import messagePage
from ruocun.agent.runtime_context import buildRuntimeContext
from ruocun.agent.session_scheduler import SessionScheduler
from ruocun.session.contract import AcceptedInput
from ruocun.session.session import Session
from ruocun.tools.types import ToolContext
from ruocun.tui.render import plainEvents


def test_deck_message_projection_hides_system_and_image_payloads():
    messages = [
        {"role": "system", "content": "private instruction"},
        buildRuntimeContext(ToolContext("synthetic-runtime")),
        {"role": "user", "content": [{"type": "text", "text": "配图"}, {"type": "image_url", "image_url": "private bytes"}]},
        {"role": "assistant", "content": "长" * 24001, "tool_calls": [
            {"id": "tool", "function": {"name": "Read", "arguments": "x" * 12001}},
        ]},
        {"role": "tool", "tool_call_id": "tool", "content": "完成"},
    ]
    page = messagePage(messages, 2, 1)
    assert page["pagination"]["total"] == 3
    assert (page["pagination"]["start"], page["pagination"]["end"], page["pagination"]["nextBefore"]) == (1, 2, 1)
    projected = page["messages"][0]
    assert projected["index"] == 1
    assert len(projected["content"]) == 24000 and projected["contentTruncated"]
    assert len(projected["toolCalls"][0]["args"]) == 12000 and projected["toolCalls"][0]["argsTruncated"]
    assert messagePage(messages, 1)["messages"][0]["content"] == "配图\n[图片附件 · 请在原终端查看]"
    assert messagePage(messages)["messages"][-1]["toolCallId"] == "tool"
    assert messagePage([*messages, {"role": "user", "content": "new"}])["pagination"]["revision"] == page["pagination"]["revision"]
    assert "private" not in json.dumps(messagePage(messages), ensure_ascii=False)


@dataclass
class Outcome:
    status: str = "complete"
    error: str = ""


def test_deck_loopback_auth_commands_and_session_scoping(tmp_path):
    async def scenario():
        queue = []
        messages = []
        session = Session("private system", "synthetic-model")
        runtime = BackgroundRuntime(workspaceRoot=tmp_path)
        held = asyncio.Event()
        released = asyncio.Event()
        run_signals = []
        mode = ["default"]
        uncertain = []
        rejected = set()

        async def queue_user(text):
            if text == "unconfirmed":
                uncertain.append(text)
                raise RuntimeError("synthetic unknown write")
            item = AcceptedInput(str(len(messages) + len(queue)), len(queue), '{}', (), 'queued')
            queue.append((item, text))
            return item

        async def consume_user(input_id):
            item, value = queue.pop(0)
            assert item.input_id == input_id
            if input_id in rejected:
                deck.input(input_id, False)
                return False
            deck.input(input_id, True)
            session.addUser(value)
            messages.append(value)
            return True

        async def discard_queued(_reason):
            queue.clear()

        async def set_state(_state):
            pass

        async def run(signal: threading.Event, _boundary, _generation):
            run_signals.append(signal)
            if messages[-1] == "hold":
                held.set()
                await released.wait()
            return Outcome("cancelled" if signal.is_set() else "complete")

        scheduler = SessionScheduler(
            queued_inputs=lambda: tuple(item for item, _text in queue), queue_user=queue_user,
            consume_user=consume_user, discard_queued=discard_queued, set_state=set_state, run=run,
        )
        home = tmp_path / "deck"
        deck = await DeckBridge.start(DeckOptions(
            scheduler, session, runtime, Path(tmp_path), "synthetic-version", True,
            lambda: [], lambda: [], lambda: mode[0], lambda new: mode.__setitem__(0, new),
        ), env={"RUOCUN_DECK": "1", "RUOCUN_DECK_MANAGED": "1", "AGENT_DECK_HOME": str(home)})
        assert deck is not None
        record_path, = (home / "agents").glob("*.json")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        url = f"http://127.0.0.1:{record['port']}"
        auth = {"Authorization": "Bearer " + record["token"]}
        async with httpx.AsyncClient(base_url=url, trust_env=False) as client:
            async def command(name, kind, **payload):
                return await client.post("/command", headers=auth, json={
                    "id": name, "type": kind, "sessionId": runtime.sessionId, **payload,
                })

            async def snapshot():
                response = await client.get("/snapshot", headers=auth)
                assert response.status_code == 200
                assert response.headers["Cache-Control"] == "no-store"
                return response.json()

            try:
                assert (await client.get("/snapshot")).status_code == 403
                assert (await client.get("/snapshot", headers={**auth, "Origin": "http://127.0.0.1"})).status_code == 403
                assert (await client.get("/messages?before=-1", headers=auth)).status_code == 400
                assert (await command("mode", "permission", mode="plan")).status_code == 200
                assert (await snapshot())["permissionMode"] == "plan"
                assert (await command("unsafe-slash", "message", text="/yolo")).status_code == 400
                first, duplicate = await asyncio.gather(command("first", "message", text="first"), command("first", "message", text="first"))
                assert first.json() == duplicate.json() == {"id": "first", "status": "queued"}
                assert (await command("first", "message", text="other")).status_code == 409
                await scheduler.settled()
                assert messages == ["first"]
                assert (await snapshot())["receipts"][0]["status"] == "consumed"

                await scheduler.submit("hold")
                await asyncio.wait_for(held.wait(), 2)
                terminal = await scheduler.submit("same text")
                assert terminal is not None
                rejected.add(terminal.input_id)
                assert (await command("same-text", "message", text="same text")).status_code == 200
                released.set()
                await scheduler.settled()
                assert messages.count("same text") == 1
                assert (await snapshot())["receipts"][-1]["status"] == "consumed"
                held.clear()
                released.clear()

                first_answer = asyncio.create_task(deck.question("source first"))
                second_answer = asyncio.create_task(deck.question("source second"))
                await asyncio.sleep(0)
                attention = (await snapshot())["attention"]
                assert attention["text"] == "source first"
                assert (await command("blocked-mode", "permission", mode="bypassPermissions")).status_code == 409
                assert (await command("first-answer", "answer", promptId=attention["id"], text="yes")).status_code == 200
                assert await first_answer == "yes"
                assert (await snapshot())["attention"]["text"] == "source second"

                child_stop = threading.Event()
                child_answer = asyncio.create_task(deck.approve([{"id": "child", "summary": "child only", "toolName": "Bash", "capability": "exec"}], cancelled=child_stop.is_set))
                await asyncio.sleep(0)
                child_stop.set()
                assert await asyncio.wait_for(child_answer, 1) == {"child": "deny"}
                assert (await snapshot())["attention"]["text"] == "source second"

                old_session = runtime.sessionId
                runtime.sessionId = "new-session"
                session.messages.clear()
                assert "attention" not in await snapshot()
                assert await second_answer == "[用户中断]"
                assert (await command("old", "message", sessionId=old_session, text="old command")).status_code == 409
                assert (await snapshot())["receipts"] == []

                assert (await command("running", "message", text="hold")).status_code == 200
                await asyncio.wait_for(held.wait(), 2)
                assert (await command("queued", "message", text="waiting")).status_code == 200
                assert (await command("pause", "pause")).status_code == 200
                released.set()
                await scheduler.settled()
                assert run_signals[-1].is_set()
                assert (await snapshot())["receipts"][-1]["status"] == "canceled"

                output = []
                events = deck.events(plainEvents(output.append))
                events.reasoning("思考")
                events.content("正文")
                assert (await snapshot())["live"] == "正文"
                events.toolStart({"index": 0, "name": "Read"})
                events.toolResult({"id": "read", "function": {"name": "Read"}}, {"role": "tool", "content": "结果"})
                events.assistantDone({"role": "assistant", "content": "正文"})
                streamed = await snapshot()
                assert streamed["live"] == ""
                assert [event["kind"] for event in streamed["events"]] == ["tool_start", "tool_result"]
                assert output

                # User-approved recovery rule: keep an ambiguous mutation from replaying by command ID.
                unknown = await command("uncertain", "message", text="unconfirmed")
                assert unknown.status_code == 400
                assert (await command("uncertain", "message", text="unconfirmed")).json() == unknown.json()
                assert (await command("uncertain", "message", text="different")).status_code == 409
                assert uncertain == ["unconfirmed"]
                assert (await snapshot())["receipts"][-1]["status"] == "unknown"
            finally:
                released.set()
                await deck.close()
                assert not record_path.exists()

    asyncio.run(scenario())
