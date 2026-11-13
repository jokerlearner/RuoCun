"""冻结 loop.ts 批末 Read 图片注入（MIT），投递标记仅属于 checkpoint 投影。"""

from __future__ import annotations

import copy

from ..client.types import ChatMessage, ContentPart


def isValidToolResult(result: object, call_id: str) -> bool:
    """旧文字结果或身份匹配的完整ToolMessage；投递标记不属于journal。"""
    if isinstance(result, str):
        return True
    if not isinstance(result, dict):
        return False
    if (result.get("role") != "tool" or result.get("tool_call_id") != call_id
            or not isinstance(result.get("content"), str) or "imageDelivered" in result):
        return False
    if "imageData" in result:
        image = result["imageData"]
        if (not isinstance(image, dict) or set(image) != {"base64", "mediaType"}
                or not isinstance(image["base64"], str) or not isinstance(image["mediaType"], str)):
            return False
    return True


def flushReadImages(messages: list[ChatMessage]) -> list[ChatMessage]:
    """生成图片批末投影；不改输入，不从已压缩掉的工具journal重新注入。"""
    pending = [index for index, message in enumerate(messages)
               if message.get("role") == "tool" and message.get("imageData")
               and not message.get("imageDelivered")]
    if not pending:
        return messages
    candidate = copy.deepcopy(messages)
    parts: list[ContentPart] = []
    for index in pending:
        image = candidate[index]["imageData"]
        parts.append({"type": "image_url", "image_url": {
            "url": f"data:{image['mediaType']};base64,{image['base64']}",
        }})
        candidate[index]["imageDelivered"] = True
    parts.append({"type": "text", "text": "[以上图片由 Read 工具读取,请基于图片内容回答用户的问题]"})
    candidate.append({"role": "user", "content": parts})
    return candidate
