"""首版来源断言：loop.test.ts 33/53/74/409/691/778及execute的拒绝分支。"""

import asyncio
import copy
import json
from dataclasses import replace

import pytest

from ruocun.agent.loop import run_turn
from ruocun.client.resilient import ResilientResult
from ruocun.session.session import Session
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.types import Tool, ToolContext


def reply(content="", calls=None, *, error=None):
    message = {"role": "assistant", "content": content}
    if calls:
        message["tool_calls"] = calls
    return ResilientResult(
        status="failed" if error else "complete", deltas=[], message=message,
        usage=None, finish_reason="stop", attempts=[], request_body={}, error=error,
    )


def call(raw='{"path":"a.txt"}', name="Read", call_id="call-1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": raw}}


class Model:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.requests = []

    def __call__(self, opts, context):
        self.requests.append(copy.deepcopy(opts))
        return next(self.replies)


class Registry:
    def __init__(self, capability="read"):
        self.executed = []

        async def handler(args, ctx):
            self.executed.append(args)
            return "1\tcode"

        self.tool = Tool("Read", "read", {"type": "object"}, capability, "auto", handler)

    def get(self, name):
        return self.tool if name == "Read" else None

    def toApiTools(self):
        return [{"type": "function", "function": {"name": "Read", "parameters": self.tool.schema}}]

    def validate(self, name, rawArgs):
        if self.get(name) is None:
            raise ValueError("unknown tool")
        args = json.loads(rawArgs)
        if not isinstance(args, dict):
            raise ValueError("object required")
        return args

    async def dispatch(self, name, rawArgs, ctx):
        return await self.tool.handler(self.validate(name, rawArgs), ctx)


async def approve(name, args):
    return True


