"""CFG-01/02/03: profiles 数据模型、冻结模型目录与模型继承。

预期独立来源：
- 冻结 src/config/profiles.ts:22-211 及 src/config/profiles.test.ts:4-210
- 冻结 src/config/model_selection.ts:1-23 及 .test.ts:5-31
- 规格 R-06 / D09 研究（模型目录沿用冻结 ID/窗口/vision/output cap）
按 S/D/R 把 TS 断言改写为 Python，不回填当前实现输出。
"""

from __future__ import annotations

import pytest

from ruocun.config import model_selection, profiles

# ---------------------------------------------------------------------------
# CFG-01 · migrateConfig / resolveActive (profiles.test.ts:4-72)
# ---------------------------------------------------------------------------


def test_migrate_legacy_apikey_into_default_deepseek_profile():
    # frozen profiles.test.ts:5-15
    out = profiles.migrateConfig({"apiKey": "sk-legacy", "baseUrl": "https://x", "model": "m1"})
    assert out["version"] == 2
    assert out["activeProfile"] == "default"
    assert out["profiles"]["default"] == {
        "provider": "deepseek",
        "baseUrl": "https://x",
        "model": "m1",
        "key": "sk-legacy",
    }


def test_migrate_legacy_fills_baseurl_and_model_defaults():
    # frozen profiles.test.ts:17-21
    out = profiles.migrateConfig({"apiKey": "sk-legacy"})
    assert out["profiles"]["default"]["baseUrl"] == profiles.DEFAULTS["deepseek"]["baseUrl"]
    assert out["profiles"]["default"]["model"] == profiles.DEFAULTS["deepseek"]["model"]


def test_migrate_without_key_produces_empty_profile_set():
    # frozen profiles.test.ts:23-27
    out = profiles.migrateConfig({"baseUrl": "https://x"})
    assert out["profiles"] == {}
    assert out["activeProfile"] == "default"


