"""Independent frozen MCP stdio fixture; no server SDK or model calls."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

directory = Path(sys.argv[1])
directory.mkdir(parents=True, exist_ok=True)
(directory / "pid").write_text(str(os.getpid()), encoding="ascii")
schema = {"$schema": "http://json-schema.org/draft-07/schema#", "type": "object",
          "properties": {"msg": {"type": ["string", "null"], "description": "原样字段"}},
          "additionalProperties": True, "required": []}


def record(value):
    with (directory / "wire.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")


record({"pid": os.getpid(), "cwd": os.getcwd(), "sentinel": os.environ.get("SYNTHETIC_PARENT"),
        "configured": os.environ.get("SYNTHETIC_SERVER"), "arguments": sys.argv[2:]})
try:
    for line in sys.stdin.buffer:
        message = json.loads(line)
        record({"in": message})
        method = message.get("method")
        if "id" not in message:
            continue
        if method == "initialize":
            result = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "independent-fixture", "version": "1"},
                      "capabilities": {"tools": {}}}
        elif method == "tools/list":
            result = {"tools": [{"name": name, "description": "合成 " + name, "inputSchema": schema,
                                 "annotations": {"readOnlyHint": True}} for name in ("echo", "reject", "crash")]}
        elif method == "tools/call":
            name = message["params"]["name"]
            if name == "crash":
                count_file = directory / "effects"
                count = int(count_file.read_text()) + 1 if count_file.exists() else 1
                count_file.write_text(str(count), encoding="ascii")
                os._exit(17)
            if name == "reject":
                print(json.dumps({"jsonrpc": "2.0", "id": message["id"],
                                  "error": {"code": -32000, "message": "synthetic tool rejection"}}), flush=True)
                continue
            args = message["params"].get("arguments", {})
            result = {"content": [{"type": "text", "text": json.dumps(args, ensure_ascii=False, separators=(",", ":"))},
                                  {"type": "resource_link", "uri": "fixture://plain", "name": "fixture", "custom": None}],
                      "isError": True, "structuredContent": {"must-not-show": "ignored"}}
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": message["id"],
                              "error": {"code": -32601, "message": "method not supported"}}), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}, ensure_ascii=False), flush=True)
finally:
    record({"closed": "stdin-eof"})
