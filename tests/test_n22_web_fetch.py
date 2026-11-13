"""Frozen fetch_cache/fetch_url/fetch_extract/ssrf public behavior (MIT source)."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import httpx


def test_source_fetch_cache_ttl_and_fifo_capacity():
    from ruocun.tools.fetch_cache import (
        MAX_ENTRIES,
        clearFetchCache,
        getCachedFetch,
        setCachedFetch,
    )

    clearFetchCache()
    assert getCachedFetch("https://example.com", 1_000_000) is None
    setCachedFetch("https://example.com", "hello world", 1_000_000)
    assert getCachedFetch("https://example.com", 1_060_000) == "hello world"
    assert getCachedFetch("https://example.com", 1_900_001) is None
    for i in range(MAX_ENTRIES):
        setCachedFetch(f"https://example.com/{i}", f"page {i}", 1_000_000)
    assert getCachedFetch("https://example.com/0", 1_000_000) == "page 0"
    setCachedFetch("https://example.com/overflow", "overflow page", 1_000_000)
    assert getCachedFetch("https://example.com/0", 1_000_000) is None
    assert getCachedFetch("https://example.com/overflow", 1_000_000) == "overflow page"
    clearFetchCache()


def test_source_ssrf_literal_and_hostname_boundary():
    from ruocun.tools.ssrf import blockedUrlReason

    for url in ("http://localhost:8080/x", "http://127.0.0.1/x", "http://169.254.169.254/latest/meta-data/",
                "http://10.0.0.5/x", "http://192.168.1.1/x", "http://172.16.0.1/x", "http://[::1]/x",
                "file:///etc/passwd", "ftp://example.com", "not a url"):
        assert blockedUrlReason(url)
    for url in ("https://api.example.com/v1", "http://example.org", "https://173.16.0.1/x"):
        assert blockedUrlReason(url) is None


def test_source_extract_model_uses_current_endpoint_and_explicit_override():
    from ruocun.config.profiles import DEFAULTS
    from ruocun.tools.fetch_extract import resolveExtractModel

    assert resolveExtractModel("custom-model", "anthropic", "claude-opus-4-8") == "custom-model"
    for provider, expected in (("deepseek", "deepseek-flash"), ("volcengine", "deepseek-v4.1-flash"),
                               ("qianfan", "deepseek-v4.1-flash")):
        assert resolveExtractModel(None, provider, "deepseek-v4-pro", DEFAULTS[provider]["baseUrl"]) == expected
    assert resolveExtractModel(None, "zhipu", "glm-5.3", DEFAULTS["zhipu"]["baseUrl"]) == "glm-5.3-flash"
    assert resolveExtractModel(None, "zhipu", "glm-5.3", "https://gateway.example") == "glm-5.3"
    assert resolveExtractModel(None, "deepseek", "gateway-model") == "gateway-model"
    assert resolveExtractModel("inherit", "deepseek", "deepseek-v4-pro", DEFAULTS["deepseek"]["baseUrl"]) == "deepseek-v4-pro"
    assert resolveExtractModel(None, "openai", "gpt-5") == "gpt-5"


def test_source_webfetch_strips_caches_full_text_extracts_and_falls_back():
    from ruocun.tools.fetch_cache import clearFetchCache
    from ruocun.tools.fetch_url import fetchUrlTool
    from ruocun.tools.registry import ToolRegistry
    from ruocun.tools.types import ToolContext

    async def scenario():
        clearFetchCache()
        calls, extracted = [], []
        async def fetch(url, **kwargs):
            calls.append((url, kwargs))
            return httpx.Response(200, text="<style>.x{}</style><script>evil()</script><p>Hi &amp; bye " + "a" * 500 + "</p>")
        async def extract(text, prompt):
            extracted.append((text, prompt))
            return "抽取:" + prompt
        ctx = ToolContext("synthetic", fetchImpl=fetch, extractFromPage=extract)
        registry = ToolRegistry()
        registry.register(fetchUrlTool)
        async def call(**args):
            return await registry.dispatch("WebFetch", json.dumps({"url": "https://example.com", **args}), ctx)
        first = await call(max_chars=100)
        assert first == "Hi & bye " + "a" * 91 + "\n…(已截断)"
        assert not extracted and len(calls) == 1
        assert await call() == "Hi & bye " + "a" * 500
        assert await call(prompt="联系信息") == "抽取:联系信息"
        assert extracted == [("Hi & bye " + "a" * 500, "联系信息")] and len(calls) == 1
        async def failing(text, prompt):
            raise RuntimeError("synthetic model failure")
        ctx.extractFromPage = failing
        assert await call(prompt="extract") == "Hi & bye " + "a" * 500
        ctx.extractFromPage = None
        assert await call(prompt="no callback") == "Hi & bye " + "a" * 500
        assert fetchUrlTool.capability == "network" and fetchUrlTool.approval == "suggest"
        clearFetchCache()
    asyncio.run(scenario())


def test_source_failures_not_cached_and_initial_denial_precedes_fetch():
    from ruocun.tools.fetch_cache import clearFetchCache
    from ruocun.tools.fetch_url import fetchUrlTool
    from ruocun.tools.types import ToolContext

    async def scenario():
        clearFetchCache()
        calls = []
        async def fetch(url, **kwargs):
            calls.append(url)
            if url.endswith("timeout"):
                raise TimeoutError()
            return httpx.Response(503, text="unavailable")
        ctx = ToolContext("synthetic", fetchImpl=fetch)
        for _ in range(2):
            assert await fetchUrlTool.handler({"url": "https://flaky.example.com"}, ctx) == "Error: 抓取失败 HTTP 503"
        assert len(calls) == 2
        assert "抓取超时(30s)" in await fetchUrlTool.handler({"url": "https://example.com/timeout"}, ctx)
        assert "拒绝抓取" in await fetchUrlTool.handler({"url": "http://127.0.0.1"}, ctx)
        assert len(calls) == 3
        ctx.lang = "en"
        assert "Fetch failed HTTP 503" in await fetchUrlTool.handler({"url": "https://flaky.example.com"}, ctx)
        clearFetchCache()
    asyncio.run(scenario())


def test_actual_http_redirect_cache_and_body_cancel_use_owned_request():
    from ruocun.tools.fetch_cache import clearFetchCache
    from ruocun.tools.fetch_url import fetchUrlTool
    from ruocun.tools.types import ToolContext
    from ruocun.tools.web_network import fetchWeb

    requests, started, release = [], threading.Event(), threading.Event()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            requests.append(self.path)
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "/page")
                self.end_headers()
                return
            if self.path == "/slow":
                self.send_response(200)
                self.end_headers()
                self.wfile.flush()
                started.set()
                release.wait(3)
            else:
                self.send_response(200)
                self.end_headers()
            try:
                self.wfile.write(b"<p>actual body</p>")
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    async def scenario(server):
        clearFetchCache()
        async def route(url, **kwargs):
            # Source's fetchImpl seam maps an allowed synthetic hostname to this owned loopback.
            return await fetchWeb(f"http://127.0.0.1:{server.server_port}" + urlsplit(url).path, **kwargs)
        ctx = ToolContext("synthetic", fetchImpl=route)
        assert await fetchUrlTool.handler({"url": "https://example.com/redirect"}, ctx) == "actual body"
        assert requests == ["/redirect", "/page"]
        assert await fetchUrlTool.handler({"url": "https://example.com/redirect"}, ctx) == "actual body"
        assert requests == ["/redirect", "/page"]
        work = asyncio.create_task(fetchUrlTool.handler({"url": "https://example.com/slow"}, ctx))
        async with asyncio.timeout(3):
            while not started.is_set():
                await asyncio.sleep(.01)
        ctx.signal.set()
        assert "用户已取消" in await asyncio.wait_for(work, 2)
        clearFetchCache()

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        server.daemon_threads = True
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            asyncio.run(scenario(server))
        finally:
            release.set()
            server.shutdown()
            worker.join(3)
            assert not worker.is_alive()
