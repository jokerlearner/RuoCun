"""Chat 模型协议层：SSE 分帧、请求组装与流式累积（来源冻结 ``src/client/*``，MIT）。

按 D09:95 与 WIRE-03：按增量字节严格解码 UTF-8，不复制来源
``data.toString()`` 的 Unicode/65536 缓冲瑕疵作正确预期。
"""

from __future__ import annotations
