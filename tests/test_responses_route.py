"""WIRE-04 · 路由判据与消息转换（来源冻结 responses.ts:5-32）。

预期独立来源：
- 冻结 ``src/client/responses.ts:5-7`` usesResponses 判据；
- 冻结 ``src/client/responses.ts:11-32`` inputMessages（function_call_output 配对、
  reasoning items 携带、assistant null content、图片/文本 part 转换、内部字段不泄漏）；
- 冻结 ``src/client/responses.test.ts:41-59``（图片 + 工具结果往返）、
  ``:87-96``（自定义网关保持 Chat）、``:63-75``（官方三档）。
按 S/D/R 把 TS fixture/断言改写为 Python；不回填当前实现输出。
"""

from __future__ import annotations

from typing import Any

from ruocun.client import responses

# 冻结 responses.test.ts:6-8 的 fixture
REASONING: dict[str, Any] = {
    "type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext",
}
CALL_ARGUMENTS = '{"path":"中文.ts"}'
CALL: dict[str, Any] = {
    "type": "function_call", "id": "fc_1", "call_id": "call_1",
    "name": "Read", "arguments": CALL_ARGUMENTS,
}


# ---------------------------------------------------------------------------
# 路由判据（responses.ts:5-7；注释「仅官方 OpenAI 的 GPT-6 使用」）
# ---------------------------------------------------------------------------


def test_official_gpt6_three_tiers_use_responses():
    for model in ("gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"):
        assert responses.usesResponses("https://api.openai.com/v1", model) is True


def test_base_url_trailing_slashes_and_model_case_are_tolerated():
    assert responses.usesResponses("https://api.openai.com/v1/", "gpt-6-astra") is True
    assert responses.usesResponses("https://api.openai.com/v1///", "GPT-6-LUNA") is True
    assert responses.usesResponses("https://api.openai.com/v1", "gpt-6") is True


def test_gateway_and_non_gpt6_stay_on_chat_completions():
    # 冻结 responses.test.ts:87-96：自定义网关保持 Chat 协议，不推定原生支持 Responses
    assert responses.usesResponses("https://gateway.example/v1", "gpt-6.1-sol") is False
    assert responses.usesResponses("https://api.openai.com/v2", "gpt-6.1-sol") is False
    assert responses.usesResponses("https://api.openai.com/v1", "gpt-5") is False
    assert responses.usesResponses("https://api.openai.com/v1", "gpt-6x") is False
    assert responses.usesResponses("https://api.openai.com/v1", "gpt-60") is False
    assert responses.usesResponses("https://api.openai.com/v1", "claude-opus-5-5") is False


# ---------------------------------------------------------------------------
# 消息转换（responses.ts:11-32）
# ---------------------------------------------------------------------------


def test_tool_message_becomes_function_call_output_pairing():
    # 冻结 responses.test.ts:56-59：tool_call_id → call_id，content → output
    msgs: list[dict[str, Any]] = [
        {"role": "tool", "tool_call_id": "call_1", "content": "文件内容"},
    ]
    assert responses.inputMessages(msgs) == [
        {"type": "function_call_output", "call_id": "call_1", "output": "文件内容"},
    ]


def test_assistant_turn_carries_reasoning_items_and_function_calls_not_null_content():
    # 冻结 responses.test.ts:57-59：input.slice(2) == [reasoning, function_call, function_call_output]
    # assistant content 为 null → 不生成 assistant content item；只携带 reasoning items
    msg: dict[str, Any] = {
        "role": "assistant", "content": None,
        "tool_calls": [{
            "id": "call_1", "type": "function",
            "function": {"name": "Read", "arguments": CALL_ARGUMENTS},
        }],
        "responseItems": [REASONING, {"type": "message", "content": []}],
    }
    assert responses.inputMessages([msg]) == [
        REASONING,
        {"type": "function_call", "call_id": "call_1",
         "name": "Read", "arguments": CALL_ARGUMENTS},
    ]


def test_assistant_non_null_content_is_emitted_after_reasoning():
    msg: dict[str, Any] = {
        "role": "assistant", "content": "此前回答",
        "responseItems": [REASONING],
    }
    assert responses.inputMessages([msg]) == [
        REASONING,
        {"role": "assistant", "content": "此前回答"},
    ]


def test_user_multimodal_parts_become_input_text_and_input_image():
    # 冻结 responses.test.ts:51 / responses.ts:25-29
    msgs: list[dict[str, Any]] = [{"role": "user", "content": [
        {"type": "text", "text": "看图并读文件"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
    ]}]
    assert responses.inputMessages(msgs) == [{"role": "user", "content": [
        {"type": "input_text", "text": "看图并读文件"},
        {"type": "input_image", "image_url": "data:image/png;base64,test"},
    ]}]


def test_string_content_is_kept_verbatim():
    assert responses.inputMessages([{"role": "system", "content": "系统"}]) == [
        {"role": "system", "content": "系统"},
    ]
    assert responses.inputMessages([{"role": "user", "content": "你好"}]) == [
        {"role": "user", "content": "你好"},
    ]


def test_internal_fields_never_leak_into_responses_input():
    # R-06/WIRE-05：responseItems / reasoningContent / imageData 是内部字段，
    # 最终 Responses input 只含转换后的 items（冻结 responses.ts:11-32 不读这些字段）
    msgs: list[dict[str, Any]] = [
        {"role": "assistant", "content": None,
         "responseItems": [REASONING], "reasoningContent": "内部思维链",
         "reasoning_content": "内部字段"},
        {"role": "tool", "tool_call_id": "c1", "content": "ok",
         "imageData": {"base64": "AAA", "mediaType": "image/png"}},
    ]
    out = responses.inputMessages(msgs)
    assert out == [
        REASONING,
        {"type": "function_call_output", "call_id": "c1", "output": "ok"},
    ]
    for item in out:
        assert "responseItems" not in item
        assert "reasoningContent" not in item
        assert "imageData" not in item
        assert "reasoning_content" not in item
