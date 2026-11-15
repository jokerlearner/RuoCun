"""将 Ctrl+B 转后台操作交给活跃的 Bash 和 Agent 执行方，汇总各方确认的转换数量及未决状态。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable


async def convertAll(*owners: Callable[[], Awaitable[int]]) -> tuple[int, bool]:
    # 各执行方负责转移自己持有的任务，等所有结果返回后才汇报确认数和未决状态。
    results = await asyncio.gather(*(owner() for owner in owners), return_exceptions=True)
    confirmed = sum(result for result in results if isinstance(result, int))
    uncertain = any(isinstance(result, BaseException) for result in results)
    return confirmed, uncertain
