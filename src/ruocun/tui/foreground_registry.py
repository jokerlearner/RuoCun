"""Combine the active Bash and Agent owners for the frozen Ctrl+B command."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def convertAll(*owners: Callable[[], Awaitable[int]]) -> tuple[int, bool]:
    # Each owner fences its own live executions. Join both before reporting success.
    results = await asyncio.gather(*(owner() for owner in owners), return_exceptions=True)
    confirmed = sum(result for result in results if isinstance(result, int))
    uncertain = any(isinstance(result, BaseException) for result in results)
    return confirmed, uncertain
