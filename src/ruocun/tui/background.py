"""为界面确定亮色或暗色背景。优先采用显式环境信息，再使用同一终端输入链路取得的查询结果。其后尝试 Apple Terminal，最后回退到暗色。"""

from __future__ import annotations

import asyncio
import re
import sys
from collections.abc import Awaitable, Callable, Mapping


def bgFromEnv(env: Mapping[str, str]) -> str | None:
    forced = env.get("RUOCUN_THEME", "").lower()
    if forced in {"light", "dark"}:
        return forced
    part = env.get("COLORFGBG", "").split(";")[-1]
    match = re.match(r"^[+-]?\d+", part)
    if match:
        value = int(match[0])
        return "light" if value == 7 or value >= 9 else "dark"
    return None


def fromRGB(red: int, green: int, blue: int) -> str:
    return "light" if (.299 * red + .587 * green + .114 * blue) / 65535 > .5 else "dark"


async def detectBackgroundAppleTerminal(env: Mapping[str, str], timeoutMs: int = 400) -> str | None:
    if sys.platform != "darwin" or env.get("TERM_PROGRAM") != "Apple_Terminal":
        return None
    process = None
    try:
        process = await asyncio.create_subprocess_exec(
            "/usr/bin/osascript", "-e", 'tell application "Terminal" to get background color of window 1',
            env=dict(env), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        raw, _ = await asyncio.wait_for(process.communicate(), timeoutMs / 1000)
        values = [int(part.strip()) for part in raw.decode().strip().split(",")]
        return fromRGB(*values[:3]) if process.returncode == 0 and len(values) >= 3 else None
    except (OSError, ValueError, TimeoutError):
        if process is not None and process.returncode is None:
            process.kill()
            await process.wait()
        return None


async def resolveBackground(env: Mapping[str, str], *, probe: Callable[[], Awaitable[str | None]] | None = None) -> str:
    hint = bgFromEnv(env)
    if hint is not None:
        return hint
    queried = await probe() if probe is not None else None
    return queried or await detectBackgroundAppleTerminal(env) or "dark"
