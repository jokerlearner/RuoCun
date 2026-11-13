"""Frozen config/validate_key.ts (MIT), provider auth and gateway model probes."""
from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, cast

from ..client.responses import buildResponsesRequest, usesResponses
from .profiles import DEFAULTS, Provider

Fetch = Callable[[str, dict[str, str], dict[str, Any] | None], Awaitable[tuple[int, bytes]]]


async def _fetch(url: str, headers: dict[str, str], body: dict[str, Any] | None) -> tuple[int, bytes]:
    def perform() -> tuple[int, bytes]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            try:
                return error.code, b""
            finally:
                error.close()

    return await asyncio.to_thread(perform)


async def validateCredential(cred: Mapping[str, Any], fetchImpl: Fetch = _fetch) -> dict[str, Any]:
    try:
        base = str(cred["baseUrl"])
        provider = cred.get("provider")
        headers = {"Authorization": f"Bearer {cred['key']}"}
        body = None
        if cred.get("model") or provider in {"volcengine", "qianfan", "zhipu"}:
            model = cred.get("model") or DEFAULTS[cast(Provider, provider)]["model"]
            responses = usesResponses(base, model)
            body = {"model": model, "messages": [{"role": "user", "content": "1"}],
                    "max_tokens": 16 if responses else 1}
            if responses:
                body = buildResponsesRequest(body)
                body.pop("stream", None)
            url = base + ("/responses" if responses else "/chat/completions")
            headers["Content-Type"] = "application/json"
        else:
            url = base + "/models"
        status, _ = await fetchImpl(url, headers, body)
    except Exception:
        return {"ok": False, "reason": "unreachable"}
    if 200 <= status < 300:
        return {"ok": True}
    if status in {401, 403}:
        return {"ok": False, "reason": "invalid"}
    return {"ok": False, "reason": "http", "status": status}


async def fetchModels(baseUrl: str, key: str, fetchImpl: Fetch = _fetch) -> list[str]:
    try:
        status, raw = await fetchImpl(baseUrl + "/models", {"Authorization": f"Bearer {key}"}, None)
        if not 200 <= status < 300:
            return []
        data = json.loads(raw)
        rows = data.get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            return []
        return [row["id"] for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"]]
    except Exception:
        return []
