"""Frozen commands/index/App routing names; CMD inventory preserves excluded provenance.

Names are case-sensitive. This module only recognizes lexical command form;
dispatch, permission changes and pause/settled belong to the composition root.
"""

from __future__ import annotations

import re

# Fixed 52 CMD-* records, including source aliases and the excluded plugin record.
COMMAND_NAMES = (
    "model", "plan", "clear", "compact", "cost", "lang", "help", "exit", "quit", "skills",
    "context", "context-window", "tasks", "mcp", "diff", "doctor", "memory", "permissions",
    "session", "audit", "resume", "branch", "rename", "rewind", "export", "Config", "effort",
    "status", "plugin", "hooks", "agents", "files", "copy", "btw", "account", "accounts",
    "bypass", "yolo", "mode", "goal", "task", "coordinator", "restore", "recovery", "simplify",
    "remember", "review", "init", "batch", "skillify", "theme", "loop", "archive",
)
PUBLIC_COMMAND_NAMES = tuple(name for name in COMMAND_NAMES if name != "plugin")
COMMAND_ALIASES = {"accounts": "account", "yolo": "bypass", "task": "goal", "quit": "exit"}

# ECMAScript trim / \s, rather than Python's extra U+001C..001F whitespace.
_JS_WHITESPACE = "\t\n\v\f\r \u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
_SPACE = re.compile("[" + _JS_WHITESPACE + "]+")
_NAME = re.compile(r"[a-zA-Z0-9:_-]+")


def parseSlashCommand(text: str) -> tuple[str, str] | None:
    trimmed = text.strip(_JS_WHITESPACE)
    if not trimmed.startswith("/"):
        return None
    parts = _SPACE.split(trimmed[1:])
    name = parts[0]
    if _NAME.fullmatch(name) is None:
        return None
    return name, " ".join(parts[1:])
