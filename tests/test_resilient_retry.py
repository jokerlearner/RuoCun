"""WIRE-07 · 重试循环 / 非流式 fallback / 部分输出不重复（独立来源）。

预期来源（冻结 ``src/client/client.ts`` 与 ``client.test.ts``）：
- ``:338-350`` 首次 socket 瞬断自动重试、第二次成功（calls=2, content="hi"）。
- ``:352-359`` 持续失败：流式重试耗尽 + 非流式兜底也失败 → 清晰错误，calls=4
  （1 + 2 重试 + 1 兜底，对应 ``maxRetries=2``）。
- ``:361-381`` 流式持续失败 → 非流式兜底成功（streamCalls=2/nonStreamCalls=1、
  content="recovered"、兜底内容也显示、非流式 usage 也计入）。
- ``:383-397`` 非流式兜底恢复 tool_calls（maxRetries=0）。
- ``:556-569`` 流中途断开：返回已累积部分，不抛错、不重试（content="part", calls=1）。
- ``:271-278,346-347`` 产出后不再重试（避免重复内容）；ADR-0003 未知结果不自动重放。
按 S/D/R 改写 TS 断言；期望是冻结 fixture 的字面量，未从 Python 输出回填。
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ruocun.client import client
from ruocun.client import resilient as r

BASE: dict[str, Any] = {"baseUrl": "https://x", "apiKey": "sk", "model": "deepseek-v4-pro"}


def _opts(**kw: Any) -> dict[str, Any]:
    return {**BASE, "messages": [{"role": "user", "content": "hi"}], **kw}


def _sse(payload: dict[str, Any] | str) -> bytes:
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return ("data: " + body + "\n\n").encode("utf-8")


def _ok(*payloads: dict[str, Any] | str) -> client.HttpResponse:
    return client.HttpResponse(200, {}, iter([_sse(p) for p in payloads]))


class _Script:
    """按调用序号返回脚本项（异常则抛出），超出重复最后一项；记录每次请求。"""

    def __init__(self, items: list[Any]) -> None:
        self.items = items
        self.calls: list[tuple[str, dict[str, str], bytes]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        self.calls.append((url, headers, body))
        index = min(len(self.calls) - 1, len(self.items) - 1)
        item = self.items[index]
        if isinstance(item, BaseException):
            raise item
        return item


def _ctx(**kw: Any) -> r.ResilientContext:
    return r.ResilientContext(sleep=lambda _s: None, jitter_ms=lambda: 0.0, **kw)


def _texts(deltas: list[dict[str, Any]], kind: str = "content") -> list[str]:
    return [str(d["text"]) for d in deltas if d.get("kind") == kind]


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:338-350
# ---------------------------------------------------------------------------


def test_transient_socket_error_retried_once_then_success():
    script = _Script([
        RuntimeError("The socket connection was closed unexpectedly"),
        _ok({"choices": [{"delta": {"content": "hi"}}]}, "[DONE]"),
    ])
    result = r.streamChatResilient(
        _opts(maxRetries=2, retryDelayMs=0), transport=script, context=_ctx(),
    )
    assert len(script.calls) == 2                       # 冻结 :348
    assert result.status == "complete"
    assert result.message["content"] == "hi"            # 冻结 :349
    assert [a.outcome for a in result.attempts] == ["retry", "complete"]
    assert result.content_duplicated is False
    assert result.replayed is False


def test_native_connection_reset_retries_without_english_error_message():
    script = _Script([
        ConnectionResetError("连接被重置"),
        _ok({"choices": [{"delta": {"content": "ok"}}]}, "[DONE]"),
    ])
    result = r.streamChatResilient(
        _opts(maxRetries=1), transport=script, context=_ctx(), env={},
    )
    assert result.status == "complete"
    assert result.message["content"] == "ok"
    assert len(script.calls) == 2


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:352-359
# ---------------------------------------------------------------------------


def test_persistent_failure_exhausts_retries_and_fallback_then_clear_error():
    script = _Script([RuntimeError("fetch failed")])
    result = r.streamChatResilient(
        _opts(maxRetries=2, retryDelayMs=0), transport=script, context=_ctx(),
    )
    assert result.status == "failed"
    assert "重试" in (result.error or "") and "非流式" in (result.error or "")
    assert result.exit_code != 0
    assert len(script.calls) == 4                       # 冻结 :358：1 + 2 流式重试 + 1 兜底
    assert result.fallback_used is True
    assert result.content_duplicated is False


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:361-381
# ---------------------------------------------------------------------------


def test_stream_fails_then_nonstream_fallback_succeeds():
    stream_calls = 0
    non_stream_calls = 0
    seen: dict[str, Any] = {}

    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        nonlocal stream_calls, non_stream_calls
        parsed = json.loads(body)
        if parsed.get("stream"):
            stream_calls += 1
            raise RuntimeError("fetch failed: ECONNRESET")
        non_stream_calls += 1
        # 冻结 :367-370 的非流式响应体
        return client.HttpResponse(200, {}, iter([json.dumps({
            "choices": [{"message": {"role": "assistant", "content": "recovered"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }).encode("utf-8")]))

    result = r.streamChatResilient(
        _opts(maxRetries=1, retryDelayMs=0, onUsage=lambda u: seen.update(u)),
        transport=transport, context=_ctx(),
    )
    assert stream_calls == 2                            # 冻结 :376：1 + 1 retry
    assert non_stream_calls == 1                       # 冻结 :377
    assert result.status == "complete"
    assert result.message["content"] == "recovered"     # 冻结 :378
    assert "recovered" in _texts(result.deltas)         # 冻结 :379 兜底内容也显示
    assert seen.get("prompt_tokens") == 5               # 冻结 :380 非流式 usage 也计入
    assert result.usage is not None and result.usage["prompt_tokens"] == 5
    assert result.fallback_used is True


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:383-397
# ---------------------------------------------------------------------------


def test_nonstream_fallback_restores_tool_calls():
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        parsed = json.loads(body)
        if parsed.get("stream"):
            raise RuntimeError("fetch failed")
        return client.HttpResponse(200, {}, iter([json.dumps({
            "choices": [{"message": {
                "role": "assistant", "content": None,
                "tool_calls": [{"id": "c1", "type": "function",
                                "function": {"name": "Read", "arguments": "{}"}}],
            }}],
        }).encode("utf-8")]))

    result = r.streamChatResilient(
        _opts(maxRetries=0, retryDelayMs=0), transport=transport, context=_ctx(),
    )
    assert result.status == "complete"
    assert result.message["tool_calls"][0]["function"]["name"] == "Read"  # 冻结 :395
    assert any(d.get("kind") == "tool_call" and d.get("name") == "Read"
               for d in result.deltas)                                     # 冻结 :396


def test_responses_route_nonstream_fallback_keeps_output_and_usage():
    seen = []

    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        parsed = json.loads(body)
        seen.append((url, parsed["stream"]))
        if parsed["stream"]:
            raise RuntimeError("fetch failed")
        return client.HttpResponse(200, {}, [json.dumps({
            "status": "completed",
            "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "done"}]},
                {"type": "function_call", "call_id": "c1", "name": "Read", "arguments": "{}"},
                {"type": "reasoning", "id": "r1"},
            ],
            "usage": {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7},
        }).encode("utf-8")])

    result = r.streamChatResilient(
        _opts(baseUrl="https://api.openai.com/v1", model="gpt-6.1-sol", maxRetries=0),
        transport=transport, context=_ctx(), env={},
    )
    assert seen == [("https://api.openai.com/v1/responses", True),
                    ("https://api.openai.com/v1/responses", False)]
    assert result.status == "complete" and result.message["content"] == "done"
    assert result.message["tool_calls"][0]["function"]["name"] == "Read"
    assert result.message["responseItems"][0]["id"] == "r1"
    assert result.usage is not None and result.usage["prompt_tokens"] == 5


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:556-569 + ADR-0003（已产出部分不重放、不重复）
# ---------------------------------------------------------------------------


def test_mid_stream_disconnect_keeps_partial_and_never_retries():
    calls = 0

    def gen():
        yield _sse({"choices": [{"delta": {"content": "part"}}]})
        raise client.StreamDisconnected("断流")

    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        nonlocal calls
        calls += 1
        return client.HttpResponse(200, {}, gen())

    result = r.streamChatResilient(
        _opts(maxRetries=2, retryDelayMs=0), transport=transport, context=_ctx(),
    )
    assert result.message["content"] == "part"          # 冻结 :567
    assert calls == 1                                   # 冻结 :568 已产出内容 → 不重试
    assert result.status == "partial"                   # 明确标记，不伪报成功
    assert result.content_duplicated is False
    assert result.replayed is False                     # ADR-0003 未知结果不自动重放


def test_ruocun_idle_environment_takes_precedence_over_dao():
    now = [0.0]

    def delayed_chunks():
        now[0] = 0.05
        yield _sse({"choices": [{"delta": {"content": "ok"}}]})
        yield _sse("[DONE]")

    result = r.streamChatResilient(
        _opts(maxRetries=0),
        transport=lambda *_args: client.HttpResponse(200, {}, delayed_chunks()),
        env={"RUOCUN_STREAM_IDLE_MS": "1000", "DAO_STREAM_IDLE_MS": "10"},
        context=_ctx(clock=lambda: now[0]),
    )
    assert result.status == "complete"
    assert result.message["content"] == "ok"


@pytest.mark.parametrize(("raw", "times_out", "seconds"), [
    ("", False, None), ("0", False, None), ("NaN", False, None),
    ("-1", True, "0"), ("Infinity", True, "Infinity"),
    ("-Infinity", True, "-Infinity"), ("0.1", True, "0"),
    ("2147483648", True, "2147484"), ("0x10", False, None),
])
def test_idle_environment_matches_frozen_node_number_and_timer(raw, times_out, seconds):
    now = [0.0]

    def chunks():
        now[0] = 0.002
        yield _sse({"choices": [{"delta": {"content": "ok"}}]})
        yield _sse("[DONE]")

    def transport(_url, _headers, body):
        if json.loads(body)["stream"]:
            return client.HttpResponse(200, {}, chunks())
        return client.HttpResponse(400, {}, [])

    result = r.streamChatResilient(
        _opts(maxRetries=0), transport=transport,
        env={"RUOCUN_STREAM_IDLE_MS": raw}, context=_ctx(clock=lambda: now[0]),
    )
    assert (result.status == "failed") is times_out
    if times_out:
        assert f"({seconds}s " in (result.error or "")
    else:
        assert result.message["content"] == "ok"


def test_already_cancelled_request_does_not_start_transport():
    calls = []

    def transport(*_args):
        calls.append(1)
        return _ok("[DONE]")

    result = r.streamChatResilient(
        _opts(), transport=transport, env={}, context=_ctx(cancel=lambda: True),
    )
    assert result.cancelled is True
    assert calls == []


def test_deltas_are_delivered_before_the_stream_finishes():
    observed = []

    def chunks():
        yield _sse({"choices": [{"delta": {"content": "first"}}]})
        assert observed == [{"kind": "content", "text": "first"}]
        yield _sse("[DONE]")

    result = r.streamChatResilient(
        _opts(), transport=lambda *_args: client.HttpResponse(200, {}, chunks()),
        context=_ctx(on_delta=observed.append), env={},
    )
    assert result.status == "complete"
    assert result.message["content"] == "first"


def test_public_cancel_between_coalesced_frames_keeps_only_first_delta():
    cancelled = [False]
    observed = []

    def on_delta(delta):
        observed.append(delta)
        cancelled[0] = True

    frames = (_sse({"choices": [{"delta": {"content": "first"}}]})
              + _sse({"choices": [{"delta": {"content": "late"}}]})
              + _sse("[DONE]"))
    result = client.streamChat(
        _opts(), transport=lambda *_args: client.HttpResponse(200, {}, [frames]),
        context=_ctx(on_delta=on_delta, cancel=lambda: cancelled[0]), env={},
    )
    assert result.status == "partial"
    assert result.message["content"] == "first"
    assert observed == [{"kind": "content", "text": "first"}]
