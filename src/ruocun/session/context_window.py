"""冻结 ``src/index.ts`` 的 /context-window 参数解析（MIT）。

模型默认窗口复用 config.profiles.contextWindowFor；手动锁及环境写回由入口
维持，来源不把窗口覆写存入 Session 或会话数据库。
"""

from __future__ import annotations

import re


def parseContextWindow(argument: str) -> float:
    """200K / 1M / 纯数字（单位 K）；非法格式或低于 1K 抛 ValueError。"""
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([KkMm])?", argument)
    if match is None:
        raise ValueError(
            f"无效格式:「{argument}」。用法:/context-window <200K|1M|<数字>K>(纯数字单位为 K)",
        )
    number = float(match[1])
    tokens = number * (1_000_000 if (match[2] or "K").upper() == "M" else 1_000)
    if tokens < 1000:
        raise ValueError(f"上下文窗口过小({tokens:g} tok),最小 1K。")
    return tokens
