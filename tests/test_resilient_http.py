"""Client 重试在真实本机 HTTP 传输上的行为；服务和凭据均为合成。"""

from __future__ import annotations

import socketserver
import ssl
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from ruocun.client import client
from ruocun.client.resilient import (
    IdleTimeoutError,
    ResilientContext,
    streamChatResilient,
)


@pytest.fixture(autouse=True)
def synthetic_no_system_proxy(monkeypatch) -> None:
    # Windows urllib 可从系统代理配置读取值；本文件默认仅允许直接访问本机。
    monkeypatch.setattr(urllib.request, "getproxies", lambda: {})


@pytest.mark.parametrize(("status", "retry_after"), [(503, None), (429, "0")])
def test_real_http_retryable_status_before_success(status, retry_after) -> None:
    calls: list[int] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            calls.append(1)
            if len(calls) == 1:
                self.send_response(status)
                if retry_after is not None:
                    self.send_header("Retry-After", retry_after)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            body = b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = client.streamChat(
            {"baseUrl": f"http://127.0.0.1:{server.server_port}", "apiKey": "synthetic",
             "model": "deepseek-v4-pro", "messages": [], "maxRetries": 1,
             "retryDelayMs": 0},
            context=ResilientContext(sleep=lambda _seconds: None, jitter_ms=lambda: 0),
            env={},
        )
        assert result.status == "complete"
        assert result.message["content"] == "ok"
        assert len(calls) == 2
        assert result.request_body["stream"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize(("status", "background"), [(429, False), (529, True)])
def test_real_http_429_without_retry_after_and_background_529_do_not_retry(
    status: int, background: bool,
) -> None:
    calls: list[int] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            calls.append(1)
            self.send_response(status)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = streamChatResilient({
            "baseUrl": f"http://127.0.0.1:{server.server_port}", "apiKey": "synthetic",
            "model": "deepseek-v4-pro", "messages": [], "background": background,
        }, context=ResilientContext(sleep=lambda _seconds: None), env={})
        assert result.status == "failed"
        assert result.error_status == status
        assert len(calls) == 1
        assert not result.fallback_used
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_real_http_processes_first_frame_before_response_ends() -> None:
    seen = threading.Event()
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'data: {"usage":{"prompt_tokens":5}}\n\n')
            self.wfile.flush()
            release.wait(2)
            self.wfile.write(b'data: [DONE]\n\n')

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    worker = threading.Thread(target=lambda: client.streamChat({
        "baseUrl": f"http://127.0.0.1:{server.server_port}", "apiKey": "synthetic",
        "model": "deepseek-v4-pro", "messages": [], "onUsage": lambda _u: seen.set(),
    }, env={}))
    worker.start()
    try:
        assert seen.wait(1), "第一帧应在响应结束前处理"
    finally:
        release.set()
        worker.join(3)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


def test_real_idle_after_delta_interrupts_stalled_connection() -> None:
    release = threading.Event()
    seen = threading.Event()
    done = threading.Event()
    results: list[Any] = []
    deltas: list[Any] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"part"}}]}\n\n')
            self.wfile.flush()
            release.wait(3)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    def record_delta(delta: Any) -> None:
        deltas.append(delta)
        seen.set()

    def run() -> None:
        try:
            results.append(client.streamChat({
                "baseUrl": f"http://127.0.0.1:{server.server_port}",
                "apiKey": "synthetic", "model": "deepseek-v4-pro", "messages": [],
                "idleTimeoutMs": 100, "maxRetries": 0,
            }, context=ResilientContext(on_delta=record_delta),
                env={}))
        except Exception as error:
            results.append(error)
        finally:
            done.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert seen.wait(1)
        assert done.wait(1), "idle 必须中止无后续字节的连接"
        assert isinstance(results[0], IdleTimeoutError)
        assert "空闲超时" in str(results[0])
        assert deltas == [{"kind": "content", "text": "part"}]
    finally:
        release.set()
        worker.join(4)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


