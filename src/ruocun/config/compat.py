"""原生运行环境设置与各加载器使用的可选来源数据。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

Scope = Literal["user", "project", "managed"]


@dataclass(frozen=True)
class CompatibilitySource:
    id: str
    scope: Scope
    resource: str
    path: str
    workspace: str | None = None


@dataclass(frozen=True)
class Compatibility:
    version: int
    sources: tuple[CompatibilitySource, ...]


DEFAULT_COMPATIBILITY = Compatibility(version=1, sources=())


def resolve_env(suffix: str, environ: Mapping[str, str]) -> str | None:
    return environ.get("RUOCUN_" + suffix)


def auto_approve(environ: Mapping[str, str]) -> bool:
    # 非空字符串即真，"0" 也为真。
    value = resolve_env("AUTO_APPROVE", environ)
    return bool(value) if value is not None else False


def trust(environ: Mapping[str, str]) -> bool:
    return resolve_env("TRUST", environ) == "1"


def use_keychain_enabled(environ: Mapping[str, str]) -> bool:
    # 仅 "0"/"off" 关闭，平台后端可用性由凭据端口决定。
    value = resolve_env("USE_KEYCHAIN", environ)
    return value not in ("0", "off") if value is not None else True


def _number_or(value: str | None, default: int) -> int:
    # 冻结 client.ts:104/127/390 Number(process.env.X) || default
    if value is None:
        return default
    try:
        number = int(value)
    except ValueError:
        return default
    return number or default


def max_output_tokens(environ: Mapping[str, str]) -> int:
    return _number_or(resolve_env("MAX_OUTPUT_TOKENS", environ), 128000)


def stream_idle_ms(environ: Mapping[str, str]) -> int:
    return _number_or(resolve_env("STREAM_IDLE_MS", environ), 240000)


def max_continue(environ: Mapping[str, str]) -> int:
    return _number_or(resolve_env("MAX_CONTINUE", environ), 3)


def reasoning_effort(environ: Mapping[str, str]) -> str:
    value = resolve_env("REASONING_EFFORT", environ)
    return value if value else "max"


def third_party(name: str, environ: Mapping[str, str]) -> str | None:
    """第三方标准/协议变量保留原名，不机械改名（D09:148）。"""
    return environ.get(name)
