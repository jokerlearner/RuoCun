"""模型流重试、非流式兜底与 idle watchdog（来源冻结 ``src/client/client.ts``，MIT）。

WIRE-07：仅在参考允许阶段/次数重试；已产出内容不从头重复；ADR-0003 未知结果
不自动重放；529 background、无 Retry-After 的 429 保留来源分支。
WIRE-08：默认 240s idle，仅有效 delta 重置；用户取消保留部分；产出后 idle 明确错误。

本模块只在 ``src/ruocun/client/`` 内组织重试/watchdog，复用 04/05 已建立的
``client.py`` 请求组装、SSE 分帧、累积器与 Responses 路由（不重定义 chunks
消费逻辑、不另起第二套 client、不修改公共类型契约）。
"""

from __future__ import annotations

import http.client
import ipaddress
import json
import math
import os
import random
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast

from ..config.compat import resolve_env
from . import client, responses
from .types import StreamChatOptions, StreamDelta

# 冻结 client.ts:15 —— 过载/网关/限流状态；429 是否真走重试见 !res.ok 分支。
RETRYABLE_STATUS: frozenset[int] = frozenset(
    {408, 409, 425, 429, 500, 502, 503, 504, 529}
)
# 冻结 client.ts:127-130 默认值。
DEFAULT_IDLE_MS: int = 240000
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_RETRY_DELAY_MS: int = 600
# 冻结 client.ts:303 Math.min(s * 1000, 120_000)。
RETRY_AFTER_CAP_MS: int = 120000

# 冻结 client.ts:20 —— 上下文超限（loop 反应式压缩，client 不重试/不兜底）。
_CONTEXT_LENGTH_RE = re.compile(
    r"context length|maximum context|too many tokens|reduce the length|"
    r"context_length_exceeded|prompt is too long|exceeds? the maximum|input is too long",
    re.IGNORECASE,
)
# 冻结 client.ts:30 —— 限流/配额（loop 的用户决策/退避路径，client 不自动换模型）。
_RATE_LIMIT_RE = re.compile(
    r"\b429\b|rate[_ -]?limit|quota_exceeded|限流|请求频率",
    re.IGNORECASE,
)
# 冻结 client.ts:40 —— 凭证/认证（400 含订阅关键词）。
_CREDENTIAL_RE = re.compile(
    r"invalid.*key|authentication|unauthorized|subscription|CodingPlan|billing|"
    r"InvalidSubscription",
    re.IGNORECASE,
)
# 冻结 client.ts:141 —— 网络瞬断关键词（产出前失败才可重试）。
_RETRYABLE_RE = re.compile(
    r"socket|ECONNRESET|ECONNREFUSED|ETIMEDOUT|EPIPE|closed unexpectedly|"
    r"fetch failed|terminated|ENOTFOUND|EAI_AGAIN|network",
    re.IGNORECASE,
)


def idleErrorMessage(idle_ms: float) -> str:
    """冻结 client.ts:128 ``模型流空闲超时(${Math.round(idleMs/1000)}s ...)``。

    JS ``Math.round`` 对非负数等于 ``floor(x + 0.5)``，不用 Python banker's rounding。
    """
    value = idle_ms / 1000
    if math.isnan(value):
        seconds: int | str = "NaN"
    elif math.isinf(value):
        seconds = "Infinity" if value > 0 else "-Infinity"
    else:
        seconds = int(math.floor(value + 0.5))
    return f"模型流空闲超时({seconds}s 未收到数据),已停止本回合"


def _jsNumber(value: str) -> float:
    """环境变量的 JS Number：识别空白、十进制/指数、Infinity 与无符号进制前缀。"""
    token = value.strip()
    if not token:
        return 0.0
    if re.fullmatch(r"0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+", token):
        try:
            return float(int(token, 0))
        except OverflowError:
            return math.inf
    if re.fullmatch(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|Infinity)", token):
        return float(token)
    return math.nan


def _nodeTimerMs(value: float) -> float:
    """Node 22 setTimeout 的到期时长；保留原值供错误消息而不静默改配置。"""
    if not math.isfinite(value) or value < 1 or value > 2147483647:
        return 1.0
    return float(math.floor(value))


def isContextLengthError(e: BaseException) -> bool:
    """冻结 client.ts:18-21；导出给 loop 判定（client 不重试/不兜底）。"""
    return bool(_CONTEXT_LENGTH_RE.search(str(e)))


def isRateLimitError(e: BaseException) -> bool:
    """冻结 client.ts:26-31；status 429 或限流/配额关键词。"""
    status = getattr(e, "status", None)
    if status == 429:
        return True
    return bool(_RATE_LIMIT_RE.search(str(e)))


