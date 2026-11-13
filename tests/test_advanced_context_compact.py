"""DAO assertions with explicitly selected DeepSeek-style compaction differences."""

import asyncio
import copy

import pytest

from ruocun.agent.compact import (
    buildCompaction,
    compactMessages,
    estimateTokens,
    shouldCompact,
    stripImagesFromMessages,
)
from ruocun.client.types import ChatMessage


def test_estimate_scales_with_text_and_counts_tool_arguments():
    # 来源 estimateTokens / scales with content length and counts tool_calls args。
    assert estimateTokens([{"role": "user", "content": "abcdef"}]) > estimateTokens([
        {"role": "user", "content": "abc"},
    ])
    assert estimateTokens([{
        "role": "assistant", "content": None, "tool_calls": [{
            "id": "x", "type": "function",
            "function": {"name": "Read", "arguments": '{"path":"a"}'},
        }],
    }]) > 0


def test_compaction_only_at_or_over_threshold():
    messages = [{"role": "user", "content": "x" * 300}]
    assert shouldCompact(messages, 1000, 0.05)
    assert not shouldCompact(messages, 1000, 0.9)


def test_confirmed_policy_summarizes_old_region_and_keeps_a_verbatim_tail():
    messages = [{"role": "system", "content": "SYSTEM PREFIX"}]
    for index in range(1, 4):
        messages.extend([
            {"role": "user", "content": f"u{index}" * 300},
            {"role": "assistant", "content": f"a{index}" * 300},
        ])

    async def summarize(received: list[ChatMessage]) -> str:
        return f"SUMMARY({len(received)})"

    out = asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}))
    assert out[0] == messages[0]
    assert out[1]["role"] == "system"
    assert "早期对话摘要" in out[1]["content"]
    assert "SUMMARY(6)" in out[1]["content"]
    assert len(out) == 3 and out[-1] == messages[-1]


def test_pinned_task_list_is_reinjected_after_compaction():
    messages = [{"role": "system", "content": "SYSTEM PREFIX"}]
    for text in ("a", "b", "c"):
        messages.extend([
            {"role": "user", "content": text * 300},
            {"role": "assistant", "content": ("r" + text) * 300},
        ])

    async def summarize(_: list[ChatMessage]) -> str:
        return "早期摘要内容"

    out = asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}, "☐ 任务A\n▶ 任务B"))
    joined = "\n".join(message["content"] for message in out)
    assert "当前任务清单" in joined
    assert "任务A" in joined
    assert "早期摘要内容" in joined


def test_system_only_is_returned_unchanged():
    messages = [{"role": "system", "content": "SYSTEM PREFIX"}]

    async def summarize(received: list[ChatMessage]) -> str:
        return f"SUMMARY({len(received)})"

    assert asyncio.run(compactMessages(messages, {"summarize": summarize})) == messages


def test_prior_summary_only_is_returned_unchanged():
    messages = [
        {"role": "system", "content": "SYSTEM PREFIX"},
        {"role": "system", "content": "[早期对话摘要——旧格式示例]\n旧"},
    ]

    async def summarize(received: list[ChatMessage]) -> str:
        return f"SUMMARY({len(received)})"

    assert asyncio.run(compactMessages(messages, {"summarize": summarize})) == messages


def test_confirmed_policy_remerges_the_old_summary_instead_of_permanent_append():
    prior = "[早期对话摘要——旧格式示例]\n旧:做了 A" * 100
    messages = [
        {"role": "system", "content": "SYS"}, {"role": "system", "content": prior},
        {"role": "user", "content": "新1" * 300}, {"role": "assistant", "content": "n1" * 300},
        {"role": "user", "content": "近1" * 100}, {"role": "assistant", "content": "c1" * 100},
    ]
    received_text = ""

    async def summarize(received: list[ChatMessage]) -> str:
        nonlocal received_text
        received_text = "|".join(message["content"] for message in received)
        return "新摘要:做了 B"

    out = asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}))
    assert not out[1]["content"].startswith(prior)
    assert "[本次补充]" not in out[1]["content"]
    assert "新摘要:做了 B" in out[1]["content"]
    assert "旧:做了 A" in received_text
    assert "SYS" in received_text and "新1" in received_text


