"""冻结 evals/score.mjs（MIT）：加权完成度与逻辑回归跨度。"""

import math
from typing import Any


def weightedCompletion(checkpoints: list[dict[str, Any]], passedIds: list[str]) -> dict[str, Any]:
    passed = set(passedIds)
    known = {item["id"] for item in checkpoints}
    weight_total = weight_passed = passed_count = 0
    for item in checkpoints:
        weight = item.get("weight")
        weight = 1 if weight is None else weight
        weight_total += weight
        if item["id"] in passed:
            weight_passed += weight
            passed_count += 1
    return {
        "completion": weight_passed / weight_total if weight_total > 0 else 0,
        "passed": passed_count, "total": len(checkpoints), "weightPassed": weight_passed,
        "weightTotal": weight_total, "unknown": [case for case in passedIds if case not in known],
    }


def metasToSamples(metas: list[dict[str, Any]], threshold: float = 1) -> list[dict[str, Any]]:
    return [
        {"humanMinutes": row["humanMinutes"], "completion": row.get("completion"),
         "success": (row.get("completion") or 0) >= threshold}
        for row in metas if type(row.get("humanMinutes")) in (int, float) and row["humanMinutes"] > 0
    ]


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp = math.exp(value)
    return exp / (1 + exp)


def fitTimeHorizon(
    samples: list[dict[str, Any]], *, l2: float = 0.5, iters: int = 500, lr: float = 0.1,
) -> dict[str, Any]:
    points = [point for point in samples if point["humanMinutes"] > 0]
    count = len(points)
    positives = sum(bool(point["success"]) for point in points)
    counts = {"n": count, "nPos": positives, "nNeg": count - positives}
    if count < 4 or positives in (0, count):
        return {"degenerate": True, **counts}
    logs = [math.log(point["humanMinutes"]) for point in points]
    mean = sum(logs) / count
    std = math.sqrt(sum((value - mean) ** 2 for value in logs) / count) or 1
    scaled = [(value - mean) / std for value in logs]
    intercept = slope = 0.0
    for _ in range(iters):
        residual = [_sigmoid(intercept + slope * value) - bool(point["success"])
                    for value, point in zip(scaled, points, strict=True)]
        intercept -= lr * sum(residual) / count
        slope -= lr * (sum(diff * value for diff, value in zip(residual, scaled, strict=True)) / count + l2 * slope)
    if slope >= -1e-6:
        return {"degenerate": True, "reason": "斜率非负（数据无单调趋势）", "a": intercept, "b": slope}

    def horizon(probability: float) -> float:
        logit = math.log(probability / (1 - probability))
        return math.exp(mean + std * (logit - intercept) / slope)

    return {"degenerate": False, "p50": horizon(0.5), "p80": horizon(0.8),
            **counts, "a": intercept, "b": slope}
