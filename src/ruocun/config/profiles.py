"""账户/模型目录（来源冻结 ``src/config/profiles.ts``，MIT）。

按 R-06 / D09：provider 为冻结的 6 种定义；模型目录中的 ID、contextWindow、
vision、maxOutputTokens 与每 provider 默认端点/模型都是冻结数据，不以新目录替换基线。
``ProfilesConfig`` 用宽松映射保留来源的未知顶层字段宽容边界（R-12）。
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict, TypeGuard, cast

Provider = Literal["deepseek", "anthropic", "openai", "volcengine", "qianfan", "zhipu"]


class ModelInfo(TypedDict, total=False):
    id: str
    contextWindow: int
    vision: bool
    maxOutputTokens: int


# 一个 profile = provider + baseUrl + model + (key | keyRef)；保留未知/迁移字段。
Profile = dict[str, Any]
ProfilesConfig = dict[str, Any]


class ResolvedCredential(TypedDict):
    key: str
    provider: Provider
    baseUrl: str
    model: str
    source: str


DEFAULTS: dict[Provider, dict[str, str]] = {
    "deepseek": {"baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-pro"},
    "volcengine": {
        "baseUrl": "https://ark.cn-beijing.volces.com/api/coding/v3",
        "model": "deepseek-v4-pro",
    },
    "qianfan": {
        "baseUrl": "https://qianfan.baidubce.com/v2/tokenplan/personal",
        "model": "deepseek-v4-pro",
    },
    "zhipu": {
        "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
        "model": "glm-5.3",
    },
    "anthropic": {"baseUrl": "https://api.anthropic.com", "model": "claude-opus-5-5"},
    "openai": {"baseUrl": "https://api.openai.com/v1", "model": "gpt-6-astra"},
}

MODELS_BY_PROVIDER: dict[Provider, list[ModelInfo]] = {
    "deepseek": [
        {"id": "deepseek-v4-pro", "contextWindow": 1_000_000},
        {"id": "deepseek-flash", "contextWindow": 1_000_000, "vision": True},
    ],
    "volcengine": [
        {"id": "deepseek-v4-pro", "contextWindow": 1_000_000},
        {"id": "deepseek-v4-flash", "contextWindow": 1_000_000},
        {"id": "deepseek-v4.1-flash", "contextWindow": 1_000_000, "vision": True},
        {"id": "deepseek-v4.1-flash-economy", "contextWindow": 1_000_000, "vision": True},
        {"id": "doubao-seed-2.1-pro", "contextWindow": 1_024_000, "vision": True},
        {"id": "doubao-seed-2.1-lite", "contextWindow": 1_024_000, "vision": True},
        {"id": "doubao-seed-2.0-mini", "contextWindow": 256_000, "vision": True},
        {"id": "doubao-seed-evolving", "contextWindow": 1_024_000, "vision": True},
        {"id": "glm-5.3", "contextWindow": 1_000_000},
        {"id": "glm-5.3-flash", "contextWindow": 1_000_000, "vision": True},
        {"id": "kimi-k2.8-preview", "contextWindow": 1_000_000, "vision": True},
        {"id": "kimi-k3", "contextWindow": 1_000_000, "vision": True},
        {"id": "ark-code-latest", "contextWindow": 256_000, "vision": True,
         "maxOutputTokens": 32_000},
    ],
    "qianfan": [
        {"id": "deepseek-v4-pro", "contextWindow": 1_000_000},
        {"id": "deepseek-v4.1-flash-1017", "contextWindow": 1_000_000, "vision": True},
        {"id": "deepseek-v4.1-flash", "contextWindow": 1_000_000, "vision": True},
        {"id": "deepseek-v4-pro-0813", "contextWindow": 1_000_000},
        {"id": "deepseek-v4-flash-0731", "contextWindow": 1_000_000},
        {"id": "glm-5.3", "contextWindow": 1_000_000},
        {"id": "glm-5.3-flash", "contextWindow": 1_000_000, "vision": True},
        {"id": "glm-5.2", "contextWindow": 1_000_000},
        {"id": "glm-5.1", "contextWindow": 198_000},
        {"id": "kimi-k2.6", "contextWindow": 256_000, "vision": True},
        {"id": "ernie-5.1", "contextWindow": 128_000, "maxOutputTokens": 65_536},
    ],
    "zhipu": [
        {"id": "glm-5.3", "contextWindow": 1_000_000},
        {"id": "glm-5.3-flash", "contextWindow": 1_000_000, "vision": True},
    ],
    "anthropic": [
        {"id": "claude-opus-5-5", "contextWindow": 1_000_000, "vision": True},
        {"id": "claude-fable-5-1", "contextWindow": 1_000_000, "vision": True},
        {"id": "claude-sonnet-5-5", "contextWindow": 1_000_000, "vision": True},
        {"id": "claude-haiku-5-5", "contextWindow": 1_000_000, "vision": True},
    ],
    "openai": [
        {"id": "gpt-6-astra", "contextWindow": 1_050_000, "vision": True,
         "maxOutputTokens": 128_000},
        {"id": "gpt-6.1-sol", "contextWindow": 1_050_000, "vision": True,
         "maxOutputTokens": 128_000},
        {"id": "gpt-6-luna", "contextWindow": 1_050_000, "vision": True,
         "maxOutputTokens": 128_000},
        {"id": "gpt-5", "contextWindow": 400_000, "vision": True,
         "maxOutputTokens": 128_000},
    ],
}

# 自定义网关的兼容属性，独立于官方渠道当前公布的窗口（不加入 /model 选择项）。
LEGACY_MODELS: list[ModelInfo] = [
    {"id": "glm-5.2", "contextWindow": 200_000},
    {"id": "glm-5.1", "contextWindow": 1_000_000},
    {"id": "kimi-k2.7-code", "contextWindow": 256_000, "vision": True,
     "maxOutputTokens": 32_000},
    {"id": "minimax-m3", "contextWindow": 1_000_000, "vision": True},
]

DEFAULT_CONTEXT_WINDOW = 1_000_000

MODEL_INDEX: dict[str, ModelInfo] = {}
for _group in [*MODELS_BY_PROVIDER.values(), LEGACY_MODELS]:
    for _info in _group:
        MODEL_INDEX[_info["id"].lower()] = _info

VISION_MODEL_IDS: list[str] = list(dict.fromkeys(
    _info["id"]
    for _group in [*MODELS_BY_PROVIDER.values(), LEGACY_MODELS]
    for _info in _group
    if _info.get("vision") is True
))
VISION_MODELS: frozenset[str] = frozenset(VISION_MODEL_IDS)


def supportsVision(model: str) -> bool:
    """不在索引中的模型一律视为不支持（冻结 profiles.ts:130-132）。"""
    info = MODEL_INDEX.get(model.lower())
    return info is not None and info.get("vision") is True


def modelInfoFor(
    model: str, provider: Provider | None = None, baseUrl: str | None = None,
) -> ModelInfo | None:
    normalized = baseUrl.rstrip("/") if baseUrl else None
    resolved: Provider | None = provider
    if resolved is None:
        for key, default in DEFAULTS.items():
            if default["baseUrl"] == normalized:
                resolved = key
                break
    if resolved is not None and (
        baseUrl is None or (baseUrl.rstrip("/") if baseUrl else "") == DEFAULTS[resolved]["baseUrl"]
    ):
        for info in MODELS_BY_PROVIDER[resolved]:
            if info["id"].lower() == model.lower():
                return info
    return MODEL_INDEX.get(model.lower())


def contextWindowFor(
    model: str, provider: Provider | None = None, baseUrl: str | None = None,
) -> int:
    info = modelInfoFor(model, provider, baseUrl)
    return info["contextWindow"] if info is not None else DEFAULT_CONTEXT_WINDOW


def outputLimitFor(model: str, requested: int, baseUrl: str | None = None) -> int:
    """限制已知模型输出天花板，避免长输出重试发送超过服务端上限的预算。"""
    info = modelInfoFor(model, None, baseUrl)
    cap = info.get("maxOutputTokens") if info is not None else None
    return min(requested, cap) if cap is not None else requested


def _is_v2(raw: object) -> TypeGuard[ProfilesConfig]:
    return isinstance(raw, dict) and raw.get("version") == 2


def migrateConfig(raw: object) -> ProfilesConfig:
    """旧版 ``{apiKey,baseUrl?,model?}`` 或 v2 → 规范化 v2；null/损坏 → 空档案。"""
    if _is_v2(raw):
        return dict(raw)
    legacy: dict[Any, Any] = raw if isinstance(raw, dict) else {}
    api_key = legacy.get("apiKey")
    if isinstance(api_key, str) and api_key:
        base_url = legacy.get("baseUrl")
        model = legacy.get("model")
        return {
            "version": 2,
            "activeProfile": "default",
            "profiles": {
                "default": {
                    "provider": "deepseek",
                    "baseUrl": base_url if isinstance(base_url, str)
                    else DEFAULTS["deepseek"]["baseUrl"],
                    "model": model if isinstance(model, str)
                    else DEFAULTS["deepseek"]["model"],
                    "key": api_key,
                },
            },
        }
    return {"version": 2, "activeProfile": "default", "profiles": {}}


def resolveActive(cfg: ProfilesConfig) -> ResolvedCredential | None:
    """只看激活 profile 的内联 key；不读环境变量，缺 key → None。

    冻结 profiles.ts:196-211：交互模式只有 profile 一条路径，headless 通过
    ``--api-key`` CLI 参数传入；不从 OPENAI_API_KEY 等通用环境变量自动挑账户。
    """
    active = cfg.get("activeProfile")
    profiles_map = cfg.get("profiles")
    if not isinstance(active, str) or not isinstance(profiles_map, dict):
        return None
    p = profiles_map.get(active)
    if not isinstance(p, dict):
        return None
    key = p.get("key")
    if not isinstance(key, str) or not key:
        return None
    return cast(ResolvedCredential, {
        "key": key,
        "provider": p.get("provider"),
        "baseUrl": p.get("baseUrl"),
        "model": p.get("model"),
        "source": f"profile:{active}",
    })
