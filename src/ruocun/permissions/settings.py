"""合并各层权限规则和模式，提供原生设置文件的读写入口。

读取时容忍损坏的配置，修改时要求已有文件可以解析，以免覆盖用户原有内容。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

PermissionMode = Literal["default", "auto", "bypassPermissions", "plan"]
RuleKind = Literal["allow", "ask", "deny"]
MODES = {"default", "auto", "bypassPermissions", "plan"}


def _rejectConstant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


class AutoModeRules(TypedDict, total=False):
    allow: list[str]
    deny: list[str]
    environment: list[str]


class PermissionsConfig(TypedDict):
    allow: list[str]
    ask: list[str]
    deny: list[str]
    additionalDirectories: list[str]
    defaultMode: NotRequired[PermissionMode]
    bashClassifier: NotRequired[list[str]]
    autoMode: NotRequired[AutoModeRules]


class CliPermissions(TypedDict):
    config: PermissionsConfig
    rest: list[str]


class SourcedPermissions(TypedDict):
    config: PermissionsConfig
    sources: dict[str, str]


def emptyPermissions() -> PermissionsConfig:
    return {"allow": [], "ask": [], "deny": [], "additionalDirectories": []}


def _arr(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def parseSettings(raw: str) -> PermissionsConfig:
    try:
        obj = json.loads(raw, parse_constant=_rejectConstant)
    except ValueError:
        return emptyPermissions()
    p = obj.get("permissions", {}) if isinstance(obj, dict) else {}
    if not isinstance(p, dict):
        p = {}
    cfg: PermissionsConfig = {
        "allow": _arr(p.get("allow")), "ask": _arr(p.get("ask")),
        "deny": _arr(p.get("deny")), "additionalDirectories": _arr(p.get("additionalDirectories")),
    }
    mode = p.get("defaultMode")
    if isinstance(mode, str) and mode in MODES:
        cfg["defaultMode"] = cast(PermissionMode, mode)
    bc = _arr(p.get("bashClassifier"))
    if bc:
        cfg["bashClassifier"] = bc
    am = p.get("autoMode")
    auto: AutoModeRules = {}
    if isinstance(am, dict):
        for key in ("allow", "deny", "environment"):
            values = _arr(am.get(key))
            if values:
                auto[key] = values
    if bc:
        auto["deny"] = auto.get("deny", []) + bc
    if auto:
        cfg["autoMode"] = auto
    return cfg


def enterpriseSettingsPath(platform: str = sys.platform) -> str:
    if platform == "darwin":
        return "/Library/Application Support/RuoCun/managed-settings.json"
    if platform == "win32":
        return "C:/ProgramData/RuoCun/managed-settings.json"
    return "/etc/ruocun/managed-settings.json"


def extractCliPermissions(args: list[str]) -> CliPermissions:
    config, rest = emptyPermissions(), []
    index = 0
    flags: dict[str, Literal["allow", "deny", "ask", "additionalDirectories"]] = {
        "--allow": "allow", "--deny": "deny", "--ask": "ask", "--add-dir": "additionalDirectories",
    }
    while index < len(args):
        arg = args[index]
        value = args[index + 1] if index + 1 < len(args) else None
        if value == "--api-key":
            value = None  # 认证参数应由凭据配置处理，不纳入权限规则。
        if arg in flags and value is not None:
            config[flags[arg]].append(value)
            index += 2
        elif arg == "--permission-mode" and value is not None:
            if value in MODES:
                config["defaultMode"] = cast(PermissionMode, value)
            index += 2
        else:
            rest.append(arg)
            index += 1
    return {"config": config, "rest": rest}


def mergePermissions(tiers: list[PermissionsConfig]) -> PermissionsConfig:
    out = emptyPermissions()
    for key in ("allow", "ask", "deny", "additionalDirectories"):
        out[key] = list(dict.fromkeys(value for tier in tiers for value in tier[key]))
    for tier in tiers:
        if "defaultMode" in tier:
            out["defaultMode"] = tier["defaultMode"]
    bc = list(dict.fromkeys(value for tier in tiers for value in tier.get("bashClassifier", [])))
    if bc:
        out["bashClassifier"] = bc
    auto: AutoModeRules = {}
    autoKeys: tuple[Literal["allow", "deny", "environment"], ...] = ("allow", "deny", "environment")
    for key in autoKeys:
        values = list(dict.fromkeys(value for tier in tiers for value in tier.get("autoMode", cast(AutoModeRules, {})).get(key, [])))
        if values:
            auto[key] = values
    if auto:
        out["autoMode"] = auto
    return out


def _readForWrite(file: Path) -> dict[str, Any]:
    try:
        raw = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    obj = json.loads(raw, parse_constant=_rejectConstant)
    if not isinstance(obj, dict):
        raise ValueError(f"{file}: 现有设置不是对象，保留原文件")
    return obj


def _write(file: Path, obj: dict[str, Any]) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def appendRuleSync(file: str | Path, rule: str, kind: RuleKind = "allow") -> None:
    path = Path(file)
    obj = _readForWrite(path)
    permissions = obj.setdefault("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError(f"{file}: permissions 不是对象，保留原文件")
    values = permissions.get(kind, [])
    if not isinstance(values, list):
        raise ValueError(f"{file}: permissions.{kind} 不是数组，保留原文件")
    if rule not in values:
        values.append(rule)
    permissions[kind] = values
    _write(path, obj)


async def appendRule(file: str | Path, rule: str, kind: RuleKind = "allow") -> None:
    appendRuleSync(file, rule, kind)


def removeRuleSync(file: str | Path, rule: str, kind: RuleKind = "allow") -> bool:
    path = Path(file)
    if not path.exists():
        return False
    obj = _readForWrite(path)
    permissions = obj.get("permissions", {})
    values = permissions.get(kind, []) if isinstance(permissions, dict) else []
    if not isinstance(values, list) or rule not in values:
        return False
    values.remove(rule)
    _write(path, obj)
    return True


async def removeRule(file: str | Path, rule: str, kind: RuleKind = "allow") -> bool:
    return removeRuleSync(file, rule, kind)


async def loadPermissions(files: list[str | Path]) -> SourcedPermissions:
    tiers: list[PermissionsConfig] = []
    sources: dict[str, str] = {}
    for file in files:
        try:
            raw = Path(file).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        cfg = parseSettings(raw)
        tiers.append(cfg)
        for key in ("allow", "ask", "deny"):
            for rule in cfg[key]:
                sources[f"{key}:{rule}"] = str(file)
    return {"config": mergePermissions(tiers), "sources": sources}
