"""Controlled LSP server with fragmented UTF-8 response and coalesced reverse replies."""

import json
import os
import sys
from pathlib import Path

trace = Path(sys.argv[1])
held = None


def log(message):
    with trace.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")


def frame(mid, result):
    data = json.dumps(
        {"jsonrpc": "2.0", "id": mid, "result": result}, ensure_ascii=False
    ).encode("utf-8")
    framed = b"Content-Length: " + str(len(data)).encode("ascii") + b"\r\n\r\n" + data
    log(
        {
            "generated_frame_hex": framed.hex(),
            "content_length_bytes": len(data),
            "json_characters": len(data.decode("utf-8")),
        }
    )
    return framed


log({"pid": os.getpid()})
while True:
    header = b""
    while not header.endswith(b"\r\n\r\n"):
        chunk = sys.stdin.buffer.read(1)
        if not chunk:
            sys.exit(0)
        header += chunk
    length = int(header.decode("ascii").split(":", 1)[1].strip())
    msg = json.loads(sys.stdin.buffer.read(length))
    log(msg)
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params", {})
    if method == "exit":
        log({"stopped": "exit"})
        break
    if mid is None:
        continue
    if method == "initialize":
        data = frame(
            mid,
            {
                "capabilities": {"positionEncoding": "utf-16", "textDocumentSync": 1},
                "serverInfo": {"name": "中文😀"},
            },
        )
        # Split at the middle of an emoji's UTF-8 bytes; OS reads may coalesce.
        split = data.index("😀".encode("utf-8")) + 1
        sys.stdout.buffer.write(data[:split])
        sys.stdout.buffer.flush()
        sys.stdout.buffer.write(data[split:])
        sys.stdout.buffer.flush()
    elif method == "d15/echo":
        current = frame(mid, params["value"])
        if held is None:
            held = current
        else:
            sys.stdout.buffer.write(current + held)
            sys.stdout.buffer.flush()
            held = None
    elif method == "d15/never":
        pass
    else:
        result = (
            None
            if method == "shutdown"
            else [
                {
                    "uri": params["textDocument"]["uri"],
                    "range": {
                        "start": {"line": 0, "character": 4},
                        "end": {"line": 0, "character": 5},
                    },
                }
            ]
        )
        sys.stdout.buffer.write(frame(mid, result))
        sys.stdout.buffer.flush()
