"""用合成账户和本地服务验证 Responses 路由在同一对话中的工具往返。

演示保留正式端点的路径判定，再把 HTTP 传输定向到回环服务。记录服务收到的请求、发出的 SSE 事件和客户端转换后的结果，方便逐层核对。
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
    """演示配置、凭据或路由条件无效。"""


# 演示的合成事件面向固定的两轮对话。
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
    """为指定回合构造合成 Responses 事件。"""
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
    """将 Responses 事件编码为使用 CRLF 的 SSE 字节。"""
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
        turn = len(server.captured)  # 回合从 1 开始编号，与服务端已收到的请求数量对齐。
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
    """在回环地址和临时端口启动合成 Responses 服务。"""

    daemon_threads = True

    def __init__(self, turns: list[list[dict[str, Any]]]) -> None:
        super().__init__(("127.0.0.1", 0), _ResponsesHandler)
        self.turns = turns
        self.captured: list[dict[str, Any]] = []

    def sse_bytes(self, turn: int) -> bytes:
        events = self.turns[min(turn - 1, len(self.turns) - 1)]
        return _encode_responses_sse(events)


def _loopback_transport(port: int) -> client.Transport:
    """将请求转到本地服务，并把收到的响应按 17 字节分片交回客户端。"""
    def transport(url: str, headers: dict[str, str], body: bytes) -> client.HttpResponse:
        # 先按正式地址检查 Responses 路由，再将有效的路径转往回环服务。
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

    # 演示只读显式传入的合成账户目录，并用内存凭据库承接密钥查询。
    env_file.applyDotenv(root / ".env", env)
    config = profiles_store.loadProfiles(root / "config.json")
    store = credential.MemoryKeychain()
    resolved = credential.resolveCredential(config, store)
    if resolved is None:
        raise ResponsesDemoError(
            "缺少有效凭据：激活 profile 无内联 key，且未配置可用的合成 keyRef")

    model = model_override or resolved["model"]
    # 路由必须实际命中 Responses，避免以 Chat 路径的数据误作演示结果。
    if not responses.usesResponses(resolved["baseUrl"], model):
        raise ResponsesDemoError(
            "配置未命中 Responses 路由判据：需 https://api.openai.com/v1 + gpt-6 模型")

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
        base_url = resolved["baseUrl"]
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

        # 用第一轮回复的响应项和工具调用，加上工具结果构造下一轮请求。
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
        # 保留服务端接到的请求体，便于核对编码后的内容。
        "request_golden": [first.request_body, second.request_body],
        # 保留服务端发出的事件序列，便于核对协议输入。
        "responses_events_golden": turns,
        # 保留客户端转换后的事件，便于查看统一接口的解析结果。
        "event_golden": [
            {"deltas": first.deltas, "finish_reason": first.finish_reason,
             "usage": first.usage, "message": first.message},
            {"deltas": second.deltas, "finish_reason": second.finish_reason,
             "usage": second.usage, "message": second.message},
        ],
        "server_captured": captured,
        "wire_request_validated": wire_ok,
        "configured_base_url": resolved["baseUrl"],
        "local_endpoint": f"http://127.0.0.1:{port}/responses",
        "model": model,
        "provider": resolved["provider"],
        "selection": "native",
        "server_closed": not thread.is_alive(),
        "server_socket_fileno": socket_fileno,
        "port_not_listening": not port_listening,
        "port": port,
    }
