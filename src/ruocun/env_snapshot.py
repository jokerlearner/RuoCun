"""环境探测纯函数（来源冻结 ``src/env_snapshot.ts``，MIT）。

保留来源的格式化、代理凭据脱敏、文件名清洗、顶层目录与内存快照、延迟探测
tag 等纯函数；真实 Windows/Python 运行时探测命令由平台端口按 R-05 替换，
本模块不 spawn 外部进程、不读真实用户状态、不发起网络探测。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_ENTRY_NAME_MAX_LEN = 80
_TOP_LEVEL_DIR_CAP = 40


def redactProxyCredentials(raw: str) -> str:
    """只抹 userinfo，保留 scheme/host/port；幂等（env_snapshot.ts:68-72）。"""
    match = re.match(r"^([a-zA-Z][a-zA-Z0-9+.-]*://)?([^/]*@)(.*)$", raw)
    if not match:
        return raw
    return f"{match.group(1) or ''}***@{match.group(3) or ''}"


def formatEnvSnapshot(data: dict[str, Any] | None, is_en: bool) -> str:
    """纯格式化，不做 I/O（env_snapshot.ts:163-196）。"""
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
    """C0/C1 控制字符压成 U+FFFD，单条名字限长（env_snapshot.ts:205-211）。"""
    flattened = _CONTROL.sub("\ufffd", name)
    if len(flattened) > _ENTRY_NAME_MAX_LEN:
        return flattened[:_ENTRY_NAME_MAX_LEN - 1] + "…"
    return flattened


def probeTopLevelDir(cwd: str | Path) -> list[str] | None:
    """只列 cwd 直接子项（不递归），排除 .git；目录优先、字母序。"""
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
    """慢字段补投递时包一层 tag，措辞中性不暗示迟到（env_snapshot.ts:285-290）。"""
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
