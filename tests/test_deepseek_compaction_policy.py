"""Public compaction policy and pure candidate behavior, synthetic inputs only."""

import asyncio
import copy

import pytest


def test_default_budget_keeps_a_small_window_usable_with_the_actual_output_limit():
    from ruocun.agent.compaction_policy import resolveCompactionBudget

    budget = resolveCompactionBudget(1000, 128000, output_explicit=False)
    assert (budget.output_limit, budget.headroom_tokens, budget.threshold_tokens,
            budget.retain_tokens, budget.summary_max_tokens) == (250, 60, 690, 120, 172)


def test_explicit_output_is_preserved_and_an_impossible_reservation_is_rejected():
    from ruocun.agent.compaction_policy import resolveCompactionBudget

    budget = resolveCompactionBudget(1000, 300)
    assert (budget.output_limit, budget.threshold_tokens, budget.retain_tokens) == (300, 644, 112)
    with pytest.raises(ValueError, match="output"):
        resolveCompactionBudget(1000, 1000)


def test_native_budget_overrides_are_applied_and_conflicting_or_nonfinite_values_rejected():
    from ruocun.agent.compaction_policy import resolveCompactionBudget

    budget = resolveCompactionBudget(1000, 300, env={
        "RUOCUN_COMPACT_THRESHOLD_RATIO": ".7", "RUOCUN_COMPACT_HEADROOM_TOKENS": "40",
        "RUOCUN_COMPACT_RETAIN_TOKENS": "60", "RUOCUN_COMPACT_SUMMARY_MAX_TOKENS": "144",
    })
    assert (budget.threshold_tokens, budget.retain_tokens, budget.summary_max_tokens) == (660, 60, 144)
    with pytest.raises(ValueError, match="RETAIN"):
        resolveCompactionBudget(1000, 300, env={
            "RUOCUN_COMPACT_RETAIN_TOKENS": "60", "RUOCUN_COMPACT_RETAIN_RATIO": ".1",
        })
    with pytest.raises(ValueError, match="THRESHOLD"):
        resolveCompactionBudget(1000, 300, env={"RUOCUN_COMPACT_THRESHOLD_RATIO": "NaN"})


def test_request_meter_counts_final_tools_and_prices_images_without_counting_base64_bytes():
    from ruocun.agent.compaction_policy import estimateRequestTokens

    small = {"messages": [{"role": "user", "content": "abcabc"}], "max_tokens": 999999}
    assert estimateRequestTokens(small) == 6
    assert estimateRequestTokens({**small, "tools": [{"type": "function", "function": {
        "name": "Read", "description": "读取合成材料" * 100,
    }}]}) > 200
    short_image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,QQ=="}}
    large_image = {"type": "image_url", "image_url": {"url": "data:image/png;base64," + "Q" * 50000}}
    assert estimateRequestTokens({"messages": [{"role": "user", "content": [short_image]}]}) == 1028
    assert estimateRequestTokens({"input": [{"role": "user", "content": [large_image]}]}) == 1028


def test_candidate_merges_old_summary_preserves_the_hook_and_a_complete_recent_tool_group():
    from ruocun.agent.compact import buildCompaction

    messages = [
        {"role": "system", "content": "SYSTEM"},
        {"role": "system", "content": "[[ruocun:session-start-hook]]\nCURRENT HOOK"},
        {"role": "system", "content": "[早期对话摘要]\n" + "过时进度与待核事实" * 100},
        {"role": "system", "content": "[当前任务清单]\n旧任务"},
        {"role": "user", "content": "旧请求" * 300},
        {"role": "assistant", "content": "旧调查结果" * 300},
        {"role": "user", "content": "保留最新请求和最新错误的原文"},
        {"role": "assistant", "content": "", "reasoningContent": "reasoning",
         "responseItems": [{"type": "reasoning", "encrypted_content": "synthetic"}],
         "tool_calls": [{"id": value, "type": "function", "function": {"name": "Read", "arguments": "{}"}}
                        for value in ("a", "b")]},
        {"role": "tool", "tool_call_id": "a", "content": "latest-a"},
        {"role": "tool", "tool_call_id": "b", "content": "latest-error"},
    ]
    original = copy.deepcopy(messages)

    async def summarize(received):
        assert any("过时进度" in str(item.get("content")) for item in received)
        return "目前只保留已经核实的事实。"

    candidate = asyncio.run(buildCompaction(messages, {"summarize": summarize, "retainTokens": 40}, "▶ 新任务"))
    assert candidate.status == "summarized"
    assert candidate.messages[:2] == messages[:2]
    assert candidate.messages[-5:-1] == messages[-4:]
    assert candidate.messages[-1]["content"] == "[当前任务清单]\n▶ 新任务"
    assert "过时进度" not in candidate.messages[2]["content"]
    assert candidate.origins[:2] == (0, 1)
    assert candidate.replacements[0].old_indices == (0, 1, 2, 3, 4, 5)
    assert candidate.after_tokens < candidate.before_tokens
    assert messages == original


