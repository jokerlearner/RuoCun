"""Frozen validate_key.test.ts provider probes and gateway list assertions."""
import asyncio
import json

import pytest

from ruocun.config.validate_key import fetchModels, validateCredential


@pytest.mark.parametrize("provider", [None, "volcengine", "qianfan", "zhipu"])
def test_provider_probe_and_default_model(provider):
    seen = []

    async def fetch(url, headers, body):
        seen.append((url, headers, body))
        return 200, b""

    result = asyncio.run(validateCredential({"baseUrl": "https://synthetic.invalid", "key": "synthetic-key", "provider": provider}, fetch))
    assert result == {"ok": True}
    url, headers, body = seen[0]
    assert headers["Authorization"] == "Bearer synthetic-key"
    assert url.endswith("/chat/completions" if provider else "/models")
    if provider == "zhipu":
        assert body["model"] == "glm-5.3"


def test_official_responses_probe_and_custom_selected_model():
    seen = []

    async def fetch(url, headers, body):
        seen.append((url, body))
        return 200, b""

    asyncio.run(validateCredential({"baseUrl": "https://api.openai.com/v1", "key": "synthetic", "provider": "openai", "model": "gpt-6.1-sol"}, fetch))
    assert seen[0][0] == "https://api.openai.com/v1/responses"
    assert seen[0][1]["max_output_tokens"] == 16 and "max_tokens" not in seen[0][1]
    asyncio.run(validateCredential({"baseUrl": "https://synthetic.invalid", "key": "synthetic", "model": "GLM-5.3-joybuilder"}, fetch))
    assert seen[1][1]["model"] == "GLM-5.3-joybuilder"


@pytest.mark.parametrize("status,expected", [(401, {"ok": False, "reason": "invalid"}), (500, {"ok": False, "reason": "http", "status": 500})])
def test_probe_http_results(status, expected):
    async def fetch(url, headers, body):
        return status, b""

    assert asyncio.run(validateCredential({"baseUrl": "https://synthetic.invalid", "key": "synthetic"}, fetch)) == expected


def test_network_failure_and_gateway_models():
    async def unreachable(url, headers, body):
        raise OSError("synthetic failure")

    assert asyncio.run(validateCredential({"baseUrl": "https://synthetic.invalid", "key": "synthetic"}, unreachable)) == {"ok": False, "reason": "unreachable"}
    assert asyncio.run(fetchModels("https://synthetic.invalid", "synthetic", unreachable)) == []

    async def fetch(url, headers, body):
        assert url.endswith("/models") and headers["Authorization"] == "Bearer synthetic"
        assert body is None
        return 200, json.dumps({"data": [{"id": "first"}, {"id": 42}, {"id": ""}, {}, {"id": "second"}]}).encode()

    assert asyncio.run(fetchModels("https://synthetic.invalid", "synthetic", fetch)) == ["first", "second"]
