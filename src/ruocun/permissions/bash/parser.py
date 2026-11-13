"""Reference parser.ts (MIT): pure parser wrapper and resource-abort distinction."""
from __future__ import annotations

from typing import TypedDict

from .types import Node


class _ParseAborted:
    pass


PARSE_ABORTED = _ParseAborted()
_DECLARATIONS = {"export", "declare", "typeset", "readonly", "local", "unset", "unsetenv"}
_COMMANDS = {"command", "declaration_command"}
_JS_WHITESPACE = "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"


def jsTrim(value: str) -> str:
    return value.strip(_JS_WHITESPACE)


class ParsedCommandData(TypedDict):
    rootNode: Node
    envVars: list[str]
    commandNode: Node | None
    originalCommand: str


async def ensureInitialized() -> None:
    return None


def _tooLong(command: str) -> bool:
    return len(command.encode("utf-16-le", errors="surrogatepass")) // 2 > 10000


async def parseCommandRaw(command: str) -> Node | None | _ParseAborted:
    if not command or _tooLong(command):
        return None
    from .bash_parser import parseSource
    try:
        result = parseSource(command)
        return PARSE_ABORTED if result is None else result
    except Exception:
        return PARSE_ABORTED


async def parseCommand(command: str) -> ParsedCommandData | None:
    if not command or _tooLong(command):
        return None
    from .bash_parser import parseSource
    try:
        root = parseSource(command)
        if root is None:
            return None
        node = _findCommandNode(root, None)
        envVars: list[str] = []
        if node is not None and node.type == "command":
            for child in node.children:
                if child.type == "variable_assignment":
                    envVars.append(child.text)
                elif child.type in ("command_name", "word"):
                    break
        return {"rootNode": root, "envVars": envVars, "commandNode": node, "originalCommand": command}
    except Exception:
        return None


def _findCommandNode(node: Node, parent: Node | None) -> Node | None:
    if node.type in _COMMANDS:
        return node
    if node.type == "variable_assignment" and parent:
        return next((child for child in parent.children if child.type in _COMMANDS and child.startIndex > node.startIndex), None)
    if node.type == "redirected_statement":
        return next((child for child in node.children if child.type in _COMMANDS), None)
    for child in node.children:
        result = _findCommandNode(child, node)
        if result is not None:
            return result
    return None


def extractCommandArguments(commandNode: Node) -> list[str]:
    if commandNode.type == "declaration_command":
        first = commandNode.children[0] if commandNode.children else None
        return [first.text] if first and first.text in _DECLARATIONS else []
    args: list[str] = []
    foundCommandName = False
    for child in commandNode.children:
        if child.type == "variable_assignment":
            continue
        if child.type == "command_name" or (not foundCommandName and child.type == "word"):
            foundCommandName = True
            args.append(child.text)
            continue
        if child.type in ("word", "string", "raw_string", "number"):
            text = child.text
            args.append(text[1:-1] if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"') else text)
        elif child.type in ("command_substitution", "process_substitution"):
            break
    return args
