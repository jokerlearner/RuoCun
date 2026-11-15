"""计算字符串所占的终端列数，并按显示宽度填充，适配宽字符。"""


def displayWidth(text: str) -> int:
    ranges = ((0x1100, 0x115F), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3),
              (0xF900, 0xFAFF), (0xFE30, 0xFE4F), (0xFF00, 0xFF60),
              (0xFFE0, 0xFFE6), (0x1F300, 0x1FAFF), (0x20000, 0x3FFFD))
    return sum(2 if any(start <= ord(char) <= end for start, end in ranges) else 1 for char in text)


def padEnd(text: str, width: int) -> str:
    return text + " " * max(0, width - displayWidth(text))
