"""为网页工具提供异步 HTTP 读取入口，按整次请求控制超时。"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Mapping
from typing import Protocol

import httpx

from .ssrf import normalizeHttpUrl


class FetchImpl(Protocol):
    async def __call__(self, url: str, *, headers: Mapping[str, str] | None = None,
                       signal: threading.Event | None = None) -> httpx.Response: ...


async def fetchWeb(url: str, *, headers: Mapping[str, str] | None = None,
                   signal: threading.Event | None = None) -> httpx.Response:
    """发出一次 GET 请求并读取响应正文，整个请求最多等待 30 秒。"""
    async def request() -> httpx.Response:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            return await client.get(normalizeHttpUrl(url), headers=headers)

    work = asyncio.create_task(request())
    try:
        async with asyncio.timeout(30):
            while not work.done():
                if signal is not None and signal.is_set():
                    raise InterruptedError("用户已取消")
                await asyncio.wait({work}, timeout=.05)
            return work.result()
    finally:
        if not work.done():
            work.cancel()
        await asyncio.gather(work, return_exceptions=True)
