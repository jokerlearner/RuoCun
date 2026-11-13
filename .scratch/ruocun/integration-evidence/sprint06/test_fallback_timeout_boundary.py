"""独立预期：冻结 client.ts 在 fallback fetch 前构造 AbortSignal.timeout。"""

import json

import pytest

from ruocun.client import client
from ruocun.client.resilient import ResilientContext


@pytest.mark.parametrize("raw,explicit", [
    ("-1", False), ("Infinity", False), ("-Infinity", False), ("0.1", False),
    ("4294967296", False), ("9007199254740992", False), ("NaN", True),
])
def test_invalid_fallback_timeout_prevents_transport(raw, explicit):
    calls = []
    failure = None

    def transport(_url, _headers, body):
        streaming = json.loads(body)["stream"]
        calls.append(streaming)
        if streaming:
            return client.HttpResponse(503, {}, [])
        return client.HttpResponse(200, {}, [
            b'{"choices":[{"message":{"role":"assistant","content":"synthetic"}}]}'
        ])

    try:
        opts = {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic", "model": "synthetic",
                "messages": [], "maxRetries": 0}
        if explicit:
            opts["idleTimeoutMs"] = float(raw)
        client.streamChat(
            opts, transport=transport, env={"RUOCUN_STREAM_IDLE_MS": raw},
            context=ResilientContext(clock=lambda: 0.0, sleep=lambda _: None),
        )
    except Exception as exc:
        failure = exc
    assert calls == [True], "AbortSignal.timeout invalid value must prevent fallback fetch"
    assert failure is not None, "public entry must expose the fallback construction failure"


@pytest.mark.parametrize("raw", ["1", "2147483648", "4294967295", "NaN"])
def test_valid_or_environment_nan_timeout_still_allows_fallback(raw):
    calls = []

    def transport(_url, _headers, body):
        calls.append(json.loads(body)["stream"])
        if calls[-1]:
            return client.HttpResponse(503, {}, [])
        return client.HttpResponse(200, {}, [
            b'{"choices":[{"message":{"role":"assistant","content":"synthetic"}}]}'
        ])

    result = client.streamChat(
        {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic", "model": "synthetic",
         "messages": [], "maxRetries": 0},
        transport=transport, env={"RUOCUN_STREAM_IDLE_MS": raw},
        context=ResilientContext(clock=lambda: 0.0, sleep=lambda _: None),
    )
    assert calls == [True, False]
    assert result.status == "complete" and result.message["content"] == "synthetic"
