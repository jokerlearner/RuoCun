"""一次性 prompt 产品路径：合成账户配置 → 冻结提示/参数 → Chat SSE → 回答。

来源冻结 ``src/index.ts:330-423`` 的账户/模型路由与 ``src/prompt/system_prompt.ts``
提示组装，叠加快照 D09 兼容契约（ADR-0005）。

本路径只用**显式传入的合成配置目录**与**本地 loopback 合成 SSE 服务**：
- 不调用任何真实模型、不访问公网、不读真实用户配置/凭据/密钥；
- 凭据仅来自合成 config.json 的内联 key（经合成内存 keychain，不接系统后端）；
- 真实 HTTP POST + 真实 SSE 字节流（含中文/emoji 跨字节分片），服务端是本次
  拥有的本地合成服务，请求完成后 shutdown/thread.join 关闭并留回执；
- 输出结构化请求 golden 与回答，绝不回显 secret。

这是任务04 的开发/验收演示入口；完整 Agent（工具、会话、权限、恢复）仍由后续
任务实现，普通 prompt 仍返回 ``Agent 运行路径尚未实现``（退出码 69）。
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
    """无效配置 / 缺凭据 / 坏 JSON 的明确失败。"""


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
        # 按 3 字节分块写：中文（3 字节）与 emoji（4 字节）被切碎，验证严格增量解码。
        for i in range(0, len(data), server.chunk_size):
            self.wfile.write(data[i:i + server.chunk_size])
            self.wfile.flush()

    def log_message(self, format: str, *args: Any) -> None:
        return


class SyntheticSSEServer(ThreadingHTTPServer):
    """本次拥有的本地合成 SSE 服务（仅 127.0.0.1 随机端口）。"""

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

    # 1) dotenv：只加载 cwd 的 .env；已有 process env（含空值）优先。
    env_file.applyDotenv(root / ".env", env)

    # 2) 读取当前演示目录的原生账户配置。
    config = profiles_store.loadProfiles(root / "config.json")

    # 3) 凭据：只用合成内存 keychain；缺 key 明确失败，不靠通用环境变量挑账户。
    store = credential.MemoryKeychain()
    resolved = credential.resolveCredential(config, store)
    if resolved is None:
        raise ChatConfigError(
            "缺少有效凭据：激活 profile 无内联 key，且未配置可用的合成 keyRef")

    # 4) 模型覆盖：调用 override > profile.model。
    model = model_override or resolved["model"]

    # 5) 冻结提示：品牌/环境差异白名单 + 真实 Python/Windows 环境说明。
    system_text = system_prompt.buildSystemPrompt({
        "modelId": model,
        "toolSummaries": "- Read:读取文件",
        "cwd": str(root),
        "platform": "win32",
        "interactive": False,
    })

    # 6) 本地合成 SSE 服务 + 真实 urllib HTTP transport。
    server = SyntheticSSEServer(_synthetic_sse_bytes(), chunk_size=3)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        opts: StreamChatOptions = {
            "baseUrl": f"http://127.0.0.1:{port}",
            "apiKey": resolved["key"],  # 合成 key，仅发本次本地服务
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
        "request_golden": result.request_body,  # 不含 apiKey（密钥在 header）
        "wire_request_validated": wire_ok,
        "model": model,
        "provider": resolved["provider"],
        "selection": "native",
        "configured_base_url": resolved["baseUrl"],  # 合成配置端点，未连接
        "server_closed": not thread.is_alive(),
    }
