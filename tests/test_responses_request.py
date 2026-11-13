"""WIRE-04 · 请求体转换 / usage / message 构造（冻结 responses.ts:34-72）。

预期独立来源：
- 冻结 ``src/client/responses.ts:34-39`` usage()、``:41-49`` message()、
  ``:53-65`` 请求体（store/include/effort/max_output_tokens/tools/可选字段）；
- 冻结 ``src/client/responses.test.ts:48-50``（store/include/tools）、
  ``:63-75``（三档 effort、128000、无 max_tokens）、``:10-13``（usage fixture）、
  ``:54``（命中/未命中补齐）、``:51``（图片 input_image）；
- 冻结 ``src/client/client.ts:50-55`` normalizeUsage（04 已建立，本票联动复用）。
按 S/D/R 改写；不回填当前实现输出。
"""

from __future__ import annotations

from typing import Any

from ruocun.client import client, responses

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


def _chat(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "model": "gpt-6.1-sol", "messages": [], "stream": True,
        "max_completion_tokens": 128000,
    }
    base.update(extra)
    return base


# ---------------------------------------------------------------------------
# 请求体（responses.ts:53-65）
# ---------------------------------------------------------------------------


def test_request_fixed_fields_and_no_chat_only_fields():
    body = responses.buildResponsesRequest(_chat())
    assert body["model"] == "gpt-6.1-sol"
    assert body["input"] == []
    assert body["stream"] is True
    assert body["store"] is False
    assert body["include"] == ["reasoning.encrypted_content"]
    # 冻结 responses.test.ts:69：请求里不出现 max_tokens（用 max_output_tokens）
    assert "max_tokens" not in body
    assert "max_completion_tokens" not in body
    assert "messages" not in body
    assert "stream_options" not in body
    assert responses.RESPONSES_ENDPOINT == "https://api.openai.com/v1/responses"


def test_request_max_output_tokens_capped_and_field_fallback():
    # 冻结 responses.test.ts:67：256000 → 128000
    assert responses.buildResponsesRequest(
        _chat(model="gpt-6-astra", max_completion_tokens=256000),
    )["max_output_tokens"] == 128000
    # 冻结 responses.ts:58：max_completion_tokens ?? max_tokens
    fallback = {"model": "gpt-6.1-sol", "messages": [], "stream": True,
                "max_tokens": 64000}
    assert responses.buildResponsesRequest(fallback)["max_output_tokens"] == 64000


def test_request_effort_mapping_for_three_official_tiers():
    # 冻结 responses.test.ts:64-69：reasoning_effort="none" 下 astra/6.1-sol→low、luna→none
    for model, expected in (("gpt-6-astra", "low"), ("gpt-6.1-sol", "low"),
                            ("gpt-6-luna", "none")):
        body = responses.buildResponsesRequest(
            _chat(model=model, reasoning_effort="none"),
        )
        assert body["reasoning"] == {"effort": expected}
        assert body["max_output_tokens"] == 128000


def test_request_effort_defaults_and_special_values():
    # 冻结 responses.ts:54/59（&& 优先于 || 的真实运算顺序）
    assert responses.buildResponsesRequest(_chat())["reasoning"] == {"effort": "medium"}
    assert responses.buildResponsesRequest(
        _chat(thinking={"type": "disabled"}),
    )["reasoning"] == {"effort": "low"}
    assert responses.buildResponsesRequest(
        _chat(model="gpt-6-luna", reasoning_effort="minimal"),
    )["reasoning"] == {"effort": "low"}
    assert responses.buildResponsesRequest(
        _chat(reasoning_effort="high"),
    )["reasoning"] == {"effort": "high"}
    assert responses.buildResponsesRequest(
        _chat(reasoning_effort="none"),
    )["reasoning"] == {"effort": "low"}  # 6.1-sol 命中 /astra|6\.1-sol/


def test_request_tools_and_optional_fields():
    # 冻结 responses.test.ts:49-50 / responses.ts:60-63
    body = responses.buildResponsesRequest(_chat(
        tools=[{"type": "function", "function": {
            "name": "Read", "description": "读取",
            "parameters": {"type": "object"}}}],
        parallel_tool_calls=True, tool_choice="required", service_tier="flex",
    ))
    assert body["tools"] == [{
        "type": "function", "name": "Read", "description": "读取",
        "parameters": {"type": "object"}, "strict": False,
    }]
    assert body["parallel_tool_calls"] is True
    assert body["tool_choice"] == "required"
    assert body["service_tier"] == "flex"
    plain = responses.buildResponsesRequest(_chat())
    for key in ("tools", "parallel_tool_calls", "tool_choice", "service_tier"):
        assert key not in plain


def test_request_input_is_converted_messages():
    body = responses.buildResponsesRequest(_chat(messages=[{
        "role": "user", "content": [
            {"type": "text", "text": "看图"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
        ],
    }]))
    assert body["input"] == [{"role": "user", "content": [
        {"type": "input_text", "text": "看图"},
        {"type": "input_image", "image_url": "data:image/png;base64,test"},
    ]}]


# ---------------------------------------------------------------------------
# usage 归一化（responses.ts:34-39 + client.ts:50-55 联动）
# ---------------------------------------------------------------------------


def test_responses_usage_maps_to_chat_fields_and_cache_is_completed():
    # 冻结 responses.test.ts:11-12 的 usage fixture 与 :54 的断言
    raw: dict[str, Any] = {
        "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
        "input_tokens_details": {"cached_tokens": 80},
    }
    out = responses.responsesUsage(raw)
    assert out == {
        "prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110,
        "prompt_tokens_details": {"cached_tokens": 80},
    }
    normalized = client.normalizeUsage(out)
    assert normalized["prompt_cache_hit_tokens"] == 80
    assert normalized["prompt_cache_miss_tokens"] == 20


def test_responses_usage_without_details_has_no_invented_cache():
    out = responses.responsesUsage({"input_tokens": 5, "output_tokens": 2, "total_tokens": 7})
    assert out == {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}
    assert "prompt_tokens_details" not in out
    assert client.normalizeUsage(out) == out


def test_native_cache_fields_take_priority():
    # R-06：原生 cache 字段优先，不被 details.cached_tokens 覆盖
    native = {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110,
              "prompt_cache_hit_tokens": 60, "prompt_cache_miss_tokens": 40,
              "prompt_tokens_details": {"cached_tokens": 80}}
    assert client.normalizeUsage(native) == native


# ---------------------------------------------------------------------------
# message 构造（responses.ts:41-49）
# ---------------------------------------------------------------------------


def test_message_from_output_items():
    out = responses.responsesMessage([REASONING, CALL, ANSWER])
    assert out["content"] == "完成"
    assert out["tool_calls"] == [{
        "id": "call_1", "type": "function",
        "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
    }]
    assert out["responseItems"] == [REASONING]


def test_message_without_text_is_null_and_refusal_is_used():
    out = responses.responsesMessage([REASONING, CALL])  # 无 message item
    assert out["content"] is None
    assert out["tool_calls"] == [{
        "id": "call_1", "type": "function",
        "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
    }]
    assert out["responseItems"] == [REASONING]
    # 冻结 responses.ts:43 part.text ?? part.refusal ?? ""
    refused = responses.responsesMessage([
        {"type": "message", "content": [{"type": "refusal", "refusal": "拒绝"}]},
    ])
    assert refused["content"] == "拒绝"
    assert "tool_calls" not in refused
