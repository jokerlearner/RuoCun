"""规范化抓取 URL 并静态检查主机名或字面 IP，拦截不允许的目标。检查范围止于解析后的 URL，DNS 解析由网络层处理。"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import unquote, urlsplit


def _ipv4(host: str) -> str:
    parts = host.rstrip(".").split(".")
    numbers = []
    if not 1 <= len(parts) <= 4:
        return host
    for part in parts:
        base = 16 if part.lower().startswith("0x") else 8 if len(part) > 1 and part.startswith("0") else 10
        value = part[2:] if base == 16 else part[1:] if base == 8 else part
        try:
            numbers.append(int(value or "0", base))
        except ValueError:
            return host
    if any(number < 0 or number > 255 for number in numbers[:-1]) or not 0 <= numbers[-1] < 256 ** (5 - len(numbers)):
        raise ValueError("invalid IPv4")
    value = sum(number * 256 ** (3 - i) for i, number in enumerate(numbers[:-1])) + numbers[-1]
    return str(ipaddress.IPv4Address(value))


def normalizeHttpUrl(raw: str) -> str:
    value = raw.strip().replace("\t", "").replace("\r", "").replace("\n", "")
    match = re.match(r"^(https?):", value, re.I)
    if match:
        parts = re.split(r"([?#])", value[match.end():], maxsplit=1)
        value = match[1].lower() + "://" + parts[0].replace("\\", "/").lstrip("/") + "".join(parts[1:])
    return value


def blockedUrlReason(raw: str) -> str | None:
    try:
        url = urlsplit(normalizeHttpUrl(raw))
        if not url.scheme:
            return "URL 非法"
        if url.scheme not in {"http", "https"}:
            return f"仅允许 http/https(收到 {url.scheme}:)"
        host = unquote(url.hostname or "", errors="strict").lower()
        _ = url.port
        if not host or any(c.isspace() or ord(c) < 32 for c in host):
            return "URL 非法"
        if ":" in host:
            host = ipaddress.IPv6Address(host).compressed
        else:
            host = _ipv4(host.encode("idna").decode("ascii"))
    except (ValueError, UnicodeError):
        return "URL 非法"
    if host == "localhost" or host.endswith(".localhost"):
        return "禁止访问 localhost"
    if host in {"metadata.google.internal", "169.254.169.254"}:
        return "禁止访问云元数据端点"
    if host in {"0.0.0.0", "::1", "::"}:
        return "禁止访问环回/未指定地址"
    for prefix, reason in (("127.", "环回地址(127/8)"), ("10.", "内网地址(10/8)"),
                           ("192.168.", "内网地址(192.168/16)"), ("169.254.", "链路本地地址(169.254/16)")):
        if host.startswith(prefix):
            return "禁止访问" + reason
    if re.match(r"^172\.(1[6-9]|2\d|3[01])\.", host):
        return "禁止访问内网地址(172.16/12)"
    if re.match(r"^(fc|fd)[0-9a-f]{2}:|^fe80:", host, re.I):
        return "禁止访问内网 IPv6"
    return None
