"""冻结tui/capabilities.ts（MIT）的颜色能力检测，无启动时环境快照。"""

import re
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    tier: str
    isTTY: bool
    columns: int


def detectCapabilities(env: Mapping[str, str], isTTY: bool, columns: int | None = None) -> Capabilities:
    parsed = re.match(r"^[+-]?\d+", env.get("COLUMNS", ""))
    cols = columns or (int(parsed[0]) if parsed else 0) or 80
    if not isTTY or env.get("NO_COLOR"):
        return Capabilities("none", isTTY, cols)
    force, color, term = env.get("FORCE_COLOR"), env.get("COLORTERM", "").lower(), env.get("TERM", "").lower()
    tier = "truecolor" if force == "3" or re.search("truecolor|24bit", color) else (
        "ansi256" if force == "2" or "256color" in term else "ansi16")
    return Capabilities(tier, isTTY, cols)
