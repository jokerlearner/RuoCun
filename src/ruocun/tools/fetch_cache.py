"""Frozen src/tools/fetch_cache.ts (MIT), URL text cache before truncation."""

from __future__ import annotations

import time

TTL_MS = 15 * 60_000
MAX_ENTRIES = 50
_cache: dict[str, tuple[str, float]] = {}


def getCachedFetch(url: str, now: float | None = None) -> str | None:
    entry = _cache.get(url)
    if entry is None:
        return None
    current = time.time() * 1000 if now is None else now
    if entry[1] <= current:
        del _cache[url]
        return None
    return entry[0]


def setCachedFetch(url: str, text: str, now: float | None = None) -> None:
    if url not in _cache and len(_cache) >= MAX_ENTRIES:
        del _cache[next(iter(_cache))]
    _cache[url] = text, (time.time() * 1000 if now is None else now) + TTL_MS


def clearFetchCache() -> None:
    _cache.clear()
