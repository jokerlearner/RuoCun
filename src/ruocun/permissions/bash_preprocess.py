"""提取 Bash 命令用于规则匹配的文本形式。

检查拒绝时可去掉所有可识别的前置环境赋值，检查允许时仅剥掉安全清单里的赋值和包装命令。
"""

import re

_SAFE_ENV = set("NODE_ENV RUST_BACKTRACE RUST_LOG PYTHONUNBUFFERED PYTHONDONTWRITEBYTECODE GOOS GOARCH CGO_ENABLED GO111MODULE GOEXPERIMENT LANG LC_ALL LC_CTYPE TZ TERM NO_COLOR FORCE_COLOR CI".split())
_ENV_SAFE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=([A-Za-z0-9_./:-]+)[ \t]+")
_ENV_ALL = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(?:'[^']*'|\"[^\"]*\"|[^ \t\n\r$`;|&()<>\\]+)[ \t]+")
_WRAPPERS = [re.compile(pattern) for pattern in (
    r"^time(?:[ \t]+--)?[ \t]+", r"^nohup(?:[ \t]+--)?[ \t]+",
    r"^nice(?:[ \t]+-n[ \t]+-?\d+|[ \t]+-\d+)?(?:[ \t]+--)?[ \t]+",
    r"^stdbuf(?:[ \t]+-[ioe][LN0-9]+)+(?:[ \t]+--)?[ \t]+",
)]


def _comments(command: str) -> str:
    kept = [line for line in command.split("\n") if line.strip() and not line.strip().startswith("#")]
    return "\n".join(kept) if kept else command


def _timeout(command: str) -> str | None:
    if not re.search(r"^timeout[ \t]", command):
        return None
    tokens = re.split(r"\s+", command.strip())
    index = 1
    while index < len(tokens) and tokens[index].startswith("-"):
        if tokens[index] == "--":
            index += 1
            break
        if tokens[index] in {"-k", "-s"} and index + 1 < len(tokens) and not tokens[index + 1].startswith("-"):
            index += 2
        else:
            index += 1
    if index < len(tokens) and re.fullmatch(r"\d+(?:\.\d+)?[smhd]?", tokens[index]):
        index += 1
    if index < len(tokens) and tokens[index] == "--":
        index += 1
    return " ".join(tokens[index:])


def stripSafeWrappers(command: str) -> str:
    previous = ""
    while command != previous:
        previous, command = command, _comments(command)
        match = _ENV_SAFE.match(command)
        if match and match[1] in _SAFE_ENV:
            command = command[match.end():]
    previous = ""
    while command != previous:
        previous, command = command, _comments(command)
        timeout = _timeout(command)
        if timeout is not None:
            command = timeout
            continue
        for wrapper in _WRAPPERS:
            command = wrapper.sub("", command, count=1)
    return command.strip()


def stripAllLeadingEnvVars(command: str) -> str:
    previous = ""
    while command != previous:
        previous, command = command, _comments(command)
        match = _ENV_ALL.match(command)
        if match:
            command = command[match.end():]
    return command.strip()


def extractOutputRedirections(command: str) -> str:
    command = re.sub(r"\s+\d*>{1,2}\s*(?:&\d+|[^\s|;&<>\"'])+", "", command)
    return re.sub(r"\s+&>{1,2}\s*[^\s|;&<>\"']+", "", command).strip()


def isCompoundCommand(command: str) -> bool:
    return re.search(r"\s*(?:&&|\|\||[;\n|])\s*", command) is not None
