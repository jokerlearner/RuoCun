"""Frozen client.ts uses AbortSignal.timeout before sending the fallback request."""

import json
import math

import pytest

from ruocun.client import client
from ruocun.client.resilient import ResilientContext


@pytest.mark.parametrize("delay", [-1, -math.inf, math.inf, math.nan, 0.1,
                                 4294967296, 9007199254740992])
def test_invalid_abort_timeout_prevents_fallback_transport(delay):
    # Node 22 AbortSignal.timeout: integer delay in [0, 4294967295].
    calls = []

    def transport(_url, _headers, body):
        calls.append(json.loads(body)["stream"])
        if calls[-1]:
            return client.HttpResponse(503, {}, [])
        return client.HttpResponse(200, {}, [
            b'{"choices":[{"message":{"role":"assistant","content":"fallback"}}]}'
        ])

    with pytest.raises(RuntimeError, match="delay") as caught:
        client.streamChat(
            {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic",
             "model": "synthetic", "messages": [], "maxRetries": 0,
             "idleTimeoutMs": delay},
            transport=transport, env={},
            context=ResilientContext(clock=lambda: 0.0, sleep=lambda _: None),
        )
    assert calls == [True]
    assert getattr(caught.value, "status", None) is None


@pytest.mark.parametrize("delay", [0, 1, 4294967295])
def test_valid_abort_timeout_keeps_fallback_available(delay):
    calls = []

    def transport(_url, _headers, body):
        calls.append(json.loads(body)["stream"])
        if calls[-1]:
            return client.HttpResponse(503, {}, [])
        return client.HttpResponse(200, {}, [
            b'{"choices":[{"message":{"role":"assistant","content":"fallback"}}]}'
        ])

    result = client.streamChat(
        {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic",
         "model": "synthetic", "messages": [], "maxRetries": 0,
         "idleTimeoutMs": delay},
        transport=transport, env={},
        context=ResilientContext(clock=lambda: 0.0, sleep=lambda _: None),
    )
    assert calls == [True, False]
    assert result.message["content"] == "fallback"
