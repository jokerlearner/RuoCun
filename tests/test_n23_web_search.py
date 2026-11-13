"""Frozen src/tools/web_search.test.ts behavior via the fetchImpl public port."""

from __future__ import annotations

import asyncio
import json

import httpx

FIXTURE = '''
<div class="result">
  <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa&rut=x">Title <b>A</b></a>
  <a class="result__snippet">Snippet A &amp; more</a>
</div>
<div class="result">
  <a class="result__a" href="https://example.com/b">Title B</a>
  <a class="result__snippet">Snippet B</a>
</div>
'''


def test_source_ddg_html_result_format_limit_and_snippet_ownership():
    from ruocun.tools.registry import ToolRegistry
    from ruocun.tools.types import ToolContext
    from ruocun.tools.web_search import webSearchTool

    async def scenario():
        captured = []
        html = FIXTURE
        async def fetch(url, **kwargs):
            captured.append((url, kwargs))
            return httpx.Response(200, text=html)
        ctx = ToolContext("synthetic", fetchImpl=fetch)
        registry = ToolRegistry()
        registry.register(webSearchTool)
        async def call(**arguments):
            return await registry.dispatch("WebSearch", json.dumps({"query": "C++ 中文 /?", **arguments}), ctx)
        assert await call() == "1. Title A\n   https://example.com/a\n   Snippet A & more\n\n2. Title B\n   https://example.com/b\n   Snippet B"
        assert captured[0][0] == "https://html.duckduckgo.com/html/?q=C%2B%2B%20%E4%B8%AD%E6%96%87%20%2F%3F"
        assert captured[0][1]["headers"] == {"User-Agent": "Mozilla/5.0"} and captured[0][1]["signal"] is ctx.signal
        assert "Title B" not in await call(max_results=1)
        html = '<a class="result__a" href="https://x.com/1">First</a><a class="result__a" href="https://x.com/2">Second</a><a class="result__snippet">Snippet for second</a>'
        assert await call() == "1. First\n   https://x.com/1\n\n2. Second\n   https://x.com/2\n   Snippet for second"
        html = "<html></html>"
        assert await call() == "(无搜索结果)"
        assert webSearchTool.capability == "network" and webSearchTool.approval == "suggest"
    asyncio.run(scenario())


def test_source_search_http_failure_timeout_and_cancel_remain_readable_errors():
    from ruocun.tools.types import ToolContext
    from ruocun.tools.web_search import webSearchTool

    async def scenario():
        async def fetch(url, **kwargs):
            return httpx.Response(503, text="unavailable")
        ctx = ToolContext("synthetic", fetchImpl=fetch)
        assert await webSearchTool.handler({"query": "x"}, ctx) == "Error: 搜索失败 HTTP 503"
        async def timeout(url, **kwargs):
            raise TimeoutError()
        ctx.fetchImpl = timeout
        assert "搜索超时(30s)" in await webSearchTool.handler({"query": "x"}, ctx)
        async def cancel(url, **kwargs):
            raise InterruptedError("用户已取消")
        ctx.fetchImpl = cancel
        ctx.lang = "en"
        assert await webSearchTool.handler({"query": "x"}, ctx) == "Error: Search failed (用户已取消)"
    asyncio.run(scenario())
