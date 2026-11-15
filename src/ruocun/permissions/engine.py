"""结合权限规则、操作风险和当前模式决定允许、拒绝或询问。

明确的拒绝优先。Bash 异步入口可借助语法树逐项匹配，单个工具的附加权限由审批层核对。
"""
from __future__ import annotations

import json
import re
from typing import TypedDict

from .bash.types import BashParser
from .bash_safety import isDangerousCommand, isReadOnlyShellCommand
from .dangerous_patterns import isDangerousBashPermission
from .identity import toCcIdentity
from .rules import Decision, evaluate, evaluateWithAst, parseRule, ruleMatches
from .settings import PermissionMode, PermissionsConfig


class DecideParams(TypedDict):
    toolName: str
    argsJson: str
    capability: str
    mode: PermissionMode
    rules: PermissionsConfig


_SECRET = re.compile(r"\.ssh/|id_rsa|id_ed25519|id_ecdsa|authorized_keys|\.aws/|\.npmrc|\.netrc|credentials|\.(?:dao|ruocun)/config\.json|/etc/(shadow|gshadow|ssl/private|ssh/ssh_host_\w+_key)\b", re.ASCII)
_WRITE_SENSITIVE = re.compile(r"\.gitconfig|\.git/|\.bashrc|\.zshrc|\.bash_profile|\.zprofile|/etc/")
_AUTO_ALLOWLIST = set("Read Grep Glob ListDir TodoWrite AskUserQuestion MemoryRead Skill echo WebSearch WebFetch LSP TaskCreate TaskList TaskGet TaskUpdate TaskOutput TaskStop TaskWait CronList".split())


def _rejectConstant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def isSensitiveCall(toolName: str, argsJson: str) -> bool:
    identity = toCcIdentity(toolName, argsJson)
    return bool(identity and identity["value"] and (_SECRET.search(identity["value"]) or _WRITE_SENSITIVE.search(identity["value"])))


def _extractCommand(argsJson: str) -> str:
    try:
        raw = json.loads(argsJson, parse_constant=_rejectConstant)
        value = raw.get("command", "") if isinstance(raw, dict) else ""
        return value if isinstance(value, str) else ""
    except ValueError:
        return ""


def isDangerousCall(toolName: str, argsJson: str) -> bool:
    return toolName == "Bash" and isDangerousCommand(_extractCommand(argsJson)) is not None


def _isSensitiveTargetCall(p: DecideParams) -> bool:
    identity = toCcIdentity(p["toolName"], p["argsJson"])
    if not identity or not identity["value"]:
        return False
    if _SECRET.search(identity["value"]):
        return True
    if p["capability"] in ("write", "exec") and _WRITE_SENSITIVE.search(identity["value"]):
        return not (p["toolName"] == "Bash" and isReadOnlyShellCommand(_extractCommand(p["argsJson"])))
    return False


def _autoEditAllow(p: DecideParams) -> bool:
    identity = toCcIdentity(p["toolName"], p["argsJson"])
    return bool(identity and identity["ccTool"] in ("Edit", "Write")
                and not isDangerousCall(p["toolName"], p["argsJson"])
                and not _isSensitiveTargetCall(p) and evaluate(p["rules"], identity) != "ask")


def _base(p: DecideParams, ruleDec: Decision | None, *, ast: bool = False) -> Decision:
    if ruleDec == "deny":
        return "deny"
    if ruleDec != "allow" and p["mode"] != "plan" and isDangerousCall(p["toolName"], p["argsJson"]):
        return "ask"
    if p["mode"] == "bypassPermissions":
        return "allow"
    if ruleDec != "allow" and p["mode"] != "plan" and _isSensitiveTargetCall(p):
        return "ask"
    if ruleDec == "ask":
        return "ask"
    if ruleDec == "allow":
        # 自动模式下，同步 Bash 路径会把过宽的允许规则降为人工确认。
        # 异步语法树路径使用解析后的规则结果，此处分支直接返回允许。
        identity = toCcIdentity(p["toolName"], p["argsJson"])
        if not ast and p["mode"] == "auto" and identity and identity["ccTool"] == "Bash":
            hit = next((parseRule(rule) for rule in p["rules"]["allow"] if ruleMatches(parseRule(rule), identity)), None)
            if hit and isDangerousBashPermission(hit.get("specifier")):
                return "ask"
        return "allow"
    if p["mode"] != "plan" and p["toolName"] == "Bash" and isReadOnlyShellCommand(_extractCommand(p["argsJson"])) and not _isSensitiveTargetCall(p):
        return "allow"
    sideEffecting = p["capability"] in ("write", "exec", "network")
    if p["mode"] == "plan":
        return "deny" if sideEffecting else "allow"
    if p["mode"] == "auto" and sideEffecting:
        if p["toolName"] in _AUTO_ALLOWLIST and not _isSensitiveTargetCall(p):
            return "allow"
        if _autoEditAllow(p):
            return "allow"
        return "ask"
    return "ask" if sideEffecting else "allow"


def decide(p: DecideParams) -> Decision:
    identity = toCcIdentity(p["toolName"], p["argsJson"])
    result = _base(p, evaluate(p["rules"], identity) if identity else None)
    if result == "ask" and p["mode"] == "auto":
        if isDangerousCall(p["toolName"], p["argsJson"]) or _isSensitiveTargetCall(p):
            return "ask"
        if p["toolName"] in _AUTO_ALLOWLIST or _autoEditAllow(p):
            return "allow"
    return result


async def decideAsync(p: DecideParams, *, parseBash: BashParser | None = None) -> Decision:
    if p["toolName"] != "Bash":
        return decide(p)
    identity = toCcIdentity(p["toolName"], p["argsJson"])
    if not identity:
        return decide(p)
    return _base(p, await evaluateWithAst(p["rules"], identity, parseBash=parseBash), ast=True)


def matchesIfClause(ifPattern: str, toolName: str, argsJson: str) -> bool:
    identity = toCcIdentity(toolName, argsJson)
    return bool(identity and ruleMatches(parseRule(ifPattern), identity))