def test_tool_pruning_can_relieve_pressure_without_a_summary_and_retains_its_source_mapping():
    from ruocun.agent.compact import buildCompaction

    full = "H" * 4096 + "M" * 10000 + "T" * 1024
    messages = [
        {"role": "system", "content": "SYS"}, {"role": "user", "content": "核对输出"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "read", "type": "function",
         "function": {"name": "Read", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "read", "content": full,
         "imageData": {"base64": "Qg==", "mediaType": "image/png"}, "imageDelivered": True},
    ]
    original = copy.deepcopy(messages)

    async def unnecessary_summary(_messages):
        pytest.fail("sufficient deterministic reduction must not call the model")

    candidate = asyncio.run(buildCompaction(messages, {
        "summarize": unnecessary_summary, "retainTokens": 40, "thresholdTokens": 3000,
        "archiveIdForRange": lambda indices, kind: "saved-read-result",
    }))
    assert candidate.status == "pruned" and candidate.after_tokens < 3000
    assert candidate.messages[3]["content"].startswith("H" * 4096)
    assert "T" * 1024 in candidate.messages[3]["content"] and "M" * 100 not in candidate.messages[3]["content"]
    assert "ArchiveRead" in candidate.messages[3]["content"] and "saved-read-result" in candidate.messages[3]["content"]
    assert candidate.messages[3]["imageData"] == original[3]["imageData"]
    assert candidate.messages[3]["imageDelivered"] is True
    assert candidate.origins == (0, 1, 2, None)
    assert candidate.replacements[0].old_indices == (3,)
    assert messages == original


def test_pruning_text_blocks_preserves_nontext_blocks_and_uses_one_shared_text_budget():
    from ruocun.agent.compact import buildCompaction

    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,Qg=="}}
    messages = [
        {"role": "system", "content": "SYS"}, {"role": "user", "content": "read"},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "a", "type": "function",
         "function": {"name": "Read", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "a", "content": [
            {"type": "text", "text": "H" * 4096 + "M" * 5000}, image,
            {"type": "text", "text": "M" * 5000 + "T" * 1024},
        ]},
    ]

    async def no_summary(_messages):
        pytest.fail("the text-block reduction alone fits")

    candidate = asyncio.run(buildCompaction(messages, {
        "summarize": no_summary, "thresholdTokens": 3500,
    }))
    assert candidate.status == "pruned"
    parts = candidate.messages[-1]["content"]
    assert image in parts
    text = "".join(part["text"] for part in parts if part["type"] == "text")
    assert text.startswith("H" * 4096) and "T" * 1024 in text
    assert "M" * 10 not in text and text.count("中间已省略") == 1


def test_schema_property_names_contribute_to_current_request_pressure():
    from ruocun.agent.compaction_policy import estimateRequestTokens

    body = {"messages": [], "tools": [{"type": "function", "function": {
        "name": "Read", "parameters": {"type": "object", "properties": {
            "property_" + "x" * 900: {"type": "string"},
        }},
    }}]}
    assert estimateRequestTokens(body) > 300


def test_pressure_with_only_an_existing_checkpoint_reports_no_safe_progress():
    from ruocun.agent.compact import CompactionError, buildCompaction

    messages = [{"role": "system", "content": "SYS"},
                {"role": "system", "content": "[早期对话摘要]\n" + "fact" * 2000}]

    async def unused(_messages):
        pytest.fail("the only retained checkpoint is not a safely replaceable old region")

    with pytest.raises(CompactionError, match="旧区段"):
        asyncio.run(buildCompaction(messages, {"summarize": unused, "thresholdTokens": 100}))


def test_recent_region_is_selected_after_tool_reduction_using_the_same_meter():
    from ruocun.agent.compact import buildCompaction

    messages = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "old request" * 300},
        {"role": "assistant", "content": "old answer" * 300},
        {"role": "user", "content": "latest request" * 15},
        {"role": "assistant", "content": "", "tool_calls": [{"id": "a", "type": "function",
         "function": {"name": "Read", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "a", "content": "H" * 4096 + "M" * 10000 + "T" * 1024},
    ]

    async def summarize(_messages):
        return "Earlier work is complete."

    candidate = asyncio.run(buildCompaction(messages, {
        "summarize": summarize, "thresholdTokens": 2000, "retainTokens": 1750,
    }))
    assert candidate.status == "summarized"
    assert candidate.messages[-3] == messages[3]
    assert candidate.replacements[0].old_indices == (0, 1, 2)
