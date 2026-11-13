"""本次请求的隔离解析子进程；stdin/stdout 为有界 JSON 协议。"""

from __future__ import annotations

import json
import socket
import sys
from typing import Any


def main() -> int:
    try:
        request: Any = json.loads(sys.stdin.read(8193))
        host, port = request["host"], request["port"]
        if not isinstance(host, str) or not isinstance(port, int):
            raise ValueError("invalid resolver request")
        addresses = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        print(json.dumps({"addresses": addresses}))
        return 0
    except socket.gaierror as error:
        print(json.dumps({"error": {"errno": error.errno, "message": str(error)}}))
        return 0
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
