"""冻结 src/session/cost.test.ts 的 9 项人民币计费语义（MIT）。"""

import pytest

from ruocun.session.cost import estimateCostCNY, formatCNY, loadPrices, pricesFor


def test_prices_hit_miss_output_separately():
    result = estimateCostCNY(
        {"promptTokens": 2_000_000, "completionTokens": 1_000_000,
         "cacheHitTokens": 1_000_000, "cacheMissTokens": 1_000_000},
        {"inputHit": .5, "inputMiss": 2, "output": 8},
    )
    assert result == pytest.approx(10.5, abs=.00001)


def test_miss_derived_from_prompt_minus_hit():
    result = estimateCostCNY(
        {"promptTokens": 1_000_000, "completionTokens": 0,
         "cacheHitTokens": 1_000_000, "cacheMissTokens": 0},
        {"inputHit": .5, "inputMiss": 2, "output": 8},
    )
    assert result == pytest.approx(.5, abs=.00001)


def test_env_overrides_fallback_prices():
    p = loadPrices({"RUOCUN_PRICE_INPUT_MISS": "4", "RUOCUN_PRICE_OUTPUT": "16"})
    assert p == {"inputHit": .9, "inputMiss": 4, "output": 16}


def test_format_small_amount_with_more_decimals():
    assert "0.0040" in formatCNY(.004)
    assert formatCNY(12.3) == "￥12.30"


def test_known_non_deepseek_model_prices():
    assert pricesFor("doubao-seed-2.0-pro", {}) == {"inputHit": .64, "inputMiss": 3.2, "output": 16}
    assert pricesFor("glm-5.2", {}) == {"inputHit": 2, "inputMiss": 8, "output": 28}
    assert pricesFor("kimi-k2.6", {}) == {"inputHit": 1.1, "inputMiss": 6.5, "output": 27}
    assert pricesFor("ernie-5.1", {}) == {"inputHit": 1.6, "inputMiss": 4, "output": 18}


def test_gateway_names_normalize_case_dots_and_suffix():
    fixtures = [
        ("DeepSeek-V4-Pro-joybuilder", {"inputHit": .9, "inputMiss": 9, "output": 27}),
        ("DeepSeek-V4-Flash-joybuilder", {"inputHit": .2, "inputMiss": 2, "output": 8.2}),
        ("Claude-Opus-4.8-joybuilder", {"inputHit": 3.4, "inputMiss": 34, "output": 170}),
        ("Claude-Sonnet-5-joybuilder", {"inputHit": 1.36, "inputMiss": 13.6, "output": 68}),
        ("GLM-5.3-joybuilder", {"inputHit": 2, "inputMiss": 8, "output": 28}),
        ("GLM-5.2-joybuilder", {"inputHit": 2, "inputMiss": 8, "output": 28}),
        ("GPT-5.5-joybuilder", {"inputHit": 3.4, "inputMiss": 34, "output": 204}),
    ]
    for model, expected in fixtures:
        assert pricesFor(model, {}) == expected


def test_gateway_double_suffix():
    assert pricesFor("DeepSeek-V4-Pro-local-joybuilder", {}) == {"inputHit": .9, "inputMiss": 9, "output": 27}


def test_glm_flash_tier():
    assert pricesFor("GLM-5.3-Flash", {}) == {"inputHit": .2, "inputMiss": .8, "output": 2.8}


def test_unknown_model_fallbacks():
    assert pricesFor("some-new-flash-model", {})["inputMiss"] == 2
    assert pricesFor("some-new-model", {})["inputMiss"] == 9
