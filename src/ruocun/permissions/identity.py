"""冻结identity.ts：工具身份及remember规则（MIT）。"""

import json
import re
from urllib.parse import urlsplit

from .bash_preprocess import stripSafeWrappers
from .rules import CallIdentity

_MAP = {"Bash": ("Bash", "command"), "Read": ("Read", "path"), "Edit": ("Edit", "path"),
        "NotebookEdit": ("Edit", "path"), "Write": ("Write", "path"), "ListDir": ("LS", "path"),
        "Grep": ("Grep", "path"), "Glob": ("Glob", "glob"), "WebFetch": ("WebFetch", "url"),
        "WebSearch": ("WebSearch", "query"), "ArchiveRead": ("ArchiveRead", "id")}


def _rejectConstant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def toCcIdentity(toolName: str, argsJson: str) -> CallIdentity | None:
    if toolName.startswith("mcp__"):
        return {"ccTool": toolName, "value": ""}
    if toolName not in _MAP:
        return None
    tool, argument = _MAP[toolName]
    try:
        args = json.loads(argsJson, parse_constant=_rejectConstant)
    except ValueError:
        args = {}
    value = args.get(argument) if isinstance(args, dict) else None
    return {"ccTool": tool, "value": value if isinstance(value, str) else ""}


def rememberRule(toolName: str, argsJson: str) -> str | None:
    identity = toCcIdentity(toolName, argsJson)
    if identity is None:
        return None
    tool, value = identity["ccTool"], identity["value"]
    if not value:
        return tool
    if tool == "WebFetch":
        try:
            parsed = urlsplit(value)
            host = parsed.hostname if parsed.scheme and parsed.hostname else value
        except ValueError:
            host = value
        return f"WebFetch(domain:{host})"
    if tool == "WebSearch":
        return "WebSearch"
    if tool == "Bash":
        stripped = stripSafeWrappers(value)
        if stripped and len(stripped.encode("utf-16-le", errors="surrogatepass")) // 2 <= 200 and not re.search(r"[|&;<>`\n]|\$\(", stripped):
            tokens = re.split(r"\s+", stripped)
            program = tokens[0]
            sub = " " + tokens[1] if len(tokens) > 1 and not tokens[1].startswith("-") else ""
            return f"Bash({program}{sub}:*)"
        return f"Bash({value})"
    return f"{tool}({value})"
