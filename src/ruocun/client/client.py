"""Chat 请求组装、SSE 累积与流式路径（来源冻结 ``src/client/client.ts``，MIT）。

- WIRE-01：固定 system/messages/tool schema 顺序、角色/字段/空值与 extra 覆盖。
- WIRE-02：默认 128000、特殊空截断重试 256000，均受模型 cap 裁剪；按模型选择
  max_tokens/max_completion_tokens；不加未配置 temperature/top_p 等采样参数。
- WIRE-03：文本/reasoning/工具调用参数按 index 完整累积；usage/finish_reason
  只按有效数据确认。
- WIRE-05：assistant null content 转空串；工具轮 reasoning 回传；内部字段不泄漏。
- 取消/失败边界：非 2xx、SSE error、非法 UTF-8、中途断流/无产出都明确失败或
  保留已累积部分并标 ``partial``，不伪报成功；按 ADR-0003 精神本票不引入重放语义。

传输用注入式 ``Transport``：默认走真实 ``urllib`` HTTP；演示与测试注入 fake
HTTP/SSE（合成账户配置 + 合成字节流，绝不调用真实模型）。
"""

from __future__ import annotations

import http.client
import json
import os
import re
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlsplit

from ..config import compat
from ..config.profiles import outputLimitFor
from . import responses
from .sse import SSEStreamParser
from .types import ChatMessage, StreamChatOptions, StreamDelta

if TYPE_CHECKING:
    from .resilient import ResilientContext

_MAX_COMPLETION = re.compile(r"^(gpt-[56]|o1|o3|o4)", re.IGNORECASE)
_EMPTY_TRUNCATION_RETRY_TOKENS = 256000