def isCredentialError(e: BaseException) -> bool:
    """冻结 client.ts:35-43；401/403 或含订阅关键词的 400。"""
    status = getattr(e, "status", None)
    if status == 401 or status == 403:
        return True
    if status == 400:
        return bool(_CREDENTIAL_RE.search(str(e)))
    return False


def isRetryable(e: BaseException) -> bool:
    """冻结 client.ts:138-142；retryableStatus 内部标记或网络瞬断关键词。"""
    if getattr(e, "retryableStatus", False) is True:
        return True
    # Python/Windows 的本地化错误文本不一定含 Node 错误码；按对应异常类型识别。
    if isinstance(e, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError,
                      socket.gaierror)):
        return True
    if isinstance(e, urllib.error.URLError) and isinstance(e.reason, BaseException):
        return isRetryable(e.reason)
    # 冻结把 ``${e.name} ${e.message}`` 一起纳入；Python 用类名近似 name。
    return bool(_RETRYABLE_RE.search(f"{type(e).__name__} {e}"))


def retryAfterMs(headers: Mapping[str, str], status: int) -> float | None:
    """冻结 client.ts:301-303：Retry-After 秒→毫秒、下限 0、上限 120000。

    header 名按 HTTP Headers 规范大小写不敏感（JS ``headers.get`` 语义）；非法
    数字（``Number("abc")`` → NaN）或负值跳过。仅可重试状态才需要等待时长，
    其余状态直接 fatal、不会进入退避（与冻结可观察行为等价）。
    """
    if status not in RETRYABLE_STATUS:
        return None
    raw: str | None = None
    for key, value in headers.items():
        if key.lower() == "retry-after":
            raw = value
            break
    if raw is None or raw == "":
        return None
    seconds = _jsNumber(raw)
    if not math.isfinite(seconds) or seconds < 0:
        return None
    return min(seconds * 1000, RETRY_AFTER_CAP_MS)


def backoffMs(retry_delay_ms: float, attempt: int, jitter_ms: float) -> float:
    """冻结 client.ts:352 ``retryDelayMs*(attempt+1)+floor(random()*250)``。

    jitter 由调用方注入（冻结的 ``Math.floor(Math.random()*250)``），便于 oracle
    用固定值验证公式，而不是照抄「指数退避」注释。
    """
    return retry_delay_ms * (attempt + 1) + jitter_ms


# ---------------------------------------------------------------------------
# 任务06 · 重试 / watchdog 编排（冻结 client.ts:271-378 的 client 层重试循环）
# ---------------------------------------------------------------------------


class IdleTimeoutError(RuntimeError):
    """idle watchdog 触发（冻结 client.ts:283-286）。"""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class RequestCancelled(RuntimeError):
    """用户取消请求。"""


def _monotonic() -> float:
    return time.monotonic()


def _realSleep(seconds: float) -> None:
    time.sleep(seconds)


def _defaultJitter() -> float:
    # 冻结 client.ts:352 Math.floor(Math.random() * 250)
    return float(random.randrange(250))


@dataclass
class ResilientContext:
    """注入式系统边界依赖（时钟 / 退避 / jitter / 取消 / 证据回调）。

    默认真实时钟与真实 sleep；测试注入 fake clock 与 no-op sleep，让 240s idle
    与退避可确定性验证，不真等、不访问网络（mocking.md：只在系统边界注入）。
    """

    clock: Callable[[], float] = _monotonic
    sleep: Callable[[float], None] = _realSleep
    jitter_ms: Callable[[], float] = _defaultJitter
    cancel: Callable[[], bool] | None = None
    on_delta: Callable[[StreamDelta], None] | None = None
    on_attempt: Callable[[AttemptRecord], None] | None = None
    resolver_command: tuple[str, ...] | None = None
    on_resolver_start: Callable[[subprocess.Popen[bytes]], None] | None = None


@dataclass(frozen=True)
class AttemptRecord:
    """每次尝试的独立证据（08 契约 request/attempt identity：同事实只累计一次）。"""

    index: int
    kind: str                       # "stream" | "fallback"
    http_status: int | None
    retry_after_ms: float | None
    deltas_count: int
    yielded_any: bool
    replayed: bool                  # 是否「已产出后重放」（冻结从不发生）
    outcome: str                    # complete/partial/retry/fallback/fatal/idle/cancelled
    idle_triggered: bool
    classification: str             # no-output-before-failure / sent-but-outcome-unknown
    error: str | None


