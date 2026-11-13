"""任务05 可运行产品路径：合成账户配置 → Responses 路由 → 同一对话/工具回合。

来源冻结 ``src/client/responses.ts`` / ``responses.test.ts``（MIT）与 04 已建立的
配置/提示/流式契约。本路径只用**显式传入的合成配置目录**与**本次拥有的本地
loopback 合成 HTTP/SSE 服务**：
- 不调用任何真实模型、不访问公网、不读真实用户配置/凭据/密钥；
- 配置里使用官方端点（满足路由判据），但实际请求经注入式 transport 重写到
  ``127.0.0.1`` 随机端口的本地合成服务，服务端按 17 字节分块写 Responses SSE；
- 两轮 ``streamChat`` 复现冻结 ``responses.test.ts:30-62`` 的函数调用/输出与
  reasoning items 往返；输出两轮请求 golden、原始 Responses 事件 golden、
  统一 Chat 事件 golden 与资源清理回执，绝不回显 secret；
- 服务在 ``finally`` 中 shutdown/server_close/thread.join，报告端口/线程/socket 回执。

这是显式演示/验收入口；既有 ``--version`` / ``--help`` / 普通 prompt 退出码 69
与 04 的 ``--chat-demo`` 行为不变。完整 Agent 运行路径仍由后续任务实现。
"""

from __future__ import annotations

import json
import os
import socket
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, cast

from .client import client, responses
from .client.types import StreamChatOptions
from .config import compat, credential, env_file, profiles_store
from .prompt import system_prompt


class ResponsesDemoError(RuntimeError):
    """无效配置 / 缺凭据 / 路由不命中的明确失败。"""


# 冻结 responses.test.ts:6-8 / :10-13 的 fixture（服务端合成事件，产品不发真实请求）
_REASONING: dict[str, Any] = {
    "type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "ciphertext",
}
_CALL_ARGUMENTS = '{"path":"中文.ts"}'
_CALL: dict[str, Any] = {
    "type": "function_call", "id": "fc_1", "call_id": "call_1",
    "name": "Read", "arguments": _CALL_ARGUMENTS,
}
_ANSWER: dict[str, Any] = {
    "type": "message", "content": [{"type": "output_text", "text": "完成"}],
}
_USAGE: dict[str, Any] = {
    "input_tokens": 100, "output_tokens": 10, "total_tokens": 110,
    "input_tokens_details": {"cached_tokens": 80},
}
_TOOLS: list[dict[str, Any]] = [{
    "type": "function", "function": {
        "name": "Read", "description": "读取", "parameters": {"type": "object"},
    },
}]


def _completed(output: list[dict[str, Any]], *extra: dict[str, Any]) -> list[dict[str, Any]]:
    return [*extra, {"type": "response.completed",
                     "response": {"output": output, "usage": _USAGE}}]


def _turn_events() -> list[list[dict[str, Any]]]:
    """冻结 responses.test.ts:34-39 的两轮事件序列（含中文跨字节参数增量）。"""
    first = _completed([_REASONING, _CALL],
        {"type": "response.output_item.added", "output_index": 1,
         "item": {**_CALL, "arguments": ""}},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '{"path":'},
        {"type": "response.function_call_arguments.delta", "output_index": 1,
         "delta": '"中文.ts"}'},
        {"type": "response.output_item.done", "output_index": 1, "item": _CALL},
    )
    second = _completed([_ANSWER],
        {"type": "response.output_text.delta", "delta": "完成"},
    )
    return [first, second]


def _encode_responses_sse(events: list[dict[str, Any]]) -> bytes:
    """冻结 responses.test.ts:14-15：event:<type> CRLF data:<json> CRLFCRLF。"""
    parts: list[str] = []
    for event in events:
        parts.append("event: " + str(event["type"]) + "\r\ndata: "
                     + json.dumps(event, ensure_ascii=False) + "\r\n\r\n")
    return "".join(parts).encode("utf-8")


class _ResponsesHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length else b""
        server = cast("SyntheticResponsesServer", self.server)
        try:
            parsed: Any = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = None
        server.captured.append({"path": self.path, "body": parsed})
        turn = len(server.captured)  # 1-based，对应冻结 requests.length === 1
        data = server.sse_bytes(turn)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for i in range(0, len(data), 17):
            self.wfile.write(data[i:i + 17])
            self.wfile.flush()

    def log_message(self, format: str, *args: Any) -> None:
        return


class SyntheticResponsesServer(ThreadingHTTPServer):
    """本次拥有的本地合成 Responses SSE 服务（仅 127.0.0.1 随机端口）。"""

    daemon_threads = True

    def __init__(self, turns: list[list[dict[str, Any]]]) -> None:
        super().__init__(("127.0.0.1", 0), _ResponsesHandler)
        self.turns = turns
        self.captured: list[dict[str, Any]] = []

    def sse_bytes(self, turn: int) -> bytes:
        events = self.turns[min(turn - 1, len(self.turns) - 1)]
        return _encode_responses_sse(events)


