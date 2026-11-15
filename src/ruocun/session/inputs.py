"""在 AcceptedInput.payload 中保存用户原文和模型投影。

用户可见历史读取原文。发送模型请求时可使用处理后的内容，旧格式仍可以作为原文读取。
"""

from __future__ import annotations

import json
from typing import Any, cast

Content = str | list[dict[str, Any]]
_KIND = "ruocun-queued-projection-v1"


def packQueuedInput(original: Content, model: Content | None = None) -> str:
    value = original if model is None else {"kind": _KIND, "original": original, "model": model}
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def _reject_constant(value: str) -> None:
    raise ValueError("排队输入不是有效JSON。")


def _content(payload: str, field: str) -> Content:
    value = json.loads(payload, parse_constant=_reject_constant)
    if isinstance(value, dict):
        if set(value) != {"kind", "original", "model"} or value["kind"] != _KIND:
            raise ValueError("排队输入的投影格式无法恢复，保留原记录。")
        value = value[field]
    if not isinstance(value, (str, list)):
        raise ValueError("排队输入内容无法恢复，保留原记录。")
    return cast(Content, value)


def originalInput(payload: str) -> Content:
    return _content(payload, "original")


def modelInput(payload: str) -> Content:
    return _content(payload, "model")
