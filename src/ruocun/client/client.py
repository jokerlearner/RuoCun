"""组装 Chat 请求并消费流式响应。收到的文字、推理和工具参数按索引累积，结束后统一交给调用方。

重试层复用一次流式尝试。解析中断后保留已有内容并标记部分结果。真实 HTTP 由默认传输负责，调用方也可提供独立传输。
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
    """明确的 API 失败。保留状态码和响应头，供重试层识别限流和服务过载，并读取 Retry-After。"""

    def __init__(
        self, message: str, status: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.headers = headers or {}


class SseError(RuntimeError):
    """流内收到的 SSE 错误事件，交给重试层按状态处理。"""


class StreamError(RuntimeError):
    """SSE 在产生任何有效内容前中断。"""


class StreamDisconnected(RuntimeError):
    """传输层报告流在接收过程中断开或被取消。"""


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
    """将保存的会话历史转换为适合外发的消息，保留当前协议需要的字段。"""
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
                    # 通常只在有工具调用的助手轮保留推理。官方 DeepSeek 带工具时另行保留完整历史。
                    out.append({"role": role, "content": wire_content})
            else:
                rest = {k: v for k, v in m.items() if k != "responseItems"}
                rest["content"] = wire_content
                if use_responses and response_items:
                    rest["responseItems"] = response_items
                out.append(rest)
        elif role == "tool" and m.get("imageData") is not None:
            # imageData 供程序内部使用，图片已通过单独的用户消息发出。
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
    """单次输出上限优先使用显式参数。默认档为 128000，并可从环境读取。空截断重试档为 256000。各档都受模型能力裁剪。"""
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
    """组装请求体，最后应用 extra 覆盖。只有明确配置时才附采样参数。

    use_responses 控制是否保留 responseItems。官方 DeepSeek 带工具的 Chat 请求按协议保留历史助手推理。
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
        # 官方 Chat 请求携带工具时，已结束的普通轮也要保留历史推理。
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
    """优先采用原生缓存字段，缺失时用 details.cached_tokens 补齐。"""
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
    """保存一次流式请求的增量状态，直到能生成完整或标明部分的结果。"""

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
            return []  # 忽略该条不可解析的 SSE 数据。
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
                    acc["id"] = frag_id  # 保留之前取得的有效 ID。
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
    """通过 urllib 发送实际 HTTP 请求。"""
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
            # 继续由 urllib 处理代理、重定向和 HTTP 错误。登记实际连接可中断正在读写的套接字。
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
                            # 沿用 HTTPConnection 的 TCP 和 CONNECT 顺序，先登记 SSL
                            # 使用的套接字，再进行可能阻塞的证书校验和握手。
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
        # urllib 通过异常报告非 2xx，状态码和响应头供上层选择处理办法。
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
        # HTTP/1.0 或 Connection: close 时，套接字由 HTTPConnection 移交给 response。
        register_socket(response)

    def chunks() -> Iterable[bytes]:
        # read1 及时返回已到达的字节，首帧可在填满缓冲区前交付。
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
    """消费一次流式尝试。能重试的入口复用这里的解码、分帧和累积逻辑。

    on_chunk 可观察字节进度，on_effective_delta 用于更新有效输出计时，state_out 保存已产出内容的证据。不给回调时也可独立完成一次请求。
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
    # 序列化时转义 UTF-16 截断留下的孤立代理项，普通 Unicode 字节照常发送。
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
            status = "partial"  # 返回已累积的内容，并标记为部分结果。
        else:
            raise StreamError("SSE 中途断流且尚无产出") from None
    finally:
        for stream in (chunks, response.chunks):
            close_chunks = getattr(stream, "close", None)
            if close_chunks is not None:
                close_chunks()
    # 正常流已结束，推理若耗尽输出预算且没有正文和工具，交给上层切换重试上限。
    # 中断的流走部分结果或错误路径，只有正常结束才确认空截断。
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
    """发送模型请求并累积流式结果。传输和路由确定后，统一执行取消、重试和部分结果处理。

    可选 context 提供取消信号和增量投递，既有参数仍可直接使用。
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


# Usage 在 types.py 定义。归一化结果继续用普通映射承载，
# 使协议层能保留现有的宽容字段边界。