def run(session, model, registry=None, approval=approve, context=None, **kwargs):
    return asyncio.run(run_turn(
        session, {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic-key", "model": session.model},
        registry or Registry(), context or ToolContext("synthetic-workspace"), approve=approval, request=model,
        **kwargs,
    ))


def test_reply_is_appended_without_tools():
    session = Session("SYS", "m", env={})
    session.addUser("hi")
    result = run(session, Model([reply("answer")]))
    assert result.status == "complete"
    assert session.messages[-1] == {"role": "assistant", "content": "answer"}


def test_source_health_failure_is_not_pardoned_by_a_write_and_child_nudges_locally():
    async def written(args,ctx):
        return 'written'

    async def failed(args,ctx):
        return 'Error: unchanged synthetic error'

    async def scenario(child):
        session = Session('SYS', 'm', env={})
        session.addUser('synthetic task')
        registry=ToolRegistry()
        registry.register(Tool('Write','write',{'type':'object'},'write','auto',written))
        registry.register(Tool('Read','read',{'type':'object'},'read','auto',failed))
        model=Model([*[reply(calls=[call('{}','Write',f'w{i}'),call('{}','Read',f'r{i}')]) for i in range(3)],reply('done')])
        kinds=[]

        async def reflect(kind):
            kinds.append(kind)
            return 'synthetic challenger verdict'

        result=await run_turn(session,{'baseUrl':'http://127.0.0.1:1','apiKey':'synthetic','model':'m'},
            registry,ToolContext('synthetic-workspace'),approve=approve,request=model,
            reflect=None if child else reflect,self_challenge=child,
            model_recovery_env={'RUOCUN_FAIL_STREAK':'3','RUOCUN_REPEAT_ERR':'99'})
        assert result.status=='complete'
        tail=[m['content'] for m in session.messages[1:] if m['role']=='system']
        assert len(tail)==1
        assert kinds==([] if child else ['challenger'])
        assert ('synthetic challenger verdict' in tail[0]) != child
        assert all(len([m for m in request['messages'] if m.get('role')=='tool'])%2==0 for request in model.requests)
    asyncio.run(scenario(False))
    asyncio.run(scenario(True))


def test_scheduler_boundary_waits_for_tool_pair_and_old_request_delta_is_ignored():
    # 迁移scheduler安全边界/迟到流语义到Python请求线程的必要接线，复用原Read回合。
    async def scenario():
        session = Session("SYS", "m", env={})
        session.addUser("hi" + "x" * 900)
        callbacks, rendered, requests, settled = [], [], [], []

        def model(opts, context):
            requests.append(opts)
            callbacks.append(context.on_delta)
            if len(requests) == 1:
                raise RuntimeError("maximum context length exceeded")
            if len(requests) == 2:
                context.on_delta({"kind": "content", "text": "current-first"})
                return reply(calls=[call()])
            callbacks[1]({"kind": "content", "text": "late-old"})
            context.on_delta({"kind": "content", "text": "current-second"})
            return replace(reply("done"), usage={"prompt_tokens": 5, "completion_tokens": 2})

        async def boundary():
            if len(requests) == 2:
                assert session.messages[-1]["role"] == "tool"
                assert settled == [session.messages[-1]["tool_call_id"]]
                session.addUser("queued-at-boundary")

        async def tool_boundary():
            assert len(requests) == 2 and session.messages[-1]["role"] == "tool"
            settled.append(session.messages[-1]["tool_call_id"])

        async def compact():
            callbacks[0]({"kind": "content", "text": "late-during-compact"})
            await asyncio.sleep(0)
            session.messages = [session.messages[0], {"role": "system", "content": "saved summary"},
                                *session.messages[2:]]

        result = await run_turn(
            session, {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic-key", "model": "m"},
            Registry(), ToolContext("synthetic-workspace"), approve=approve, request=model,
            on_boundary=boundary, on_tool_boundary=tool_boundary,
            accepts_delta=lambda: True, on_delta=lambda delta: rendered.append(delta["text"]),
            compact=compact,
        )
        callbacks[-1]({"kind": "content", "text": "late-after-return"})
        await asyncio.sleep(0)
        assert result.status == "complete"
        assert requests[2]["messages"][-1]["content"] == "queued-at-boundary"
        assert rendered == ["current-first", "current-second"]
        assert session.usage["promptTokens"] == 5

    asyncio.run(scenario())


def test_plan_switch_in_batch_blocks_write_before_dispatch_and_trims_next_api():
    from ruocun.tools.plan_mode import enterPlanModeTool
    from ruocun.tools.tools_for_mode import apiToolsForMode

    registry, executed = ToolRegistry(), []

    async def write(args, ctx):
        executed.append(True)
        return "written"

    registry.register(enterPlanModeTool)
    registry.register(Tool("Write", "write", {"type": "object", "properties": {}}, "write", "auto", write))
    session = Session("SYS", "m", env={})
    ctx = ToolContext("synthetic-workspace", setMode=lambda mode: setattr(session, "mode", mode))
    model = Model([reply(calls=[call("{}", "EnterPlanMode", "plan"), call("{}", "Write", "write")]), reply("done")])

    async def allow_batch(batch):
        assert session.mode == "normal"
        assert [item.call_id for item in batch] == ["plan", "write"]
        # 派发硬门不依赖预批恰好拒绝，源plan约束在工具批内即时生效。
        return {item.call_id: True for item in batch}

    assert run(session, model, registry, context=ctx, authorize_batch=allow_batch,
               permission_mode=lambda: "plan" if session.mode == "plan" else "default",
               api_tools=lambda: apiToolsForMode(registry, session.mode)).status == "complete"
    assert executed == []
    assert "Write" not in [tool["function"]["name"] for tool in model.requests[1]["tools"]]
    assert "规划" in session.messages[-2]["content"]


def test_three_empty_replies_are_not_saved():
    session = Session("SYS", "m", env={})
    session.addUser("hi")
    model = Model([reply(), reply(), reply()])
    assert run(session, model).status == "failed"
    assert len(model.requests) == 3
    assert len(session.messages) == 2


def test_retry_empty_then_use_real_reply():
    session = Session("SYS", "m", env={})
    model = Model([reply(), reply("real")])
    assert run(session, model).status == "complete"
    assert session.messages[-1]["content"] == "real"
    assert [o["extra"]["reasoning_effort"] for o in model.requests] == ["max", "max"]
    assert all("maxTokens" not in o for o in model.requests)


def test_tools_are_executed_and_followup_uses_session_model():
    session = Session("SYS", "chosen-model", env={})
    registry = Registry()
    model = Model([reply(calls=[call()]), reply("done")])
    assert run(session, model, registry).status == "complete"
    assert registry.executed == [{"path": "a.txt"}]
    assert model.requests[1]["model"] == "chosen-model"
    assert model.requests[1]["messages"][-1] == {
        "role": "tool", "tool_call_id": "call-1", "content": "1\tcode",
    }


def test_invalid_json_is_not_executed_and_history_is_sanitized():
    session = Session("SYS", "m", env={})
    registry = Registry()
    assert run(session, Model([reply(calls=[call('{"path":')]), reply("fixed")]), registry).status == "complete"
    assert registry.executed == []
    assert session.messages[-3]["tool_calls"][0]["function"]["arguments"] == "{}"
    assert "Error" in session.messages[-2]["content"]


def test_denied_write_is_paired_without_side_effect():
    async def deny(name, args):
        return False

    session = Session("SYS", "m", env={})
    registry = Registry("write")
    assert run(session, Model([reply(calls=[call()]), reply("denied")]), registry, deny).status == "complete"
    assert registry.executed == []
    assert session.messages[-2]["tool_call_id"] == "call-1"
    assert "拒绝" in session.messages[-2]["content"]


def test_context_limit_stops_with_history_preserved():
    session = Session("SYS", "m", env={})
    session.addUser("keep")
    result = run(session, Model([reply(error="maximum context length exceeded")]))
    assert result.status == "context_limit"
    assert "新会话" in result.error
    assert session.messages[-1] == {"role": "user", "content": "keep"}


def test_source_assistant_reasoning_fields_survive_tool_followup():
    # client.test/Responses已有来源语义：工具后续请求必须保留推理现场。
    session = Session("SYS", "m", env={})
    first = reply(calls=[call()])
    first.message["reasoningContent"] = "synthetic reasoning"
    first.message["responseItems"] = [{"type": "reasoning", "id": "r1", "encrypted_content": "synthetic"}]
    model = Model([first, reply("done")])
    assert run(session, model).status == "complete"
    assistant = model.requests[1]["messages"][-2]
    assert assistant["reasoningContent"] == "synthetic reasoning"
    assert assistant["responseItems"] == first.message["responseItems"]


def test_failed_exec_skips_later_effects_in_same_batch():
    # 冻结execute.test.ts:169-186，使用首版Bash真实的exit/运行时间文本格式。
    registry = ToolRegistry()
    executed = []

    async def handler(args, ctx):
        executed.append(args["n"])
        return "boom\n[exit 1,运行 0s]" if args["n"] == 1 else "ok [exit 0,运行 0s]"

    schema = {"type": "object", "properties": {"n": {"type": "number"}}}
    registry.register(Tool("Bash", "", schema, "exec", "required", handler))
    registry.register(Tool("Read", "", schema, "read", "auto", handler))
    registry.register(Tool("Write", "", schema, "write", "required", handler))
    session = Session("SYS", "m", env={})
    model = Model([reply(calls=[call('{"n":1}', "Bash", "a"), call('{"n":2}', "Bash", "b"),
                                call('{"n":3}', "Read", "r"), call('{"n":4}', "Write", "w")]), reply("fixed")])
    assert run(session, model, registry).status == "complete"
    assert executed == [1, 3]
    pairs = {message["tool_call_id"]: message["content"] for message in session.messages if message["role"] == "tool"}
    assert "已跳过" in pairs["b"] and "已跳过" in pairs["w"]


def test_source_in_turn_compaction_runs_between_tool_rounds():
    # 冻结loop.test.ts §4，首轮不压，工具配对后进入第二轮才压。
    compacted = []
    session = Session("SYS", "m", env={})
    session.addUser("old source material " * 100)

    async def compact():
        compacted.append(True)
        # B requires an actual projection replacement before another model request.
        session.messages = [session.messages[0], {"role": "system", "content": "saved summary"},
                            *session.messages[2:]]

    model = Model([reply(calls=[call()]), reply("done")])
    assert run(session, model,
               compact=compact, should_compact=lambda: True).status == "complete"
    assert compacted == [True]


def test_source_max_turns_stops_after_two_tool_rounds():
    # 冻结loop.test.ts stops at maxTurns；不在到达上限后再请求模型。
    model = Model([reply(calls=[call(call_id="a")]), reply(calls=[call(call_id="b")])])
    result = run(Session("SYS", "m", env={}), model, max_turns=2)
    assert result.status == "turn_limit"
    assert len(model.requests) == 2


def test_source_empty_reasoning_retries_with_note_low_effort_and_escalated_budget():
    # frozen loop.test.ts:94–180；首请求自然档，耗尽后单档加预算。
    seen = []

    def model(opts, context):
        seen.append(copy.deepcopy(opts))
        if len(seen) == 1:
            opts["onEmptyTruncation"]()
            return reply()
        return reply("收敛后的结论")

    session = Session("SYS", "deepseek-v4-pro", env={})
    session.addUser("hi")
    assert run(session, model).status == "complete"
    assert seen[0]["extra"]["reasoning_effort"] == "max"
    assert seen[1]["extra"]["reasoning_effort"] == "low"
    assert "maxTokens" not in seen[0] and seen[1]["maxTokens"] == 256000
    assert session.messages[-2]["role"] == "system"
    guidance = session.messages[-2]["content"]
    assert "耗完预算" in guidance and "先发出一条工具调用" in guidance
    assert "Bash" in guidance and "Write" in guidance


def test_source_forced_tools_restore_after_unsupported_choice():
    # frozen loop.test.ts:180–380，网关拒绝required后退回原始全量工具。
    registry = ToolRegistry()

    async def handler(args, ctx):
        return "ok"

    for name in ("Read", "Skill", "TodoWrite", "Write", "Bash"):
        registry.register(Tool(name, "", {"type": "object"}, "read", "auto", handler))
    seen = []

    def model(opts, context):
        seen.append(copy.deepcopy(opts))
        if len(seen) == 1:
            opts["onEmptyTruncation"]()
            return reply()
        if len(seen) == 2:
            raise ValueError("tool_choice is not supported")
        return reply("回退后的回答")

    session = Session("SYS", "m", env={})
    assert run(session, model, registry).status == "complete"
    assert seen[1]["extra"]["tool_choice"] == "required"
    assert [t["function"]["name"] for t in seen[1]["tools"]] == ["Write", "Bash"]
    assert "tool_choice" not in seen[2]["extra"]
    assert [t["function"]["name"] for t in seen[2]["tools"]] == ["Read", "Skill", "TodoWrite", "Write", "Bash"]


def test_source_exhausted_reasoning_has_only_two_escalated_retries():
    seen = []

    def model(opts, context):
        seen.append(copy.deepcopy(opts))
        opts["onEmptyTruncation"]()
        return reply()

    assert run(Session("SYS", "m", env={}), model).status == "failed"
    assert len(seen) == 3
    assert [o.get("maxTokens") for o in seen] == [None, 256000, 256000]


def test_source_resume_sanitizes_bad_calls_and_keeps_other_messages():
    from ruocun.agent.loop import sanitizeHistoryForResume

    messages = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": None, "tool_calls": [call('{"content":"半截没写完')]},
        {"role": "tool", "tool_call_id": "call-1", "content": "Error: invalid JSON arguments for Write"},
    ]
    cleaned = sanitizeHistoryForResume(messages)
    assert cleaned[2]["tool_calls"][0]["function"]["arguments"] == "{}"
    assert [m for m in cleaned if m["role"] != "assistant"] == [m for m in messages if m["role"] != "assistant"]


def test_source_resume_keeps_valid_json_history_unchanged():
    from ruocun.agent.loop import sanitizeHistoryForResume

    messages = [{"role": "assistant", "content": None, "tool_calls": [call('{"path":"a.ts"}')]}]
    assert sanitizeHistoryForResume(messages) == messages


@pytest.mark.parametrize(("headless", "done", "include_todo", "expected"), [
    (True, False, False, []),
    (True, False, True, ["TodoWrite", "Read"]),
    (True, True, False, ["Read"]),
    (False, False, False, ["Read"]),
    (True, None, False, ["Read"]),
])
def test_source_headless_five_enforcement_cases(headless, done, include_todo, expected):
    # frozen execute.test.ts:318–374，原五条；不另加排列。
    registry, executed = ToolRegistry(), []
    for name in ("Read", "TodoWrite"):
        async def handler(args, ctx, label=name):
            executed.append(label)
            return "TODO_OK" if label == "TodoWrite" else "READ"

        registry.register(Tool(name, "", {"type": "object"}, "read", "auto", handler))
    context = ToolContext("synthetic-workspace", headless=headless,
                          todoWriteRequired=None if done is None else {"done": done})
    calls = ([call("{}", "TodoWrite", "a")] if include_todo else []) + [call("{}", "Read", "b")]
    session = Session("SYS", "m", env={})
    assert run(session, Model([reply(calls=calls), reply("done")]), registry,
               context=context).status == "complete"
    assert executed == expected
    if headless and done is False and not include_todo:
        assert "[操作被拒绝]" in session.messages[-2]["content"]
    if context.todoWriteRequired is not None:
        assert context.todoWriteRequired["done"] is (True if headless and include_todo else done)


def test_source_successful_forced_tool_turn_restores_normal_request():
    # frozen loop.test.ts预算重试工具集收敛用例的第三请求正常恢复。
    registry = ToolRegistry()

    async def handler(args, ctx):
        return "ok"

    for name in ("Read", "Skill", "TodoWrite", "Write", "Bash"):
        registry.register(Tool(name, "", {"type": "object"}, "read", "auto", handler))
    seen = []

    def model(opts, context):
        seen.append(copy.deepcopy(opts))
        if len(seen) == 1:
            opts["onEmptyTruncation"]()
            return reply()
        return reply(calls=[call("{}", "Write")]) if len(seen) == 2 else reply("done")

    assert run(Session("SYS", "m", env={}), model, registry).status == "complete"
    assert [t["function"]["name"] for t in seen[1]["tools"]] == ["Write", "Bash"]
    assert "tool_choice" not in seen[2]["extra"] and "maxTokens" not in seen[2]
    assert seen[2]["extra"]["reasoning_effort"] == "max"
    assert "Skill" in [t["function"]["name"] for t in seen[2]["tools"]]



def test_source_actual_request_prefix_attributes_tool_catalog_cache_drop():
    session = Session("SYS", "m", env={})
    drops = []
    session.onCacheBust(drops.append)
    first = replace(reply("", [call()]), usage={"prompt_tokens": 8000, "prompt_cache_hit_tokens": 7900})
    second = replace(reply("done"), usage={"prompt_tokens": 8000, "prompt_cache_hit_tokens": 200})
    model = Model([first, second])
    catalog = [{"type": "function", "function": {"name": "Read", "parameters": {"type": "object"}}}]
    catalogs = iter([catalog, [*catalog, {"type": "function", "function": {"name": "Grep"}}]])
    assert run(session, model, api_tools=lambda: next(catalogs)).status == "complete"
    assert len(drops) == 1 and drops[0]["changed"] == ["tools"]


def test_source_budget_warns_once_and_only_explicit_hard_budget_blocks_next_request():
    spent = {"prompt_tokens": 100_000, "completion_tokens": 100}
    first = replace(reply("", [call()]), usage=spent)
    second = replace(reply("", [call(call_id="call-2")]), usage=spent)
    for hard in (False, True):
        session = Session("SYS", "m", env={})
        session.budgetCNY = .01
        notices = []
        model = Model([copy.deepcopy(first), copy.deepcopy(second), reply("done")])
        result = run(session, model, budget_hard=hard, notice=notices.append)
        assert result.status == ("budget_limit" if hard else "complete")
        assert len(model.requests) == (1 if hard else 3)
        assert len([notice for notice in notices if "成本提醒" in notice]) == 1



def test_source_model_unavailable_retries_original_request_then_saves_progress():
    session = Session("SYS", "same-model", env={})
    session.addUser("continue original task")
    existing = copy.deepcopy(session.messages)
    seen = []

    async def forbidden_choice(*_args):
        raise AssertionError("transient failure may not prompt or switch accounts")

    def model(opts, _context):
        seen.append(opts["model"])
        if len(seen) == 1:
            raise TimeoutError("synthetic network timeout")
        return reply(error="API 529: synthetic overload")

    saved = []

    class Journal:
        async def save(self, current):
            saved.append(copy.deepcopy(current.messages))

    async def stop_background():
        assert saved[-1] == session.messages
        raise RuntimeError("synthetic background stop receipt unavailable")

    context = ToolContext("synthetic-workspace", askChoice=forbidden_choice)
    result = run(session, model, context=context, journal=Journal(), on_model_unavailable=stop_background,
                 model_recovery_env={"RUOCUN_HARD_RETRY_DELAY_MS": "1"})
    assert seen == ["same-model", "same-model"]
    assert result.status == "model_unavailable" and "后台停止结果未确认" in result.error
    assert session.messages[:-1] == existing
    assert "可稍后重新发送消息继续" in session.messages[-1]["content"]


def test_source_rate_limit_interactive_abort_is_a_single_request():
    session = Session("SYS", "same-model", env={})
    asked = []

    async def choose(question, choices, _multi=False):
        asked.append((question, choices))
        return choices[-1]

    model = Model([reply(error="API error 429: synthetic rate_limit_exceeded")])
    result = run(session, model, context=ToolContext("synthetic-workspace", askChoice=choose))
    assert result.status == "failed" and "限流" in result.error
    assert len(model.requests) == 1 and len(asked) == 1
    assert asked[0][1] == ["等待后用当前模型重试", "中止本轮(稍后可用 /account 切换账号)"]



@pytest.mark.parametrize("switch_result", [True, False, None], ids=["confirmed", "rejected", "unknown"])
def test_source_rate_limit_only_switches_selected_account_after_saving(switch_result):
    session = Session("SYS", "old-model", env={})
    session.addUser("original user goal")
    saved = []
    selected = []
    options = {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic-old", "model": session.model}

    class Journal:
        async def save(self, current):
            saved.append(copy.deepcopy(current.messages))

    async def choose(_question, choices, _multi=False):
        assert saved[-1] == session.messages
        assert choices == ["等待后用当前模型重试", "切到账号「other」重试", "中止本轮(稍后可用 /account 切换账号)"]
        return choices[1]

    async def switch(name):
        selected.append(name)
        if switch_result is None:
            raise RuntimeError("synthetic profile save receipt unavailable")
        if switch_result:
            options.update({"baseUrl": "http://127.0.0.1:2", "apiKey": "synthetic-new", "model": "chosen-model"})
            session.setModel("chosen-model")
        return switch_result

    model = Model([replace(reply(error="synthetic provider rate exceeded"), error_status=429), reply("continued")])
    result = asyncio.run(run_turn(
        session, options, Registry(), ToolContext("synthetic-workspace", askChoice=choose),
        approve=approve, request=model, journal=Journal(),
        list_other_accounts=lambda: ["other"], switch_account_and_wait=switch,
    ))
    assert selected == ["other"]
    assert model.requests[0]["baseUrl"] == "http://127.0.0.1:1"
    if switch_result:
        assert result.status == "complete" and len(model.requests) == 2
        assert model.requests[1]["baseUrl"] == "http://127.0.0.1:2"
        assert model.requests[1]["apiKey"] == "synthetic-new" and model.requests[1]["model"] == "chosen-model"
        assert model.requests[1]["messages"] == model.requests[0]["messages"]
    else:
        assert result.status == "failed" and len(model.requests) == 1
        assert "限流" in result.error and session.messages == saved[-1]


def test_source_headless_rate_limit_budget_and_partial_response_stop_without_replay():
    rate_limited = replace(reply(error="synthetic quota"), error_status=429)
    model = Model([copy.deepcopy(rate_limited) for _ in range(3)])
    env = {"RUOCUN_RATE_LIMIT_MAX_RETRIES": "2", "RUOCUN_RATE_LIMIT_WAIT_MS": "1"}
    result = run(Session("SYS", "same-model", env={}), model, model_recovery_env=env)
    assert result.status == "failed" and len(model.requests) == 3
    assert {request["model"] for request in model.requests} == {"same-model"}

    registry = Registry()
    partial = replace(reply("already streamed", [call()], error="API 529: synthetic overload"),
                      status="partial", deltas=[{"kind": "content", "text": "already streamed"}])
    model = Model([partial])
    session = Session("SYS", "same-model", env={})
    result = run(session, model, registry)
    assert result.status == "failed" and len(model.requests) == 1 and registry.executed == []
    assert session.messages[-1] == {"role": "assistant", "content": "already streamed"}