class ApiError(RuntimeError):
    """非 2xx 响应等明确 API 失败。

    ``status`` / ``headers`` 是任务06 的兼容扩展（默认 None/空）：供重试层按
    冻结 client.ts:297-310 分类 429/529 与 Retry-After；04 的
    ``pytest.raises(ApiError)`` / 消息断言不受影响，构造函数向后兼容。
    """

    def __init__(
        self, message: str, status: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.headers = headers or {}


class SseError(RuntimeError):
    """SSE 流内 error 事件（不静默吞成空响应，也不自动重放）。"""


class StreamError(RuntimeError):
    """SSE 中途断流且无任何产出。"""


class StreamDisconnected(RuntimeError):
    """transport 信号：流在产出过程中被断开/取消。"""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    chunks: Iterable[bytes]


Transport = Callable[[str, dict[str, str], bytes], HttpResponse]


@dataclass(frozen=True)
class StreamResult:
    status: Literal["complete", "partial"]
    deltas: list[StreamDelta]
    message: dict[str, Any]
    usage: dict[str, Any] | None
    finish_reason: str | None
    request_body: dict[str, Any]


def buildWireMessages(
    messages: list[ChatMessage], *, use_responses: bool = False,
) -> list[dict[str, Any]]:
    """冻结 client.ts:72-91 的历史清洗（不机械附带 reasoning、不泄漏内部字段）。"""
    out: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        if role == "assistant":
            content = m.get("content")
            wire_content = "" if content is None else content
            reasoning = m.get("reasoningContent")
            response_items = m.get("responseItems")
            tool_calls = m.get("tool_calls")
            if isinstance(reasoning, str) and reasoning:
                if tool_calls is not None:
                    wm: dict[str, Any] = {
                        "role": role, "content": wire_content,
                        "tool_calls": tool_calls, "reasoning_content": reasoning,
                    }
                    if use_responses and response_items:
                        wm["responseItems"] = response_items
                    out.append(wm)
                else:
                    # 默认不回传无工具轮 reasoning；官方 DeepSeek 带工具请求另行保留。
                    out.append({"role": role, "content": wire_content})
            else:
                rest = {k: v for k, v in m.items() if k != "responseItems"}
                rest["content"] = wire_content
                if use_responses and response_items:
                    rest["responseItems"] = response_items
                out.append(rest)
        elif role == "tool" and m.get("imageData") is not None:
            # imageData 是内部字段，不发 API（图片已通过单独 user message 注入）
            out.append({
                "role": role, "tool_call_id": m.get("tool_call_id"),
                "content": m.get("content"),
            })
        else:
            out.append(dict(m))
    return out


def resolveMaxTokens(
    opts: StreamChatOptions,
    *,
    empty_truncation_retry: bool = False,
    env: Mapping[str, str] | None = None,
) -> int:
    """默认 128000（env/单次覆盖）；特殊空截断重试 256000；均受模型 cap 裁剪。"""
    explicit = opts.get("maxTokens")
    if explicit is not None:
        requested = int(explicit)
    elif empty_truncation_retry:
        requested = _EMPTY_TRUNCATION_RETRY_TOKENS
    else:
        requested = compat.max_output_tokens(os.environ if env is None else env)
    return outputLimitFor(opts["model"], requested, opts.get("baseUrl"))


def buildRequestBody(
    opts: StreamChatOptions,
    *,
    max_tokens_override: int | None = None,
    env: Mapping[str, str] | None = None,
    use_responses: bool = False,
) -> dict[str, Any]:
    """冻结 client.ts:104-120 的请求体。extra 覆盖放最后，不加未配置采样参数。

    ``use_responses`` 为 WIRE-04 兼容扩展：控制 responseItems 是否保留。
    官方 DeepSeek 的带工具 Chat 请求按当前协议保留全部历史 assistant reasoning。
    """
    requested = (
        max_tokens_override if max_tokens_override is not None
        else resolveMaxTokens(opts, env=env)
    )
    max_tokens = outputLimitFor(opts["model"], requested, opts.get("baseUrl"))
    field = "max_completion_tokens" if _MAX_COMPLETION.match(opts["model"]) else "max_tokens"
    messages = list(opts.get("messages", []))
    wire_messages = buildWireMessages(messages, use_responses=use_responses)
    tools = opts.get("tools")
    extra = opts.get("extra")
    effective_tools = extra.get("tools", tools) if extra else tools
    if (not use_responses and effective_tools and opts.get("provider") == "deepseek"
            and urlsplit(opts["baseUrl"]).hostname == "api.deepseek.com"):
        # 官方 Chat 带 tools 时要求完整重放历史 reasoning，包括已结束的普通回合。
        for message, wire in zip(messages, wire_messages, strict=True):
            reasoning = message.get("reasoningContent")
            if message.get("role") == "assistant" and isinstance(reasoning, str):
                wire.pop("reasoningContent", None)
                wire["reasoning_content"] = reasoning
    body: dict[str, Any] = {
        "model": opts["model"],
        "messages": wire_messages,
        "stream": True,
        "stream_options": {"include_usage": True},
        field: max_tokens,
    }
    if tools is not None:
        body["tools"] = tools
    parallel = opts.get("parallelToolCalls")
    if parallel is not None:
        body["parallel_tool_calls"] = parallel
    if extra:
        body.update(extra)
    return body


def normalizeUsage(raw: dict[str, Any]) -> dict[str, Any]:
    """冻结 client.ts:50-55：原生 cache 字段优先；缺则用 details.cached_tokens 补齐。"""
    if "prompt_cache_hit_tokens" in raw:
        return dict(raw)
    details = raw.get("prompt_tokens_details")
    cached = details.get("cached_tokens") if isinstance(details, dict) else None
    if not isinstance(cached, int):
        return dict(raw)
    return {
        **raw,
        "prompt_cache_hit_tokens": cached,
        "prompt_cache_miss_tokens": max(0, raw.get("prompt_tokens", 0) - cached),
    }


@dataclass
class ChatAccumulator:
    """请求级累积器（冻结 client.ts:208-269, 380-415）。"""

    content: str = ""
    reasoning: str = ""
    response_items: list[dict[str, Any]] = field(default_factory=list)
    finish_reason: str | None = None
    last_usage: dict[str, Any] | None = None
    tool_acc: dict[int, dict[str, str]] = field(default_factory=dict)
    announced: set[int] = field(default_factory=set)
    on_usage: Callable[..., None] | None = None
    on_finish_reason: Callable[[str], None] | None = None

    def process(self, payload: str) -> list[StreamDelta]:
        if payload in ("[DONE]", ""):
            return []
        try:
            parsed: Any = json.loads(payload)
        except json.JSONDecodeError:
            return []  # 半个 JSON 不该出现，保险跳过
        if not isinstance(parsed, dict):
            return []
        error = parsed.get("error")
        if error is not None:
            raise SseError(f"SSE error from API: {error}")
        usage = parsed.get("usage")
        if isinstance(usage, dict):
            normalized = normalizeUsage(usage)
            self.last_usage = normalized
            if self.on_usage is not None:
                self.on_usage(normalized)
        items = parsed.get("response_items")
        if isinstance(items, list):
            self.response_items = items
        choices = parsed.get("choices")
        delta: Any = None
        finish: Any = None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            finish = choices[0].get("finish_reason")
            delta = choices[0].get("delta")
        if isinstance(finish, str):
            self.finish_reason = finish
            if self.on_finish_reason is not None:
                self.on_finish_reason(finish)
        out: list[StreamDelta] = []
        if not isinstance(delta, dict):
            return out
        reasoning = delta.get("reasoning_content")
        if isinstance(reasoning, str) and reasoning:
            self.reasoning += reasoning
            out.append({"kind": "reasoning", "text": reasoning})
        content = delta.get("content")
        if isinstance(content, str) and content:
            self.content += content
            out.append({"kind": "content", "text": content})
        tool_calls = delta.get("tool_calls")
        if isinstance(tool_calls, list):
            for frag in tool_calls:
                if not isinstance(frag, dict):
                    continue
                raw_index = frag.get("index")
                index = raw_index if isinstance(raw_index, int) else 0
                acc = self.tool_acc.setdefault(
                    index, {"id": "", "name": "", "args": ""})
                frag_id = frag.get("id")
                if isinstance(frag_id, str) and frag_id:
                    acc["id"] = frag_id  # 空串不冲掉已捕获的真实 id
                function = frag.get("function")
                if isinstance(function, dict):
                    name = function.get("name")
                    if isinstance(name, str):
                        acc["name"] += name
                    arguments = function.get("arguments")
                    if isinstance(arguments, str):
                        acc["args"] += arguments
                if acc["name"] and index not in self.announced:
                    self.announced.add(index)
                    out.append({"kind": "tool_call", "index": index, "name": acc["name"]})
        return out

    def buildMessage(self) -> dict[str, Any]:
        message: dict[str, Any] = {
            "role": "assistant", "content": self.content or None,
        }
        calls = [
            {
                "id": self.tool_acc[i]["id"], "type": "function",
                "function": {"name": self.tool_acc[i]["name"],
                             "arguments": self.tool_acc[i]["args"]},
            }
            for i in sorted(self.tool_acc) if self.tool_acc[i]["name"]
        ]
        if calls:
            message["tool_calls"] = calls
        if self.reasoning:
            message["reasoningContent"] = self.reasoning
        if self.response_items:
            message["responseItems"] = self.response_items
        return message


def urllib_transport(
    url: str, headers: dict[str, str], body: bytes, *,
    on_connection: Callable[[http.client.HTTPConnection], None] | None = None,
    on_socket: Callable[[socket.socket], None] | None = None,
    timeout: float = 60,
) -> HttpResponse:
    """默认真实 HTTP transport（产品路径）。"""
    def register_socket(response_object: Any) -> None:
        current = response_object
        for _ in range(4):
            found = getattr(current, "_sock", None)
            if isinstance(found, socket.socket):
                if on_socket is not None:
                    on_socket(found)
                return
            current = getattr(current, "raw", None) or getattr(current, "fp", None)
            if current is None:
                return

    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        if on_connection is None:
            response = urllib.request.urlopen(request, timeout=timeout)
        else:
            connection_hook = on_connection
            # urllib 仍负责代理、重定向与错误处理；记录真实连接以便中断正在读写的 socket。
            class ObservedHTTP(urllib.request.HTTPHandler):
                def http_open(self, req: urllib.request.Request) -> Any:
                    def make(host: str, **kwargs: Any) -> http.client.HTTPConnection:
                        conn = http.client.HTTPConnection(host, **kwargs)
                        connection_hook(conn)
                        return conn
                    return self.do_open(make, req)

            class ObservedHTTPS(urllib.request.HTTPSHandler):
                def https_open(self, req: urllib.request.Request) -> Any:
                    class ObservedHTTPSConnection(http.client.HTTPSConnection):
                        def connect(self) -> None:
                            # 保持 HTTPConnection 原 TCP 与 CONNECT 顺序；先登记 SSL
                            # 持有的实际 socket，再进入可能阻塞的证书校验/握手。
                            http.client.HTTPConnection.connect(self)
                            hostname = getattr(self, "_tunnel_host", None) or self.host
                            context = getattr(self, "_context")
                            wrapped = context.wrap_socket(
                                self.sock, server_hostname=hostname,
                                do_handshake_on_connect=False,
                            )
                            self.sock = wrapped
                            if on_socket is not None:
                                on_socket(wrapped)
                            wrapped.do_handshake()

                    def make(host: str, **kwargs: Any) -> http.client.HTTPSConnection:
                        conn = ObservedHTTPSConnection(host, **kwargs)
                        connection_hook(conn)
                        return conn
                    return self.do_open(make, req, context=getattr(self, "_context", None),
                                        check_hostname=getattr(self, "_check_hostname", None))

            opener = urllib.request.build_opener(ObservedHTTP(), ObservedHTTPS())
            response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as error:
        # urllib 把非 2xx 作为异常抛出；保留状态和响应头供上层按来源规则分类。
        with error:
            register_socket(error)
            detail = error.read().decode("utf-8", errors="replace")
            raise ApiError(
                f"API error {error.code}: {detail}", status=error.code,
                headers={str(k).lower(): str(v) for k, v in error.headers.items()},
            ) from None
    status = int(response.status)
    resp_headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    if on_socket is not None:
        # HTTP/1.0/Connection: close 时 HTTPConnection 会将 socket 移交给 response。
        register_socket(response)

    def chunks() -> Iterable[bytes]:
        # read1 返回已到达的字节，不等 4096 字节或连接关闭才投递首帧。
        with response:
            while chunk := response.read1(4096):
                yield chunk

    return HttpResponse(status, resp_headers, chunks())


def runStreamAttempt(
    opts: StreamChatOptions, *,
    transport: Transport | None = None,
    env: Mapping[str, str] | None = None,
    on_chunk: Callable[[], None] | None = None,
    on_effective_delta: Callable[[], None] | None = None,
    on_delta: Callable[[StreamDelta], None] | None = None,
    state_out: dict[str, Any] | None = None,
) -> StreamResult:
    """一次流式尝试（冻结 client.ts 单个 attempt）。

    04 的 ``streamChat`` 与任务06 重试层共用这**唯一一份** chunks 消费逻辑：
    ``chunks: Iterable[bytes]`` 局部变量与 Responses 路由分支（05）保持不变，
    不在重试层重定义。``on_chunk`` / ``on_effective_delta`` / ``state_out`` 是
    可选 seam，默认关闭时行为与 04 完全一致；重试层借此接入 idle watchdog
    （仅有效 delta 重置）与「已产出部分」证据，不改动公开契约。
    """
    send: Transport = urllib_transport if transport is None else transport
    use_responses = responses.usesResponses(opts["baseUrl"], opts["model"])
    chat_body = buildRequestBody(opts, env=env, use_responses=use_responses)
    body: dict[str, Any]
    if use_responses:
        body = responses.buildResponsesRequest(chat_body)
        url = responses.RESPONSES_ENDPOINT
    else:
        body = chat_body
        url = opts["baseUrl"].rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {opts['apiKey']}",
    }
    # JSON.stringify会转义UTF-16截断留下的孤立代理项；普通Unicode字节不变。
    body_bytes = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8", errors="backslashreplace")
    if state_out is not None:
        state_out["body"] = body
    response = send(url, headers, body_bytes)
    if not 200 <= response.status < 300:
        raise ApiError(
            f"API error {response.status}",
            status=response.status,
            headers=dict(response.headers),
        )
    chunks: Iterable[bytes] = (
        responses.iterChatFrames(response.chunks) if use_responses else response.chunks
    )
    parser = SSEStreamParser()
    acc = ChatAccumulator(
        on_usage=opts.get("onUsage"),
        on_finish_reason=opts.get("onFinishReason"),
    )
    deltas: list[StreamDelta] = []
    if state_out is not None:
        state_out.update({
            "acc": acc, "deltas": deltas, "body": body,
            "http_status": response.status, "headers": dict(response.headers),
        })
    status: Literal["complete", "partial"] = "complete"
    try:
        for chunk in chunks:
            if on_chunk is not None:
                on_chunk()
            for payload in parser.feed(chunk):
                if on_chunk is not None:
                    on_chunk()
                produced = acc.process(payload)
                if produced and on_effective_delta is not None:
                    on_effective_delta()
                deltas.extend(produced)
                if on_delta is not None:
                    for delta in produced:
                        on_delta(delta)
        for payload in parser.flush():
            if on_chunk is not None:
                on_chunk()
            produced = acc.process(payload)
            if produced and on_effective_delta is not None:
                on_effective_delta()
            deltas.extend(produced)
            if on_delta is not None:
                for delta in produced:
                    on_delta(delta)
    except StreamDisconnected:
        if deltas:
            status = "partial"  # 保留已累积部分，明确标记，不伪报成功
        else:
            raise StreamError("SSE 中途断流且尚无产出") from None
    finally:
        for stream in (chunks, response.chunks):
            close_chunks = getattr(stream, "close", None)
            if close_chunks is not None:
                close_chunks()
    # 冻结 client.ts:406：推理耗尽长度预算且尚无正文/工具时，通知上层切换收敛重试档。
    # 在正常流收尾处判断；异常/断流不能冒充完整的空截断回答。
    message = acc.buildMessage()
    if (status == "complete" and acc.finish_reason == "length"
            and not message["content"] and not message.get("tool_calls")):
        on_empty_truncation = opts.get("onEmptyTruncation")
        if on_empty_truncation is not None:
            on_empty_truncation()
    return StreamResult(
        status=status,
        deltas=deltas,
        message=message,
        usage=acc.last_usage,
        finish_reason=acc.finish_reason,
        request_body=body,
    )


def streamChat(
    opts: StreamChatOptions, *,
    transport: Transport | None = None,
    env: Mapping[str, str] | None = None,
    context: ResilientContext | None = None,
) -> StreamResult:
    """从请求组装 → HTTP/SSE 字节流 → 严格解码 → 分帧 → 累积 → 回答。

    公开入口复用任务06的重试/取消，成功与部分结果保持04/05结果形状。
    原有参数仍可使用；可选 context 提供增量投递与取消。
    """
    from .resilient import streamChatResilient

    result = streamChatResilient(opts, transport=transport, env=env, context=context)
    if result.status == "failed":
        if result.error_exception is not None:
            raise result.error_exception
        raise RuntimeError(result.error or "模型请求失败")
    return StreamResult(
        status=result.status, deltas=result.deltas, message=result.message,
        usage=result.usage, finish_reason=result.finish_reason,
        request_body=result.request_body,
    )


# Usage TypedDict 在 types.py 维护；归一化结果以普通映射承载，避免协议层
# 用新校验器改写来源的宽容边界。
