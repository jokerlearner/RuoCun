"""Frozen execute.test.ts batch assertions at the foreground turn boundary."""

import asyncio
import copy

import pytest
from test_mvp_loop import Model, approve, call, reply, run

from ruocun.agent.loop import run_turn
from ruocun.config.compat import Compatibility
from ruocun.permissions.runtime import createPermissionRuntime
from ruocun.permissions.settings import emptyPermissions
from ruocun.session.contract import StoreError
from ruocun.session.session import Session
from ruocun.tools.read_file import readFileTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.schema import objectSchema
from ruocun.tools.todo_write import todoWriteTool
from ruocun.tools.types import Tool, ToolContext


def test_source_requests_one_batch_for_asks_keeps_order_and_excludes_hard_deny(tmp_path):
    # execute.test.ts:59–93. Capture the real PermissionGate batch below the
    # stdin renderer, which may ask a separate question for each request.
    async def scenario():
        from ruocun.tools.tool_batch import BatchCall

        answers, checked = iter(["y", "n"]), []

        async def ask(prompt):
            checked.append(prompt)
            return next(answers)

        cfg = {**emptyPermissions(), "defaultMode": "default", "deny": ["Write(locked.txt)"]}
        session = Session("SYS", "m", env={})
        runtime = await createPermissionRuntime(
            tmp_path, tmp_path / "user", Compatibility(1, ()), session, cfg,
            ask, interactive=True, env={"ProgramData": str(tmp_path / "program")},
        )
        requests = []

        async def prompt(batch):
            requests.append(batch)
            return {"write-1": "once", "write-2": "deny"}

        runtime.gate.prompt = prompt
        schema = objectSchema({"path": {"type": "string"}}, ["path"])
        read = Tool("Read", "", schema, "read", "auto", ask)
        write = Tool("Write", "", schema, "write", "required", ask)
        first = '{ "path": "one.txt" }'
        second = '{"path":"two.txt"}'
        out = await runtime.authorizeBatch([
            BatchCall("read", read, '{"path":"a.txt"}'),
            BatchCall("write-1", write, first),
            BatchCall("locked", write, '{"path":"locked.txt"}'),
            BatchCall("write-2", write, second),
        ])
        assert out == {"read": True, "write-1": True, "locked": False, "write-2": False}
        assert [[(item["id"], item["argsJson"]) for item in group] for group in requests] == [
            [("write-1", first), ("write-2", second)],
        ]

        # The ordinary path checks twice inside one tool and must ask again in
        # the next worker even if both workers use the same outside path.
        external = str(tmp_path.parent / "outside.txt")
        with runtime.callScope():
            assert await runtime.approveExternalRead(external)
            assert await runtime.approveExternalRead(external)

            async def sibling():
                with runtime.callScope():
                    return await runtime.approveExternalRead(external)

            assert not await asyncio.create_task(sibling())
            assert await runtime.approveExternalRead(external)
        assert len(checked) == 2
        assert all(external in prompt for prompt in checked)

    asyncio.run(scenario())


def test_source_read_group_cap_and_write_barriers_keep_results_in_request_order():
    # execute.test.ts:127–151 and RUN-05. The first Read yields twice to
    # distinguish its completion order from its tool result position.
    active = 0
    peak = 0
    completed = []
    durable_plan_started_with = []
    ctx = ToolContext("synthetic-workspace")
    registry = ToolRegistry()

    async def read(args, call_ctx):
        nonlocal active, peak
        assert call_ctx.readFiles is ctx.readFiles and call_ctx.readMeta is ctx.readMeta
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        if args["n"] == 0:
            await asyncio.sleep(0)
        active -= 1
        completed.append(f"read-{args['n']}")
        if args["n"] == 0:
            raise RuntimeError("synthetic read failure")
        return "read"

    async def write(args, call_ctx):
        if args["n"] == 2:
            durable_plan_started_with.append(active)
        assert active == 0
        assert call_ctx is ctx
        await asyncio.sleep(0)
        completed.append(f"write-{args['n']}")
        return "write"

    schema = objectSchema({"n": {"type": "integer"}}, ["n"])
    registry.register(Tool("Read", "", schema, "read", "auto", read))
    registry.register(Tool("Write", "", schema, "write", "required", write))
    registry.register(Tool("MemoryWrite", "", schema, "plan", "auto", write, persistentEffect=True))
    registry.register(todoWriteTool)
    calls = [call('{"n":0}', "Write", "write-0")]
    calls.extend(call(f'{{"n":{n}}}', "Read", f"read-{n}") for n in range(9))
    calls.append(call('{"todos":[{"content":"verify","status":"in_progress"}]}', "TodoWrite", "todo"))
    calls.append(call('{"n":2}', "MemoryWrite", "memory"))
    calls.append(call('{"n":1}', "Write", "write-1"))
    session = Session("SYS", "m", env={})
    model = Model([reply(calls=calls), reply("done")])
    journal = Journal()

    assert run(session, model, registry, context=ctx, journal=journal).status == "complete"
    assert peak == 8
    assert durable_plan_started_with == [0]
    assert journal.intents["memory"] == ("MemoryWrite", '{"n":2}', True)
    assert completed[0] == "write-0" and completed[-1] == "write-1"
    assert completed[1] != "read-0"
    assert ctx.todos == [{"content": "verify", "status": "in_progress"}]
    assert model.requests[0]["parallelToolCalls"] is True
    pairs = [message for message in model.requests[1]["messages"] if message["role"] == "tool"]
    assert [message["tool_call_id"] for message in pairs] == [item["id"] for item in calls]
    assert pairs[1]["content"] == "Error: 工具读取失败（RuntimeError）。"


