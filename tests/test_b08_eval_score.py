"""来源 evals/score.test.mjs 的评分断言。"""

import importlib.util
from pathlib import Path

import pytest

source = Path(__file__).resolve().parents[1] / "evals" / "score.py"
spec = importlib.util.spec_from_file_location("ruocun_eval_score", source)
assert spec is not None and spec.loader is not None
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)
fitTimeHorizon, metasToSamples, weightedCompletion = score.fitTimeHorizon, score.metasToSamples, score.weightedCompletion


@pytest.mark.parametrize(("passed", "completion"), [
    (["a", "b", "c"], 1), ([], 0), (["b", "c"], 5 / 6), (["a", "zzz"], 1 / 6),
])
def test_source_weighted_completion(passed, completion):
    cases = [{"id": "a", "weight": 1}, {"id": "b", "weight": 2}, {"id": "c", "weight": 3}]
    assert weightedCompletion(cases, passed)["completion"] == pytest.approx(completion)


def test_source_empty_and_default_weights():
    assert weightedCompletion([], [])["completion"] == 0
    assert weightedCompletion([{"id": "x"}, {"id": "y"}], ["x"])["completion"] == 0.5


def test_source_horizon_thresholds_and_degenerate_data():
    samples = metasToSamples([{"humanMinutes": value, "completion": float(value <= 60)}
                              for value in (5, 10, 15, 20, 30, 60, 90, 120, 180, 240)])
    fit = fitTimeHorizon(samples)
    assert 30 < fit["p50"] < 120 and 0 < fit["p80"] < fit["p50"]
    assert fitTimeHorizon(samples[:4])["degenerate"]
    assert fitTimeHorizon(samples[-4:])["degenerate"]
    assert fitTimeHorizon(samples[:1])["degenerate"]
    assert [row["success"] for row in metasToSamples([
        {"humanMinutes": 30, "completion": 0.6}, {"humanMinutes": None, "completion": 1},
    ], 0.5)] == [True]
