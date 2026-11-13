"""Independent stdlib peer for frozen resources/prompts/notifications/elicitation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

directory = Path(sys.argv[1])
directory.mkdir(parents=True, exist_ok=True)
revision = 0


def send(value):
    print(json.dumps({"jsonrpc": "2.0", **value}, ensure_ascii=False), flush=True)


def receive():
    value = json.loads(next(sys.stdin))
    with (directory / "wire.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
    return value


while True:
    try:
        message = receive()
    except StopIteration:
        break
    if "id" not in message:
        continue
    method, params = message.get("method"), message.get("params", {})
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "caps-fixture", "version": "1"},
                  "capabilities": {key: {"listChanged": True} for key in ("tools", "resources", "prompts")}}
    elif method == "tools/list":
        names = ("fresh" if revision else "echo", "change", "ask", "four", "five", "late_tool")
        result = {"tools": [{"name": name, "description": "source " + name,
                             "inputSchema": {"type": "object", "properties": {}}} for name in names]}
    elif method == "resources/list":
        result = {"resources": [{"uri": "fixture://readme", "name": "说明"}, {"uri": "fixture://plain", "name": ""}]}
    elif method == "resources/read":
        result = {"contents": [{"uri": params["uri"], "text": "原文"},
                               {"uri": "fixture://binary", "mimeType": "application/octet-stream", "blob": "YWJj"}]}
    elif method == "prompts/list":
        result = {"prompts": [{"name": "template", "description": "说明"}, {"name": "plain"}]}
    elif method == "prompts/get":
        result = {"messages": [{"role": "user", "content": {"type": "text", "text": params.get("arguments", {}).get("word", "空")}},
                               {"role": "assistant", "content": {"type": "image", "data": "YWJj", "mimeType": "image/png"}}]}
    elif method == "tools/call":
        name = params["name"]
        if name == "change":
            revision += 1
            for kind in ("tools", "resources", "prompts"):
                send({"method": f"notifications/{kind}/list_changed"})
            result = {"content": [{"type": "text", "text": "actual change result"}]}
        elif name == "ask":
            send({"id": "ask-1", "method": "elicitation/create", "params": {"message": "合成问题", "requestedSchema": {
                "type": "object", "properties": {"choice": {"type": "string"}}}}})
            answer = receive()
            assert answer["id"] == "ask-1" and "result" in answer
            result = {"content": [{"type": "text", "text": json.dumps(answer["result"], ensure_ascii=False, separators=(",", ":"))}]}
        else:
            result = {"content": [{"type": "text", "text": name}]}
    else:
        send({"id": message["id"], "error": {"code": -32601, "message": "unsupported method"}})
        continue
    send({"id": message["id"], "result": result})