@dataclass(frozen=True)
class ResilientResult:
    """任务06 结构化结果（不改动 04 的 ``StreamResult`` 公共契约）。"""

    status: Literal["complete", "partial", "failed"]
    deltas: list[StreamDelta]
    message: dict[str, Any]
    usage: dict[str, Any] | None
    finish_reason: str | None
    attempts: list[AttemptRecord]
    request_body: dict[str, Any]
    error: str | None = None
    error_exception: Exception | None = None
    error_status: int | None = None
    exit_code: int = 0
    watchdog_triggered: bool = False
    fallback_used: bool = False
    replayed: bool = False
    content_duplicated: bool = False
    cancelled: bool = False


class IdleWatchdog:
    """冻结 client.ts:280-286, 321-328：默认 240s，**仅有效 delta 重置**。

    每帧主动检查并仅在有效 delta 重置；计时线程向默认 HTTP transport 发出
    socket 中断，结束前必须 join。自定义 transport 须自行保证可及时返回，
    域名解析等尚无 socket 的阻塞阶段不能仅凭 socket 中断保证及时停止。
    """

    def __init__(
        self, timeout_s: float, clock: Callable[[], float], message: str,
        cancel: Callable[[], bool] | None = None,
    ) -> None:
        self._timeout_s = timeout_s
        self._clock = clock
        self._message = message
        self._last_delta_at = clock()
        self._triggered = False
        self._cancel = cancel
        self._cancelled = False
        self._done = threading.Event()
        self._thread: threading.Thread | None = None

    def arm(self) -> None:
        self._last_delta_at = self._clock()  # 连接/首字节阶段也纳入看门狗

    def reset(self) -> None:
        self._last_delta_at = self._clock()  # 仅有效 delta 调用

    def check(self) -> None:
        if self._cancelled or (self._cancel is not None and self._cancel()):
            self._cancelled = True
            raise RequestCancelled("请求已取消")
        if self._triggered or self._clock() - self._last_delta_at >= self._timeout_s:
            self._triggered = True
            raise IdleTimeoutError(self._message)

    def start(self, abort: Callable[[], None]) -> None:
        def watch() -> None:
            while not self._done.wait(0.02):
                try:
                    self.check()
                except (IdleTimeoutError, RequestCancelled):
                    # 在连接尚未建立时 socket 可能暂不存在；持续尝试直到被停止。
                    abort()

        self._thread = threading.Thread(target=watch, name="ruocun-idle-watchdog")
        self._thread.start()

    def stop(self) -> None:
        self._done.set()
        if self._thread is not None:
            self._thread.join()

    @property
    def triggered(self) -> bool:
        return self._triggered

    @property
    def cancelled(self) -> bool:
        return self._cancelled


def _resolve_addresses(
    host: str, port: int, context: ResilientContext, watchdog: IdleWatchdog,
) -> list[Any]:
    """以本次请求私有 helper 解析；中断时必须停止并等待该子进程。"""
    watchdog.check()
    if context.resolver_command is None and getattr(sys, "frozen", False):
        raise RuntimeError("独立程序尚未配置 DNS helper")
    command = context.resolver_command or (
        sys.executable, "-I", "-X", "utf8", "-m", "ruocun.client._dns_helper",
    )
    # 解析不需要账户、凭据或配置路径；仅保留 Windows 进程启动所需环境。
    allowed = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT")
    child_env = {name: os.environ[name] for name in allowed if name in os.environ}
    child_env["PATH"] = os.path.dirname(sys.executable)
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=child_env, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    finished_io = False
    try:
        if context.on_resolver_start is not None:
            context.on_resolver_start(process)
        payload: bytes | None = json.dumps({"host": host, "port": port}).encode("utf-8")
        while True:
            watchdog.check()
            try:
                stdout, stderr = process.communicate(input=payload, timeout=0.05)
                finished_io = True
                break
            except subprocess.TimeoutExpired:
                payload = None
        watchdog.check()
        if process.wait() != 0 or stderr:
            raise RuntimeError("DNS helper 执行失败")
        data: Any = json.loads(stdout.decode("utf-8"))
        if not isinstance(data, dict):
            raise RuntimeError("DNS helper 返回无效结果")
        error = data.get("error")
        if isinstance(error, dict):
            raise socket.gaierror(error.get("errno"), error.get("message"))
        result = data.get("addresses")
        if not isinstance(result, list):
            raise RuntimeError("DNS helper 未返回地址")
        return result
    finally:
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                if process.poll() is None:
                    raise
        if not finished_io:
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5)
        process.wait()


