"""解析 /context-window 的窗口大小参数。

组合入口负责选择模型默认值、管理手动覆盖和写回环境，会话数据库无需保存这一设置。
"""

from __future__ import annotations

import re


def parseContextWindow(argument: str) -> float:
    """接受 200K、1M 或以 K 为单位的纯数字，非法格式和低于 1K 的值抛出 ValueError。"""
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
