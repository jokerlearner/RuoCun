"""为子代理和辅助任务选择模型。

子代理优先使用本次指定的模型，其次使用代理定义中的模型，最后才继承父代理。辅助模型由当前提供商和已知模型目录共同决定。
"""

from __future__ import annotations

import re
from typing import TypedDict

from .profiles import DEFAULTS, Provider

_DEEPSEEK_FAMILY = re.compile(
    r"^deepseek-(?:v4(?:\.1)?-(?:pro|flash)(?:-\d+|-economy)?|flash)$",
    re.IGNORECASE,
)
_GLM53 = re.compile(r"^glm-5\.3$", re.IGNORECASE)


class ModelSelectionContext(TypedDict):
    model: str
    provider: Provider
    baseUrl: str


def getAgentModel(
    agentModel: str | None,
    parentModel: str | None,
    overrideModel: str | None = None,
) -> str:
    selected = (overrideModel or "").strip() or (agentModel or "").strip()
    if selected and selected.lower() != "inherit":
        return selected
    parent = (parentModel or "").strip()
    if not parent or parent.lower() == "inherit":
        raise ValueError("缺少可继承的主模型，请选择模型或显式配置子代理模型 ID。")
    return parent


def defaultAuxiliaryModel(context: ModelSelectionContext) -> str:
    """按提供商约定选择辅助模型，在候选不适用时沿用当前模型。"""
    model = context["model"]
    provider = context["provider"]
    base_url = context["baseUrl"]
    if base_url.rstrip("/") != DEFAULTS[provider]["baseUrl"].rstrip("/"):
        return model
    if provider in ("deepseek", "volcengine", "qianfan") and _DEEPSEEK_FAMILY.match(model):
        return "deepseek-flash" if provider == "deepseek" else "deepseek-v4.1-flash"
    if provider == "zhipu" and _GLM53.match(model):
        return "glm-5.3-flash"
    return model