def _resolveIdleMs(
    opts: StreamChatOptions, env: Mapping[str, str] | None,
) -> float:
    explicit = opts.get("idleTimeoutMs")
    if explicit is not None:
        return float(explicit)
    source = os.environ if env is None else env
    raw = resolve_env("STREAM_IDLE_MS", source)
    parsed = _jsNumber(raw) if raw is not None else math.nan
    # 冻结 client.ts:127 Number(env) || 240000；负数和无穷大为真。
    return float(DEFAULT_IDLE_MS) if parsed == 0 or math.isnan(parsed) else parsed


def _resolveMaxRetries(opts: StreamChatOptions) -> int:
    value = opts.get("maxRetries")
    return DEFAULT_MAX_RETRIES if value is None else int(value)


def _resolveRetryDelayMs(opts: StreamChatOptions) -> float:
    value = opts.get("retryDelayMs")
    return float(DEFAULT_RETRY_DELAY_MS) if value is None else float(value)


def _stateHadOutput(state_out: dict[str, Any]) -> bool:
    # Frozen yieldedAny is set by emitted StreamDelta, not buffered tool fragments.
    deltas = state_out.get("deltas")
    return isinstance(deltas, list) and bool(deltas)


def _partialFromState(
    state_out: dict[str, Any],
) -> tuple[list[StreamDelta], dict[str, Any], dict[str, Any] | None, str | None]:
    acc = state_out.get("acc")
    deltas = state_out.get("deltas")
    items: list[StreamDelta] = list(deltas) if isinstance(deltas, list) else []
    if acc is None:
        return items, {"role": "assistant", "content": None}, None, None
    return items, acc.buildMessage(), acc.last_usage, acc.finish_reason


def _classification(yielded_any: bool) -> str:
    # ADR-0003：产出后「已发送但结果未知」不自动重放；产出前才允许重试。
    return "sent-but-outcome-unknown" if yielded_any else "no-output-before-failure"


def _emptyMessage() -> dict[str, Any]:
    return {"role": "assistant", "content": None}


def _recoverable(
    err: BaseException, idled_out: bool, status: int | None,
    retry_after_ms: float | None,
) -> bool:
    """冻结 client.ts:344-346 recoverable 判定（idle / 瞬断 / 过载状态）。"""
    if idled_out:
        return True
    if isinstance(err, client.SseError):
        return True  # 冻结 :226 SSE error 带 retryableStatus=true
    if isinstance(err, (client.StreamError, client.StreamDisconnected)):
        return True  # 断流/网络瞬断（产出前）
    if isinstance(err, client.ApiError):
        if status == 429 and retry_after_ms is None:
            return False  # 冻结 :308 429 无 Retry-After → 立即上抛，不重试/不兜底
        return status in RETRYABLE_STATUS if status is not None else False
    return isRetryable(err)