class Journal:
    def __init__(self):
        self.checkpoint = []
        self.intents = {}
        self.results = {}

    async def save(self, session):
        self.checkpoint = copy.deepcopy(session.messages)

    async def intent(self, call_id, name, raw, effect):
        assert call_id in {call["id"] for call in self.checkpoint[-1]["tool_calls"]}
        assert call_id not in self.intents
        self.intents[call_id] = (name, raw, effect)

    async def result(self, call_id, text, image=None):
        assert call_id in self.intents
        self.results[call_id] = (text, copy.deepcopy(image))

    async def replace_context(self, session, messages, *, reset_prompt=True):
        assert reset_prompt is False
        session.messages = messages
        await self.save(session)


def test_source_all_settled_drains_started_tools_before_propagating_storage_failure():
    # execute.ts:239–257 and RUN-05. A failed approval must not mask an
    # in-flight tool's failed receipt or let the foreground leave early.
    async def scenario():
        reading, failure, finish = asyncio.Event(), asyncio.Event(), asyncio.Event()
        registry = ToolRegistry()

        async def read(args, ctx):
            if args["path"] == "third":
                reading.set()
            await finish.wait()
            return args["path"]

        async def authorize(tool, raw):
            if raw == '{"path":"first"}':
                await reading.wait()
                failure.set()
                raise RuntimeError("synthetic approval failure")
            return True

        class FailingJournal(Journal):
            async def result(self, call_id, text, image=None):
                if call_id == "second":
                    raise StoreError("synthetic result receipt failure")
                await super().result(call_id, text, image)

        async def write(args, ctx):
            pytest.fail("a write cannot start after a failed receipt")

        registry.register(Tool("Read", "", readFileTool.schema, "read", "auto", read))
        registry.register(Tool("Write", "", objectSchema({}, []), "write", "required", write))
        journal = FailingJournal()
        model = Model([reply(calls=[
            call('{"path":"first"}', call_id="first"),
            call('{"path":"second"}', call_id="second"),
            call('{"path":"third"}', call_id="third"),
            call("{}", "Write", "write"),
        ])])
        task = asyncio.create_task(run_turn(
            Session("SYS", "m", env={}), {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic-key", "model": "m"},
            registry, ToolContext("synthetic-workspace"), approve=approve, request=model, journal=journal,
            authorize=authorize,
        ))
        try:
            await asyncio.wait_for(failure.wait(), timeout=2)
            done, _ = await asyncio.wait({task}, timeout=0.02)
            assert not done
        finally:
            # Release a first approval even if a serial regression prevents
            # its siblings from entering the handlers.
            reading.set()
            finish.set()
            with pytest.raises(StoreError, match="synthetic result receipt failure"):
                await task
        assert journal.results == {"third": ("third", None)}
        assert set(journal.intents) == {"second", "third"}
        assert journal.checkpoint[-1]["role"] == "assistant"

    asyncio.run(scenario())


def test_real_read_images_commit_in_call_order_before_publishing_batch_boundary(tmp_path):
    # Adapt the existing N0 frozen execute/loop image fixture to two actual
    # parallel Read calls, with a text Read to catch a leaked image slot.
    (tmp_path / "one.png").write_bytes(b"\x89PNG")
    (tmp_path / "two.jpg").write_bytes(b"\xff\xd8")
    (tmp_path / "plain.txt").write_text("fixture", encoding="utf-8")
    registry = ToolRegistry()
    registry.register(readFileTool)
    session = Session("SYS", "glm-5.3-flash", env={})
    calls = [call('{ "path": "one.png" }', call_id="one"),
             call('{"path":"plain.txt"}', call_id="plain"),
             call('{"path":"two.jpg"}', call_id="two")]
    model = Model([reply(calls=calls), reply("done")])
    journal = Journal()
    ctx = ToolContext(str(tmp_path))
    approved, boundaries = [], []

    async def authorize_batch(batch):
        approved.append([(call.call_id, call.raw_args) for call in batch])
        return {call.call_id: True for call in batch}

    async def tool_boundary():
        assert journal.checkpoint == session.messages
        assert len(journal.results) == 3
        boundaries.append(copy.deepcopy(journal.checkpoint[-1]))

    assert run(session, model, registry, context=ctx, journal=journal,
               authorize_batch=authorize_batch, on_tool_boundary=tool_boundary).status == "complete"
    assert approved == [[(item["id"], item["function"]["arguments"]) for item in calls]]
    assert list(journal.intents.values()) == [
        ("Read", item["function"]["arguments"], False) for item in calls
    ]
    assert journal.results["one"][1] == {"base64": "iVBORw==", "mediaType": "image/png"}
    assert journal.results["two"][1] == {"base64": "/9g=", "mediaType": "image/jpeg"}
    assert journal.results["plain"][1] is None
    assert ctx.currentImageData is None
    assert len(boundaries) == 1
    assert [part["image_url"]["url"] for part in boundaries[0]["content"][:-1]] == [
        "data:image/png;base64,iVBORw==", "data:image/jpeg;base64,/9g=",
    ]
