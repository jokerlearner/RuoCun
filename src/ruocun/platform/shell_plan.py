"""D10 immutable execution snapshot and actual-dialect inspection.

Command strings are kept verbatim. Unknown syntax remains a human decision;
only an actual Bash child is sent to the migrated Bash parser.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import shlex
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from ..permissions.sanitize import hasSuspiciousUnicode
from .process_tree import scrubbed_env

Dialect = Literal["cmd", "bash", "sh", "powershell", "pwsh"]


@dataclass(frozen=True)
class ShellAnalysis:
    known: bool
    commands: tuple[str, ...]
    wrappers: tuple[str, ...] = ()
    reason: str = ""
    bashPayloads: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShellExecutionPlan:
    command: str
    argv: tuple[str, ...]
    commandLine: str | None
    cwd: str
    environment: tuple[tuple[str, str], ...]
    dialect: Dialect
    codec: str
    analysis: ShellAnalysis

    def summary(self) -> str:
        wrappers = "\n".join(self.analysis.wrappers)
        unresolved = "\n实际方言或展开语义未能静态确定，此批准仅限本次。" if not self.analysis.known else ""
        return f"[{self.dialect}] {self.argv[0]}\n$ {self.command}" + (f"\n{wrappers}" if wrappers else "") + unresolved


def _words(text: str) -> list[str] | None:
    words: list[str] = []
    current = ""
    quoted = False
    for char in text:
        if char == '"':
            quoted = not quoted
        elif char.isspace() and not quoted:
            if current:
                words.append(current)
                current = ""
        else:
            current += char
    if quoted:
        return None
    if current:
        words.append(current)
    return words


def _cmdParts(command: str) -> tuple[list[str], bool]:
    parts: list[str] = []
    start, quoted, known = 0, False, not hasSuspiciousUnicode(command) and '\\"' not in command
    for index, char in enumerate(command):
        if char == '"':
            quoted = not quoted
        if char in "%!^":
            known = False
        if not quoted and char in "()<>":
            known = False
        if not quoted and char in "&|\r\n":
            if command[start:index].strip():
                parts.append(command[start:index].strip())
            start = index + 1
    if command[start:].strip():
        parts.append(command[start:].strip())
    return parts, known and not quoted


def _resolve(program: str, cwd: str, env: dict[str, str]) -> Path | None:
    path = Path(program)
    if path.is_absolute():
        return path.resolve() if path.is_file() else None
    # cmd searches the current directory before PATH. Inspect the same first hit.
    directories = [cwd] if "/" in program or "\\" in program else [cwd, *env.get("PATH", "").split(os.pathsep)]
    for directory in directories:
        base = Path(directory) if Path(directory).is_absolute() else Path(cwd) / directory
        for suffix in ([""] if path.suffix else ["", *env.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";")]):
            candidate = base / (program + suffix)
            if candidate.is_file():
                return candidate.resolve()
    return None


_PS_PARSE = r"""$u=New-Object System.Text.UTF8Encoding $false; [Console]::InputEncoding=$u; $s=[Console]::In.ReadToEnd(); $t=$null; $e=$null;
$a=[System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$t,[ref]$e);
$c=@($a.FindAll({param($n) $n -is [System.Management.Automation.Language.CommandAst]},$true));
$d=@($a.FindAll({param($n) $n -is [System.Management.Automation.Language.VariableExpressionAst] -or $n -is [System.Management.Automation.Language.SubExpressionAst] -or $n -is [System.Management.Automation.Language.ScriptBlockExpressionAst] -or $n -is [System.Management.Automation.Language.InvokeMemberExpressionAst] -or $n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true));
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding $false;
@{version=$PSVersionTable.PSVersion.ToString();errors=@($e).Count;dynamic=@($d).Count;commands=@($c|ForEach-Object{@{name=$_.GetCommandName();text=$_.Extent.Text;words=@($_.CommandElements|ForEach-Object{if($_ -is [System.Management.Automation.Language.StringConstantExpressionAst]){$_.Value}else{$null}})}})}|ConvertTo-Json -Compress -Depth 5
"""


def _powershell(command: str, engine: Path, cwd: str, env: dict[str, str], depth: int) -> ShellAnalysis:
    system_engine = Path(env.get("SYSTEMROOT", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    program_files = Path(env.get("PROGRAMFILES", env.get("ProgramFiles", r"C:\Program Files")))
    trusted = engine == system_engine.resolve() or (engine.name.lower() == "pwsh.exe"
        and engine.parent.parent == (program_files / "PowerShell").resolve() and engine.parent.name.replace(".", "").isdigit())
    if not trusted:
        return ShellAnalysis(False, (command,), reason="untrusted parser executable")
    try:
        result = subprocess.run([str(engine), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _PS_PARSE],
                                input=command.encode("utf-8"), capture_output=True, cwd=cwd, env=env, timeout=10,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        data = json.loads(result.stdout.decode("utf-8-sig"))
        if result.returncode or not isinstance(data, dict) or not isinstance(data.get("commands"), list):
            raise ValueError("parser output")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return ShellAnalysis(False, (command,), reason="PowerShell parser unavailable")
    commands = tuple(str(item.get("text", "")) for item in data["commands"] if isinstance(item, dict))
    known = not data.get("errors") and not data.get("dynamic") and bool(commands)
    # Aliases, functions and unqualified commands cannot prove cmdlet/native identity.
    wrappers = [f"{engine} {data.get('version', '?')}\n{command}"]
    for item in data["commands"]:
        name = item.get("name") if isinstance(item, dict) else None
        if not isinstance(name, str) or not Path(name).is_absolute() or Path(name).suffix.casefold() != ".exe":
            known = False
        if isinstance(name, str) and Path(name).name.lower() in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe", "bash", "bash.exe"}:
            tokens = item.get("words")
            nested = _wrapper(str(item["text"]), cwd, env, depth + 1, tokens=tokens) if isinstance(tokens, list) and all(isinstance(token, str) for token in tokens) else ShellAnalysis(False, (str(item["text"]),), reason="dynamic nested arguments")
            # Native argument marshalling differs across PS5.1/pwsh, retain human approval.
            nested = replace(nested, known=False, reason="nested PowerShell native arguments")
            known = known and nested.known
            commands += nested.commands
            wrappers.extend(nested.wrappers)
    return ShellAnalysis(bool(known), commands, tuple(wrappers), "" if known else "PowerShell dynamic or unresolved syntax")


def _wrapper(command: str, cwd: str, env: dict[str, str], depth: int, *, tokens: list[str] | None = None) -> ShellAnalysis:
    if depth > 5:
        return ShellAnalysis(False, (command,), reason="nested interpreter limit")
    words = _words(command) if tokens is None else tokens
    if not words:
        return ShellAnalysis(False, (command,), reason="unbalanced quotes")
    name = Path(words[0]).name.casefold()
    if name in {"call", "for", "if", "set", "setlocal", "endlocal", "start", "doskey", "env", "env.exe", "sudo", "nohup", "xargs", "wsl", "wsl.exe"} or name.endswith((".bat", ".cmd")):
        return ShellAnalysis(False, (command,), reason="dynamic cmd operation")
    if name not in {"cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "pwsh.exe", "bash", "bash.exe"}:
        builtins = {"echo", "dir", "type", "cd", "chdir", "ver", "vol", "cls", "color", "copy", "del", "erase", "exit", "md", "mkdir", "rd", "rmdir", "ren", "rename", "pushd", "popd", "shift", "title", "verify"}
        if name in builtins:
            return ShellAnalysis(True, (command,))
        resolved = _resolve(words[0], cwd, env)
        if resolved is None or resolved.suffix.casefold() not in {".exe", ".com"}:
            return ShellAnalysis(False, (command,), reason="script or unresolved command identity")
        return ShellAnalysis(True, (command,), (f"native {resolved}",))
    engine = _resolve(words[0], cwd, env)
    if engine is None:
        return ShellAnalysis(False, (command,), reason="interpreter not resolved")
    flags = [word.casefold() for word in words[1:]]
    if name in {"cmd", "cmd.exe"}:
        official_cmd = (Path(env.get("SYSTEMROOT", r"C:\Windows")) / "System32/cmd.exe").resolve()
        if engine != official_cmd:
            return ShellAnalysis(False, (command,), reason="custom cmd interpreter")
        if "/c" not in flags or any(flag.startswith("/v") for flag in flags):
            return ShellAnalysis(False, (command,), reason="unknown cmd invocation")
        index = flags.index("/c") + 2
        child = " ".join(words[index:])
        nested = analyzeCmd(child, cwd, env, depth + 1)
    elif name in {"bash", "bash.exe"}:
        if engine.parent == (Path(env.get("SYSTEMROOT", r"C:\Windows")) / "System32").resolve():
            return ShellAnalysis(False, (command,), reason="WSL interpreter requires explicit environment analysis")
        # PermissionRuntime consumes actual Bash payload with the migrated AST.
        if "-c" not in flags and "-lc" not in flags:
            return ShellAnalysis(False, (command,), reason="unknown Bash invocation")
        index = next(i for i, flag in enumerate(flags, 1) if flag in {"-c", "-lc"})
        if len(words) != index + 2:
            return ShellAnalysis(False, (command,), reason="Bash dynamic arguments")
        child = words[index + 1]
        return ShellAnalysis("-lc" not in flags and not env.get("BASH_ENV"), (command, child), (f"bash {engine}\n{child}",), bashPayloads=(child,))
    else:
        if ("-encodedcommand" in flags) == ("-command" in flags):
            return ShellAnalysis(False, (command,), reason="unknown PowerShell invocation")
        if "-encodedcommand" in flags:
            index = flags.index("-encodedcommand") + 2
            try:
                child = base64.b64decode(words[index], validate=True).decode("utf-16-le")
            except (ValueError, IndexError, UnicodeError):
                return ShellAnalysis(False, (command,), reason="invalid encoded command")
        elif "-command" in flags:
            index = flags.index("-command") + 2
            child = " ".join(words[index:])
        else:
            return ShellAnalysis(False, (command,), reason="PowerShell file or dynamic invocation")
        nested = _powershell(child, engine, cwd, env, depth + 1)
        if "-noprofile" not in flags or len(words) != index + 1:
            nested = replace(nested, known=False, reason="profile or extra interpreter arguments")
    return ShellAnalysis(nested.known, (command, *nested.commands), (f"{engine}\n{child}", *nested.wrappers), nested.reason, nested.bashPayloads)


def analyzeCmd(command: str, cwd: str, env: dict[str, str], depth: int = 0) -> ShellAnalysis:
    parts, known = _cmdParts(command)
    commands: list[str] = []
    wrappers: list[str] = []
    bash_payloads: list[str] = []
    for part in parts:
        nested = _wrapper(part, cwd, env, depth)
        known = known and nested.known
        commands.extend(nested.commands)
        wrappers.extend(nested.wrappers)
        bash_payloads.extend(nested.bashPayloads)
    return ShellAnalysis(known and bool(parts), tuple(commands), tuple(wrappers), "" if known else "cmd expansion or complex syntax", tuple(bash_payloads))


def buildShellPlan(
    command: str, cwd: str, *, analyze: bool = True, environ: Mapping[str, str] | None = None,
) -> ShellExecutionPlan:
    if "\0" in command:
        raise ValueError("Shell命令包含空字节，无法执行。")
    directory = str(Path(cwd).resolve())
    env = scrubbed_env(environ)
    if os.name == "nt":
        shell = Path(env.get("COMSPEC", env.get("ComSpec", str(Path(env.get("SYSTEMROOT", r"C:\Windows")) / "System32/cmd.exe"))))
        if not shell.is_absolute() or shell.name.lower() != "cmd.exe" or not shell.is_file():
            raise ValueError("ComSpec必须指向绝对cmd.exe路径，请修正后重试。")
        argv = (str(shell.resolve()), "/d", "/s", "/c", command)
        command_line = f'"{argv[0]}" /d /s /c "{command}"'
        analysis = analyzeCmd(command, directory, env) if analyze else ShellAnalysis(False, (command,), reason="execution-only snapshot")
        official_cmd = (Path(env.get("SYSTEMROOT", r"C:\Windows")) / "System32/cmd.exe").resolve()
        if shell.resolve() != official_cmd:
            analysis = replace(analysis, known=False, reason="custom cmd executable")
        return ShellExecutionPlan(command, argv, command_line, directory, tuple(sorted(env.items())), "cmd", "auto:oem", analysis)
    posix_shell = "/bin/sh"
    dialect: Dialect = "bash" if Path(posix_shell).name == "bash" else "sh"
    try:
        simple = bool(shlex.split(command)) and not any(char in command for char in "|&;$`<>\n*?[]")
    except ValueError:
        simple = False
    return ShellExecutionPlan(command, (posix_shell, "-c", command), None, directory, tuple(sorted(env.items())), dialect, "utf-8", ShellAnalysis(simple, (command,), reason="" if simple else "unresolved sh syntax"))


async def prepareShellPlan(
    command: str, cwd: str, *, environ: Mapping[str, str] | None = None,
) -> ShellExecutionPlan:
    from ..permissions.bash.bash_ast import parseBashForSecurity
    plan = await asyncio.to_thread(buildShellPlan, command, cwd, environ=environ)
    payloads = plan.analysis.bashPayloads
    if plan.dialect == "bash":
        payloads = (command,)
    known = plan.analysis.known
    commands = list(plan.analysis.commands)
    for payload in payloads:
        result = await parseBashForSecurity(payload)
        known = known and result["kind"] == "simple"
        if result["kind"] == "simple":
            commands.extend(result["subcommands"])
    return replace(plan, analysis=replace(plan.analysis, known=known, commands=tuple(commands)))
