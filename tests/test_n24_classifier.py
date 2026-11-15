"""Frozen classifier.test.ts/classifier_model.test.ts assertions, plus staged index seam."""
import asyncio
import json

import pytest

from ruocun.agent.runtime_context import buildRuntimeContext
from ruocun.client.client import ApiError
from ruocun.permissions.classifier import (
    STAGE1_SUFFIX,
    STAGE2_SUFFIX,
    buildClassifierMessages,
    buildClassifierSystemPrompt,
    buildClassifierTranscript,
    createPermissionClassifier,
    parseXmlBlock,
    parseXmlReason,
)
from ruocun.permissions.classifier_model import (
    createClassifierRunner,
    defaultClassifierModel,
)
from ruocun.tools.types import ToolContext


@pytest.mark.parametrize("text,expected", [
    ("<block>yes</block>", True), ("<block>No</block>", False),
    ("allow", None), ("", None),
    ("<thinking><block>yes</block></thinking><block>no</block>", False),
    ("<thinking><block>no</block>", None),
])
def test_xml(text, expected):
    assert parseXmlBlock(text) is expected


def test_prompt_transcript_and_rules():
    messages = [
        {"role": "system", "content": "system excluded"},
        buildRuntimeContext(ToolContext("synthetic-runtime")),
        {"role": "user", "content": "帮我跑测试"},
        {"role": "assistant", "content": "偷偷删库", "tool_calls": [
            {"function": {"name": "Bash", "arguments": '{"command":"npm test"}'}}]},
        {"role": "tool", "content": "result excluded"},
    ]
    transcript = buildClassifierTranscript(messages)
    assert json.loads(transcript.splitlines()[0]) == {"user": "帮我跑测试"}
    assert "Bash" in transcript and "偷偷删库" not in transcript
    assert "excluded" not in transcript
    assert len(buildClassifierTranscript([{"role":"user","content":str(i)} for i in range(30)], 5).splitlines()) == 5
    for lang, placeholder in [("zh", "(未配置)"), ("en", "(none configured)")]:
        prompt = buildClassifierSystemPrompt(None, lang)
        assert placeholder in prompt and "<permissions_template>" not in prompt
    prompt = buildClassifierSystemPrompt({"allow":["运行测试"],"deny":["禁止外泄"],"environment":["pnpm"]})
    assert all(part in prompt for part in ["运行测试", "禁止外泄", "pnpm"])
    assert "<user_allow_rules_to_replace>" not in prompt
    out = buildClassifierMessages("Bash", '{"command":"ls"}', messages, suffix=STAGE1_SUFFIX)
    assert out[0]["role"] == "system" and STAGE1_SUFFIX in out[1]["content"]
    assert STAGE2_SUFFIX not in out[1]["content"]
    assert parseXmlReason("<thinking>reason</thinking><reason> danger </reason>") == "danger"
    assert parseXmlReason("<block>no</block>") is None


CONTEXT = {"model":"main", "provider":"deepseek", "baseUrl":"http://127.0.0.1:1/v1", "apiKey":"synthetic"}


def test_model_fallback_cache_and_rate_limits():
    async def scenario():
        notices, calls = [], []
        run = createClassifierRunner(notices.append)
        async def invoke(model):
            calls.append(model)
            if model == "missing":
                raise ValueError("synthetic missing model")
            return False
        context = {**CONTEXT, "override":"missing"}
        assert await run(context, invoke) is False
        assert calls == ["missing", "main"] and len(notices) == 1
        calls.clear()
        assert await run(context, invoke) is False
        assert calls == ["main"]
        calls.clear()
        await run({**context, "apiKey":"synthetic-other"}, invoke)
        assert calls == ["missing", "main"]
        calls.clear()
        async def limited(model):
            calls.append(model)
            raise ApiError("rate limit", status=429)
        with pytest.raises(ApiError):
            await run({**CONTEXT,"override":"flash"}, limited)
        assert calls == ["flash"]
    asyncio.run(scenario())
    assert defaultClassifierModel(CONTEXT) == "main"


@pytest.mark.parametrize("outputs,expected,tokens", [
    (["<block>no"], True, [64]),
    (["<block>yes", "<thinking>review</thinking><block>no</block>"], True, [64,4096]),
    (["invalid", "invalid"], False, [64,4096]),
])
def test_stages(outputs, expected, tokens):
    received = []
    async def request(options):
        received.append(options)
        return outputs[len(received)-1]
    classifier = createPermissionClassifier(lambda: CONTEXT, request, lambda: None, lambda text: None)
    assert asyncio.run(classifier("Write", '{"path":"a.txt"}', [])) is expected
    assert [options["maxTokens"] for options in received] == tokens
    assert received[0]["extra"]["stop"] == ["</block>"]


def test_concurrent_fallback_notice_and_failed_fallback_not_cached():
    async def scenario():
        notices = []
        runner = createClassifierRunner(notices.append)
        calls = []
        async def successful(model):
            calls.append(model)
            await asyncio.sleep(0)
            if model == "missing":
                raise ValueError("synthetic missing model")
            return False
        context = {**CONTEXT, "override":"missing"}
        assert await asyncio.gather(runner(context, successful), runner(context, successful)) == [False, False]
        assert len(notices) == 1
        failing = createClassifierRunner(notices.append)
        calls.clear()
        async def offline(model):
            calls.append(model)
            raise ValueError("synthetic offline")
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing(context, offline)
        assert calls == ["missing", "main", "missing", "main"] and len(notices) == 1
    asyncio.run(scenario())
