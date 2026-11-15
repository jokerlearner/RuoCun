"""用合成账户和本地 SSE 服务验证一次对话的完整请求路径。

调用方显式传入演示目录。客户端仍发起真实的 HTTP 请求，目标是本模块启动的回环服务。服务端按字节切分响应，验证客户端能把跨分片的中文和表情拼回原文。
"""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, cast

from .client import client
from .client.types import StreamChatOptions
from .config import compat, credential, env_file, profiles_store
from .prompt import system_prompt


class ChatConfigError(RuntimeError):
    """合成账户配置、凭据或 JSON 格式无效。"""


_SYNTHETIC_FRAMES: tuple[dict[str, Any] | str, ...] = (
    {"choices": [{"delta": {"content": "你好"}}]},
    {"choices": [{"delta": {"content": "，世界"}}]},
    {"choices": [{"delta": {"content": " 😀"}}]},
    {"choices": [], "usage": {
        "prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17,
    }},
    "[DONE]",
)


def _synthetic_sse_bytes() -> bytes:
    parts: list[str] = []
    for frame in _SYNTHETIC_FRAMES:
        body = frame if isinstance(frame, str) else json.dumps(frame, ensure_ascii=False)
        parts.append("data: " + body + "\n\n")
    return "".join(parts).encode("utf-8")


class _SSEHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b""
        server = cast("SyntheticSSEServer", self.server)
        try:
            parsed: Any = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        server.captured.append({"path": self.path, "body": parsed})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        data = server.sse_bytes
        # 按固定字节数分片，让中文或表情的 UTF-8 字节跨越分片，验证解码器能正确拼接。
        for i in range(0, len(data), server.chunk_size):
            self.wfile.write(data[i:i + server.chunk_size])
            self.wfile.flush()

    def log_message(self, format: str, *args: Any) -> None:
        return


class SyntheticSSEServer(ThreadingHTTPServer):
    """在回环地址和临时端口启动合成 SSE 服务。"""

    daemon_threads = True

    def __init__(self, sse_bytes: bytes, chunk_size: int) -> None:
        super().__init__(("127.0.0.1", 0), _SSEHandler)
        self.sse_bytes = sse_bytes
        self.chunk_size = chunk_size
        self.captured: list[dict[str, Any]] = []


def run_chat_demo(
    config_dir: str | Path,
    prompt: str,
    *,
    environ: Mapping[str, str] | None = None,
    model_override: str | None = None,
) -> dict[str, Any]:
    root = Path(config_dir).resolve()
    env: dict[str, str] = dict(os.environ if environ is None else environ)

    env_file.applyDotenv(root / ".env", env)

    config = profiles_store.loadProfiles(root / "config.json")

    # 演示只从合成内存凭据库获取账户密钥，缺失时以配置错误结束。
    store = credential.MemoryKeychain()
    resolved = credential.resolveCredential(config, store)
    if resolved is None:
        raise ChatConfigError(
            "缺少有效凭据：激活 profile 无内联 key，且未配置可用的合成 keyRef")

    model = model_override or resolved["model"]

    system_text = system_prompt.buildSystemPrompt({
        "modelId": model,
        "toolSummaries": "- Read:读取文件",
        "cwd": str(root),
        "platform": "win32",
        "interactive": False,
    })

    server = SyntheticSSEServer(_synthetic_sse_bytes(), chunk_size=3)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        opts: StreamChatOptions = {
            "baseUrl": f"http://127.0.0.1:{port}",
            "apiKey": resolved["key"],
            "model": model,
            "messages": [
                {"role": "system", "content": system_text},
                {"role": "user", "content": prompt},
            ],
            "extra": {"reasoning_effort": compat.reasoning_effort(env)},
        }
        result = client.streamChat(opts, env=env)
        captured = server.captured[0] if server.captured else {}
        wire_ok = (
            captured.get("path") == "/chat/completions"
            and captured.get("body") == result.request_body
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    return {
        "status": result.status,
        "answer": result.message.get("content"),
        "deltas": result.deltas,
        "usage": result.usage,
        "finish_reason": result.finish_reason,
        "request_golden": result.request_body,  # 报告保存请求体。用于认证的密钥通过请求头传递。
        "wire_request_validated": wire_ok,
        "model": model,
        "provider": resolved["provider"],
        "selection": "native",
        "configured_base_url": resolved["baseUrl"],
        "server_closed": not thread.is_alive(),
    }
