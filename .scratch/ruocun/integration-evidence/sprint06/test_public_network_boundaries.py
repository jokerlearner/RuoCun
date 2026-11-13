"""独立验证公开入口的 helper 取消和非流式响应体停滞。仅本机合成输入。"""
import json
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ruocun.client.client import streamChat
from ruocun.client.resilient import IdleTimeoutError, ResilientContext


def test_public_dns_cancel_stops_owned_helper(tmp_path, monkeypatch):
    monkeypatch.setattr(urllib.request, "getproxies", lambda: {})
    cancel, done = threading.Event(), threading.Event()
    marker = tmp_path / "started"
    script = tmp_path / "synthetic_resolver.py"
    script.write_text("import pathlib,sys,threading\nsys.stdin.read()\n"
                      "pathlib.Path(sys.argv[1]).write_text('synthetic')\nthreading.Event().wait()\n")
    helpers, results, deltas = [], [], []

    def request():
        try:
            results.append(streamChat(
                {"baseUrl": "http://localhost:9", "apiKey": "synthetic", "model": "synthetic",
                 "messages": [], "maxRetries": 0}, env={},
                context=ResilientContext(cancel=cancel.is_set, on_delta=deltas.append,
                    resolver_command=(sys.executable, "-I", str(script), str(marker)),
                    on_resolver_start=helpers.append),
            ))
        except Exception as exc:
            results.append(exc)
        finally:
            done.set()

    worker = threading.Thread(target=request, name="sprint06-public-dns")
    worker.start()
    try:
        deadline = time.monotonic() + 3
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists(), "owned helper must actually enter the blocking resolver"
        cancel.set()
        assert done.wait(0.8), "public DNS cancellation must not await resolver completion"
        assert len(helpers) == 1 and helpers[0].poll() is not None
        assert results[0].status == "partial" and results[0].message["content"] is None
        assert deltas == []
    finally:
        cancel.set()
        for helper in helpers:
            if helper.poll() is None:
                helper.terminate()
                helper.communicate(timeout=3)
        worker.join(4)
        assert not worker.is_alive()


@pytest.mark.parametrize("trigger", ["cancel", "idle"])
def test_public_fallback_stalled_body_stops_without_late_delta(trigger, monkeypatch):
    monkeypatch.setattr(urllib.request, "getproxies", lambda: {})
    cancel, body_started, release, done = (threading.Event() for _ in range(4))
    requests, results, deltas = [], [], []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(body["stream"])
            if body["stream"]:
                self.send_response(503)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Length", "9999")
            self.end_headers()
            self.wfile.write(b'{"choices":[')
            self.wfile.flush()
            body_started.set()
            release.wait(4)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    serving = threading.Thread(target=server.serve_forever, name="sprint06-fallback-server")
    serving.start()

    def request():
        try:
            results.append(streamChat(
                {"baseUrl": f"http://127.0.0.1:{server.server_port}", "apiKey": "synthetic",
                 "model": "synthetic", "messages": [], "maxRetries": 0,
                 "idleTimeoutMs": 150 if trigger == "idle" else 10000}, env={},
                context=ResilientContext(cancel=cancel.is_set, on_delta=deltas.append),
            ))
        except Exception as exc:
            results.append(exc)
        finally:
            done.set()

    worker = threading.Thread(target=request, name="sprint06-fallback-request")
    worker.start()
    try:
        assert body_started.wait(2), "fallback must receive actual partial response bytes"
        if trigger == "cancel":
            cancel.set()
        assert done.wait(0.8), "fallback response body must be interruptible"
        if trigger == "cancel":
            assert results[0].status == "partial" and results[0].message["content"] is None
        else:
            assert isinstance(results[0], IdleTimeoutError)
        assert requests == [True, False]
        assert deltas == []
    finally:
        cancel.set()
        release.set()
        worker.join(4)
        server.shutdown()
        server.server_close()
        serving.join(4)
        assert not worker.is_alive() and not serving.is_alive()
        assert deltas == []