def _nonStreamingFallback(
    opts: StreamChatOptions, transport: client.Transport,
    env: Mapping[str, str] | None,
) -> tuple[list[StreamDelta], dict[str, Any], dict[str, Any] | None, str | None]:
    """冻结 client.ts:145-175 + responses.ts:66-71：流式彻底失败后一次性兜底。

    - Chat：``{...body, stream:false}`` 删 stream_options，POST /chat/completions，
      解析 ``choices[0].message``（content/tool_calls/reasoning_content/responseItems）。
    - Responses：经 05 桥转 ``stream:false`` 请求，非流式 ``output`` 经
      ``responsesMessage`` 归一化后走**同一段** Chat 形状解析（冻结 responsesFetch
      对包装 fetch 的处理），保留工具调用与推理项（responses.test.ts:76-86）。
    """
    use_responses = responses.usesResponses(opts["baseUrl"], opts["model"])
    chat_body = client.buildRequestBody(opts, env=env, use_responses=use_responses)
    ns_chat: dict[str, Any] = {**chat_body, "stream": False}
    ns_chat.pop("stream_options", None)
    if use_responses:
        body = responses.buildResponsesRequest(ns_chat)
        url = responses.RESPONSES_ENDPOINT
    else:
        body = ns_chat
        url = opts["baseUrl"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {opts['apiKey']}",
    }
    body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8", errors="backslashreplace")
    response = transport(url, headers, body_bytes)
    if not 200 <= response.status < 300:
        raise client.ApiError(
            f"API error {response.status}", status=response.status,
            headers=dict(response.headers),
        )
    raw = b"".join(response.chunks)
    data: Any = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("非流式兜底响应不是 JSON 对象")
    chat_data: dict[str, Any]
    if use_responses:
        # 冻结 responsesFetch:67-71：非流式 Responses → 统一 Chat 形状
        if data.get("error") or data.get("status") == "failed":
            raise client.ApiError(
                f"Responses error: {data.get('error')}", status=response.status,
            )
        output = data.get("output")
        items: list[dict[str, Any]] = (
            cast("list[dict[str, Any]]", output) if isinstance(output, list) else []
        )
        finish0: str = "length" if data.get("status") == "incomplete" else "stop"
        chat_data = {"choices": [{"message": responses.responsesMessage(items),
                                  "finish_reason": finish0}]}
        usage_raw = data.get("usage")
        if isinstance(usage_raw, dict):
            chat_data["usage"] = responses.responsesUsage(
                cast("dict[str, Any]", usage_raw))
    else:
        chat_data = cast("dict[str, Any]", data)
    choices = chat_data.get("choices")
    choice: dict[str, Any] = (
        cast("dict[str, Any]", choices[0])
        if isinstance(choices, list) and choices and isinstance(choices[0], dict)
        else {}
    )
    msg0_any = choice.get("message")
    msg0: dict[str, Any] = (
        cast("dict[str, Any]", msg0_any) if isinstance(msg0_any, dict) else {}
    )
    finish = choice.get("finish_reason")
    finish_str = finish if isinstance(finish, str) else None
    usage_raw2 = chat_data.get("usage")
    usage = (
        client.normalizeUsage(cast("dict[str, Any]", usage_raw2))
        if isinstance(usage_raw2, dict) else None
    )
    content_any = msg0.get("content")
    content = content_any if isinstance(content_any, str) and content_any else None
    tcs = msg0.get("tool_calls")
    tool_calls: list[dict[str, Any]] = []
    if isinstance(tcs, list):
        for item in tcs:
            if not isinstance(item, dict):
                continue
            fn = item.get("function")
            if isinstance(fn, dict) and fn.get("name"):
                tool_calls.append({
                    "id": item.get("id", ""), "type": "function",
                    "function": {"name": fn["name"],
                                 "arguments": fn.get("arguments", "")},
                })
    reasoning = msg0.get("reasoning_content")
    response_items = msg0.get("responseItems")
    message: dict[str, Any] = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    if isinstance(reasoning, str) and reasoning:
        message["reasoningContent"] = reasoning
    if isinstance(response_items, list) and response_items:
        message["responseItems"] = response_items
    # 冻结 client.ts:162-163 / responsesFetch:70-71 的回调
    usage_cb = opts.get("onUsage")
    if usage_cb is not None and usage is not None:
        usage_cb(cast("Any", usage))
    finish_cb = opts.get("onFinishReason")
    if finish_cb is not None and finish_str is not None:
        finish_cb(finish_str)
    # 冻结 client.ts:357-363：兜底内容也作为 delta 实时显示
    deltas: list[StreamDelta] = []
    if content:
        deltas.append({"kind": "content", "text": content})
    for i, tc in enumerate(tool_calls):
        deltas.append({"kind": "tool_call", "index": i,
                       "name": tc["function"]["name"]})
    return deltas, message, usage, finish_str