def test_heartbeat_bytes_do_not_prevent_idle_timeout_after_delta() -> None:
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.end_headers()
            try:
                self.wfile.write(b'data: {"choices":[{"delta":{"content":"part"}}]}\n\n')
                self.wfile.flush()
                while not stop.wait(0.03):
                    self.wfile.write(b'data: {"choices":[]}\n\n')
                    self.wfile.flush()
            except OSError:
                pass

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = streamChatResilient({
            "baseUrl": f"http://127.0.0.1:{server.server_port}", "apiKey": "synthetic",
            "model": "deepseek-v4-pro", "messages": [], "idleTimeoutMs": 100,
            "maxRetries": 0,
        }, env={})
        assert result.status == "failed"
        assert result.watchdog_triggered
        assert result.message["content"] == "part"
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        thread.join()


def test_real_cancel_after_delta_interrupts_stalled_connection() -> None:
    release, seen, cancel, done = (threading.Event() for _ in range(4))
    results: list[Any] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'data: {"choices":[{"delta":{"content":"part"}}]}\n\n')
            self.wfile.flush()
            release.wait(3)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    def run() -> None:
        try:
            results.append(client.streamChat({
                "baseUrl": f"http://127.0.0.1:{server.server_port}",
                "apiKey": "synthetic", "model": "deepseek-v4-pro", "messages": [],
            }, context=ResilientContext(on_delta=lambda _delta: seen.set(),
                                        cancel=cancel.is_set), env={}))
        finally:
            done.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert seen.wait(1)
        cancel.set()
        assert done.wait(1), "用户取消必须中止无后续字节的连接"
        assert results[0].status == "partial"
        assert results[0].message["content"] == "part"
    finally:
        release.set()
        worker.join(4)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


@pytest.mark.parametrize("trigger", ["cancel", "idle"])
def test_tls_handshake_stall_stops_on_cancel_or_idle(trigger) -> None:
    hello, release, done, cancel = (threading.Event() for _ in range(4))
    results: list[Any] = []

    class Handler(socketserver.BaseRequestHandler):
        def handle(self) -> None:
            self.request.settimeout(3)
            try:
                if self.request.recv(4096):
                    hello.set()  # 收到 ClientHello，故障点是真实 TLS 握手等待。
                    release.wait(3)
            except OSError:
                pass

    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    def run() -> None:
        try:
            results.append(client.streamChat({
                "baseUrl": f"https://127.0.0.1:{server.server_address[1]}",
                "apiKey": "synthetic", "model": "deepseek-v4-pro", "messages": [],
                "idleTimeoutMs": 150 if trigger == "idle" else 10000, "maxRetries": 0,
            }, context=ResilientContext(cancel=cancel.is_set), env={}))
        except Exception as error:
            results.append(error)
        finally:
            done.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert hello.wait(1), "服务端应先收到真实 ClientHello"
        if trigger == "cancel":
            cancel.set()
        assert done.wait(1), "TLS 握手停顿必须可被取消或 idle 中止"
        if trigger == "cancel":
            assert results[0].status == "partial"
        else:
            assert isinstance(results[0], IdleTimeoutError)
    finally:
        release.set()
        worker.join(4)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


def test_real_fallback_timeout_interrupts_stalled_response_headers() -> None:
    release, fallback_started, done = (threading.Event() for _ in range(3))
    results: list[Any] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if not fallback_started.is_set():
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                fallback_started.set()
            else:
                release.wait(3)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    def run() -> None:
        try:
            results.append(streamChatResilient({
                "baseUrl": f"http://127.0.0.1:{server.server_port}",
                "apiKey": "synthetic", "model": "deepseek-v4-pro", "messages": [],
                "idleTimeoutMs": 100, "maxRetries": 0,
            }, env={}))
        finally:
            done.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert fallback_started.wait(1)
        assert done.wait(1), "非流式兜底响应头停滞也必须被超时中止"
        assert results[0].status == "failed"
        assert results[0].fallback_used
    finally:
        release.set()
        worker.join(4)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


