"""编排模型请求的超时、取消、重试与非流式兜底。一次尝试由 client.py 完成，本模块决定失败能否再试。

只在尚无有效产出时考虑重试或兜底。已经产出后发生断流时保留部分结果。空闲计时只由有效增量重置。
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

# 过载、网关失败和限流候选状态。429 最终还要核对 Retry-After。
RETRYABLE_STATUS: frozenset[int] = frozenset(
    {408, 409, 425, 429, 500, 502, 503, 504, 529}
)
# 缺少配置时的等待、空闲和重试默认值。
DEFAULT_IDLE_MS: int = 240000
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_RETRY_DELAY_MS: int = 600
# 请求声明的退避等待最长两分钟。
RETRY_AFTER_CAP_MS: int = 120000

# 上下文超限由回合循环考虑压缩，客户端将错误向上传递。
_CONTEXT_LENGTH_RE = re.compile(
    r"context length|maximum context|too many tokens|reduce the length|"
    r"context_length_exceeded|prompt is too long|exceeds? the maximum|input is too long",
    re.IGNORECASE,
)
# 限流与配额状态由上层处理，当前模型由用户或上层策略决定。
_RATE_LIMIT_RE = re.compile(
    r"\b429\b|rate[_ -]?limit|quota_exceeded|限流|请求频率",
    re.IGNORECASE,
)
# 订阅和认证错误分类。部分订阅错误会使用 HTTP 400。
_CREDENTIAL_RE = re.compile(
    r"invalid.*key|authentication|unauthorized|subscription|CodingPlan|billing|"
    r"InvalidSubscription",
    re.IGNORECASE,
)
# 识别瞬断特征，是否重试还取决于此前有无有效产出。
_RETRYABLE_RE = re.compile(
    r"socket|ECONNRESET|ECONNREFUSED|ETIMEDOUT|EPIPE|closed unexpectedly|"
    r"fetch failed|terminated|ENOTFOUND|EAI_AGAIN|network",
    re.IGNORECASE,
)


def idleErrorMessage(idle_ms: float) -> str:
    """生成空闲错误文案，对非负秒数按 JavaScript Math.round 取整。"""
    value = idle_ms / 1000
    if math.isnan(value):
        seconds: int | str = "NaN"
    elif math.isinf(value):
        seconds = "Infinity" if value > 0 else "-Infinity"
    else:
        seconds = int(math.floor(value + 0.5))
    return f"模型流空闲超时({seconds}s 未收到数据),已停止本回合"


def _jsNumber(value: str) -> float:
    """解析环境变量中的 JavaScript Number，支持空白、十进制、指数、无穷大和无符号进制前缀。"""
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
    """按 Node 22 定时规则计算到期时长，错误提示仍使用用户配置的原值。"""
    if not math.isfinite(value) or value < 1 or value > 2147483647:
        return 1.0
    return float(math.floor(value))


def isContextLengthError(e: BaseException) -> bool:
    """识别上下文超限，交由回合循环决定是否压缩。"""
    return bool(_CONTEXT_LENGTH_RE.search(str(e)))


def isRateLimitError(e: BaseException) -> bool:
    """识别 HTTP 429 或带限流、配额特征的错误。"""
    status = getattr(e, "status", None)
    if status == 429:
        return True
    return bool(_RATE_LIMIT_RE.search(str(e)))


def isCredentialError(e: BaseException) -> bool:
    """识别 401、403 和带订阅特征的 400 错误。"""
    status = getattr(e, "status", None)
    if status == 401 or status == 403:
        return True
    if status == 400:
        return bool(_CREDENTIAL_RE.search(str(e)))
    return False


def isRetryable(e: BaseException) -> bool:
    """根据流内可重试标记和连接异常信号识别可能恢复的失败。"""
    if getattr(e, "retryableStatus", False) is True:
        return True
    # Windows 错误文本可能已经本地化，因此也按 Python 异常类型判断。
    if isinstance(e, (ConnectionResetError, ConnectionRefusedError, BrokenPipeError,
                      socket.gaierror)):
        return True
    if isinstance(e, urllib.error.URLError) and isinstance(e.reason, BaseException):
        return isRetryable(e.reason)
    # 同时匹配异常类名和消息，以兼容按错误名称识别的情形。
    return bool(_RETRYABLE_RE.search(f"{type(e).__name__} {e}"))


def retryAfterMs(headers: Mapping[str, str], status: int) -> float | None:
    """解析 Retry-After 的等待秒数，换算为毫秒并限制为至多 120000。

    响应头名称忽略大小写，非法值和负数跳过。只有可重试状态才使用这个等待值。
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
    """按尝试次数线性递增等待时长，再加调用方提供的随机扰动。"""
    return retry_delay_ms * (attempt + 1) + jitter_ms


