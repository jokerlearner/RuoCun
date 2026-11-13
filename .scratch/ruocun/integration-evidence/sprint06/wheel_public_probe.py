"""仓库外纯产品 wheel：公开入口503→fallback，真实localhost解析及helper收尾。"""
import importlib.metadata
import json
from pathlib import Path
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import ruocun
from ruocun.client.client import streamChat
from ruocun.client.resilient import ResilientContext

assert "site-packages" in str(Path(ruocun.__file__).resolve())
assert ".worktrees" not in str(Path(ruocun.__file__).resolve())
assert not importlib.metadata.requires("ruocun")
try:
    importlib.metadata.version("pytest")
except importlib.metadata.PackageNotFoundError:
    pass
else:
    raise AssertionError("wheel-only environment must not contain pytest")
urllib.request.getproxies = lambda: {}
flags, helpers, deltas = [], [], []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        flags.append(request["stream"])
        if request["stream"]:
            self.send_response(503)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b'{"choices":[{"message":{"role":"assistant","content":"wheel-recovered"}}]}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
serving = threading.Thread(target=server.serve_forever, name="sprint06-wheel-server")
serving.start()
try:
    result = streamChat(
        {"baseUrl": f"http://localhost:{server.server_port}", "apiKey": "synthetic",
         "model": "synthetic", "messages": [], "maxRetries": 0, "idleTimeoutMs": 10000},
        env={}, context=ResilientContext(on_resolver_start=helpers.append, on_delta=deltas.append),
    )
    assert result.status == "complete" and result.message["content"] == "wheel-recovered"
    assert flags == [True, False]
    assert deltas == [{"kind": "content", "text": "wheel-recovered"}]
    assert len(helpers) == 2 and all(helper.poll() == 0 for helper in helpers)
finally:
    server.shutdown()
    server.server_close()
    serving.join(4)
    assert not serving.is_alive()
    assert not any(t.name == "ruocun-idle-watchdog" for t in threading.enumerate())
print(json.dumps({"wheel_only": True, "public_fallback": True, "helper_count": len(helpers),
                  "helpers_exited": True, "server_joined": True, "late_delta": False}))