def test_cancel_during_dns_resolution_returns_without_waiting_for_dns(tmp_path) -> None:
    cancel, done = (threading.Event() for _ in range(2))
    results: list[Any] = []
    helpers: list[Any] = []
    marker = tmp_path / "inside-helper"
    helper = tmp_path / "hanging_resolver.py"
    helper.write_text(
        "import pathlib,sys,threading\n"
        "sys.stdin.read()\n"
        "pathlib.Path(sys.argv[1]).write_text('started')\n"
        "threading.Event().wait()\n", encoding="utf-8",
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self.send_response(200)
            self.end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    def run() -> None:
        try:
            results.append(streamChatResilient({
                "baseUrl": f"http://localhost:{server.server_port}",
                "apiKey": "synthetic", "model": "deepseek-v4-pro", "messages": [],
            }, context=ResilientContext(
                cancel=cancel.is_set,
                resolver_command=(sys.executable, "-I", str(helper), str(marker)),
                on_resolver_start=helpers.append,
            ), env={}))
        finally:
            done.set()

    worker = threading.Thread(target=run)
    worker.start()
    try:
        deadline = time.monotonic() + 3
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists(), f"合成 helper 必须实际进入阻塞，当前结果：{results!r}"
        cancel.set()
        assert done.wait(1), "DNS 阶段取消不应依赖解析返回"
        assert results[0].cancelled
        assert len(helpers) == 1 and helpers[0].poll() is not None
    finally:
        worker.join(4)
        server.shutdown()
        server.server_close()
        server_thread.join()
        assert not worker.is_alive()


def test_default_helper_resolves_localhost_and_exits() -> None:
    helpers: list[Any] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            data = b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = streamChatResilient({
            "baseUrl": f"http://localhost:{server.server_port}", "apiKey": "synthetic",
            "model": "deepseek-v4-pro", "messages": [], "idleTimeoutMs": 3000,
            "maxRetries": 0,
        }, context=ResilientContext(on_resolver_start=helpers.append), env={})
        assert result.status == "complete", repr(result)
        assert result.message["content"] == "ok"
        assert len(helpers) == 1 and helpers[0].poll() == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_dns_timeout_stops_each_owned_helper_and_uses_isolated_environment(
    tmp_path, monkeypatch,
) -> None:
    helpers: list[Any] = []
    helper = tmp_path / "timeout_resolver.py"
    helper.write_text(
        "import os,sys,threading\n"
        "assert 'RUOCUN_TEST_SECRET_SENTINEL' not in os.environ\n"
        "sys.stdin.read()\n"
        "threading.Event().wait()\n", encoding="utf-8",
    )
    monkeypatch.setenv("RUOCUN_TEST_SECRET_SENTINEL", "synthetic-not-a-real-secret")
    start = time.monotonic()
    result = streamChatResilient({
        "baseUrl": "http://localhost:9", "apiKey": "synthetic",
        "model": "deepseek-v4-pro", "messages": [], "idleTimeoutMs": 250,
        "maxRetries": 0,
    }, context=ResilientContext(
        resolver_command=(sys.executable, "-I", str(helper)),
        on_resolver_start=helpers.append,
    ), env={})
    assert time.monotonic() - start < 3
    assert result.status == "failed" and result.watchdog_triggered and result.fallback_used
    assert len(helpers) == 2 and all(p.poll() is not None for p in helpers)


def test_product_redirect_resolves_each_connection_and_preserves_urllib_method(tmp_path) -> None:
    methods: list[str] = []
    helpers: list[Any] = []
    helper = tmp_path / "local_resolver.py"
    helper.write_text(
        "import json,socket,sys\n"
        "p=json.loads(sys.stdin.read())['port']\n"
        "print(json.dumps({'addresses':socket.getaddrinfo('127.0.0.1',p,0,socket.SOCK_STREAM)}))\n",
        encoding="utf-8",
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            methods.append("POST")
            self.send_response(302)
            self.send_header("Location", f"http://localhost:{self.server.server_port}/next")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self) -> None:
            methods.append("GET")
            payload = b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
            self.send_response(200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = streamChatResilient({
            "baseUrl": f"http://localhost:{server.server_port}", "apiKey": "synthetic",
            "model": "deepseek-v4-pro", "messages": [], "idleTimeoutMs": 3000,
            "maxRetries": 0,
        }, context=ResilientContext(on_resolver_start=helpers.append,
                                    resolver_command=(sys.executable, "-I", str(helper))), env={})
        assert result.status == "complete", repr((result, methods, [p.poll() for p in helpers]))
        assert result.message["content"] == "ok"
        assert methods == ["POST", "GET"]
        assert len(helpers) == 2 and all(p.poll() == 0 for p in helpers)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_product_proxy_connect_tls_sni_and_certificate_failures(monkeypatch) -> None:
    # 使用 CPython 自带的公开 localhost 测试证书，缺失时不伪装成 TLS 已验证。
    cert = Path(sys.base_prefix) / "Lib" / "test" / "certdata" / "keycert.pem"
    if not cert.is_file():
        pytest.skip("CPython synthetic TLS fixture unavailable")
    sni_names: list[str | None] = []
    targets: list[str] = []
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert)
    server_context.set_servername_callback(lambda _sock, name, _ctx: sni_names.append(name))

    class Proxy(BaseHTTPRequestHandler):
        def do_CONNECT(self) -> None:
            targets.append(self.path)
            self.send_response(200, "Connection Established")
            self.end_headers()
            try:
                with server_context.wrap_socket(self.connection, server_side=True) as secure:
                    secure.settimeout(3)
                    received = b""
                    while b"\r\n\r\n" not in received:
                        part = secure.recv(4096)
                        if not part:
                            return
                        received += part
                    payload = b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\ndata: [DONE]\n\n'
                    secure.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: "
                                   + str(len(payload)).encode() + b"\r\n\r\n" + payload)
            except (ssl.SSLError, OSError):
                pass

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    monkeypatch.setattr(urllib.request, "getproxies", lambda: {
        "https": f"http://localhost:{server.server_port}",
    })
    monkeypatch.setattr(urllib.request, "proxy_bypass", lambda _host: False)
    create_default = ssl._create_default_https_context
    helpers: list[Any] = []
    try:
        monkeypatch.setattr(ssl, "_create_default_https_context",
                            lambda: ssl.create_default_context(cafile=str(cert)))
        context = ResilientContext(on_resolver_start=helpers.append)
        opts: Any = {"baseUrl": "https://localhost", "apiKey": "synthetic",
                     "model": "deepseek-v4-pro", "messages": [], "idleTimeoutMs": 3000}
        result = streamChatResilient(opts, context=context, env={})
        assert result.status == "complete" and result.message["content"] == "ok"
        assert targets[-1] == "localhost:443" and sni_names[-1] == "localhost"
        # 并行工程检查下首轮可能触发合法重试；每次stream尝试各持有一个DNS helper。
        assert result.attempts and all(attempt.kind == "stream" for attempt in result.attempts)
        assert len(helpers) == len(result.attempts) and helpers[-1].poll() == 0
        assert all(process.poll() is not None for process in helpers)

        opts["baseUrl"] = "https://wrong.synthetic.test"
        wrong_name = streamChatResilient(opts, context=context, env={})
        assert wrong_name.status == "failed" and sni_names[-1] == "wrong.synthetic.test"
        assert "CERTIFICATE_VERIFY_FAILED" in (wrong_name.error or "")

        monkeypatch.setattr(ssl, "_create_default_https_context", create_default)
        opts["baseUrl"] = "https://localhost"
        untrusted = streamChatResilient(opts, context=context, env={})
        assert untrusted.status == "failed"
        assert "CERTIFICATE_VERIFY_FAILED" in (untrusted.error or "")
        assert all(p.poll() is not None for p in helpers)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
