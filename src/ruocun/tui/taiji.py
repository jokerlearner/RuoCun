"""生成适合终端列宽的太极标识，供纯文本欢迎横幅使用。"""

from itertools import groupby

from .capabilities import Capabilities

_UPPER_HALF = (
    ".....aaaabb.....",
    "...aaaaabbbbb...",
    "..aaaabaaaabbb..",
    ".aaaaaaaabbbbbb.",
)
_SWAP_FISH = str.maketrans("ab", "ba")
_TILE = _UPPER_HALF + tuple(row[::-1].translate(_SWAP_FISH) for row in reversed(_UPPER_HALF))
_TEXT = ("    .----.", "  /   o   \\", " |     /   |", " |   /     |", "  \\   o   /", "    '----'")
_COLORS = {
    "dark": {"a": ((222, 239, 235), 254), "b": ((58, 139, 124), 66)},
    "light": {"a": ((39, 66, 77), 237), "b": ((91, 168, 143), 72)},
}
_RESET = "\x1b[0m"


def renderTaiji(caps: Capabilities, bg: str = "dark") -> list[str]:
    if caps.tier in {"none", "ansi16"}:
        return list(_TEXT)
    escapes = {".": _RESET}
    for fish, ((red, green, blue), index) in _COLORS[bg].items():
        escapes[fish] = (f"\x1b[48;2;{red};{green};{blue}m" if caps.tier == "truecolor"
                         else f"\x1b[48;5;{index}m")
    return [
        "".join(escapes[pixel] + " " * len(tuple(cells)) for pixel, cells in groupby(row)) + _RESET
        for row in _TILE
    ]


def TAIJI_WIDTH(caps: Capabilities) -> int:
    return max(map(len, _TEXT)) if caps.tier in {"none", "ansi16"} else len(_TILE[0])
