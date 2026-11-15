"""解析权限规则写法，并依次匹配拒绝、询问和允许规则。

对 Bash 逐个检查子命令，任何一项命中拒绝都能拦住整条调用。已知语法过于复杂时交给人工审批。
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict
from urllib.parse import urlsplit

from .bash.types import BashParser
from .bash_preprocess import (
    extractOutputRedirections,
    isCompoundCommand,
    stripAllLeadingEnvVars,
    stripSafeWrappers,
)

Decision = Literal["allow", "ask", "deny"]


class ParsedRule(TypedDict, total=False):
    tool: str
    specifier: str


class CallIdentity(TypedDict):
    ccTool: str
    value: str


class RuleSets(TypedDict):
    allow: list[str]
    ask: list[str]
    deny: list[str]


def parseRule(value: str) -> ParsedRule:
    value = value.strip()
    opening = value.find("(")
    if opening == -1 or not value.endswith(")"):
        return {"tool": value}
    return {"tool": value[:opening], "specifier": value[opening + 1:-1]}


def _utf16Units(value: str) -> str:
    encoded = value.encode("utf-16-le", errors="surrogatepass")
    return "".join(chr(encoded[index] | encoded[index + 1] << 8) for index in range(0, len(encoded), 2))


def _glob(pattern: str) -> re.Pattern[str]:
    pattern = _utf16Units(pattern)
    pieces: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if pattern[index:index + 2] == "**":
            pieces.append(".*")
            index += 2
        else:
            pieces.append("[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char))
            index += 1
    return re.compile("^" + "".join(pieces) + "$")


def _matchBash(specifier: str, command: str) -> bool:
    command = command.strip()
    if specifier == "*":
        return True
    if specifier.endswith(":*"):
        prefix = specifier[:-2]
        return (command == prefix or command.startswith(prefix + " ")
                or command == "xargs " + prefix or command.startswith("xargs " + prefix + " "))
    if "*" in specifier:
        return _glob(specifier).search(_utf16Units(command)) is not None
    return command == specifier.strip()


def ruleMatches(rule: ParsedRule, identity: CallIdentity) -> bool:
    if rule["tool"] != identity["ccTool"]:
        return False
    if "specifier" not in rule:
        return True
    specifier, value = rule["specifier"], identity["value"]
    if rule["tool"] == "Bash":
        return _matchBash(specifier, value)
    if rule["tool"] == "WebFetch":
        wanted = specifier.removeprefix("domain:")
        try:
            parsed = urlsplit(value)
            host = parsed.hostname or ("" if parsed.scheme else value)
        except ValueError:
            host = value
        return host == wanted or host.endswith("." + wanted)
    if rule["tool"] in {"Read", "Edit", "Write", "LS", "Glob", "Grep"}:
        pattern = specifier[1:] if specifier.startswith("//") else specifier
        regexp = _glob(pattern)
        return regexp.search(_utf16Units(value)) is not None or (
            "/" not in pattern and regexp.search(_utf16Units(value.rsplit("/", 1)[-1])) is not None
        )
    return _glob(specifier).search(_utf16Units(value)) is not None if "*" in specifier else value == specifier


def splitBashCommands(command: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*(?:&&|\|\||[;\n|])\s*", command) if part.strip()]


def _bashCandidates(command: str, stripAllEnv: bool) -> list[str]:
    command = command.strip()
    withoutRedirect = extractOutputRedirections(command)
    base = [command, withoutRedirect] if withoutRedirect != command else [command]
    result: list[str] = []

    def add(value: str) -> None:
        value = value.strip()
        if value and value not in result:
            result.append(value)

    for value in base:
        add(value)
        add(stripSafeWrappers(value))
        if stripAllEnv:
            previous, current = "", value
            while current != previous:
                previous = current
                current = stripSafeWrappers(stripAllLeadingEnvVars(current))
            add(current)
    return result


def bashRulesMatch(
    rules: list[str], command: str, *, stripAllEnv: bool = False, checkCompound: bool = True,
) -> bool:
    compound = checkCompound and isCompoundCommand(command)
    for rule in map(parseRule, rules):
        if rule["tool"] != "Bash":
            continue
        if "specifier" not in rule:
            return True
        specifier = rule["specifier"]
        for candidate in _bashCandidates(command, stripAllEnv):
            if compound:
                if specifier != "*" and not specifier.endswith(":*") and "*" not in specifier and candidate == specifier.strip():
                    return True
            elif _matchBash(specifier, candidate):
                return True
    return False


def _evaluateBash(rules: RuleSets, command: str, parts: list[str]) -> Decision | None:
    if any(bashRulesMatch(rules["deny"], part, stripAllEnv=True, checkCompound=False) for part in parts):
        return "deny"
    if bashRulesMatch(rules["ask"], command, stripAllEnv=True):
        return "ask"
    sawAsk = sawUnmatched = False
    for part in parts:
        if bashRulesMatch(rules["ask"], part, stripAllEnv=True, checkCompound=False):
            sawAsk = True
        elif not bashRulesMatch(rules["allow"], part, checkCompound=False):
            sawUnmatched = True
    if sawAsk:
        return "ask"
    if bashRulesMatch(rules["allow"], command):
        return "allow"
    return None if sawUnmatched else "allow"


def evaluate(rules: RuleSets, identity: CallIdentity) -> Decision | None:
    if identity["ccTool"] == "Bash":
        return _evaluateBash(rules, identity["value"], splitBashCommands(identity["value"]))
    for decision in ("deny", "ask", "allow"):
        if any(ruleMatches(parseRule(rule), identity) for rule in rules[decision]):
            return decision
    return None


async def evaluateWithAst(
    rules: RuleSets, identity: CallIdentity, *, parseBash: BashParser | None = None,
) -> Decision | None:
    if identity["ccTool"] != "Bash":
        return evaluate(rules, identity)
    if parseBash is None:
        from .bash.bash_ast import parseBashForSecurity
        parseBash = parseBashForSecurity
    command = identity["value"]
    result = await parseBash(command)
    if result["kind"] == "too-complex":
        if bashRulesMatch(rules["deny"], command, stripAllEnv=True, checkCompound=False):
            return "deny"
        return "ask"
    parts = result["subcommands"] if result["kind"] == "simple" else splitBashCommands(command)
    return _evaluateBash(rules, command, parts)
