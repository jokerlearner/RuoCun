"""WIRE-07/08 · 分类谓词、默认值与退避公式（独立来源，非当前实现自证）。

预期来源：
- 冻结 ``src/client/client.ts:15``（RETRYABLE_STATUS）、``:18-43``（三谓词）、
  ``:127-131``（idle/maxRetries/retryDelayMs 默认）、``:128``（idleErrMsg）、
  ``:139-142``（isRetryable）、``:301-303``（Retry-After）、``:352``（退避公式）。
- 冻结 ``src/client/client.test.ts:541-554``（isRateLimitError/isContextLengthError）、
  ``:650-693``（isCredentialError）、``:338-359``（重试次数）。
按 S/D/R 把 TS 断言改写；期望全是冻结源码里的字面量/公式，不从 Python 输出回填。
"""

from __future__ import annotations

from ruocun.client import resilient as r


class _Err(Exception):
    """模拟冻结 JS ``Object.assign(new Error(msg), {status, retryableStatus})``。"""

    def __init__(
        self, message: str, status: int | None = None, retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        if status is not None:
            self.status = status
        if retryable is not None:
            self.retryableStatus = retryable


# ---------------------------------------------------------------------------
# 冻结 client.ts:15 / :127-131 的常量与默认值
# ---------------------------------------------------------------------------


def test_retryable_status_set_is_frozen():
    assert r.RETRYABLE_STATUS == frozenset({408, 409, 425, 429, 500, 502, 503, 504, 529})


def test_defaults_are_frozen_240s_2retries_600ms():
    assert r.DEFAULT_IDLE_MS == 240000
    assert r.DEFAULT_MAX_RETRIES == 2
    assert r.DEFAULT_RETRY_DELAY_MS == 600
    assert r.RETRY_AFTER_CAP_MS == 120000


def test_idle_error_message_matches_frozen_template():
    # 冻结 client.ts:128 `模型流空闲超时(${Math.round(idleMs/1000)}s 未收到数据),已停止本回合`
    assert r.idleErrorMessage(240000) == "模型流空闲超时(240s 未收到数据),已停止本回合"
    assert r.idleErrorMessage(50000) == "模型流空闲超时(50s 未收到数据),已停止本回合"


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:541-548 · isRateLimitError
# ---------------------------------------------------------------------------


def test_is_rate_limit_error_matches_frozen_assertions():
    assert r.isRateLimitError(_Err("boom", status=429)) is True
    assert r.isRateLimitError(_Err("API error 429 from x: quota_exceeded")) is True
    assert r.isRateLimitError(_Err("rate_limit_exceeded")) is True
    assert r.isRateLimitError(_Err("请求频率超限")) is True
    assert r.isRateLimitError(_Err("boom", status=500)) is False
    assert r.isRateLimitError(_Err("ECONNRESET")) is False


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:550-554 · isContextLengthError
# ---------------------------------------------------------------------------


def test_is_context_length_error_matches_frozen_assertions():
    assert r.isContextLengthError(_Err("maximum context length is 65536 tokens")) is True
    assert r.isContextLengthError(_Err("prompt is too long")) is True
    assert r.isContextLengthError(_Err("ECONNRESET")) is False


# ---------------------------------------------------------------------------
# 冻结 client.test.ts:650-693 · isCredentialError
# ---------------------------------------------------------------------------


def test_is_credential_error_matches_frozen_assertions():
    assert r.isCredentialError(_Err("API error 401", status=401)) is True
    assert r.isCredentialError(_Err("API error 403", status=403)) is True
    assert r.isCredentialError(_Err("API error 400 from ark: InvalidSubscription", status=400)) is True
    assert r.isCredentialError(_Err("API error 400: subscription expired", status=400)) is True
    assert r.isCredentialError(_Err("API error 400: authentication fails", status=400)) is True
    assert r.isCredentialError(_Err("API error 400: bad request", status=400)) is False
    assert r.isCredentialError(_Err("not found", status=404)) is False
    assert r.isCredentialError(_Err("rate limited", status=429)) is False
    assert r.isCredentialError(_Err("something")) is False


# ---------------------------------------------------------------------------
# 冻结 client.ts:138-142 · isRetryable（socket/网络瞬断 / retryableStatus）
# ---------------------------------------------------------------------------


def test_is_retryable_matches_frozen_network_keywords():
    assert r.isRetryable(_Err("The socket connection was closed unexpectedly")) is True
    assert r.isRetryable(_Err("fetch failed: ECONNRESET")) is True
    assert r.isRetryable(_Err("ECONNREFUSED")) is True
    assert r.isRetryable(_Err("ETIMEDOUT")) is True
    assert r.isRetryable(_Err("EPIPE")) is True
    assert r.isRetryable(_Err("terminated")) is True
    assert r.isRetryable(_Err("ENOTFOUND")) is True
    assert r.isRetryable(_Err("EAI_AGAIN")) is True
    assert r.isRetryable(_Err("network is down")) is True
    assert r.isRetryable(_Err("401 unauthorized")) is False
    assert r.isRetryable(_Err("bad request", retryable=True)) is True
    assert r.isRetryable(_Err("bad request", retryable=False)) is False


# ---------------------------------------------------------------------------
# 冻结 client.ts:301-303 · Retry-After 秒→毫秒、上限 120000、非法/负值跳过
# ---------------------------------------------------------------------------


def test_retry_after_parsing_matches_frozen_rules():
    assert r.retryAfterMs({"retry-after": "0"}, 429) == 0.0
    assert r.retryAfterMs({"retry-after": "2"}, 503) == 2000.0
    assert r.retryAfterMs({"retry-after": "999"}, 429) == 120000.0
    assert r.retryAfterMs({"retry-after": "abc"}, 429) is None  # Number("abc")=NaN
    assert r.retryAfterMs({"retry-after": "-1"}, 429) is None  # s >= 0
    assert r.retryAfterMs({}, 429) is None
    assert r.retryAfterMs({"Retry-After": "1"}, 429) == 1000.0  # header 名大小写归一


# ---------------------------------------------------------------------------
# 冻结 client.ts:352 · 退避公式 retryDelayMs*(attempt+1)+floor(random*250)
# ---------------------------------------------------------------------------


def test_backoff_formula_matches_frozen_client_ts():
    assert r.backoffMs(600, 0, 0) == 600.0   # 第1次重试
    assert r.backoffMs(600, 1, 0) == 1200.0  # 第2次重试
    assert r.backoffMs(600, 0, 123) == 723.0
    assert r.backoffMs(0, 2, 0) == 0.0