def test_image_placeholders_preserve_source_messages_and_deduplicate_adjacent_images():
    # 来源 compact.ts stripImagesFromMessages，Python 适配所需最小确认；非新增压力矩阵。
    system = {"role": "system", "content": "SYS"}
    user = {"role": "user", "content": [
        {"type": "text", "text": "看图"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,U1lOVEhFVElD"}},
        {"type": "image_url", "image_url": {"url": "https://synthetic.invalid/example.png"}},
    ]}
    messages = [system, user]
    out = stripImagesFromMessages(messages)
    assert out[0] is system
    assert out[1]["content"] == [{"type": "text", "text": "看图"}, {"type": "text", "text": "[image]"}]
    assert user["content"][1]["type"] == "image_url"

    async def summarize(received: list[ChatMessage]) -> str:
        assert received == messages
        return "图片说明已保留"

    with_tail = [*messages, {"role": "assistant", "content": "recent answer"}]
    compacted = asyncio.run(compactMessages(with_tail, {"summarize": summarize, "retainTokens": 0}))
    assert "图片说明已保留" in compacted[1]["content"]


def test_summary_receives_an_original_contiguous_prefix_and_tracks_every_source():
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,U1lOVEhFVElD"}}
    messages = [
        {"role": "system", "content": "SYSTEM PREFIX"},
        {"role": "system", "content": "[早期对话摘要]\n" + "earlier facts" * 100},
        {"role": "user", "content": "old request" * 100},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "read", "type": "function",
         "function": {"name": "Read", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "read", "content": "original tool result" * 1000},
        {"role": "system", "content": "[[ruocun:session-start-hook]]\nHOOK IN ORIGINAL POSITION"},
        {"role": "system", "content": "[当前任务清单]\nold task pin"},
        {"role": "user", "content": [{"type": "text", "text": "original image"}, image]},
        {"role": "assistant", "content": "old image analysis" * 100},
        {"role": "user", "content": "U" * 600},
        {"role": "assistant", "content": "R" * 600},
    ]
    original = copy.deepcopy(messages)

    async def summarize(received: list[ChatMessage]) -> str:
        assert received == original[:9]
        received[1]["content"] = "callback-local change"
        return "Earlier facts and image analysis."

    candidate = asyncio.run(buildCompaction(messages, {
        "summarize": summarize, "thresholdTokens": 100, "retainTokens": 300,
    }, "▶ current task"))
    assert candidate.status == "summarized"
    assert candidate.replacements[0].old_indices == (0, 1, 2, 3, 4, 5, 6, 7, 8)
    assert candidate.messages[-3:-1] == original[9:]
    assert messages == original


def test_no_pinned_task_list_is_inserted_without_pinned_argument():
    messages = [{"role": "system", "content": "SYSTEM PREFIX"}]
    for text in ("a", "b", "c"):
        messages.extend([
            {"role": "user", "content": text * 300},
            {"role": "assistant", "content": ("r" + text) * 300},
        ])

    async def summarize(_: list[ChatMessage]) -> str:
        return "x"

    out = asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}))
    assert "当前任务清单" not in "\n".join(message["content"] for message in out)


def test_system_anchor_keeps_identity_and_bytes():
    messages = [{"role": "system", "content": "SYS-ANCHOR"}]
    for text in ("旧1", "近1"):
        messages.extend([
            {"role": "user", "content": text * 300}, {"role": "assistant", "content": "a1" * 300},
        ])

    async def summarize(_: list[ChatMessage]) -> str:
        return "SUMMARY"

    out = asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}))
    assert out[0] is messages[0]
    assert out[0] == {"role": "system", "content": "SYS-ANCHOR"}
    assert out[1]["role"] == "system" and "SUMMARY" in out[1]["content"]
    assert len(out) == 3 and out[-1] == messages[-1]


def test_python_adaptation_counts_utf16_and_image_estimates():
    # 四个 UTF-16 代码单元 -> ceil(4/3)=2；单张图片 100 -> ceil(100/3)=34。
    assert estimateTokens([{"role": "user", "content": "😀😀"}]) == 2
    assert estimateTokens([{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "x"}}]}]) == 34


def test_confirmed_failure_policy_propagates_and_preserves_source_context():
    # ADR-0012 Q2 保留停止；这是明确差异的最小确认，不声称来源硬截断断言通过。
    messages = [{"role": "system", "content": "SYS"}, {"role": "user", "content": "已确认输入" * 300},
                {"role": "assistant", "content": "latest answer"}]
    failure = RuntimeError("synthetic summary unavailable")

    async def summarize(_: list[ChatMessage]) -> str:
        raise failure

    with pytest.raises(RuntimeError) as caught:
        asyncio.run(compactMessages(messages, {"summarize": summarize, "retainTokens": 0}))
    assert caught.value is failure
    assert messages == [{"role": "system", "content": "SYS"}, {"role": "user", "content": "已确认输入" * 300},
                        {"role": "assistant", "content": "latest answer"}]
