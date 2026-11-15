"""读取吉祥物的动画资源和静态图，将静态图转换为终端字符网格。"""

import json
from functools import cache
from importlib.resources import files
from itertools import combinations
from typing import Any

_DATA: dict[str, Any] = json.loads(files("ruocun.tui").joinpath("resources/mascot-frames.json").read_text("utf-8"))
MASCOT_FRAMES: dict[int, str] = {int(key): value for key, value in _DATA["frames"].items()}
MASCOT_TIMELINE: list[dict[str, int]] = _DATA["timeline"]
MASCOT_IMAGE: dict[str, Any] = _DATA["image"]


@cache
def _static_rgb_rows() -> tuple[bytes, ...]:
    data = json.loads(files("ruocun.tui").joinpath("resources/mascot-static.json").read_text("utf-8"))
    return tuple(bytes.fromhex(row) for row in data["rgb_rows"])


def renderStaticMascot(max_columns: int, max_rows: int, tier: str) -> tuple[int, list[str]]:
    pixels = _static_rgb_rows()
    width, height = len(pixels[0]) // 3, len(pixels)
    columns = min(width // 2, max_columns, max_rows * width * 2 // height)
    rows = columns * height // (2 * width)
    if rows < 1:
        return 0, []

    def sample(x: int, y: int) -> bytes:
        start = 3 * ((2 * x + 1) * width // (4 * columns))
        return pixels[(2 * y + 1) * height // (4 * rows)][start:start + 3]

    def cell(samples: tuple[bytes, bytes, bytes, bytes]) -> str:
        if tier not in {"truecolor", "ansi256"}:
            intensity = sum((r * 3 + g * 6 + b) for r, g, b in samples) // 40
            return " ░▒▓█"[min(4, intensity // 40)]
        mask, foreground, background = _quadrants(samples)
        glyph = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"[mask]
        if tier == "truecolor":
            r, g, b = foreground
            br, bg, bb = background
            return f"\x1b[38;2;{r};{g};{b};48;2;{br};{bg};{bb}m{glyph}"

        def cube(rgb: bytes) -> int:
            r, g, b = (round(channel * 5 / 255) for channel in rgb)
            return 16 + 36 * r + 6 * g + b
        return f"\x1b[38;5;{cube(foreground)};48;5;{cube(background)}m{glyph}"

    reset = "\x1b[0m" if tier in {"truecolor", "ansi256"} else ""
    return columns, ["".join(cell((sample(2 * x, 2 * y), sample(2 * x + 1, 2 * y),
                                  sample(2 * x, 2 * y + 1), sample(2 * x + 1, 2 * y + 1)))
                             for x in range(columns)) + reset for y in range(rows)]


def _distance(first: bytes, second: bytes) -> int:
    return sum((a - b) ** 2 for a, b in zip(first, second, strict=True))


def _quadrants(samples: tuple[bytes, bytes, bytes, bytes]) -> tuple[int, bytes, bytes]:
    """把一个终端字符覆盖的四个采样点归入两种显示色。"""
    first, second = max(combinations(samples, 2), key=lambda pair: _distance(*pair))
    if first == second:
        return 0, first, second
    mask = 0
    foreground, background = [], []
    for index, color in enumerate(samples):
        if _distance(color, first) <= _distance(color, second):
            mask |= 1 << index
            foreground.append(color)
        else:
            background.append(color)

    def average(group: list[bytes]) -> bytes:
        return bytes(sum(channel) // len(group) for channel in zip(*group, strict=True))

    return mask, average(foreground), average(background)