# ---------------------------------------------------------------------------
# 重试和空闲监视使用的依赖、状态和证据。
# ---------------------------------------------------------------------------


class IdleTimeoutError(RuntimeError):
    """已超过允许的无有效增量时长。"""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class RequestCancelled(RuntimeError):
    """用户取消当前请求。"""


def _monotonic() -> float:
    return time.monotonic()


def _realSleep(seconds: float) -> None:
    time.sleep(seconds)


def _defaultJitter() -> float:
    # 每次退避叠加小于 250 毫秒的随机扰动。
    return float(random.randrange(250))


@dataclass
class ResilientContext:
    """提供时钟、退避、随机扰动、取消和证据回调。默认使用系统时钟，测试可控制经过时间和退避选择。"""

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
    """记录一次尝试的状态，按请求和尝试身份归并证据。"""

    index: int
    kind: str                       # 尝试路径可为流式或非流式兜底。
    http_status: int | None
    retry_after_ms: float | None
    deltas_count: int
    yielded_any: bool
    replayed: bool                  # 记录是否重放已产出的内容，当前流程按规则始终避免这种重放。
    outcome: str                    # 记录尝试实际结束原因，供调用方区分成功、部分结果和故障。
    idle_triggered: bool
    classification: str             # 区分产出前失败和请求已发出但结果未确认。
    error: str | None


