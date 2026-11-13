"""独立边界：冻结源码的 Number(header) 与 yieldedAny 只由渲染 delta 设置。"""
import json

import pytest

from ruocun.client import client
from ruocun.client.resilient import ResilientContext


def options():
    return {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic", "model": "synthetic",
            "messages": [], "maxRetries": 1, "retryDelayMs": 0}


def success():
    return client.HttpResponse(200, {}, [
        b'data: {"choices":[{"delta":{"content":"recovered"}}]}\n\n'
    ])


def test_fallback_parse_error_does_not_inherit_previous_http_429():
    calls = []

    def send(*_args):
        calls.append(1)
        if len(calls) == 1:
            return client.HttpResponse(429, {"retry-after": "0"}, [])
        return client.HttpResponse(200, {}, [b"synthetic-invalid-json"])

    opts = {**options(), "maxRetries": 0}
    with pytest.raises(Exception) as failed:
        client.streamChat(opts, transport=send, env={},
                          context=ResilientContext(sleep=lambda _: None))
    assert len(calls) == 2
    assert getattr(failed.value, "status", None) is None, "source only preserves fallback error status"


@pytest.mark.parametrize("header", ["0x0", "0b0"])
def test_retry_after_uses_frozen_javascript_number(header):
    calls = []

    def send(*_args):
        calls.append(1)
        return client.HttpResponse(429, {"retry-after": header}, []) if len(calls) == 1 else success()

    result = client.streamChat(options(), transport=send, env={},
                              context=ResilientContext(sleep=lambda _: None, jitter_ms=lambda: 0))
    assert result.message["content"] == "recovered"
    assert len(calls) == 2


@pytest.mark.parametrize("fragment", [{"index": 0, "id": "synthetic-call"},
                                    {"index": 0, "function": {"arguments": "{"}}])
@pytest.mark.parametrize("error_class", [ConnectionResetError, client.StreamDisconnected])
def test_tool_fragment_without_rendered_delta_remains_retryable(fragment, error_class):
    calls = []

    def broken():
        yield ("data: " + json.dumps({"choices": [{"delta": {"tool_calls": [fragment]}}]}) + "\n\n").encode()
        raise error_class("synthetic socket closed unexpectedly")

    def send(*_args):
        calls.append(1)
        return client.HttpResponse(200, {}, broken()) if len(calls) == 1 else success()

    result = client.streamChat(options(), transport=send, env={},
                              context=ResilientContext(sleep=lambda _: None, jitter_ms=lambda: 0))
    assert len(calls) == 2, "source yieldedAny remains false until an actual render delta"
    assert result.message["content"] == "recovered"
