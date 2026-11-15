"""衔接 Bash 解析器和安全分析，向权限流程提供子命令及分析结果。"""
from __future__ import annotations

from ..rules import splitBashCommands
from .ast import checkSemantics, parseForSecurityFromAst
from .parser import _ParseAborted, jsTrim, parseCommandRaw
from .types import BashParseResult


async def parseBashForSecurity(command: str) -> BashParseResult:
    if not command or not jsTrim(command):
        return {"kind": "simple", "subcommands": []}
    root = await parseCommandRaw(command)
    if root is None:
        return {"kind": "fallback"}
    if isinstance(root, _ParseAborted):
        return {"kind": "too-complex", "reason": "Parser aborted (timeout or resource limit) — possible adversarial input"}
    result = parseForSecurityFromAst(command, root)
    if result["kind"] == "too-complex":
        return {"kind": "too-complex", "reason": result["reason"]}
    if result["kind"] == "parse-unavailable":
        return {"kind": "fallback"}
    semantics = checkSemantics(result["commands"])
    if not semantics["ok"]:
        return {"kind": "too-complex", "reason": semantics["reason"]}
    return {"kind": "simple", "subcommands": [command["text"] for command in result["commands"]]}


def parseBashSubcommandsSync(command: str) -> list[str]:
    return splitBashCommands(command)