@dataclass(frozen=True)
class ResilientResult:
    """聚合流结果和重试记录，供调用方同时取得回答及尝试过程。"""

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
    """监视连续无有效增量的时长，默认 240 秒。有效增量才重置计时。

    超时后通知默认传输中断本请求的套接字，退出前回收计时线程。自带传输需要处理自己的阻塞，在尚无套接字时也要单独处理解析等阻塞阶段。
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
        self._last_delta_at = self._clock()  # 空闲计时已经覆盖连接建立和首字节等待。

    def reset(self) -> None:
        self._last_delta_at = self._clock()  # 只有有效内容才重置空闲起点。

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
                    # 连接建立前可能还没有可中断的套接字，继续观察直到停止。
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
    """在本次请求私有的子进程解析地址，取消时终止并等待该进程退出。"""
    watchdog.check()
    if context.resolver_command is None and getattr(sys, "frozen", False):
        raise RuntimeError("独立程序尚未配置 DNS helper")
    command = context.resolver_command or (
        sys.executable, "-I", "-X", "utf8", "-m", "ruocun.client._dns_helper",
    )
    # DNS 解析只需 Windows 进程启动环境，过滤账户凭据和配置路径。
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
    # 空闲时长沿用 Number(env) 的默认值选择语义，负数和无穷大仍视为已配置。
    return float(DEFAULT_IDLE_MS) if parsed == 0 or math.isnan(parsed) else parsed


def _resolveMaxRetries(opts: StreamChatOptions) -> int:
    value = opts.get("maxRetries")
    return DEFAULT_MAX_RETRIES if value is None else int(value)


def _resolveRetryDelayMs(opts: StreamChatOptions) -> float:
    value = opts.get("retryDelayMs")
    return float(DEFAULT_RETRY_DELAY_MS) if value is None else float(value)


def _stateHadOutput(state_out: dict[str, Any]) -> bool:
    # 只有已经发出的有效 StreamDelta 才算产出，仍在缓冲的工具片段不计入。
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
    # 产出前失败可进入重试判断。产出后结果不明时保留部分结果，避免重复请求。
    return "sent-but-outcome-unknown" if yielded_any else "no-output-before-failure"


def _emptyMessage() -> dict[str, Any]:
    return {"role": "assistant", "content": None}


def _recoverable(
    err: BaseException, idled_out: bool, status: int | None,
    retry_after_ms: float | None,
) -> bool:
    """判断空闲超时、瞬时断流或过载是否允许后续恢复处理。"""
    if idled_out:
        return True
    if isinstance(err, client.SseError):
        return True  # 流内错误携带 retryableStatus 标记。
    if isinstance(err, (client.StreamError, client.StreamDisconnected)):
        return True  # 请求在产出前发生断流或瞬断。
    if isinstance(err, client.ApiError):
        if status == 429 and retry_after_ms is None:
            return False  # 429 缺少 Retry-After 时，把原错误向上报告，结束此次尝试链。
        return status in RETRYABLE_STATUS if status is not None else False
    return isRetryable(err)


def _nonStreamingFallback(
    opts: StreamChatOptions, transport: client.Transport,
    env: Mapping[str, str] | None,
) -> tuple[list[StreamDelta], dict[str, Any], dict[str, Any] | None, str | None]:
    """流式失败且允许兜底时，执行一次非流式请求。

    Chat 直接解析首条消息，Responses 先归一成同样的消息结构，两路均保留工具和推理项。
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
        # 将非流式 Responses 结果归一为 Chat 的消息形状。
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
    # 调用方可沿用同一个增量接收入口接收兜底结果。
    usage_cb = opts.get("onUsage")
    if usage_cb is not None and usage is not None:
        usage_cb(cast("Any", usage))
    finish_cb = opts.get("onFinishReason")
    if finish_cb is not None and finish_str is not None:
        finish_cb(finish_str)
    # 兜底得到的内容也通过 delta 投递。
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
    """执行可恢复的流式请求。只有产出前且可恢复的失败才退避重试，Retry-After 优先。

    重试额度耗尽且仍无产出时，可做一次非流式兜底。已有增量的流中断时返回部分结果，产出后空闲则报告明确错误。上下文、认证和受限状态按各自规则交回上层。
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

    yielded_any = False  # 跨尝试累计产出状态，一旦有产出就停止后续重试。
    for attempt in range(max_retries + 2):
        if ctx.cancel is not None and ctx.cancel():
            return emit(
                "partial", deltas=[], message=_emptyMessage(), cancelled=True,
                rec=mkrec(attempt, "stream", None, None, 0, False,
                          "cancelled", False, "no-output-before-failure", None),
            )
        watchdog = IdleWatchdog(timer_ms / 1000.0, ctx.clock, idle_err_msg, ctx.cancel)
        watchdog.arm()  # 空闲计时从连接建立之前开始。
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
                    # Windows 中 socket.makefile() 会持有套接字引用，普通 close 可能延迟。
                    # 对本次请求的套接字执行底层关闭，使阻塞的 recv 尽快返回。
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
                # 常量 IP 直接使用，避免为数字地址启动 DNS 进程。
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
            # 连接钩子只挂到当前 CPython 3.11 实例，其他请求沿用各自的解析路径。
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
            # 用户取消或已产出后发生可恢复断流时，进入部分结果收尾。
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

            # 用户主动取消时，把已累积的内容交给调用方。
            if (watchdog.cancelled or (ctx.cancel is not None and ctx.cancel())) and not idled_out:
                deltas, message, usage, finish = _partialFromState(state_out)
                return emit(
                    "partial", deltas=deltas, message=message, usage=usage,
                    finish_reason=finish, cancelled=True,
                    rec=mkrec(attempt, "stream", status, retry_after_ms,
                              len(deltas), had_output, "cancelled", False,
                              classification, err_text),
                )

            # 上下文超限直接交由会话回合处理。
            if isContextLengthError(err):
                return emit(
                    "failed", deltas=[], message=_emptyMessage(),
                    error=err_text, error_exception=err, error_status=status,
                    rec=mkrec(attempt, "stream", status, retry_after_ms, 0,
                              had_output, "fatal", False, classification, err_text),
                )

            # 后台查询遇到 529 立即交回调用方，避免后台请求扩大重试量。
            if background and status == 529:
                return emit(
                    "failed", deltas=[], message=_emptyMessage(),
                    error=err_text, error_exception=err, error_status=status,
                    rec=mkrec(attempt, "stream", status, retry_after_ms, 0,
                              had_output, "fatal", False, classification, err_text),
                )

            # 已经产出后长时间无有效增量，明确报告空闲错误，保留失败原因。
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

            # 已经交付过部分内容，返回这些内容即可，避免重试重复输出。
            if recoverable and yielded_any:
                deltas, message, usage, finish = _partialFromState(state_out)
                return emit(
                    "partial", deltas=deltas, message=message, usage=usage,
                    finish_reason=finish,
                    rec=mkrec(attempt, "stream", status, retry_after_ms,
                              len(deltas), had_output, "partial", False,
                              classification, err_text),
                )

            # 只有产出前且可恢复时，才进入退避重试或非流式兜底。
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
                    # 非流式兜底先按 AbortSignal.timeout 的规则检查时长。
                    # 该规则要求 uint32 范围内的整数，与流式定时器的截断规则不同。
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

            # 其余不可重试错误原样返回给调用方。
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
