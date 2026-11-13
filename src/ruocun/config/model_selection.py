"""模型继承与辅助模型选择（来源冻结 ``src/config/model_selection.ts``，MIT）。

CFG-03：调用 override > agent 定义 > parent；缺可继承主模型明确失败，
不暗换 provider。CFG-02：自定义网关不猜便宜档。
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
    """仅对已知官方端点的同族模型选择便宜档；自定义网关及其他模型用当前主模型。"""
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
