"""Frozen permissions/classifier_model.ts (MIT), session-local fallback cache."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import NotRequired, TypedDict, TypeVar

from ..client.resilient import isContextLengthError, isRateLimitError
from ..config.model_selection import defaultAuxiliaryModel, getAgentModel
from ..config.profiles import Provider


class ModelContext(TypedDict):
    model: str
    provider: Provider
    baseUrl: str
    apiKey: str
    override: NotRequired[str | None]


T = TypeVar("T")


def defaultClassifierModel(context: ModelContext) -> str:
    return defaultAuxiliaryModel({"model": context["model"], "provider": context["provider"], "baseUrl": context["baseUrl"]})


def createClassifierRunner(notice: Callable[[str], None]) -> Callable[[ModelContext, Callable[[str], Awaitable[T]]], Awaitable[T]]:
    fallbacks: set[tuple[str, ...]] = set()

    async def runner(context: ModelContext, run: Callable[[str], Awaitable[T]]) -> T:
        preferred = getAgentModel(defaultClassifierModel(context), context["model"], context.get("override"))
        key = (context["provider"], context["baseUrl"], context["apiKey"], context["model"], preferred)
        model = context["model"] if key in fallbacks else preferred
        try:
            return await run(model)
        except Exception as error:
            if model == context["model"] or isContextLengthError(error) or isRateLimitError(error):
                raise
            result = await run(context["model"])
            if key not in fallbacks:
                fallbacks.add(key)
                notice(f"\n[智能判定] 分类器模型 {model} 不可用,本会话已改用主模型 {context['model']} 判定。\n")
            return result

    return runner
