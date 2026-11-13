"""Frozen memory metrics.ts (MIT)."""

from statistics import fmean, median, pstdev
from typing import TypedDict


class PR(TypedDict):
    p: float
    r: float
    f1: float


def precisionRecall(predicted: set[str], gold: set[str]) -> PR:
    tp = len(predicted & gold)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    return {"p": precision, "r": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def aggregate(samples: list[float]) -> dict[str, float]:
    if not samples:
        return dict.fromkeys(("median", "mean", "stdev", "min", "max"), 0.0)
    return {"median": median(samples), "mean": fmean(samples), "stdev": pstdev(samples),
            "min": min(samples), "max": max(samples)}


def majorityVote(votes: list[bool]) -> tuple[bool, float]:
    count = sum(votes)
    return bool(votes) and 2 * count >= len(votes), max(count, len(votes) - count) / len(votes) if votes else 0.0


def relevanceGap(injected: set[str], gold: set[str]) -> float:
    return len(gold - injected) / len(gold) if gold else 0.0
