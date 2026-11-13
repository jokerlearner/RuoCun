"""Chat 协议类型（来源冻结 ``src/client/types.ts``，MIT）。

消息、工具、流式增量用宽松映射保留来源对角色/字段/空值/未知字段的宽容
边界（R-12）：不借 Pydantic 式默认删未知/补 default 改写发送契约。
``Usage`` / ``StreamChatOptions`` 用 TypedDict 表达已确认字段。
"""

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
