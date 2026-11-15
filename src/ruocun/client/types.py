"""定义 Chat 消息、工具和流式增量的共享类型。协议映射保留未知字段和空值语义，Usage 等已确认结构用 TypedDict 描述。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypedDict

ContentPart = dict[str, Any]
ChatMessage = dict[str, Any]
ApiTool = dict[str, Any]
ToolCall = dict[str, Any]
StreamDelta = dict[str, Any]


class ImageData(TypedDict):
    base64: str
    mediaType: str


class Usage(TypedDict, total=False):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_cache_hit_tokens: int
    prompt_cache_miss_tokens: int
    prompt_tokens_details: dict[str, Any]


class StreamChatOptions(TypedDict, total=False):
    baseUrl: str
    apiKey: str
    provider: str
    model: str
    messages: list[ChatMessage]
    tools: list[ApiTool]
    parallelToolCalls: bool
    extra: dict[str, Any]
    maxTokens: int
    idleTimeoutMs: int
    maxRetries: int
    retryDelayMs: int
    background: bool
    onUsage: Callable[[Usage], None]
    onFinishReason: Callable[[str], None]
    onEmptyTruncation: Callable[[], None]
