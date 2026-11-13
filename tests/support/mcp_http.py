"""Independent stdlib MCP HTTP/SSE server for frozen transport semantics."""

from __future__ import annotations

import json
import queue
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


class HttpFixture:
    def __init__(self, *, effect_file=None, diagnostic_secret=""):
        self.wire = []
        self.notifications = queue.Queue()
        self.stop = threading.Event()
        self.sse_closed = threading.Event()
        self.drop_sse = threading.Event()
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_):
                pass

            def body(self, status, payload=None, session=False):
                data = json.dumps(payload).encode() if payload is not None else b""
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                if session:
                    self.send_header("Mcp-Session-Id", "synthetic-session")
                self.end_headers()
                self.wfile.write(data)
                self.wfile.flush()

            def do_GET(self):
                fixture.wire.append({"method": "GET", "path": self.path, "headers": dict(self.headers)})
                if urlsplit(self.path).path != "/sse":
                    self.body(405)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                try:
                    endpoint = "/messages?session_id=fixture" + ("&access_token=" + diagnostic_secret if diagnostic_secret else "")
                    self.wfile.write(("event: endpoint\ndata: " + endpoint + "\n\n").encode())
                    self.wfile.flush()
                    while not fixture.stop.is_set() and not fixture.drop_sse.is_set():
                        try:
                            value = fixture.notifications.get(timeout=.05)
                            data = b"event: message\ndata: " + json.dumps(value).encode() + b"\n\n"
                        except queue.Empty:
                            data = b": synthetic heartbeat\n\n"
                        self.wfile.write(data)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
                finally:
                    fixture.sse_closed.set()
                    self.close_connection = True

            def do_POST(self):
                message = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                fixture.wire.append({"method": "POST", "path": self.path, "headers": dict(self.headers), "body": message})
                if fixture.redirect is not None:
                    self.send_response(307)
                    self.send_header("Location", fixture.redirect)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                if "id" not in message:
                    self.body(202)
                    return
                method = message.get("method")
                if method == "initialize":
                    result = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "fixture", "version": "1"},
                              "capabilities": {"tools": {}}}
                elif method == "tools/list":
                    names = ("echo", "reject", "effect") if effect_file is not None else ("echo",)
                    result = {"tools": [{"name": name, "description": "actual " + name,
                                         "inputSchema": {"type": "object", "properties": {}}} for name in names]}
                elif method == "tools/call":
                    if effect_file is not None and message["params"]["name"] == "effect":
                        count = int(effect_file.read_text()) if effect_file.exists() else 0
                        effect_file.write_text(str(count + 1), encoding="ascii")
                        # The request reached its irreversible effect, but no RPC result follows.
                        self.body(503, {"error": "synthetic lost result"})
                        fixture.drop_sse.set()
                        self.close_connection = True
                        self.connection.shutdown(socket.SHUT_RDWR)
                        return
                    result = {"content": [{"type": "text", "text": "actual:" + message["params"].get("arguments", {}).get("msg", "")}]}
                else:
                    result = {}
                reply = {"jsonrpc": "2.0", "id": message["id"], "result": result}
                if effect_file is not None and method == "tools/call" and message["params"]["name"] == "reject":
                    reply = {"jsonrpc": "2.0", "id": message["id"], "error": {
                        "code": -32000, "message": "synthetic rejected " + diagnostic_secret}}
                if self.path.startswith("/messages"):
                    fixture.notifications.put(reply)
                    self.body(202)
                else:
                    self.body(200, reply, session=method == "initialize")

            def do_DELETE(self):
                fixture.wire.append({"method": "DELETE", "path": self.path, "headers": dict(self.headers)})
                self.body(200)

        self.redirect = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.stop.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)
        assert not self.thread.is_alive()
