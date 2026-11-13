"""WIRE-04 · Responses SSE → 统一 Chat 事件回传（冻结 responses.ts:73-131）。

预期独立来源：
- 冻结 ``src/client/responses.ts:73-131`` 的事件分发（completed/incomplete、
  error/failed、output_text/refusal/reasoning delta、function_call 增量、
  output_item.added/done、[DONE] 跳过、无完成事件断流抛错）；
- 冻结 ``src/client/responses.test.ts:9-20`` 的 sse() fixture（17 字节分块、
  中文跨字节、含 type 的 data 事件）、``:34-39`` 工具参数增量、
  ``:98-104`` 错误/断流边界、``:10-13`` usage fixture；
- 04 已建立的 ``client.ChatAccumulator`` / ``sse.SSEStreamParser``（复用，不重造）。
按 S/D/R 改写；不回填当前实现输出。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ruocun.client import client, responses, sse

REASONING: dict[str, Any] = {
    "type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext",
}
CALL_ARGUMENTS = '{"path":"中文.ts"}'
CALL: dict[str, Any] = {
    "type": "function_call", "id": "fc_1", "call_id": "call_1",
    "name": "Read", "arguments": CALL_ARGUMENTS,
}
ANSWER: dict[str, Any] = {
    "type": "message", "content": [{"type": "output_text", "text": "完成"}],
}
USAGE: dict[str, Any] = {
    "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
    "input_tokens_details": {"cached_tokens": 80},
}


def _completed(output: list[dict[str, Any]], *extra: dict[str, Any]) -> list[Any]:
    return [*extra, {"type": "response.completed", "response": {"output": output, "usage": USAGE}}]


def _responses_sse(events: list[Any]) -> list[bytes]:
    """冻结 responses.test.ts:14-20：event:<type> CRLF data:<json> CRLFCRLF，按 17 字节分块。"""
    parts: list[str] = []
    for event in events:
        if isinstance(event, str):
            parts.append("data: " + event + "\r\n\r\n")
        else:
            parts.append("event: " + str(event["type"]) + "\r\ndata: "
                         + json.dumps(event, ensure_ascii=False) + "\r\n\r\n")
    raw = "".join(parts).encode("utf-8")
    return [raw[i:i + 17] for i in range(0, len(raw), 17)]


def _chat_payloads(events: list[Any]) -> list[dict[str, Any]]:
    """经公开 iterChatFrames 转换，再用 04 的 SSEStreamParser 解析成 Chat payload。"""
    parser = sse.SSEStreamParser()
    out: list[dict[str, Any]] = []
    for frame in responses.iterChatFrames(_responses_sse(events)):
        for payload in parser.feed(frame):
            out.append(json.loads(payload))
    for payload in parser.flush():
        out.append(json.loads(payload))
    return out


def _feed_payloads(events: list[Any]) -> list[dict[str, Any]]:
    """只测 feed（不 flush）：用于 error 帧这种会被客户端提前中断的场景。"""
    converter = responses.ResponsesToChat()
    out: list[dict[str, Any]] = []
    for chunk in _responses_sse(events):
        for frame in converter.feed(chunk):
            for payload in sse.parseSSEChunk(frame.decode("utf-8")).payloads:
                out.append(json.loads(payload))
    return out


# ---------------------------------------------------------------------------
# 结束 / 错误事件（responses.ts:115-127, 85）
# ---------------------------------------------------------------------------


def test_completed_emits_terminal_frame_with_usage_reasoning_and_stop():
    frames = _chat_payloads(_completed([REASONING, ANSWER]))
    # 无 output_text.delta 时 completed 补发一次完整 content（冻结 responses.ts:123）
    assert frames[0] == {"choices": [{"delta": {"content": "完成"}}]}
    final = frames[-1]
    assert final["response_items"] == [REASONING]
    assert final["usage"] == {
        "prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110,
        "prompt_tokens_details": {"cached_tokens": 80},
    }
    assert final["choices"] == [{"delta": {}, "finish_reason": "stop"}]


def test_incomplete_terminal_finish_reason_is_length():
    events = [{"type": "response.incomplete", "response": {"output": [ANSWER], "usage": USAGE}}]
    assert _chat_payloads(events)[-1]["choices"][0]["finish_reason"] == "length"


def test_function_call_terminal_finish_reason_is_tool_calls():
    frames = _chat_payloads(_completed([REASONING, CALL]))
    assert frames[-1]["choices"][0]["finish_reason"] == "tool_calls"
    # completed 的 items.forEach 对 function_call 调用 call()：注册 + 补齐完整 arguments
    assert any("tool_calls" in f.get("choices", [{}])[0].get("delta", {}) for f in frames)


def test_error_event_becomes_chat_error_frame_not_empty_success():
    # 冻结 responses.test.ts:98-104；客户端在 error 帧处抛 SseError，不会走到 flush
    payloads = _feed_payloads([
        {"type": "response.failed", "response": {"error": {"message": "bad request"}}},
    ])
    assert payloads == [{"error": {"message": "bad request"}}]


def test_stream_without_completed_event_is_explicit_failure():
    # 冻结 responses.ts:85「Responses stream closed unexpectedly」
    with pytest.raises(responses.ResponsesStreamError):
        list(responses.iterChatFrames(_responses_sse([
            {"type": "response.output_text.delta", "delta": "部分"},
        ])))


# ---------------------------------------------------------------------------
# 增量事件（responses.ts:106-114）
# ---------------------------------------------------------------------------


def test_text_refusal_and_reasoning_deltas():
    frames = _chat_payloads([
        {"type": "response.output_text.delta", "delta": "第一"},
        {"type": "response.refusal.delta", "delta": "第二"},
        {"type": "response.reasoning_summary_text.delta", "delta": "思考"},
        {"type": "response.completed", "response": {"output": [], "usage": USAGE}},
    ])
    assert frames[0] == {"choices": [{"delta": {"content": "第一"}}]}
    assert frames[1] == {"choices": [{"delta": {"content": "第二"}}]}
    assert frames[2] == {"choices": [{"delta": {"reasoning_content": "思考"}}]}
    # hadText=True → completed 不再补发 content
    assert frames[-1]["choices"] == [{"delta": {}, "finish_reason": "stop"}]


def test_tool_call_arguments_delta_roundtrip_and_usage_normalization():
    # 冻结 responses.test.ts:34-39 的事件序列与 :52-54 的最终断言
    events = _completed([REASONING, CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**CALL, "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '{"path":'},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '"中文.ts"}'},
        {"type": "response.output_item.done", "output_index": 1, "item": CALL},
    )
    frames = _chat_payloads(events)  # 17 字节分块验证中文跨字节严格解码
    acc = client.ChatAccumulator()
    for frame in frames:
        acc.process(json.dumps(frame, ensure_ascii=False))
    msg = acc.buildMessage()
    assert msg["tool_calls"] == [{
        "id": "call_1", "type": "function",
        "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
    }]
    assert msg["responseItems"] == [REASONING]
    assert acc.last_usage is not None
    assert acc.last_usage["prompt_cache_hit_tokens"] == 80
    assert acc.last_usage["prompt_cache_miss_tokens"] == 20


def test_output_item_done_completes_missing_arguments():
    # 冻结 responses.ts:98-101：完整 item.arguments 按已累积长度发差量
    events = _completed([REASONING, CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**CALL, "arguments": ""}},
        {"type": "response.output_item.done", "output_index": 1, "item": CALL},
    )
    frames = _chat_payloads(events)
    argument_frags = [
        frag["function"]["arguments"]
        for f in frames for frag in f.get("choices", [{}])[0].get("delta", {}).get("tool_calls", [])
        if "arguments" in frag.get("function", {})
    ]
    assert "".join(argument_frags) == CALL_ARGUMENTS


def test_arguments_delta_without_matching_call_is_protocol_error():
    # 冻结 responses.ts:109「Responses 工具参数缺少对应调用」
    with pytest.raises(responses.ResponsesStreamError):
        _chat_payloads(_completed([ANSWER],
            {"type": "response.function_call_arguments.delta",
             "output_index": 1, "delta": "{}"},
        ))


def test_done_sentinel_and_unknown_events_are_ignored():
    frames = _chat_payloads([
        "[DONE]",
        {"type": "response.created", "response": {}},
        {"type": "response.completed", "response": {"output": [ANSWER], "usage": USAGE}},
    ])
    # 只有 completed 补发的一次 content + 终止帧；[DONE]/created 不产生帧
    assert len(frames) == 2
    assert frames[0] == {"choices": [{"delta": {"content": "完成"}}]}
    assert frames[-1]["choices"][0]["finish_reason"] == "stop"
