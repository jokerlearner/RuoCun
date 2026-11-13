"""Responses 路由桥（来源冻结 ``src/client/responses.ts``，MIT）。

- WIRE-04：仅官方 OpenAI 的 GPT-6 系列走 Responses；自定义网关与其它模型保持
  Chat Completions（冻结 responses.ts:5-7；不以 SDK 支持推定另一套原生协议）。
- 复用 04 的 SSE 增量解码/分帧、请求组装与统一事件回传，不另起第二套 client。
- ADR-0003 精神：错误与未知结果如实报告；无完成事件的断流不伪报成功。
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from .sse import SSEStreamParser

RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"

# 冻结 responses.ts:6 /^gpt-6(?:[.-]|$)/i
_GPT6 = re.compile(r"^gpt-6(?:[.-]|$)", re.IGNORECASE)
# 冻结 responses.ts:59 /astra|6\.1-sol/（&& 优先于 || 的真实运算顺序）
_ASTRA_SOL = re.compile(r"astra|6\.1-sol")
_MAX_OUTPUT_TOKENS = 128_000
_INCLUDE = ("reasoning.encrypted_content",)


def usesResponses(baseUrl: str, model: str) -> bool:
    """冻结 responses.ts:5-7：官方 v1 端点 + GPT-6 前缀判据。"""
    return baseUrl.rstrip("/") == "https://api.openai.com/v1" and bool(_GPT6.match(model))


def inputMessages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """冻结 responses.ts:11-32：Chat messages → Responses input items。

    tool → function_call_output；assistant → reasoning items + 可选 content +
    function_call；多模态 user → input_text/input_image。内部字段不进入 wire。
    """
    out: list[dict[str, Any]] = []
    for message in messages:
        role = message.get("role")
        if role == "tool":
            out.append({
                "type": "function_call_output",
                "call_id": message.get("tool_call_id"),
                "output": message.get("content"),
            })
            continue
        if role == "assistant":
            items = message.get("responseItems")
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and item.get("type") == "reasoning":
                        out.append(item)
            content = message.get("content")
            if content:
                out.append({"role": "assistant", "content": content})
            calls = message.get("tool_calls")
            if isinstance(calls, list):
                for call in calls:
                    if not isinstance(call, dict):
                        continue
                    function = call.get("function")
                    fn = function if isinstance(function, dict) else {}
                    out.append({
                        "type": "function_call",
                        "call_id": call.get("id"),
                        "name": fn.get("name"),
                        "arguments": fn.get("arguments"),
                    })
            continue
        content = message.get("content")
        if isinstance(content, list):
            parts: list[dict[str, Any]] = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "image_url":
                    image_url = part.get("image_url")
                    url = image_url.get("url") if isinstance(image_url, dict) else None
                    parts.append({"type": "input_image", "image_url": url})
                else:
                    parts.append({"type": "input_text", "text": part.get("text")})
            out.append({"role": role, "content": parts})
        else:
            out.append({"role": role, "content": content})
    return out


def responsesUsage(raw: dict[str, Any]) -> dict[str, Any]:
    """冻结 responses.ts:34-39：Responses usage → Chat usage 字段名。

    ``input_tokens`` → ``prompt_tokens``，``output_tokens`` → ``completion_tokens``，
    ``input_tokens_details`` → ``prompt_tokens_details``；原生 cache 字段优先与
    ``cached_tokens`` 补齐由 04 的 ``client.normalizeUsage`` 联动完成（R-06）。
    """
    out: dict[str, Any] = {
        "prompt_tokens": raw.get("input_tokens"),
        "completion_tokens": raw.get("output_tokens"),
        "total_tokens": raw.get("total_tokens"),
    }
    details = raw.get("input_tokens_details")
    if details is not None:
        out["prompt_tokens_details"] = details
    return out


def responsesMessage(output: list[dict[str, Any]]) -> dict[str, Any]:
    """冻结 responses.ts:41-49：output items → assistant message 片段。

    text/refusal 拼接、function_call → tool_calls、只保留 reasoning items；
    空文本为 ``None``，空 tool_calls 不生成键。
    """
    texts: list[str] = []
    calls: list[dict[str, Any]] = []
    reasoning: list[dict[str, Any]] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "message":
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        texts.append(part.get("text") or part.get("refusal") or "")
        elif kind == "function_call":
            calls.append({
                "id": item.get("call_id"), "type": "function",
                "function": {"name": item.get("name"),
                             "arguments": item.get("arguments")},
            })
        elif kind == "reasoning":
            reasoning.append(item)
    result: dict[str, Any] = {"content": "".join(texts) or None}
    if calls:
        result["tool_calls"] = calls
    result["responseItems"] = reasoning
    return result


def buildResponsesRequest(chat: dict[str, Any]) -> dict[str, Any]:
    """冻结 responses.ts:53-65：Chat 请求体 → Responses 请求体。

    store/include 固定；max_output_tokens 取 ``max_completion_tokens ?? max_tokens``
    并裁到 128000；effort 按 reasoning_effort / thinking / 特殊模型映射；
    tools 展开为顶层 function 声明 + strict:false；可选字段仅定义时透传。
    """
    effort = chat.get("reasoning_effort")
    if effort is None:
        thinking = chat.get("thinking")
        effort = ("low" if isinstance(thinking, dict)
                  and thinking.get("type") == "disabled" else "medium")
    model = chat.get("model")
    if effort == "minimal" or (
        effort == "none" and isinstance(model, str)
        and _ASTRA_SOL.search(model) is not None
    ):
        mapped_effort: Any = "low"
    else:
        mapped_effort = effort
    max_completion = chat.get("max_completion_tokens")
    limit_value = max_completion if max_completion is not None else chat.get("max_tokens")
    # 04 的 buildRequestBody 总带上限字段；非数值仅作内部契约防御，产品路径不触发。
    limit = int(limit_value) if isinstance(limit_value, (int, float)) else _MAX_OUTPUT_TOKENS
    messages = chat.get("messages")
    body: dict[str, Any] = {
        "model": model,
        "input": inputMessages(messages if isinstance(messages, list) else []),
        "stream": chat.get("stream"),
        "store": False,
        "include": list(_INCLUDE),
        "max_output_tokens": min(limit, _MAX_OUTPUT_TOKENS),
        "reasoning": {"effort": mapped_effort},
    }
    tools = chat.get("tools")
    if isinstance(tools, list) and tools:
        mapped_tools: list[dict[str, Any]] = []
        for tool in tools:
            if isinstance(tool, dict):
                function = tool.get("function")
                fn = function if isinstance(function, dict) else {}
                mapped_tools.append({"type": "function", **fn, "strict": False})
        body["tools"] = mapped_tools
    for key in ("parallel_tool_calls", "tool_choice", "service_tier"):
        if key in chat:
            body[key] = chat[key]
    return body


class ResponsesStreamError(RuntimeError):
    """Responses 流中断 / 协议错误（不伪报成功空回复）。"""


def _chatFrame(value: dict[str, Any]) -> bytes:
    """冻结 responses.ts:90：emit 标准 Chat SSE ``data: {json}\\n\\n`` 帧。"""
    return ("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode("utf-8")


class ResponsesToChat:
    """冻结 responses.ts:73-131：Responses SSE 事件流 → 标准 Chat SSE data 帧。

    复用 04 的 ``SSEStreamParser`` 做增量严格 UTF-8 解码与 CRLF/空行分帧，
    输出统一 Chat 帧，使 04 的 ``ChatAccumulator`` 直接复用（不另起事件类型）。
    """

    def __init__(self) -> None:
        self._parser = SSEStreamParser()
        self._completed = False
        self._had_text = False
        self._calls: dict[int, dict[str, str]] = {}
        self._output: dict[int, dict[str, Any]] = {}

    def feed(self, chunk: bytes) -> list[bytes]:
        frames: list[bytes] = []
        for payload in self._parser.feed(chunk):
            frames.extend(self._drain(payload))
        return frames

    def flush(self) -> list[bytes]:
        """冻结 transform.flush：残余补帧后 drain；无完成事件明确抛错。"""
        frames: list[bytes] = []
        for payload in self._parser.flush():
            frames.extend(self._drain(payload))
        if not self._completed:
            raise ResponsesStreamError("Responses stream closed unexpectedly")
        return frames

    def _delta(self, value: dict[str, Any]) -> bytes:
        return _chatFrame({"choices": [{"delta": value}]})

    def _call(self, index: int, item: dict[str, Any], frames: list[bytes]) -> None:
        """冻结 responses.ts:92-102：注册调用并按已累积长度发 arguments 差量。"""
        if index not in self._calls:
            self._calls[index] = {"name": str(item.get("name") or ""), "args": ""}
            frames.append(self._delta({"tool_calls": [{
                "index": index, "id": item.get("call_id"),
                "function": {"name": item.get("name"), "arguments": ""},
            }]}))
        acc = self._calls[index]
        arguments = item.get("arguments")
        if isinstance(arguments, str) and len(arguments) > len(acc["args"]):
            frames.append(self._delta({"tool_calls": [{
                "index": index,
                "function": {"arguments": arguments[len(acc["args"]):]},
            }]}))
            acc["args"] = arguments

    def _drain(self, payload: str) -> list[bytes]:
        """冻结 responses.ts:88-129 的事件分发。"""
        if payload in ("[DONE]", ""):
            return []
        event: Any = json.loads(payload)  # 坏 JSON 明确失败，不静默跳过
        if not isinstance(event, dict):
            return []
        etype = event.get("type")
        frames: list[bytes] = []
        index = int(event.get("output_index") or 0)
        if etype == "response.output_item.added":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "function_call":
                self._call(index, item, frames)
        elif etype == "response.function_call_arguments.delta":
            acc = self._calls.get(index)
            if acc is None:
                raise ResponsesStreamError("Responses 工具参数缺少对应调用")
            delta = event.get("delta", "")
            acc["args"] += delta
            frames.append(self._delta({"tool_calls": [{
                "index": index, "function": {"arguments": delta},
            }]}))
        elif etype in ("response.output_text.delta", "response.refusal.delta"):
            self._had_text = True
            frames.append(self._delta({"content": event.get("delta", "")}))
        elif etype == "response.reasoning_summary_text.delta":
            frames.append(self._delta({"reasoning_content": event.get("delta", "")}))
        elif etype == "response.output_item.done":
            item = event.get("item")
            if isinstance(item, dict):
                self._output[index] = item
                if item.get("type") == "function_call":
                    self._call(index, item, frames)
        elif etype in ("response.completed", "response.incomplete"):
            self._completed = True
            data = event.get("response")
            data = data if isinstance(data, dict) else {}
            items = data.get("output")
            if not isinstance(items, list):
                items = [self._output[i] for i in sorted(self._output)]
            for position, item in enumerate(items):
                if isinstance(item, dict) and item.get("type") == "function_call":
                    self._call(position, item, frames)
            msg = responsesMessage(items)
            if not self._had_text and msg.get("content"):
                frames.append(self._delta({"content": msg["content"]}))
            final: dict[str, Any] = {"response_items": msg["responseItems"]}
            usage_raw = data.get("usage")
            if isinstance(usage_raw, dict):
                final["usage"] = responsesUsage(usage_raw)
            finish = ("length" if etype == "response.incomplete"
                      else "tool_calls" if self._calls else "stop")
            final["choices"] = [{"delta": {}, "finish_reason": finish}]
            frames.append(_chatFrame(final))
        elif etype in ("error", "response.failed"):
            error = event.get("error")
            if error is None and isinstance(event.get("response"), dict):
                error = event["response"].get("error")
            if error is None:
                error = {"message": event.get("message") or "Responses 请求失败"}
            frames.append(_chatFrame({"error": error}))
        return frames


def iterChatFrames(chunks: Iterable[bytes]) -> Iterator[bytes]:
    """把 Responses SSE 字节流增量转成标准 Chat SSE 字节流。

    对应冻结 ``responsesFetch`` 对 fetch/流的包装：client 侧仍用同一套
    ``SSEStreamParser`` + ``ChatAccumulator`` 消费，不另起第二套 client。
    """
    converter = ResponsesToChat()
    for chunk in chunks:
        for frame in converter.feed(chunk):
            yield frame
    for frame in converter.flush():
        yield frame