def _loopback_transport(port: int) -> client.Transport:
    """注入式 transport：官方端点 URL 重写到本次拥有的本地服务，保留 path。

    真实 HTTP POST + 真实响应字节；返回按 17 字节切分的 chunks，确定性复现
    跨字节 UTF-8 分片（与冻结 sse() 的 17 字节分块一致）。
    """
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        # 路由判据保证是官方 Responses 端点；本地合成服务只暴露 /responses 路径
        if url != responses.RESPONSES_ENDPOINT:
            raise ResponsesDemoError("transport 收到非 Responses 端点 URL")
        local_url = f"http://127.0.0.1:{port}/responses"
        request = urllib.request.Request(
            local_url, data=body, headers=headers, method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            pieces: list[bytes] = []
            while True:
                piece = response.read(4096)
                if not piece:
                    break
                pieces.append(piece)
            raw = b"".join(pieces)
            status = int(response.status)
        chunks = [raw[i:i + 17] for i in range(0, len(raw), 17)]
        return client.HttpResponse(status, {}, tuple(chunks))

    return transport


def run_responses_demo(
    config_dir: str | Path,
    prompt: str,
    *,
    environ: Mapping[str, str] | None = None,
    model_override: str | None = None,
) -> dict[str, Any]:
    root = Path(config_dir).resolve()
    env: dict[str, str] = dict(os.environ if environ is None else environ)

    # 1) dotenv / 原生与兼容 profiles / 合成凭据（复用 04 契约，不读真实密钥）
    env_file.applyDotenv(root / ".env", env)
    config = profiles_store.loadProfiles(root / "config.json")
    store = credential.MemoryKeychain()
    resolved = credential.resolveCredential(config, store)
    if resolved is None:
        raise ResponsesDemoError(
            "缺少有效凭据：激活 profile 无内联 key，且未配置可用的合成 keyRef")

    model = model_override or resolved["model"]
    # 2) 路由判据必须成立；不静默用 Chat 冒充 Responses 演示（R-06）
    if not responses.usesResponses(resolved["baseUrl"], model):
        raise ResponsesDemoError(
            "配置未命中 Responses 路由判据：需 https://api.openai.com/v1 + gpt-6 模型")

    # 3) 冻结提示（品牌/环境差异白名单）
    system_text = system_prompt.buildSystemPrompt({
        "modelId": model,
        "toolSummaries": "- Read:读取文件",
        "cwd": str(root),
        "platform": "win32",
        "interactive": False,
    })

    turns = _turn_events()
    server = SyntheticResponsesServer(turns)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = int(server.server_address[1])
        transport = _loopback_transport(port)
        base_url = resolved["baseUrl"]  # 官方端点，仅用于判据/请求组装
        reasoning_effort = compat.reasoning_effort(env)
        messages1: list[dict[str, Any]] = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,test"}},
            ]},
        ]
        opts1: StreamChatOptions = {
            "baseUrl": base_url, "apiKey": resolved["key"], "model": model,
            "messages": messages1, "tools": _TOOLS,
            "extra": {"reasoning_effort": reasoning_effort},
        }
        first = client.streamChat(opts1, transport=transport, env=env)

        # 同一对话/工具回合：回灌 assistant（含 responseItems/tool_calls）与工具结果
        messages2: list[dict[str, Any]] = [
            *messages1, first.message,
            {"role": "tool", "tool_call_id": "call_1", "content": "文件内容"},
        ]
        opts2: StreamChatOptions = {
            "baseUrl": base_url, "apiKey": resolved["key"], "model": model,
            "messages": messages2,
            "extra": {"reasoning_effort": reasoning_effort},
        }
        second = client.streamChat(opts2, transport=transport, env=env)

        captured = list(server.captured)
        wire_ok = (
            len(captured) == 2
            and all(c.get("path") == "/responses" for c in captured)
            and captured[0].get("body") == first.request_body
            and captured[1].get("body") == second.request_body
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    try:
        socket_fileno = server.socket.fileno()
    except OSError:
        socket_fileno = -1
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            port_listening = True
    except OSError:
        port_listening = False

    return {
        "status": second.status,
        "route": "responses",
        "route_criteria": {
            "base_url": resolved["baseUrl"], "model": model,
            "uses_responses": True,
            "endpoint": responses.RESPONSES_ENDPOINT,
        },
        "answer": second.message.get("content"),
        # 请求 golden：两轮 Responses 请求体（与服务端捕获 body 逐项核对）
        "request_golden": [first.request_body, second.request_body],
        # 原始 Responses 事件 golden：服务端发送的输入事件序列（独立来源 fixture）
        "responses_events_golden": turns,
        # 统一 Chat 事件 golden：转换后的 deltas/finish_reason/usage/message
        "event_golden": [
            {"deltas": first.deltas, "finish_reason": first.finish_reason,
             "usage": first.usage, "message": first.message},
            {"deltas": second.deltas, "finish_reason": second.finish_reason,
             "usage": second.usage, "message": second.message},
        ],
        "server_captured": captured,
        "wire_request_validated": wire_ok,
        "configured_base_url": resolved["baseUrl"],  # 合成配置端点，未连接公网
        "local_endpoint": f"http://127.0.0.1:{port}/responses",
        "model": model,
        "provider": resolved["provider"],
        "selection": "native",
        "server_closed": not thread.is_alive(),
        "server_socket_fileno": socket_fileno,
        "port_not_listening": not port_listening,
        "port": port,
    }