def test_migrate_returns_v2_unchanged_including_unknown_top_level_fields():
    # frozen profiles.test.ts:29-39 + R-12「未知顶层字段保存」
    v2 = {
        "version": 2,
        "onboardingComplete": True,
        "activeProfile": "work",
        "profiles": {
            "work": {"provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                     "model": "deepseek-v4-pro", "key": "sk-w"},
        },
        "theme": "dark",  # 未知顶层字段必须保留
    }
    assert profiles.migrateConfig(v2) == v2


@pytest.mark.parametrize("raw", [None, "not-json", 5, []])
def test_migrate_corrupt_or_empty_value_is_fresh_config(raw):
    # frozen profiles.test.ts:41-44（null/undefined/损坏 → 空档案）
    out = profiles.migrateConfig(raw)
    assert out["profiles"] == {}
    assert out["version"] == 2
    assert out["activeProfile"] == "default"


CFG = {
    "version": 2,
    "activeProfile": "personal",
    "profiles": {
        "personal": {"provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                     "model": "deepseek-v4-pro", "key": "sk-personal"},
        "work": {"provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                 "model": "deepseek-v4-pro", "key": "sk-work"},
    },
}


def test_resolve_active_uses_active_profile_and_reports_source():
    # frozen profiles.test.ts:57-66
    assert profiles.resolveActive(CFG) == {
        "key": "sk-personal", "provider": "deepseek",
        "baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-pro",
        "source": "profile:personal",
    }


def test_resolve_active_returns_null_when_active_profile_has_no_key():
    # frozen profiles.test.ts:68-71 + CFG-04「缺 key 不靠通用环境变量自动挑账户」
    empty = {"version": 2, "activeProfile": "default", "profiles": {}}
    assert profiles.resolveActive(empty) is None


# ---------------------------------------------------------------------------
# CFG-02 · 冻结模型目录 (profiles.test.ts:74-209)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("provider,base_url,model", [
    ("volcengine", "https://ark.cn-beijing.volces.com/api/coding/v3", "deepseek-v4-pro"),
    ("qianfan", "https://qianfan.baidubce.com/v2/tokenplan/personal", "deepseek-v4-pro"),
    ("zhipu", "https://open.bigmodel.cn/api/coding/paas/v4", "glm-5.3"),
])
def test_defaults_coding_plan_endpoints(provider, base_url, model):
    # frozen profiles.test.ts:74-99
    assert profiles.DEFAULTS[provider] == {"baseUrl": base_url, "model": model}


def test_every_provider_default_model_is_in_catalog_with_unique_ids():
    # frozen profiles.test.ts:102-108
    for provider, models in profiles.MODELS_BY_PROVIDER.items():
        ids = [m["id"] for m in models]
        assert profiles.DEFAULTS[provider]["model"] in ids
        assert len(set(ids)) == len(ids)
        assert all(isinstance(m["contextWindow"], int) and m["contextWindow"] > 0 for m in models)


@pytest.mark.parametrize("model_id", ["gpt-6-astra", "gpt-6.1-sol", "gpt-6-luna"])
def test_openai_three_tiers_window_and_vision(model_id):
    # frozen profiles.test.ts:109-113
    assert profiles.contextWindowFor(model_id) == 1_050_000
    assert profiles.supportsVision(model_id) is True


def test_openai_output_cap_is_frozen():
    # frozen profiles.ts:90-93 (maxOutputTokens: 128000)
    assert profiles.outputLimitFor("gpt-5", 256000) == 128000
    assert profiles.outputLimitFor("gpt-6-astra", 128000) == 128000


def test_ark_code_latest_window_and_vision():
    # frozen profiles.test.ts:114-116
    assert profiles.contextWindowFor("ark-code-latest") == 256_000
    assert profiles.supportsVision("DOUBAO-SEED-2.1-PRO") is True
    assert profiles.supportsVision("doubao-seed-2.0-mini") is True


def test_ernie_qianfan_window_and_output_cap():
    # frozen profiles.test.ts:117-119
    assert profiles.contextWindowFor("ernie-5.1", "qianfan") == 128_000
    assert profiles.outputLimitFor("ernie-5.1", 128000) == 65536
    assert profiles.outputLimitFor("ark-code-latest", 128000) == 32000
    assert profiles.outputLimitFor("unknown-model", 256000) == 256000


def test_qianfan_catalog_ids_are_frozen():
    # frozen profiles.test.ts:123-129
    assert [m["id"] for m in profiles.MODELS_BY_PROVIDER["qianfan"]] == [
        "deepseek-v4-pro", "deepseek-v4.1-flash-1017", "deepseek-v4.1-flash",
        "deepseek-v4-pro-0813", "deepseek-v4-flash-0731", "glm-5.3", "glm-5.3-flash",
        "glm-5.2", "glm-5.1", "kimi-k2.6", "ernie-5.1",
    ]


def test_deepseek_catalog_only_two_tiers():
    # frozen profiles.test.ts:130-132
    assert [m["id"] for m in profiles.MODELS_BY_PROVIDER["deepseek"]] == [
        "deepseek-v4-pro", "deepseek-flash",
    ]


def test_volcengine_catalog_ids_are_frozen():
    # frozen profiles.test.ts:133-149
    assert [m["id"] for m in profiles.MODELS_BY_PROVIDER["volcengine"]] == [
        "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4.1-flash",
        "deepseek-v4.1-flash-economy", "doubao-seed-2.1-pro", "doubao-seed-2.1-lite",
        "doubao-seed-2.0-mini", "doubao-seed-evolving", "glm-5.3", "glm-5.3-flash",
        "kimi-k2.8-preview", "kimi-k3", "ark-code-latest",
    ]


def test_zhipu_catalog_two_tiers():
    # frozen profiles.test.ts:150-152
    assert [m["id"] for m in profiles.MODELS_BY_PROVIDER["zhipu"]] == [
        "glm-5.3", "glm-5.3-flash",
    ]


@pytest.mark.parametrize("model_id", [
    "deepseek-v4.1-flash", "deepseek-v4.1-flash-economy", "kimi-k2.8-preview",
    "kimi-k3", "glm-5.3-flash",
])
def test_vision_positive(model_id):
    # frozen profiles.test.ts:155-164
    assert profiles.supportsVision(model_id) is True


@pytest.mark.parametrize("model_id", [
    "deepseek-v4-pro", "glm-5.2", "glm-5.3", "unknown-model",
])
def test_vision_negative(model_id):
    # frozen profiles.test.ts:165-170
    assert profiles.supportsVision(model_id) is False


def test_context_window_channel_distinction():
    # frozen profiles.test.ts:174-209
    d = profiles.DEFAULTS
    assert profiles.contextWindowFor("glm-5.2") == 200_000
    assert profiles.contextWindowFor("GLM-5.2") == 200_000
    assert profiles.contextWindowFor("glm-5.2", "zhipu", d["zhipu"]["baseUrl"]) == 200_000
    assert profiles.contextWindowFor("glm-5.2", "qianfan", d["qianfan"]["baseUrl"]) == 1_000_000
    assert profiles.contextWindowFor("GLM-5.3-Flash") == 1_000_000
    assert profiles.contextWindowFor("glm-5.1", "qianfan", d["qianfan"]["baseUrl"]) == 198_000
    assert profiles.contextWindowFor("glm-5.2", "volcengine", d["volcengine"]["baseUrl"]) == 200_000
    assert profiles.contextWindowFor("doubao-seed-2.0-mini") == 256_000
    assert profiles.contextWindowFor("Doubao-Seed-2.0-Mini", "volcengine",
                                     d["volcengine"]["baseUrl"]) == 256_000
    assert profiles.contextWindowFor("doubao-seed-2.1-pro") == 1_024_000
    assert profiles.contextWindowFor("glm-5.3", "zhipu", d["zhipu"]["baseUrl"]) == 1_000_000
    assert profiles.contextWindowFor("glm-5.3", "deepseek", "http://llm-gw.jd.local/v1") == 1_000_000
    assert profiles.contextWindowFor("GLM-5.3-joybuilder", "deepseek",
                                     "http://llm-gw.jd.local/v1") == 1_000_000
    assert profiles.contextWindowFor("glm-5.2", "deepseek",
                                     "https://gw.example.com/v1") == 200_000
    assert profiles.contextWindowFor("deepseek-v4-pro") == 1_000_000
    assert profiles.contextWindowFor("kimi-k2.6") == 256_000
    assert profiles.contextWindowFor("unknown-model") == 1_000_000


# ---------------------------------------------------------------------------
# CFG-03 · 模型继承 / 辅助模型 (model_selection.test.ts:5-31)
# ---------------------------------------------------------------------------


def test_get_agent_model_priority_override_gt_agent_gt_parent():
    # frozen model_selection.test.ts:26-31
    assert model_selection.getAgentModel("configured", "current", " INHERIT ") == "current"
    assert model_selection.getAgentModel("gateway-pro", None) == "gateway-pro"
    assert model_selection.getAgentModel("agent-def", "parent-model") == "agent-def"
    assert model_selection.getAgentModel("agent-def", "parent-model", "over") == "over"


def test_get_agent_model_inherit_falls_through_to_parent():
    assert model_selection.getAgentModel("inherit", "parent-x") == "parent-x"
    assert model_selection.getAgentModel(None, "parent-x") == "parent-x"


def test_get_agent_model_missing_inheritable_parent_errors_not_guess_provider():
    # frozen model_selection.test.ts:26-28 + CFG-03「缺 parent 明确报错，不暗换 provider」
    with pytest.raises(ValueError, match="缺少可继承的主模型"):
        model_selection.getAgentModel(None, None)
    with pytest.raises(ValueError, match="缺少可继承的主模型"):
        model_selection.getAgentModel("inherit", " ")


def test_custom_gateway_never_guesses_cheap_model():
    # frozen model_selection.test.ts:6-10 + CFG-02「自定义网关不猜便宜档」
    for provider in profiles.DEFAULTS:
        for model in ["GLM-5.3-Flash-joybuilder", "deepseek-v4-pro", "glm-5.3"]:
            ctx = {"provider": provider, "baseUrl": "https://gateway.example/v1", "model": model}
            assert model_selection.defaultAuxiliaryModel(ctx) == model


def test_non_deepseek_main_model_not_swapped_to_deepseek():
    # frozen model_selection.test.ts:11-14
    for provider in ["anthropic", "openai", "volcengine", "qianfan"]:
        model = (profiles.DEFAULTS[provider]["model"]
                 if provider in ("anthropic", "openai") else "kimi-k2.8-preview")
        ctx = {"provider": provider, "baseUrl": profiles.DEFAULTS[provider]["baseUrl"], "model": model}
        assert model_selection.defaultAuxiliaryModel(ctx) == model


def test_known_official_endpoints_keep_same_family_cheap_tier():
    # frozen model_selection.test.ts:15-25
    assert model_selection.defaultAuxiliaryModel(
        {"provider": "deepseek", **profiles.DEFAULTS["deepseek"]}) == "deepseek-flash"
    assert model_selection.defaultAuxiliaryModel(
        {"provider": "zhipu", "model": "glm-5.3",
         "baseUrl": profiles.DEFAULTS["zhipu"]["baseUrl"] + "/"}) == "glm-5.3-flash"
    for provider in ["volcengine", "qianfan"]:
        for model in ["deepseek-v4-pro", "deepseek-v4-pro-0813", "deepseek-v4.1-flash-1017"]:
            ctx = {"provider": provider, "model": model,
                   "baseUrl": profiles.DEFAULTS[provider]["baseUrl"]}
            assert model_selection.defaultAuxiliaryModel(ctx) == "deepseek-v4.1-flash"
