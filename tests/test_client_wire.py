"""WIRE-01/02/03/05: 请求保真、输出上限/思考参数、SSE 累积与历史清洗。

预期独立来源：
- 冻结 src/client/client.ts:50-120, 208-269, 380-415 及 .test.ts:36-268, 556-569
- 冻结 src/client/types.ts:1-104
- 规格 R-06/R-07、任务票 WIRE-01/02/03/05、ADR-0003（本票不引入重放语义）
按 S/D/R 把 TS 断言改写为 Python；不回填当前实现输出。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ruocun.client import client

BASE: dict[str, Any] = {"baseUrl": "https://x", "apiKey": "sk", "model": "deepseek-v4-pro"}


def _opts(**kw: Any) -> dict[str, Any]:
    return {**BASE, "messages": [{"role": "user", "content": "hi"}], **kw}


def _sse(payload: dict[str, Any] | str) -> bytes:
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return ("data: " + body + "\n\n").encode("utf-8")


def _fake(chunks: list[bytes], status: int = 200):
    captured: list[tuple[str, dict[str, str], bytes]] = []

    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        captured.append((url, headers, body))
        return client.HttpResponse(status, {}, iter(chunks))

    return transport, captured


# ---------------------------------------------------------------------------
# WIRE-01 · 请求保真（client.test.ts:97-115, 270-278）
# ---------------------------------------------------------------------------


def test_request_body_fixed_fields_and_order():
    body = client.buildRequestBody(_opts())
    assert list(body) == ["model", "messages", "stream", "stream_options", "max_tokens"]
    assert body["model"] == "deepseek-v4-pro"
    assert body["stream"] is True
    assert body["stream_options"] == {"include_usage": True}
    assert body["messages"] == [{"role": "user", "content": "hi"}]


def test_tools_and_parallel_tool_calls_in_request():
    body = client.buildRequestBody(_opts(
        tools=[{"type": "function", "function": {"name": "Read", "description": "d",
                                                 "parameters": {}}}],
        parallelToolCalls=True,
    ))
    assert len(body["tools"]) == 1
    assert body["parallel_tool_calls"] is True
    assert body["stream"] is True


def test_request_url_and_headers_are_built_from_resolved_credential():
    transport, captured = _fake([_sse("[DONE]")])
    client.streamChat(_opts(), transport=transport)
    url, headers, _ = captured[0]
    assert url == "https://x/chat/completions"
    assert headers["Authorization"] == "Bearer sk"
    assert headers["Content-Type"] == "application/json"


# ---------------------------------------------------------------------------
# WIRE-02 · 输出上限 / 参数（client.test.ts:117-152, 270-278）
# ---------------------------------------------------------------------------


def test_max_tokens_default_is_128000():
    assert client.buildRequestBody(_opts())["max_tokens"] == 128000
    assert "max_completion_tokens" not in client.buildRequestBody(_opts())


def test_max_tokens_explicit_override():
    assert client.buildRequestBody(_opts(maxTokens=256))["max_tokens"] == 256


def test_env_max_output_tokens_override():
    body = client.buildRequestBody(_opts(), env={"RUOCUN_MAX_OUTPUT_TOKENS": "50000"})
    assert body["max_tokens"] == 50000


def test_gpt5_uses_max_completion_tokens_not_max_tokens():
    body = client.buildRequestBody(_opts(model="gpt-5"))
    assert body["max_completion_tokens"] == 128000
    assert "max_tokens" not in body


def test_no_unconfigured_sampling_parameters():
    body = client.buildRequestBody(_opts())
    assert "temperature" not in body
    assert "top_p" not in body


def test_extra_overrides_body_fields():
    # 冻结 client.ts:119 ...opts.extra 放最后覆盖；WIRE-01「extra 覆盖」
    body = client.buildRequestBody(_opts(extra={
        "reasoning_effort": "max", "tool_choice": "required", "model": "override-model",
    }))
    assert body["reasoning_effort"] == "max"
    assert body["tool_choice"] == "required"
    assert body["model"] == "override-model"  # extra 覆盖在前


def test_special_empty_truncation_retry_is_256000_and_capped():
    # R-06/WIRE-02「默认 128000、特殊空截断重试 256000，且都受模型 cap 裁剪」
    assert client.resolveMaxTokens(_opts()) == 128000
    assert client.resolveMaxTokens(_opts(), empty_truncation_retry=True) == 256000
    # ernie-5.1 cap 65536：两种档位都裁到 65536
    capped = _opts(model="ernie-5.1", baseUrl="https://qianfan.baidubce.com/v2/tokenplan/personal")
    assert client.resolveMaxTokens(capped) == 65536
    assert client.resolveMaxTokens(capped, empty_truncation_retry=True) == 65536
    build = client.buildRequestBody(_opts(), max_tokens_override=256000)
    assert build["max_tokens"] == 256000


def test_thinking_and_tool_choice_rules_come_from_extra_only():
    # 冻结 loop.ts:294-305：reasoning_effort / tool_choice 由调用方 extra 提供，client 不主动加
    body = client.buildRequestBody(_opts())
    assert "reasoning_effort" not in body
    assert "tool_choice" not in body


# ---------------------------------------------------------------------------
# WIRE-05 · 历史 wire 清洗（client.ts:72-90；client.test.ts:154-196）
# ---------------------------------------------------------------------------


def test_assistant_null_content_becomes_empty_string():
    msgs = [{"role": "assistant", "content": None}]
    assert client.buildWireMessages(msgs) == [{"role": "assistant", "content": ""}]


def test_reasoning_stripped_from_turn_without_tool_call():
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello",
         "reasoningContent": "先前的思维链,只落盘不重发"},
    ]
    wire = client.buildWireMessages(msgs)
    assert wire[1] == {"role": "assistant", "content": "hello"}
    assert "reasoningContent" not in wire[1]
    assert "reasoning_content" not in wire[1]


def test_reasoning_kept_on_wire_for_tool_call_turn():
    tool_calls = [{"id": "call_1", "type": "function",
                   "function": {"name": "Read", "arguments": "{}"}}]
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "", "tool_calls": tool_calls,
         "reasoningContent": "先想清楚该读哪个文件"},
        {"role": "tool", "tool_call_id": "call_1", "content": "file contents"},
    ]
    wire = client.buildWireMessages(msgs)
    assert wire[1]["reasoning_content"] == "先想清楚该读哪个文件"
    assert wire[1]["tool_calls"] == tool_calls
    assert "reasoningContent" not in wire[1]


def test_native_deepseek_tool_request_replays_reasoning_from_completed_turns():
    # DeepSeek 官方 Chat 协议要求带 tools 时保留所有历史 assistant 的 reasoning，
    # 包括已经结束、没有 tool_calls 的回合；期望来自官方 thinking-mode 协议。
    body = client.buildRequestBody(_opts(
        provider="deepseek", baseUrl="https://api.deepseek.com/v1",
        messages=[
            {"role": "user", "content": "first task"},
            {"role": "assistant", "content": "done", "reasoningContent": "prior reasoning"},
            {"role": "assistant", "content": "plain answer"},
            {"role": "user", "content": "next task"},
        ],
        tools=[{"type": "function", "function": {"name": "Read", "parameters": {}}}],
    ), env={})
    assert body["messages"] == [
        {"role": "user", "content": "first task"},
        {"role": "assistant", "content": "done", "reasoning_content": "prior reasoning"},
        {"role": "assistant", "content": "plain answer"},
        {"role": "user", "content": "next task"},
    ]


@pytest.mark.parametrize(("overrides", "use_responses"), [
    ({"provider": "openai"}, False),
    ({"provider": None}, False),
    ({"baseUrl": "https://gateway.example/v1"}, False),
    ({"baseUrl": "https://api.deepseek.com.example/v1"}, False),
    ({"tools": None}, False),
    ({"tools": []}, False),
    ({}, True),
], ids=["other-provider", "unknown-provider", "gateway", "different-host",
        "no-tools", "empty-tools", "responses"])
def test_completed_turn_reasoning_replay_stays_scoped_to_native_deepseek_tools(
    overrides: dict[str, Any], use_responses: bool,
):
    options = _opts(
        provider="deepseek", baseUrl="https://api.deepseek.com",
        messages=[{"role": "assistant", "content": "done", "reasoningContent": "prior reasoning"}],
        tools=[{"type": "function", "function": {"name": "Read", "parameters": {}}}],
    )
    body = client.buildRequestBody({**options, **overrides}, use_responses=use_responses, env={})
    assert body["messages"] == [{"role": "assistant", "content": "done"}]


@pytest.mark.parametrize("tools_in_extra", [True, False], ids=["extra-adds-tools", "extra-removes-tools"])
def test_native_deepseek_reasoning_replay_uses_effective_tools_after_extra(tools_in_extra: bool):
    tools = [{"type": "function", "function": {"name": "Read", "parameters": {}}}]
    body = client.buildRequestBody(_opts(
        provider="deepseek", baseUrl="https://api.deepseek.com",
        messages=[{"role": "assistant", "content": "done", "reasoningContent": "prior reasoning"}],
        tools=None if tools_in_extra else tools,
        extra={"tools": tools if tools_in_extra else []},
    ), env={})
    expected = {"role": "assistant", "content": "done"}
    if tools_in_extra:
        expected["reasoning_content"] = "prior reasoning"
    assert body["messages"] == [expected]


def test_image_data_and_response_items_never_leak_to_wire():
    msgs = [
        {"role": "tool", "tool_call_id": "c1", "content": "ok",
         "imageData": {"base64": "AAA", "mediaType": "image/png"}},
        {"role": "assistant", "content": "x", "responseItems": [{"type": "reasoning"}]},
    ]
    wire = client.buildWireMessages(msgs)
    assert wire[0] == {"role": "tool", "tool_call_id": "c1", "content": "ok"}
    assert "responseItems" not in wire[1]
    assert "imageData" not in wire[0]


# ---------------------------------------------------------------------------
# WIRE-03 · 累积器（client.test.ts:36-95, 198-268）
# ---------------------------------------------------------------------------


def _acc():
    return client.ChatAccumulator()


def test_accumulates_reasoning_and_content():
    acc = _acc()
    d1 = acc.process(json.dumps({"choices": [{"delta": {"reasoning_content": "think"}}]}))
    d2 = acc.process(json.dumps({"choices": [{"delta": {"content": "hello"}}]}))
    assert d1 == [{"kind": "reasoning", "text": "think"}]
    assert d2 == [{"kind": "content", "text": "hello"}]
    assert acc.buildMessage() == {
        "role": "assistant", "content": "hello", "reasoningContent": "think",
    }


def test_assembles_single_tool_call_from_fragments():
    acc = _acc()
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "id": "call_1", "type": "function",
         "function": {"name": "Read", "arguments": ""}}]}}]}))
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "function": {"arguments": '{"path":'}}]}}]}))
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "function": {"arguments": '"a.txt"}'}}]}}]}))
    msg = acc.buildMessage()
    assert msg["content"] is None
    assert msg["tool_calls"] == [
        {"id": "call_1", "type": "function",
         "function": {"name": "Read", "arguments": '{"path":"a.txt"}'}},
    ]


def test_assembles_two_parallel_tool_calls_by_index():
    acc = _acc()
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "id": "c0", "type": "function",
         "function": {"name": "Read", "arguments": "{}"}}]}}]}))
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 1, "id": "c1", "type": "function",
         "function": {"name": "ListDir", "arguments": "{}"}}]}}]}))
    calls = acc.buildMessage()["tool_calls"]
    assert [c["function"]["name"] for c in calls] == ["Read", "ListDir"]
    assert [c["id"] for c in calls] == ["c0", "c1"]


def test_empty_id_fragment_does_not_clobber_real_id():
    acc = _acc()
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "id": "call_real", "type": "function",
         "function": {"name": "Read", "arguments": ""}}]}}]}))
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "id": "", "function": {"arguments": '{"path":'}}]}}]}))
    acc.process(json.dumps({"choices": [{"delta": {"tool_calls": [
        {"index": 0, "id": "", "function": {"arguments": '"a.txt"}'}}]}}]}))
    assert acc.buildMessage()["tool_calls"] == [
        {"id": "call_real", "type": "function",
         "function": {"name": "Read", "arguments": '{"path":"a.txt"}'}},
    ]


def test_usage_confirmed_only_from_valid_data():
    seen: list[dict[str, Any]] = []
    acc = client.ChatAccumulator(on_usage=lambda u: seen.append(u))
    acc.process(json.dumps({"choices": [], "usage": {
        "prompt_tokens": 1000, "completion_tokens": 50, "total_tokens": 1050,
        "prompt_cache_hit_tokens": 900, "prompt_cache_miss_tokens": 100}}))
    assert seen == [{"prompt_tokens": 1000, "completion_tokens": 50,
                     "total_tokens": 1050, "prompt_cache_hit_tokens": 900,
                     "prompt_cache_miss_tokens": 100}]
    # 两种缓存字段都没有 → 不臆造 hit/miss
    acc2 = client.ChatAccumulator(on_usage=lambda u: seen.append(u))
    acc2.process(json.dumps({"choices": [], "usage": {
        "prompt_tokens": 500, "completion_tokens": 10, "total_tokens": 510}}))
    assert "prompt_cache_hit_tokens" not in seen[-1]


def test_qianfan_usage_normalized_from_cached_tokens():
    seen: list[dict[str, Any]] = []
    acc = client.ChatAccumulator(on_usage=lambda u: seen.append(u))
    acc.process(json.dumps({"choices": [], "usage": {
        "prompt_tokens": 9611, "completion_tokens": 14, "total_tokens": 9625,
        "prompt_tokens_details": {"cached_tokens": 9216}}}))
    assert seen[0]["prompt_cache_hit_tokens"] == 9216
    assert seen[0]["prompt_cache_miss_tokens"] == 395


def test_finish_reason_confirmed_only_from_valid_data():
    seen: list[str] = []
    acc = client.ChatAccumulator(on_finish_reason=lambda r: seen.append(r))
    acc.process(json.dumps({"choices": [{"delta": {"content": "x"}}]}))
    assert seen == []  # 无 finish_reason 不确认
    acc.process(json.dumps({"choices": [{"delta": {}, "finish_reason": "content_filter"}]}))
    assert seen == ["content_filter"]


def test_done_and_blank_and_bad_json_are_ignored():
    acc = _acc()
    assert acc.process("[DONE]") == []
    assert acc.process("") == []
    assert acc.process("not json") == []


# ---------------------------------------------------------------------------
# streamChat 完整路径与失败/取消边界（fake HTTP/SSE）
# ---------------------------------------------------------------------------


def test_stream_chat_full_path_returns_answer_and_golden():
    transport, captured = _fake([
        _sse({"choices": [{"delta": {"content": "你好"}}]}),
        _sse({"choices": [{"delta": {"content": "世界"}}]}),
        _sse({"choices": [], "usage": {"prompt_tokens": 5, "completion_tokens": 2,
                                       "total_tokens": 7}}),
        _sse("[DONE]"),
    ])
    result = client.streamChat(_opts(), transport=transport)
    assert result.status == "complete"
    assert result.message["content"] == "你好世界"
    assert [d["text"] for d in result.deltas if d["kind"] == "content"] == ["你好", "世界"]
    assert result.request_body["stream"] is True
    assert json.loads(captured[0][2]) == result.request_body  # 请求 golden 可验


def test_stream_chat_non_2xx_is_explicit_failure():
    transport, _ = _fake([], status=401)
    with pytest.raises(client.ApiError):
        client.streamChat(_opts(), transport=transport)


def test_reasoning_only_length_notifies_caller_once():
    # 冻结 client.test.ts:447：走真实 client → resilient → SSE 累积，不能由 loop mock 代发通知。
    transport, captured = _fake([
        _sse({"choices": [{"delta": {"reasoning_content": "想了很多但还没写结论"},
                            "finish_reason": None}]}),
        _sse({"choices": [{"delta": {}, "finish_reason": "length"}]}),
        _sse("[DONE]"),
    ])
    notifications: list[None] = []
    result = client.streamChat(_opts(onEmptyTruncation=lambda: notifications.append(None)),
                               transport=transport)
    assert len(captured) == 1
    assert result.message["content"] is None
    assert result.message["reasoningContent"] == "想了很多但还没写结论"
    assert notifications == [None]


def test_stream_chat_sse_error_event_is_explicit_failure_no_replay():
    # ADR-0003 精神：本票不引入重放语义；SSE error 明确失败
    transport, _ = _fake([
        _sse({"error": {"code": "E2004", "message": "max_concurrency"}}),
        _sse("[DONE]"),
    ])
    with pytest.raises(client.SseError):
        client.streamChat(_opts(), transport=transport)


def test_stream_chat_mid_stream_disconnect_keeps_partial_not_false_success():
    def gen():
        yield _sse({"choices": [{"delta": {"content": "part"}}]})
        raise client.StreamDisconnected("断流")

    def transport(url, headers, body):
        return client.HttpResponse(200, {}, gen())

    result = client.streamChat(_opts(), transport=transport)
    assert result.status == "partial"  # 明确标记，不伪报成功
    assert result.message["content"] == "part"


def test_stream_chat_disconnect_before_any_output_is_failure():
    def gen():
        raise client.StreamDisconnected("断流")
        yield b""  # pragma: no cover

    def transport(url, headers, body):
        return client.HttpResponse(200, {}, gen())

    with pytest.raises(client.StreamError):
        client.streamChat(_opts(), transport=transport)


def test_stream_chat_invalid_utf8_is_explicit_failure():
    transport, _ = _fake([b"data: \xff\xfe bad\n\n"])
    with pytest.raises(UnicodeDecodeError):
        client.streamChat(_opts(), transport=transport)
