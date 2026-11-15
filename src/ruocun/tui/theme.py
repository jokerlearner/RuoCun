"""定义亮色和暗色终端的语义颜色，并按终端颜色能力生成样式。"""

from collections.abc import Mapping

from .capabilities import Capabilities

PALETTES = {
    "dark": {
        "ink": ((225, 232, 240), 254, "37"),
        "jade": ((128, 193, 170), 109, "36"),
        "vermilion": ((221, 104, 99), 167, "31"),
        "dim": ((151, 159, 172), 247, "90"),
        "gold": ((218, 181, 106), 179, "33"),
        "panel": ((45, 55, 69), 237, "100"),
    },
    "light": {
        "ink": ((25, 39, 54), 235, "30"),
        "jade": ((22, 97, 79), 23, "36"),
        "vermilion": ((153, 51, 52), 95, "31"),
        "dim": ((90, 104, 119), 60, "90"),
        "gold": ((124, 93, 33), 94, "33"),
        "panel": ((224, 233, 241), 254, "47"),
    },
}
_RESET_FOREGROUND = "\x1b[39m"


def semHex(sem: str, bg: str = "dark") -> str:
    rgb, _, _ = PALETTES[bg][sem]
    return "#" + bytes(rgb).hex()


def _tier(caps: Capabilities | Mapping[str, object]) -> str:
    return caps.tier if isinstance(caps, Capabilities) else str(caps["tier"])


def _fg(rgb: tuple[int, ...]) -> str:
    red, green, blue = rgb
    return f"\x1b[38;2;{red};{green};{blue}m"


def paint(text: str, sem: str, caps: Capabilities | Mapping[str, object], bg: str = "dark") -> str:
    rgb, ansi256, ansi16 = PALETTES[bg][sem]
    tier = _tier(caps)
    if tier == "none":
        return text
    if tier == "truecolor":
        prefix = _fg(rgb)
    elif tier == "ansi256":
        prefix = f"\x1b[38;5;{ansi256}m"
    else:
        prefix = f"\x1b[{ansi16}m"
    return prefix + text + _RESET_FOREGROUND


def gradientBlock(lines: list[str], start: str, end: str, caps: Capabilities | Mapping[str, object], bg: str = "dark") -> list[str]:
    tier = _tier(caps)
    if tier == "none":
        return list(lines)
    if tier != "truecolor":
        return [paint(line, start, caps, bg) for line in lines]
    span = max(1, max(map(len, lines), default=0) - 1)
    endpoints = tuple(zip(PALETTES[bg][start][0], PALETTES[bg][end][0], strict=True))
    prefixes = [
        _fg(tuple((2 * (left * (span - index) + right * index) + span) // (2 * span)
                  for left, right in endpoints))
        for index in range(span + 1)
    ]
    return ["".join(prefix + char for prefix, char in zip(prefixes, line)) + _RESET_FOREGROUND for line in lines]
