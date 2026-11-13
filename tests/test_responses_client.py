"""WIRE-04 · ``client.streamChat`` 的 Responses 路由集成与同一对话/工具回合。

预期独立来源：
- 冻结 ``src/client/client.ts:65-66`` 路由调用点（responsesFetch 包装 fetch）、
  ``:72-91`` wireMessages（useResponses 时携带 responseItems）、``:50-55`` usage；
- 冻结 ``src/client/responses.test.ts:30-62`` 两轮工具回合（请求 body、图片、
  工具调用、加密推理、usage 归一化、第二轮 function_call_output）、
  ``:87-96`` 自定义网关保持 Chat 且不泄漏内部字段、
  ``:98-104`` 错误/断流边界；
- 04 已建立的 ``client.streamChat`` / ``ChatAccumulator`` / ``normalizeUsage``（复用）。
按 S/D/R 改写 TS 断言；不回填当前实现输出。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ruocun.client import client

SYNTHETIC_KEY = "sk-synthetic-NOT-A-REAL-KEY"

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
TOOLS: list[dict[str, Any]] = [{
    "type": "function", "function": {
        "name": "Read", "description": "读取", "parameters": {"type": "object"},
    },
}]


def _opts(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "baseUrl": "https://api.openai.com/v1", "apiKey": SYNTHETIC_KEY,
        "model": "gpt-6.1-sol", "messages": [{"role": "user", "content": "你好"}],
    }
    base.update(kw)
    return base


def _completed(output: list[dict[str, Any]], *extra: dict[str, Any]) -> list[Any]:
    return [*extra, {"type": "response.completed", "response": {"output": output, "usage": USAGE}}]


def _responses_bytes(events: list[Any]) -> list[bytes]:
    parts: list[str] = []
    for event in events:
        if isinstance(event, str):
            parts.append("data: " + event + "\r\n\r\n")
        else:
            parts.append("event: " + str(event["type"]) + "\r\ndata: "
                         + json.dumps(event, ensure_ascii=False) + "\r\n\r\n")
    raw = "".join(parts).encode("utf-8")
    return [raw[i:i + 17] for i in range(0, len(raw), 17)]


def _chat_bytes(frames: list[Any]) -> list[bytes]:
    text = "".join(
        "data: " + (f if isinstance(f, str) else json.dumps(f, ensure_ascii=False)) + "\n\n"
        for f in frames
    )
    raw = text.encode("utf-8")
    return [raw[i:i + 7] for i in range(0, len(raw), 7)]


def _responses_transport(batches: list[list[Any]], captured: list[dict[str, Any]]):
    """注入式 transport：捕获请求，按调用序号回放合成 Responses SSE（17 字节分块）。"""
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        captured.append({
            "url": url, "headers": dict(headers),
            "body": json.loads(body.decode("utf-8")),
        })
        index = len(captured) - 1
        batch = batches[min(index, len(batches) - 1)]
        return client.HttpResponse(200, {}, iter(_responses_bytes(batch)))

    return transport


def _chat_transport(chunks: list[bytes], captured: list[dict[str, Any]]):
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        captured.append({
            "url": url, "headers": dict(headers),
            "body": json.loads(body.decode("utf-8")),
        })
        return client.HttpResponse(200, {}, iter(chunks))

    return transport


# ---------------------------------------------------------------------------
# 路由与请求 golden（client.ts:65-66；responses.test.ts:48-51）
# ---------------------------------------------------------------------------


def test_responses_route_uses_official_endpoint_and_request_golden():
    captured: list[dict[str, Any]] = []
    transport = _responses_transport([_completed([ANSWER])], captured)
    result = client.streamChat(_opts(), transport=transport)
    assert captured[0]["url"] == "https://api.openai.com/v1/responses"
    assert captured[0]["headers"]["Authorization"] == f"Bearer {SYNTHETIC_KEY}"
    assert result.request_body["store"] is False
    assert result.request_body["include"] == ["reasoning.encrypted_content"]
    assert result.request_body["max_output_tokens"] == 128000
    assert captured[0]["body"] == result.request_body  # 请求 golden 服务端可核对
    assert result.message["content"] == "完成"
    assert SYNTHETIC_KEY not in json.dumps(result.request_body)  # 密钥只在 header


def test_first_turn_request_golden_tools_image_effort_and_cap():
    captured: list[dict[str, Any]] = []
    events = _completed([REASONING, CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**CALL, "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": CALL_ARGUMENTS},
        {"type": "response.output_item.done", "output_index": 1, "item": CALL},
    )
    transport = _responses_transport([events], captured)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "系统"},
        {"role": "user", "content": [
            {"type": "text", "text": "看图并读文件"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
        ]},
    ]
    result = client.streamChat(_opts(
        messages=messages, tools=TOOLS, maxTokens=256000,
        extra={"reasoning_effort": "none"},
    ), transport=transport)
    body = result.request_body
    assert body["store"] is False
    assert body["include"] == ["reasoning.encrypted_content"]
    assert body["max_output_tokens"] == 128000  # 256000 经 cap 裁剪
    assert body["reasoning"] == {"effort": "low"}  # none + 6.1-sol → low
    assert body["tools"] == [{
        "type": "function", "name": "Read", "description": "读取",
        "parameters": {"type": "object"}, "strict": False,
    }]
    # 冻结 responses.test.ts:51：input[1].content[1] 是 input_image
    assert body["input"][1]["content"][1] == {
        "type": "input_image", "image_url": "data:image/png;base64,test",
    }
    assert "max_tokens" not in body and "messages" not in body


# ---------------------------------------------------------------------------
# 同一对话 / 工具回合（responses.test.ts:30-62）
# ---------------------------------------------------------------------------


def test_same_conversation_two_turn_tool_roundtrip():
    captured: list[dict[str, Any]] = []
    first_events = _completed([REASONING, CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**CALL, "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": CALL_ARGUMENTS},
        {"type": "response.output_item.done", "output_index": 1, "item": CALL},
    )
    second_events = _completed([ANSWER],
        {"type": "response.output_text.delta", "delta": "完成"},
    )
    transport = _responses_transport([first_events, second_events], captured)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "系统"},
        {"role": "user", "content": [
            {"type": "text", "text": "看图并读文件"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
        ]},
    ]
    first = client.streamChat(_opts(messages=messages, tools=TOOLS), transport=transport)
    assert first.message["tool_calls"] == [{
        "id": "call_1", "type": "function",
        "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
    }]
    assert first.message["responseItems"] == [REASONING]
    assert first.usage is not None
    assert first.usage["prompt_cache_hit_tokens"] == 80
    assert first.usage["prompt_cache_miss_tokens"] == 20
    assert first.finish_reason == "tool_calls"

    second = client.streamChat(_opts(messages=[
        *messages, first.message,
        {"role": "tool", "tool_call_id": "call_1", "content": "文件内容"},
    ]), transport=transport)
    # 冻结 responses.test.ts:57-59：第二轮 input.slice(2)
    assert captured[1]["body"]["input"][2:] == [
        REASONING,
        {"type": "function_call", "call_id": "call_1",
         "name": "Read", "arguments": CALL_ARGUMENTS},
        {"type": "function_call_output", "call_id": "call_1", "output": "文件内容"},
    ]
    assert second.message["content"] == "完成"
    assert [d["text"] for d in second.deltas if d["kind"] == "content"] == ["完成"]


# ---------------------------------------------------------------------------
# 非路由回归（responses.test.ts:87-96；R-06 不推定原生协议）
# ---------------------------------------------------------------------------


def test_custom_gateway_stays_chat_and_internal_field_not_leaked():
    captured: list[dict[str, Any]] = []
    transport = _chat_transport(_chat_bytes([
        {"choices": [{"delta": {"content": "网关回复"}}]}, "[DONE]",
    ]), captured)
    result = client.streamChat(_opts(
        baseUrl="https://gateway.example/v1",
        messages=[{"role": "assistant", "content": "此前回答",
                   "responseItems": [REASONING]}],
    ), transport=transport)
    assert captured[0]["url"] == "https://gateway.example/v1/chat/completions"
    assert "responseItems" not in captured[0]["body"]["messages"][0]
    assert "responseItems" not in json.dumps(captured[0]["body"])
    assert result.message["content"] == "网关回复"


def test_gpt5_on_official_endpoint_stays_chat_completions():
    captured: list[dict[str, Any]] = []
    transport = _chat_transport(_chat_bytes([
        {"choices": [{"delta": {"content": "gpt5 回复"}}]}, "[DONE]",
    ]), captured)
    result = client.streamChat(_opts(model="gpt-5"), transport=transport)
    assert captured[0]["url"] == "https://api.openai.com/v1/chat/completions"
    assert result.message["content"] == "gpt5 回复"


# ---------------------------------------------------------------------------
# 失败 / 取消边界（responses.test.ts:98-104；ADR-0003 精神）
# ---------------------------------------------------------------------------


def test_failed_event_is_explicit_failure_not_empty_success():
    captured: list[dict[str, Any]] = []
    transport = _responses_transport([[
        {"type": "response.failed", "response": {"error": {"message": "bad request"}}},
    ]], captured)
    with pytest.raises(client.SseError):
        client.streamChat(_opts(), transport=transport)


def test_stream_without_completed_event_keeps_partial_without_replay():
    # 冻结 responses.ts:85 的 closed unexpectedly 被 client.ts:141/346-347
    # 识别为可恢复断流；已有 delta 时停止重放并返回已输出内容。
    captured: list[dict[str, Any]] = []
    transport = _responses_transport([[
        {"type": "response.output_text.delta", "delta": "部分"},
    ]], captured)
    result = client.streamChat(_opts(), transport=transport)
    assert result.status == "partial"
    assert result.message["content"] == "部分"
    assert len(captured) == 1


def test_non_2xx_is_explicit_failure():
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        return client.HttpResponse(401, {}, iter([]))
    with pytest.raises(client.ApiError):
        client.streamChat(_opts(), transport=transport)