def streamChatResilient(
    opts: StreamChatOptions, *,
    transport: client.Transport | None = None,
    env: Mapping[str, str] | None = None,
    context: ResilientContext | None = None,
) -> ResilientResult:
    """冻结 client.ts:271-378 的 client 层重试编排（新公开函数，不改 streamChat）。

    - 仅在「产出前」失败时按 maxRetries 退避重试；Retry-After 优先于公式。
    - 重试耗尽且仍无产出 → 非流式兜底一次。
    - 已产出内容的中途断开 → 返回 partial，不重试、不重复（ADR-0003）。
    - 429 无 Retry-After / 背景 529 / 上下文超限 / 认证错误 → 明确失败。
    - 产出后 idle → 明确错误，不静默成功。
    """
    ctx = context if context is not None else ResilientContext()
    send: client.Transport = client.urllib_transport if transport is None else transport
    idle_ms = _resolveIdleMs(opts, env)
    timer_ms = _nodeTimerMs(idle_ms)
    max_retries = _resolveMaxRetries(opts)
    retry_delay_ms = _resolveRetryDelayMs(opts)
    background = bool(opts.get("background", False))
    idle_err_msg = idleErrorMessage(idle_ms)

    attempts: list[AttemptRecord] = []
    watchdog_triggered = False
    fallback_used = False
    state_out: dict[str, Any] = {}

    def emit(
        status: Literal["complete", "partial", "failed"],
        *,
        deltas: list[StreamDelta],
        message: dict[str, Any],
        usage: dict[str, Any] | None = None,
        finish_reason: str | None = None,
        error: str | None = None,
        error_exception: Exception | None = None,
        error_status: int | None = None,
        cancelled: bool = False,
        rec: AttemptRecord | None = None,
    ) -> ResilientResult:
        if rec is not None:
            attempts.append(rec)
            if ctx.on_attempt is not None:
                ctx.on_attempt(rec)
        return ResilientResult(
            status=status, deltas=deltas, message=message, usage=usage,
            finish_reason=finish_reason, attempts=attempts,
            request_body=cast("dict[str, Any]", state_out.get("body", {})),
            error=error, error_exception=error_exception, error_status=error_status,
            exit_code=0 if status != "failed" else 1,
            watchdog_triggered=watchdog_triggered,
            fallback_used=fallback_used,
            replayed=any(a.replayed for a in attempts),
            content_duplicated=sum(1 for a in attempts if a.yielded_any) > 1,
            cancelled=cancelled,
        )

    def mkrec(
        index: int, kind: str, http_status: int | None,
        retry_after_ms: float | None, deltas_count: int, yielded_any: bool,
        outcome: str, idle_trig: bool, classification: str, error: str | None,
    ) -> AttemptRecord:
        return AttemptRecord(
            index=index, kind=kind, http_status=http_status,
            retry_after_ms=retry_after_ms, deltas_count=deltas_count,
            yielded_any=yielded_any, replayed=False, outcome=outcome,
            idle_triggered=idle_trig, classification=classification, error=error,
        )

    yielded_any = False  # 冻结 :271，在 for 循环外，产出后不再重试
    for attempt in range(max_retries + 2):
        if ctx.cancel is not None and ctx.cancel():
            return emit(
                "partial", deltas=[], message=_emptyMessage(), cancelled=True,
                rec=mkrec(attempt, "stream", None, None, 0, False,
                          "cancelled", False, "no-output-before-failure", None),
            )
        watchdog = IdleWatchdog(timer_ms / 1000.0, ctx.clock, idle_err_msg, ctx.cancel)
        watchdog.arm()  # 连接/首字节阶段也纳入
        state_out = {}
        connections: list[http.client.HTTPConnection] = []
        sockets: list[socket.socket] = []
        active_watchdog = [watchdog]

        def abort_connection() -> None:
            active = list(sockets)
            for connection in list(connections):
                connection_socket = connection.sock
                if connection_socket is not None:
                    active.append(connection_socket)
            for sock in active:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    # Windows 下 socket.makefile() 持有引用，普通 close 会延迟真正关闭，
                    # 无法唤醒已阻塞的 recv；仅对本次请求私有 socket 触发底层关闭。
                    getattr(sock, "_real_close")()
                except OSError:
                    pass

        def connect_address(
            address: tuple[str, int], timeout: float,
            source_address: tuple[str, int] | None = None,
        ) -> socket.socket:
            host, port = address
            try:
                ipaddress.ip_address(host)
            except ValueError:
                entries = _resolve_addresses(host, port, ctx, active_watchdog[0])
            else:
                # 数字地址明确禁止 DNS 查询，避免为已知 IP 启动额外进程。
                entries = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM,
                                             0, socket.AI_NUMERICHOST)
            last_error: OSError | None = None
            for family, kind, proto, _canon, sockaddr in entries:
                active_watchdog[0].check()
                sock = socket.socket(family, kind, proto)
                sockets.append(sock)
                try:
                    sock.settimeout(timeout)
                    if source_address is not None:
                        sock.bind(source_address)
                    sock.connect(tuple(sockaddr))
                    active_watchdog[0].check()
                    return sock
                except OSError as exc:
                    last_error = exc
                    sock.close()
                except BaseException:
                    sock.close()
                    raise
            raise last_error or OSError("getaddrinfo returns an empty list")

        def register_connection(connection: http.client.HTTPConnection) -> None:
            connections.append(connection)
            # CPython 3.11 实例级接入，不影响其它请求或全局 getaddrinfo。
            connection._create_connection = connect_address  # type: ignore[attr-defined]

        if transport is None:
            def observed_send(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
                return client.urllib_transport(
                    url, headers, body, on_connection=register_connection, on_socket=sockets.append,
                    timeout=timer_ms / 1000.0 + 1.0,
                )
            attempt_send: client.Transport = observed_send
        else:
            attempt_send = send
        watchdog.start(abort_connection)
        try:
            result = client.runStreamAttempt(
                opts, transport=attempt_send, env=env,
                on_chunk=watchdog.check,
                on_effective_delta=watchdog.reset,
                on_delta=ctx.on_delta,
                state_out=state_out,
            )
            watchdog.check()
            watchdog.stop()
            if _stateHadOutput(state_out):
                yielded_any = True
            # 冻结 :340 isAbort / :347 recoverable&&yieldedAny → break（返回部分）
            is_cancel = ctx.cancel is not None and ctx.cancel()
            if is_cancel and result.status == "partial":
                return emit(
                    "partial", deltas=result.deltas, message=result.message,
                    usage=result.usage, finish_reason=result.finish_reason,
                    cancelled=True,
                    rec=mkrec(attempt, "stream", 200, None, len(result.deltas),
                              yielded_any, "cancelled", False,
                              _classification(yielded_any), None),
                )
            return emit(
                result.status, deltas=result.deltas, message=result.message,
                usage=result.usage, finish_reason=result.finish_reason,
                rec=mkrec(attempt, "stream", 200, None, len(result.deltas),
                          yielded_any, result.status, False,
                          _classification(yielded_any), None),
            )
        except Exception as caught:
            err: Exception = caught
            try:
                watchdog.check()
            except (IdleTimeoutError, RequestCancelled) as control_error:
                err = control_error
            watchdog.stop()
            if _stateHadOutput(state_out):
                yielded_any = True
            idled_out = isinstance(err, IdleTimeoutError) or watchdog.triggered
            if idled_out or watchdog.triggered:
                watchdog_triggered = True
            status_any = getattr(err, "status", None)
            status = status_any if isinstance(status_any, int) else None
            headers_any = getattr(err, "headers", None)
            headers: dict[str, str] = (
                {str(k): str(v) for k, v in headers_any.items()}
                if isinstance(headers_any, dict) else {}
            )
            retry_after_ms = (
                retryAfterMs(headers, status) if status is not None else None
            )
            had_output = _stateHadOutput(state_out)
            err_text = str(err)
            classification = _classification(yielded_any)

            # (1) 用户取消：冻结 :340 isAbort && !idledOut → 优雅返回已累积部分
            if (watchdog.cancelled or (ctx.cancel is not None and ctx.cancel())) and not idled_out:
                deltas, message, usage, finish = _partialFromState(state_out)
                return emit(
                    "partial", deltas=deltas, message=message, usage=usage,
                    finish_reason=finish, cancelled=True,
                    rec=mkrec(attempt, "stream", status, retry_after_ms,
                              len(deltas), had_output, "cancelled", False,
                              classification, err_text),
                )

            # (2) 上下文超限：冻结 :341-342 致命且可救，立即上抛，不重试/不兜底
            if isContextLengthError(err):
                return emit(
                    "failed", deltas=[], message=_emptyMessage(),
                    error=err_text, error_exception=err, error_status=status,
                    rec=mkrec(attempt, "stream", status, retry_after_ms, 0,
                              had_output, "fatal", False, classification, err_text),
                )

            # (3) 背景查询 529：冻结 :343-344 立即上抛，零重试零兜底
            if background and status == 529:
                return emit(
                    "failed", deltas=[], message=_emptyMessage(),
                    error=err_text, error_exception=err, error_status=status,
                    rec=mkrec(attempt, "stream", status, retry_after_ms, 0,
                              had_output, "fatal", False, classification, err_text),
                )

            # (4) 产出后 idle：冻结 :345 清晰报错（不静默成功、不半截工具调用）
            if idled_out and yielded_any:
                deltas, message, usage, finish = _partialFromState(state_out)
                return emit(
                    "failed", deltas=deltas, message=message, usage=usage,
                    finish_reason=finish, error=idle_err_msg,
                    error_exception=IdleTimeoutError(idle_err_msg, status), error_status=status,
                    rec=mkrec(attempt, "stream", status, retry_after_ms,
                              len(deltas), had_output, "idle", True,
                              classification, idle_err_msg),
                )

            recoverable = _recoverable(err, idled_out, status, retry_after_ms)

            # (6) 已产出内容的中途断开 → 返回部分（不重试，避免重复）
            if recoverable and yielded_any:
                deltas, message, usage, finish = _partialFromState(state_out)
                return emit(
                    "partial", deltas=deltas, message=message, usage=usage,
                    finish_reason=finish,
                    rec=mkrec(attempt, "stream", status, retry_after_ms,
                              len(deltas), had_output, "partial", False,
                              classification, err_text),
                )

            # (7) recoverable 且尚无产出 → 退避重试 / 非流式兜底
            if recoverable:
                if attempt < max_retries:
                    delay = (
                        retry_after_ms if retry_after_ms is not None
                        else backoffMs(retry_delay_ms, attempt, ctx.jitter_ms())
                    )
                    ctx.sleep(delay / 1000.0)
                    record = mkrec(
                        attempt, "stream", status, retry_after_ms, 0, False,
                        "retry", idled_out, "no-output-before-failure", err_text,
                    )
                    attempts.append(record)
                    if ctx.on_attempt is not None:
                        ctx.on_attempt(record)
                    continue
                fallback_used = True
                connections.clear()
                sockets.clear()
                fallback_watchdog = IdleWatchdog(
                    timer_ms / 1000.0, ctx.clock, idle_err_msg, ctx.cancel,
                )
                active_watchdog[0] = fallback_watchdog
                fallback_watchdog.arm()
                fallback_watchdog.start(abort_connection)
                try:
                    # Frozen fallback creates AbortSignal.timeout(idleMs) before fetch.
                    # Its uint32/integer check differs from streaming setTimeout's clamp.
                    if (not math.isfinite(idle_ms) or not idle_ms.is_integer()
                            or idle_ms < 0 or idle_ms > 4294967295):
                        raise ValueError(
                            'The value of "delay" is out of range. '
                            'It must be an integer between 0 and 4294967295.'
                        )
                    fb = _nonStreamingFallback(opts, attempt_send, env)
                    fallback_watchdog.check()
                    deltas, message, usage, finish = fb
                    if ctx.on_delta is not None:
                        for delta in deltas:
                            ctx.on_delta(delta)
                    return emit(
                        "complete", deltas=deltas, message=message, usage=usage,
                        finish_reason=finish,
                        rec=mkrec(attempt, "fallback", 200, None, len(deltas),
                                  bool(deltas), "complete", False,
                                  "no-output-before-failure", None),
                    )
                except Exception as caught:
                    e2: Exception = caught
                    try:
                        fallback_watchdog.check()
                    except (IdleTimeoutError, RequestCancelled) as control_error:
                        e2 = control_error
                    if fallback_watchdog.triggered:
                        watchdog_triggered = True
                        e2 = IdleTimeoutError(idle_err_msg)
                    if fallback_watchdog.cancelled or (ctx.cancel is not None and ctx.cancel()):
                        return emit(
                            "partial", deltas=[], message=_emptyMessage(), cancelled=True,
                            rec=mkrec(attempt, "fallback", None, None, 0, False,
                                      "cancelled", False, "no-output-before-failure", None),
                        )
                    e2_status_any = getattr(e2, "status", None)
                    e2_status = e2_status_any if isinstance(e2_status_any, int) else None
                    if isContextLengthError(e2):
                        return emit(
                            "failed", deltas=[], message=_emptyMessage(),
                            error=str(e2), error_exception=e2, error_status=e2_status,
                            rec=mkrec(attempt, "fallback", e2_status, None, 0,
                                      False, "fatal", False,
                                      "no-output-before-failure", str(e2)),
                        )
                    msg = idle_err_msg if idled_out else (
                        f"连接 {opts.get('provider') or opts['baseUrl']} 失败"
                        f"(流式重试 {max_retries} 次 + 非流式兜底均失败:{e2})"
                    )
                    if idled_out or fallback_watchdog.triggered:
                        final_error: Exception = IdleTimeoutError(msg, e2_status)
                    elif isinstance(err, (client.SseError, client.StreamError)):
                        final_error = type(err)(msg)
                    elif e2_status is not None:
                        final_error = client.ApiError(msg, status=e2_status)
                    else:
                        final_error = RuntimeError(msg)
                    return emit(
                        "failed", deltas=[], message=_emptyMessage(),
                        error=msg, error_exception=final_error, error_status=e2_status,
                        rec=mkrec(attempt, "fallback", e2_status, None, 0,
                                  False, "fatal", idled_out,
                                  "no-output-before-failure", str(e2)),
                    )
                finally:
                    fallback_watchdog.stop()

            # (8) 非可重试错误（致命）原样上抛
            return emit(
                "failed", deltas=[], message=_emptyMessage(),
                error=err_text, error_exception=err, error_status=status,
                rec=mkrec(attempt, "stream", status, retry_after_ms, 0,
                          had_output, "fatal", False, classification, err_text),
            )
        except BaseException:
            watchdog.stop()
            raise

    return emit(
        "failed", deltas=[], message=_emptyMessage(),
        error="重试循环异常终止", rec=None,
    )
