"""根据账户的端点选择网页提取模型，让辅助提取兼容当前的服务商。"""

from ..config.model_selection import defaultAuxiliaryModel, getAgentModel
from ..config.profiles import Provider


def resolveExtractModel(envOverride: str | None, provider: Provider, sessionModel: str,
                        baseUrl: str | None = None) -> str:
    model = defaultAuxiliaryModel({"model": sessionModel, "provider": provider, "baseUrl": baseUrl}) if baseUrl else sessionModel
    return getAgentModel(model, sessionModel, envOverride)
