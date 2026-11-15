"""把环境探测结果整理成可放进模型请求的文本。

先处理代理地址中的凭据，再格式化平台、目录等字段。快速字段可以先显示，较晚拿到的字段由调用方单独投递。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_ENTRY_NAME_MAX_LEN = 80
_TOP_LEVEL_DIR_CAP = 40


def redactProxyCredentials(raw: str) -> str:
    """擦除代理地址中的用户名和密码，保留其余地址信息。"""
    match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*://)?([^/]*@)(.*)$", raw)
    if not match:
        return raw
    return f"{match.group(1) or ''}***@{match.group(3) or ''}"


def formatEnvSnapshot(data: dict[str, Any] | None, is_en: bool) -> str:
    """将已探测的环境字段整理为显示文本。"""
    if not data:
        return ""
    parts: list[str] = []
    toolchain = data.get("toolchain") or []
    if toolchain:
        label = "Available languages/tools" if is_en else "可用语言/工具"
        parts.append(f"{label}: {'; '.join(toolchain)}")
    branch = data.get("gitBranch")
    if branch:
        dirty = data.get("gitDirtyCount") or 0
        if dirty > 0:
            status = (f"{dirty} uncommitted change(s)" if is_en
                      else f"{dirty} 个未提交改动")
        else:
            status = "clean" if is_en else "干净"
        label = "Git branch" if is_en else "Git 分支"
        parts.append(f"{label}: {branch} ({status})")
    network = data.get("network")
    if isinstance(network, dict):
        reachable = network.get("reachable") or {}
        ok = [name for name, value in reachable.items() if value]
        bad = [name for name, value in reachable.items() if not value]
        bits: list[str] = []
        if ok:
            bits.append(f"{'reachable' if is_en else '可访问'} {', '.join(ok)}")
        if bad:
            bits.append(f"{'unreachable' if is_en else '不可访问'} {', '.join(bad)}")
        proxy = network.get("proxy")
        proxy = redactProxyCredentials(proxy) if isinstance(proxy, str) else None
        note = (
            (f" (via proxy {proxy})" if is_en else f"(经代理 {proxy})")
            if proxy else ""
        )
        if bits:
            label = "Network" if is_en else "网络"
            parts.append(f"{label}: {('; ' if is_en else ';').join(bits)}{note}")
    return "- " + "\n- ".join(parts) if parts else ""


def _sanitize_entry_name(name: str) -> str:
    """替换控制字符并限制目录项名称的长度。"""
    flattened = _CONTROL.sub("\ufffd", name)
    if len(flattened) > _ENTRY_NAME_MAX_LEN:
        return flattened[:_ENTRY_NAME_MAX_LEN - 1] + "…"
    return flattened


def probeTopLevelDir(cwd: str | Path) -> list[str] | None:
    """只检查当前目录的直接子项，返回有界的文件列表。"""
    try:
        entries = list(Path(cwd).iterdir())
    except OSError:
        return None
    names = [
        f"{_sanitize_entry_name(entry.name)}/" if entry.is_dir()
        else _sanitize_entry_name(entry.name)
        for entry in entries
        if entry.name != ".git"
    ]
    names.sort(key=lambda name: (not name.endswith("/"), name))
    return names or None


def formatFastEnvFields(
    top_level: list[str] | None, memory: dict[str, Any] | None, is_en: bool,
) -> str:
    parts: list[str] = []
    if top_level:
        capped = top_level[:_TOP_LEVEL_DIR_CAP]
        suffix = (
            (f", ...({len(top_level)} total)" if is_en
             else f",...(共 {len(top_level)} 项)")
            if len(top_level) > _TOP_LEVEL_DIR_CAP else ""
        )
        label = "Top-level entries" if is_en else "顶层目录"
        parts.append(f"{label}: {', '.join(capped)}{suffix}")
    if memory:
        if is_en:
            parts.append(
                f"System memory: {memory['totalGB']} GB total, "
                f"{memory['freeGB']} GB free")
        else:
            parts.append(
                f"系统内存: {memory['totalGB']} GB 总量,"
                f"{memory['freeGB']} GB 可用")
    return "- " + "\n- ".join(parts) if parts else ""


def wrapDelayedEnvNotice(formatted: str, is_en: bool) -> str:
    """给延迟获得的环境探测结果加上独立标记。"""
    if not formatted.strip():
        return ""
    if is_en:
        return (
            '<environment-probe note="tool and platform details collected at startup">'
            f"\n{formatted}\n</environment-probe>"
        )
    return (
        '<环境探测补充 说明="若存启动时检查的环境与工具">'
        f"\n{formatted}\n</环境探测补充>"
    )
