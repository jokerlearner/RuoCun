"""在 Chat 请求和 Responses 协议之间做路由与转换。只有符合端点和模型前缀的请求走 Responses。

将 Responses 事件转为统一的 Chat 增量，复用同一解码和结果累积路径。没有完成事件的断流以错误报告。
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from typing import Any

from .sse import SSEStreamParser

RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"

# 模型名前缀须在 gpt-6 后遇到点、连字符或结尾。
_GPT6 = re.compile(r"^gpt-6(?:[.-]|$)", re.IGNORECASE)
# 特殊模型映射同时考虑模型名和推理配置，沿用原判定优先级。
_ASTRA_SOL = re.compile(r"astra|6\.1-sol")
_MAX_OUTPUT_TOKENS = 128_000
_INCLUDE = ("reasoning.encrypted_content",)


def usesResponses(baseUrl: str, model: str) -> bool:
    """官方 v1 端点与 GPT-6 前缀同时满足时走 Responses。"""
    return baseUrl.rstrip("/") == "https://api.openai.com/v1" and bool(_GPT6.match(model))


def inputMessages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """将 Chat 历史投影为 Responses 输入项。

    工具结果对应 function_call_output，助手消息带推理和函数调用，多模态用户消息携带文字和图片。内部字段留在会话里。
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
    """将 Responses 的输入、输出用量和详情字段转换为 Chat 字段名，再由 normalizeUsage 统一补齐缓存字段。"""
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
    """汇总输出项中的文本、拒绝、函数调用和推理。空文本为 None，没有工具调用时省略该字段。"""
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
    """将 Chat 请求转换成 Responses 请求，统一输出上限、推理强度和工具定义。

    选用已给出的上限并限制为至多 128000，可选输入字段仅在已定义时传递。
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
    # 正常 Chat 请求自带输出上限。这里给内部调用传入非数值时提供防御。
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
    """Responses 流中断或事件格式错误。"""


def _chatFrame(value: dict[str, Any]) -> bytes:
    """把单条增量包装成标准 Chat SSE 数据帧。"""
    return ("data: " + json.dumps(value, ensure_ascii=False) + "\n\n").encode("utf-8")


class ResponsesToChat:
    """把 Responses SSE 增量转为 Chat SSE 帧。字节解码、CRLF 和空行分帧复用 SSEStreamParser，输出可交给原有 Chat 累积器。"""

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
        """在流结束时消费尾部残余帧。缺少完成事件则报告中断。"""
        frames: list[bytes] = []
        for payload in self._parser.flush():
            frames.extend(self._drain(payload))
        if not self._completed:
            raise ResponsesStreamError("Responses stream closed unexpectedly")
        return frames

    def _delta(self, value: dict[str, Any]) -> bytes:
        return _chatFrame({"choices": [{"delta": value}]})

    def _call(self, index: int, item: dict[str, Any], frames: list[bytes]) -> None:
        """登记工具调用，并按累计长度发出新增参数字符。"""
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
        """按 Responses 事件类型更新状态并产生相应的 Chat 帧。"""
        if payload in ("[DONE]", ""):
            return []
        event: Any = json.loads(payload)  # 数据帧 JSON 不可解析时直接报告错误。
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
    """增量转换 Responses 字节流，供原有 Chat 分帧器和累积器统一消费。"""
    converter = ResponsesToChat()
    for chunk in chunks:
        for frame in converter.feed(chunk):
            yield frame
    for frame in converter.flush():
        yield frame
