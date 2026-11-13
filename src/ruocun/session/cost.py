"""人民币费用估算：冻结 ``src/session/cost.ts`` 的 Python 迁移（MIT）。

价格为冻结来源数据，不代表当前厂商报价。已知模型优先于环境覆盖；只有
未知模型使用 pro/flash 启发式及相应环境值。环境别名遵守 D09。
"""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, TypedDict

from ..config.compat import resolve_env

if TYPE_CHECKING:
    from .session import UsageTotals


class Prices(TypedDict):
    inputHit: float
    inputMiss: float
    output: float


KNOWN_PRICES: dict[str, Prices] = {
    "deepseek-v4-pro": {"inputHit": .9, "inputMiss": 9, "output": 27},
    "deepseek-v4-flash": {"inputHit": .2, "inputMiss": 2, "output": 8.2},
    "claude-opus-4-6": {"inputHit": 3.4, "inputMiss": 34, "output": 170},
    "claude-opus-4-7": {"inputHit": 3.4, "inputMiss": 34, "output": 170},
    "claude-opus-4-8": {"inputHit": 3.4, "inputMiss": 34, "output": 170},
    "claude-sonnet-4-6": {"inputHit": 2.04, "inputMiss": 20.4, "output": 102},
    "claude-sonnet-5": {"inputHit": 1.36, "inputMiss": 13.6, "output": 68},
    "glm-5-2": {"inputHit": 2, "inputMiss": 8, "output": 28},
    "glm-5-3": {"inputHit": 2, "inputMiss": 8, "output": 28},
    "glm-5-3-flash": {"inputHit": .2, "inputMiss": .8, "output": 2.8},
    "gpt-5-5": {"inputHit": 3.4, "inputMiss": 34, "output": 204},
    "doubao-seed-2-0-pro": {"inputHit": .64, "inputMiss": 3.2, "output": 16},
    "doubao-seed-2-0-lite": {"inputHit": .12, "inputMiss": .6, "output": 3.6},
    "doubao-seed-2-0-code": {"inputHit": .64, "inputMiss": 3.2, "output": 16},
    "glm-5-1": {"inputHit": 1.3, "inputMiss": 6, "output": 24},
    "kimi-k2.6": {"inputHit": 1.1, "inputMiss": 6.5, "output": 27},
    "kimi-k2.7-code": {"inputHit": 1.3, "inputMiss": 6.5, "output": 27},
    "minimax-m2.7": {"inputHit": .42, "inputMiss": 2.1, "output": 8.4},
    "minimax-m3": {"inputHit": .42, "inputMiss": 2.1, "output": 8.4},
    "ernie-5.1": {"inputHit": 1.6, "inputMiss": 4, "output": 18},
}


def _num(value: str | None, default: float) -> float:
    """来源 Number(undefined) 为 NaN；空字符串为 0；非法/负数退回缺省。"""
    if value is None:
        return default
    text = value.strip()
    try:
        number = (float(int(text, 0)) if text.lower().startswith(("0x", "0b", "0o"))
                  else float(text or "0"))
    except (ValueError, OverflowError):
        return default
    return number if math.isfinite(number) and number >= 0 else default


def _normalizeModelKey(model: str) -> str:
    return model.lower().removesuffix("-joybuilder").removesuffix("-local").replace(".", "-")


def pricesFor(model: str, env: Mapping[str, str] | None = None) -> Prices:
    known = KNOWN_PRICES.get(model)
    if known is not None:
        return known
    known = KNOWN_PRICES.get(_normalizeModelKey(model))
    if known is not None:
        return known
    values = os.environ if env is None else env
    flash = "flash" in model.lower()
    prefix = "PRICE_FLASH_" if flash else "PRICE_"
    return {
        "inputHit": _num(resolve_env(prefix + "INPUT_HIT", values), .2 if flash else .9),
        "inputMiss": _num(resolve_env(prefix + "INPUT_MISS", values), 2 if flash else 9),
        "output": _num(resolve_env(prefix + "OUTPUT", values), 8.2 if flash else 27),
    }


def loadPrices(env: Mapping[str, str] | None = None) -> Prices:
    return pricesFor("pro", env)


def estimateCostCNY(usage: UsageTotals, prices: Prices | None = None) -> float:
    effective = loadPrices() if prices is None else prices
    hit = usage["cacheHitTokens"]
    miss = max(0, usage["promptTokens"] - hit)
    return (hit * effective["inputHit"] + miss * effective["inputMiss"]
            + usage["completionTokens"] * effective["output"]) / 1_000_000


def estimateCostByModel(
    buckets: Mapping[str, UsageTotals], env: Mapping[str, str] | None = None,
) -> float:
    return sum(estimateCostCNY(usage, pricesFor(model, env)) for model, usage in buckets.items())


def formatCNY(yuan: float) -> str:
    digits = 4 if yuan < .01 else 3 if yuan < 1 else 2
    # JS toFixed 在恰好居中时向较大绝对值舍入，Python format 默认采用偶数舍入。
    amount = Decimal.from_float(float(yuan)).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    return f"￥{amount:.{digits}f}"
