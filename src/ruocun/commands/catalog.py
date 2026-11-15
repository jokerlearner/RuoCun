"""维护斜杠命令的名称和别名，按大小写识别命令名。

解析器只切分命令和参数。入口根据解析结果选择处理器、权限模式和会话状态。
"""

from __future__ import annotations

import re

# 旧名称清单仍记录 plugin，公开清单在下方将其排除。
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

# 按 ECMAScript 的空白字符切分，避免 Python 将额外控制字符当成分隔符。
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
