"""读取原生账户配置，并将账户变更保存为 v2 格式。

读取可以给缺失的配置提供空结构。写入前则单独检查磁盘上已有的数据，避免覆盖不支持的版本或损坏的文件。
"""

from __future__ import annotations

import json
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
)
from .native_json import readNativeObjectForWrite as readProfilesForWrite
from .profiles import Profile, ProfilesConfig, migrateConfig


class UnsupportedProfilesError(ValueError):
    """配置使用了当前无法安全读取或改写的账户格式。"""


def _check_account_format(raw: object) -> None:
    if isinstance(raw, dict) and "version" in raw:
        version = raw["version"]
        if isinstance(version, bool) or version not in (1, 2):
            raise UnsupportedProfilesError("账户配置版本不受支持，已保留原文件。")
        if version == 2 and (
            not isinstance(raw.get("profiles"), dict)
            or not isinstance(raw.get("activeProfile"), str)
        ):
            raise UnsupportedProfilesError("账户配置结构不完整，已保留原文件。")


def loadProfiles(file: str | Path) -> ProfilesConfig:
    """读取原生账户配置，缺失或为空时返回空配置。"""
    try:
        raw: Any = json.loads(Path(file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return migrateConfig(None)
    _check_account_format(raw)
    return migrateConfig(raw)


def saveProfiles(file: str | Path, cfg: ProfilesConfig) -> None:
    """将账户配置保存为 v2，保留传入的扩展字段。"""
    path = Path(file).absolute()
    if sys.platform == "win32":
        path.parent.parent.mkdir(parents=True, exist_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    with PrivateDirectory(path.parent) if sys.platform == "win32" else nullcontext():
        _save_profiles(path, cfg)


def readAccountProfilesForWrite(path: Path) -> dict[str, Any]:
    existing = readProfilesForWrite(path)
    _check_account_format(existing)
    return existing


def _save_profiles(path: Path, cfg: ProfilesConfig) -> None:
    existing = readAccountProfilesForWrite(path)
    # 让传入账户配置覆盖同名字段，保留调用方未涉及的扩展字段。
    merged: dict[str, Any] = {**existing, **cfg}
    merged.pop("apiKey", None)
    merged["version"] = cfg.get("version", 2)
    merged["activeProfile"] = cfg.get("activeProfile", "default")
    merged["profiles"] = cfg.get("profiles", {})
    if "onboardingComplete" in cfg:
        merged["onboardingComplete"] = cfg["onboardingComplete"]
    else:
        merged.pop("onboardingComplete", None)
    if sys.platform == "win32":
        atomic_publish(path, json.dumps(merged, ensure_ascii=False, indent=2).encode("utf-8"))
        return
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass  # 部分文件系统不支持调整权限，继续使用已写入的配置。


def addProfile(cfg: ProfilesConfig, name: str, profile: Profile) -> ProfilesConfig:
    profiles = cfg.get("profiles")
    current: dict[str, Any] = profiles if isinstance(profiles, dict) else {}
    if name in current:
        raise ValueError(f"账户已存在:{name}(先 /account rm {name} 再新建)")
    return {
        **cfg,
        "activeProfile": name,
        "profiles": {**current, name: dict(profile)},
    }


def setActive(cfg: ProfilesConfig, name: str) -> ProfilesConfig:
    profiles = cfg.get("profiles")
    current: dict[str, Any] = profiles if isinstance(profiles, dict) else {}
    if name not in current:
        raise ValueError(f"无此 profile:{name}")
    return {**cfg, "activeProfile": name}


def removeProfile(cfg: ProfilesConfig, name: str) -> ProfilesConfig:
    profiles = cfg.get("profiles")
    current: dict[str, Any] = dict(profiles) if isinstance(profiles, dict) else {}
    current.pop(name, None)
    active = cfg.get("activeProfile", "default")
    if active == name:
        active = next(iter(current), "default")
    return {**cfg, "activeProfile": active, "profiles": current}
