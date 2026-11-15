"""根据模型窗口为实际请求划分预算。先留出输出和估算误差的空间，再决定何时压缩以及多长的近期消息须保留原文。

调用方须把返回的 output_limit 用于真正发送的请求。改编自 DeepSeek Harness compaction-basic（MIT，2026）。
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompactionBudget:
    context_window: int
    output_limit: int
    headroom_tokens: int
    threshold_tokens: int
    retain_tokens: int
    summary_max_tokens: int


def _integer(env: Mapping[str, str], key: str, default: int, *, minimum: int = 1) -> int:
    raw = env.get(key)
    try:
        value = int(raw) if raw is not None else default
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if value < minimum:
        raise ValueError(f"{key} is below its minimum")
    return value


def _ratio(env: Mapping[str, str], key: str, default: float) -> float:
    try:
        value = float(env.get(key, str(default)))
    except ValueError as exc:
        raise ValueError(f"{key} must be a finite ratio") from exc
    if not math.isfinite(value) or not 0 < value < 1:
        raise ValueError(f"{key} must be between zero and one")
    return value


def resolveCompactionBudget(
    window: int, output_limit: int, *, output_explicit: bool = True,
    env: Mapping[str, str] | None = None,
) -> CompactionBudget:
    """为实际输出、动态余量和近期消息原文预留空间。"""
    if type(window) is not int or window <= 0:
        raise ValueError("context window must be a positive integer")
    if type(output_limit) is not int or output_limit <= 0:
        raise ValueError("output limit must be a positive integer")
    output = output_limit if output_explicit else min(output_limit, window // 4)
    if output <= 0 or output >= window:
        raise ValueError("output limit must leave a positive message budget")
    settings = {} if env is None else env
    available = window - output
    headroom = _integer(settings, "RUOCUN_COMPACT_HEADROOM_TOKENS",
                        min(65536, max(32, math.floor(.08 * available))), minimum=0)
    threshold = math.floor(min(_ratio(settings, "RUOCUN_COMPACT_THRESHOLD_RATIO", .8) * window,
                               available - headroom))
    if "RUOCUN_COMPACT_RETAIN_TOKENS" in settings and "RUOCUN_COMPACT_RETAIN_RATIO" in settings:
        raise ValueError("RUOCUN_COMPACT_RETAIN_TOKENS and RETAIN_RATIO are mutually exclusive")
    retain = _integer(settings, "RUOCUN_COMPACT_RETAIN_TOKENS",
                      math.floor(_ratio(settings, "RUOCUN_COMPACT_RETAIN_RATIO", .16) * available))
    if threshold <= 0 or not 0 < retain < threshold:
        raise ValueError("compaction headroom and retention leave no usable message budget")
    return CompactionBudget(window, output, headroom, threshold,
                            retain, _integer(settings, "RUOCUN_COMPACT_SUMMARY_MAX_TOKENS",
                                             min(8192, max(128, threshold // 4))))


def _price(value: Any) -> int:
    if isinstance(value, str):
        return math.ceil(len(value.encode("utf-16-le", errors="surrogatepass")) / 6)
    if isinstance(value, list):
        return sum(_price(item) for item in value)
    if isinstance(value, dict):
        if value.get("type") in {"image_url", "input_image", "image"}:
            return 1024  # 按固定值保守估算图片，供两种请求格式共用。
        return sum(_price(item) for key, item in value.items()
                   if key not in {"role", "type"})
    return 0


def estimateRequestTokens(body: Mapping[str, Any]) -> int:
    """粗估最终 Chat 或 Responses 请求的输入 token，计入消息结构与工具定义。

    输出上限与图片的 base64 字节不计入输入估算。调用方仍需处理模型服务实际返回的上下文超限。
    """
    messages = body.get("messages", body.get("input", []))
    if isinstance(messages, list):
        used = sum(4 + _price(message) for message in messages)
    else:
        used = 4 + _price(messages)
    tools = body.get("tools", [])
    schema_tokens = _price(json.dumps(tools, ensure_ascii=False, separators=(",", ":"))) if tools else 0
    return used + schema_tokens + _price(body.get("instructions"))
