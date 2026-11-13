"""Frozen src/tools/fetch_extract.ts (MIT), endpoint-aware extraction model."""

from ..config.model_selection import defaultAuxiliaryModel, getAgentModel
from ..config.profiles import Provider


def resolveExtractModel(envOverride: str | None, provider: Provider, sessionModel: str,
                        baseUrl: str | None = None) -> str:
    model = defaultAuxiliaryModel({"model": sessionModel, "provider": provider, "baseUrl": baseUrl}) if baseUrl else sessionModel
    return getAgentModel(model, sessionModel, envOverride)
