"""内存会话：冻结 ``src/session/session.ts`` 的 Python 迁移（MIT）。

本模块仅保留来源 Session 职责；持久化仍由任务 07 的 StoragePort 承担。
分模型费用及完整会话恢复的接线属于任务 28 剩余范围。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Literal, TypedDict

from ..client.types import ChatMessage, ContentPart, Usage
from .cost import estimateCostByModel, formatCNY

Mode = Literal["normal", "plan"]


class UsageTotals(TypedDict):
    promptTokens: int
    completionTokens: int
    cacheHitTokens: int
    cacheMissTokens: int


CacheBustInfo = TypedDict("CacheBustInfo", {
    "from": float, "to": float, "promptTokens": int, "changed": list[str],
})


def _emptyUsage() -> UsageTotals:
    return {"promptTokens": 0, "completionTokens": 0, "cacheHitTokens": 0, "cacheMissTokens": 0}


class Session:
    def __init__(
        self, systemPrompt: str, model: str, *, env: Mapping[str, str] | None = None,
    ) -> None:
        self._systemPrompt = systemPrompt
        self._env = env
        self.model = model
        self.mode: Mode = "normal"
        self.messages: list[ChatMessage] = [{"role": "system", "content": systemPrompt}]
        self.usage = _emptyUsage()
        self._modelUsage: dict[str, UsageTotals] = {}
        self.lastPromptTokens: int | None = None
        self.lastSentLength = 0
        self.budgetCNY: float | None = None
        self._lastCall: tuple[int, float] | None = None
        self._cacheBustWarner: Callable[[CacheBustInfo], None] | None = None
        self._prevFp: dict[str, str] | None = None
        self._curFp: dict[str, str] | None = None

    def onCacheBust(self, fn: Callable[[CacheBustInfo], None]) -> None:
        self._cacheBustWarner = fn

    def notePrefix(self, fp: dict[str, str]) -> None:
        self._prevFp = self._curFp
        self._curFp = fp

    def addUsage(self, u: Usage, model: str | None = None) -> None:
        selected = self.model if model is None else model
        prompt = u.get("prompt_tokens", 0) or 0
        completion = u.get("completion_tokens", 0) or 0
        hit = u.get("prompt_cache_hit_tokens", 0) or 0
        miss = u.get("prompt_cache_miss_tokens", 0) or 0
        bucket = self._modelUsage.setdefault(selected, _emptyUsage())
        for totals in (self.usage, bucket):
            totals["promptTokens"] += prompt
            totals["completionTokens"] += completion
            totals["cacheHitTokens"] += hit
            totals["cacheMissTokens"] += miss
        if selected == self.model and prompt:
            self.lastPromptTokens = prompt
        ratio = hit / prompt if prompt > 0 else 0
        if prompt >= 4000:
            if (self._lastCall is not None and self._lastCall[1] >= .5
                    and self._lastCall[1] - ratio >= .5 and self._cacheBustWarner is not None):
                self._cacheBustWarner({
                    "from": self._lastCall[1], "to": ratio, "promptTokens": prompt,
                    "changed": self._changedDims(),
                })
            self._lastCall = (prompt, ratio)

    def _changedDims(self) -> list[str]:
        if self._prevFp is None or self._curFp is None:
            return []
        keys = dict.fromkeys([*self._prevFp, *self._curFp])
        return [key for key in keys if self._prevFp.get(key) != self._curFp.get(key)]

    def cacheHitRatio(self) -> float:
        prompt = self.usage["promptTokens"]
        return self.usage["cacheHitTokens"] / prompt if prompt > 0 else 0

    def costCNY(self) -> float:
        return estimateCostByModel(self._modelUsage, self._env)

    def overBudget(self) -> bool:
        return self.budgetCNY is not None and self.costCNY() >= self.budgetCNY

    def usageSummary(self) -> str:
        prompt = self.usage["promptTokens"]
        if prompt == 0:
            return "本会话暂无 token 统计。"
        suffix = f"(提醒阈值 {formatCNY(self.budgetCNY)})" if self.budgetCNY is not None else ""
        return (f"累计token（可含已恢复历史）:输入 {prompt} tok(cache 命中 {self.usage['cacheHitTokens']},"
                f"命中率 {self.cacheHitRatio() * 100:.1f}%)· 输出 {self.usage['completionTokens']} tok"
                f" · 本次进程费用约 {formatCNY(self.costCNY())}{suffix}；历史费用不完整")

    def addUser(self, content: str | list[ContentPart]) -> None:
        self.messages.append({"role": "user", "content": content})

    def clear(self) -> None:
        self.messages = [{"role": "system", "content": self._systemPrompt}]
        self.lastPromptTokens = None
        self.lastSentLength = 0
        self.usage.update(_emptyUsage())
        self._modelUsage.clear()
        self._lastCall = None

    def setModel(self, model: str) -> None:
        self.model = model

    def setSystemPrompt(self, prompt: str) -> None:
        """组合入口恢复当前能力前缀，保留对话投影和输入账本。"""
        self._systemPrompt = prompt
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = {"role": "system", "content": prompt}
        else:
            self.messages.insert(0, {"role": "system", "content": prompt})

    def toggleMode(self) -> Mode:
        self.mode = "plan" if self.mode == "normal" else "normal"
        return self.mode
