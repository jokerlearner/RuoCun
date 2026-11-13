"""Reference bash/ast.ts (MIT): explicit node allowlist and post-argv checks.

The tree producer lives in bash_parser.py. This walker never executes shell
code; an unknown node shape is returned as too-complex for human approval.
"""
from __future__ import annotations

import re
from typing import Literal, NotRequired, TypedDict, cast

from .parser import _ParseAborted, jsTrim, parseCommandRaw
from .types import Node


class Redirect(TypedDict):
    op: str
    target: str
    fd: NotRequired[float]


class EnvVar(TypedDict):
    name: str
    value: str


class Assignment(EnvVar):
    isAppend: bool


class SimpleCommand(TypedDict):
    argv: list[str]
    envVars: list[EnvVar]
    redirects: list[Redirect]
    text: str


class Simple(TypedDict):
    kind: Literal["simple"]
    commands: list[SimpleCommand]


class Complex(TypedDict):
    kind: Literal["too-complex"]
    reason: str
    nodeType: NotRequired[str]


class Unavailable(TypedDict):
    kind: Literal["parse-unavailable"]


ParseForSecurityResult = Simple | Complex | Unavailable


class SemanticCheckResult(TypedDict):
    ok: bool
    reason: NotRequired[str]


_STRUCTURAL = {"program", "list", "pipeline", "redirected_statement"}
_SEPARATORS = {"&&", "||", "|", ";", "&", "|&", "\n"}
_CMDSUB = "__CMDSUB_OUTPUT__"
_VAR = "__TRACKED_VAR__"
_SAFE_ENV = set("HOME PWD OLDPWD USER LOGNAME SHELL PATH HOSTNAME UID EUID PPID RANDOM SECONDS LINENO TMPDIR BASH_VERSION BASHPID SHLVL HISTFILE IFS".split())
_SPECIAL = {"?", "$", "!", "#", "0", "-"}
_DANGEROUS = ["command_substitution", "process_substitution", "expansion", "simple_expansion", "brace_expression", "subshell", "compound_statement", "for_statement", "while_statement", "until_statement", "if_statement", "case_statement", "function_definition", "test_command", "ansi_c_string", "translated_string", "herestring_redirect", "heredoc_redirect"]
_REDIRECT_OPS = {">", ">>", "<", ">&", "<&", ">|", "&>", "&>>", "<<<"}
_BRACE = re.compile(r"\{[^{}\s]*(,|\.\.)[^{}\s]*\}")
_NEWLINE_HASH = re.compile(r"\n[ \t]*#")
_PROC_ENVIRON = re.compile(r"/proc/.*/environ")
_ARITH_LEAF = re.compile(r"^(?:[0-9]+|0[xX][0-9a-fA-F]+|[0-9]+#[0-9a-zA-Z]+|[-+*/%^&|~!<>=?:(),]+|<<|>>|\*\*|&&|\|\||[<>=!]=|\$\(\(|\)\))$")


def _containsPlaceholder(value: str) -> bool:
    return _CMDSUB in value or _VAR in value


def nodeTypeId(nodeType: str | None) -> int:
    if not nodeType:
        return -2
    if nodeType == "ERROR":
        return -1
    return _DANGEROUS.index(nodeType) + 1 if nodeType in _DANGEROUS else 0


def _complex(node: Node) -> Complex:
    reason = "Parse error" if node.type == "ERROR" else f"Contains {node.type}" if node.type in _DANGEROUS else f"Unhandled node type: {node.type}"
    return {"kind": "too-complex", "reason": reason, "nodeType": node.type}


def _error(reason: str, nodeType: str | None = None) -> Complex:
    result: Complex = {"kind": "too-complex", "reason": reason}
    if nodeType is not None:
        result["nodeType"] = nodeType
    return result


def _maskBraces(cmd: str) -> str:
    if "{" not in cmd:
        return cmd
    output: list[str] = []
    single = double = False
    index = 0
    while index < len(cmd):
        char = cmd[index]
        if single:
            if char == "'":
                single = False
            output.append(" " if char == "{" else char)
            index += 1
        elif double:
            if char == "\\" and index + 1 < len(cmd) and cmd[index + 1] in ('"', "\\"):
                output.extend(cmd[index:index + 2])
                index += 2
            else:
                if char == '"':
                    double = False
                output.append(" " if char == "{" else char)
                index += 1
        elif char == "\\" and index + 1 < len(cmd):
            output.extend(cmd[index:index + 2])
            index += 2
        else:
            if char == "'":
                single = True
            elif char == '"':
                double = True
            output.append(char)
            index += 1
    return "".join(output)


async def parseForSecurity(cmd: str) -> ParseForSecurityResult:
    if cmd == "":
        return {"kind": "simple", "commands": []}
    root = await parseCommandRaw(cmd)
    return {"kind": "parse-unavailable"} if root is None else parseForSecurityFromAst(cmd, root)


def parseForSecurityFromAst(cmd: str, root: Node | _ParseAborted) -> ParseForSecurityResult:
    checks = (
        (r"[\x00-\x08\x0B-\x1F\x7F]", "Contains control characters"),
        (r"[\u00A0\u1680\u2000-\u200B\u2028\u2029\u202F\u205F\u3000\uFEFF]", "Contains Unicode whitespace"),
        (r"\\[ \t]|[^ \t\n\\]\\\n", "Contains backslash-escaped whitespace"),
        (r"~\[", "Contains zsh ~[ dynamic directory syntax"),
        (r"(?:^|[\s;&|])=[a-zA-Z_]", "Contains zsh =cmd equals expansion"),
    )
    for pattern, reason in checks:
        if re.search(pattern, cmd):
            return _error(reason)
    if re.search(r"\{[^}]*['\"]", _maskBraces(cmd)):
        return _error("Contains brace with quote character (expansion obfuscation)")
    if not jsTrim(cmd):
        return {"kind": "simple", "commands": []}
    if isinstance(root, _ParseAborted):
        return _error("Parser aborted (timeout or resource limit) — possible adversarial input", "PARSE_ABORT")
    commands: list[SimpleCommand] = []
    error = _collectCommands(root, commands, {})
    return error if error is not None else {"kind": "simple", "commands": commands}


def _applyVar(scope: dict[str, str], value: Assignment) -> None:
    combined = scope.get(value["name"], "") + value["value"] if value["isAppend"] else value["value"]
    scope[value["name"]] = _VAR if _containsPlaceholder(combined) else combined


def _collectCommands(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Complex | None:
    if node.type == "command":
        result = _walkCommand(node, [], commands, scope)
        if result["kind"] != "simple":
            return result
        commands.extend(result["commands"])
        return None
    if node.type == "redirected_statement":
        return _walkRedirectedStatement(node, commands, scope)
    if node.type == "comment":
        return None
    if node.type in _STRUCTURAL:
        pipeline = node.type == "pipeline"
        snapshot = dict(scope) if not pipeline and any(child.type in ("||", "&") for child in node.children) else None
        local = dict(scope) if pipeline else scope
        for child in node.children:
            if child.type in _SEPARATORS:
                if child.type in ("||", "|", "|&", "&"):
                    local = dict(scope if snapshot is None else snapshot)
                continue
            error = _collectCommands(child, commands, local)
            if error is not None:
                return error
        return None
    if node.type == "negated_command":
        return next((_collectCommands(child, commands, scope) for child in node.children if child.type != "!"), None)
    if node.type == "declaration_command":
        argv: list[str] = []
        for child in node.children:
            if child.type in ("export", "local", "readonly", "declare", "typeset", "variable_name"):
                argv.append(child.text)
            elif child.type in ("word", "number", "raw_string", "string", "concatenation"):
                arg = _walkArgument(child, commands, scope)
                if not isinstance(arg, str):
                    return arg
                if argv and argv[0] in ("declare", "typeset", "local"):
                    if re.search(r"^-[a-zA-Z]*[niaA]", arg):
                        return _error(f"declare flag {arg} changes assignment semantics (nameref/integer/array)", "declaration_command")
                    if not arg.startswith("-") and re.search(r"^[^=]*\[", arg):
                        return _error(f"declare positional '{arg}' contains array subscript — bash evaluates $(cmd) in subscripts", "declaration_command")
                argv.append(arg)
            elif child.type == "variable_assignment":
                value = _walkVariableAssignment(child, commands, scope)
                if "kind" in value:
                    return cast(Complex, value)
                _applyVar(scope, value)
                argv.append(f"{value['name']}={value['value']}")
            else:
                return _complex(child)
        commands.append({"argv": argv, "envVars": [], "redirects": [], "text": node.text})
        return None
    if node.type == "variable_assignment":
        value = _walkVariableAssignment(node, commands, scope)
        if "kind" in value:
            return cast(Complex, value)
        _applyVar(scope, value)
        return None
    if node.type == "for_statement":
        loopVar: str | None = None
        group: Node | None = None
        for child in node.children:
            if child.type == "variable_name":
                loopVar = child.text
            elif child.type == "do_group":
                group = child
            elif child.type in ("for", "in", "select", ";"):
                continue
            elif child.type == "command_substitution":
                error = _collectCommandSubstitution(child, commands, scope)
                if error is not None:
                    return error
            else:
                arg = _walkArgument(child, commands, scope)
                if not isinstance(arg, str):
                    return arg
        if loopVar is None or group is None:
            return _complex(node)
        if loopVar in ("PS4", "IFS"):
            return _error(f"{loopVar} as loop variable bypasses assignment validation", "for_statement")
        scope[loopVar] = _VAR
        local = dict(scope)
        for child in group.children:
            if child.type not in ("do", "done", ";"):
                error = _collectCommands(child, commands, local)
                if error is not None:
                    return error
        return None
    if node.type in ("if_statement", "while_statement"):
        seenThen = False
        for child in node.children:
            if child.type in ("if", "fi", "else", "elif", "while", "until", ";"):
                continue
            if child.type == "then":
                seenThen = True
                continue
            if child.type in ("do_group", "elif_clause", "else_clause"):
                local = dict(scope)
                for grandchild in child.children:
                    if grandchild.type in ("do", "done", ";", "elif", "else", "then"):
                        continue
                    error = _collectCommands(grandchild, commands, local)
                    if error is not None:
                        return error
                continue
            target = dict(scope) if seenThen else scope
            before = len(commands)
            error = _collectCommands(child, commands, target)
            if error is not None:
                return error
            if not seenThen:
                for command in commands[before:]:
                    if command["argv"] and command["argv"][0] == "read":
                        for arg in command["argv"][1:]:
                            if not arg.startswith("-") and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", arg):
                                existing = scope.get(arg)
                                if existing is not None and not _containsPlaceholder(existing):
                                    return _error(f"'read {arg}' in condition may not execute (||/pipeline/subshell); cannot prove it overwrites tracked literal '{existing}'", "if_statement")
                                scope[arg] = _VAR
        return None
    if node.type == "subshell":
        local = dict(scope)
        for child in node.children:
            if child.type not in ("(", ")"):
                error = _collectCommands(child, commands, local)
                if error is not None:
                    return error
        return None
    if node.type == "test_command":
        argv = ["[["]
        for child in node.children:
            if child.type not in ("[[", "]]", "[", "]"):
                error = _walkTestExpr(child, argv, commands, scope)
                if error is not None:
                    return error
        commands.append({"argv": argv, "envVars": [], "redirects": [], "text": node.text})
        return None
    if node.type == "unset_command":
        argv = []
        for child in node.children:
            if child.type in ("unset", "variable_name"):
                argv.append(child.text)
                if child.type == "variable_name":
                    scope.pop(child.text, None)
            elif child.type == "word":
                arg = _walkArgument(child, commands, scope)
                if not isinstance(arg, str):
                    return arg
                argv.append(arg)
            else:
                return _complex(child)
        commands.append({"argv": argv, "envVars": [], "redirects": [], "text": node.text})
        return None
    return _complex(node)


def _walkTestExpr(node: Node, argv: list[str], commands: list[SimpleCommand], scope: dict[str, str]) -> Complex | None:
    if node.type in ("unary_expression", "binary_expression", "negated_expression", "parenthesized_expression"):
        for child in node.children:
            error = _walkTestExpr(child, argv, commands, scope)
            if error is not None:
                return error
        return None
    if node.type in ("test_operator", "!", "(", ")", "&&", "||", "==", "=", "!=", "<", ">", "=~", "regex", "extglob_pattern"):
        argv.append(node.text)
        return None
    arg = _walkArgument(node, commands, scope)
    if not isinstance(arg, str):
        return arg
    argv.append(arg)
    return None


def _walkRedirectedStatement(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Complex | None:
    redirects: list[Redirect] = []
    inner: Node | None = None
    for child in node.children:
        if child.type == "file_redirect":
            redirect = _walkFileRedirect(child, commands, scope)
            if "kind" in redirect:
                return cast(Complex, redirect)
            redirects.append(redirect)
        elif child.type == "heredoc_redirect":
            error = _walkHeredocRedirect(child)
            if error is not None:
                return error
        elif child.type in ("command", "pipeline", "list", "negated_command", "declaration_command", "unset_command"):
            inner = child
        else:
            return _complex(child)
    if inner is None:
        commands.append({"argv": [], "envVars": [], "redirects": redirects, "text": node.text})
        return None
    before = len(commands)
    error = _collectCommands(inner, commands, scope)
    if error is not None:
        return error
    if len(commands) > before and redirects:
        commands[-1]["redirects"].extend(redirects)
    return None


def _walkFileRedirect(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Redirect | Complex:
    op: str | None = None
    target: str | None = None
    fd: float | None = None
    for child in node.children:
        if child.type == "file_descriptor":
            fd = float(child.text)  # Source Number(), including large descriptors.
        elif child.type in _REDIRECT_OPS:
            op = child.type
        elif child.type in ("word", "number"):
            if child.children or _BRACE.search(child.text):
                return _complex(child)
            target = re.sub(r"\\(.)", r"\1", child.text)
        elif child.type == "raw_string":
            target = child.text[1:-1]
        elif child.type in ("string", "concatenation"):
            value = _walkString(child, commands, scope) if child.type == "string" else _walkArgument(child, commands, scope)
            if not isinstance(value, str):
                return value
            target = value
        else:
            return _complex(child)
    if op is None or target is None:
        return _error("Unrecognized redirect shape", node.type)
    result: Redirect = {"op": op, "target": target}
    if fd is not None:
        result["fd"] = fd
    return result


def _walkHeredocRedirect(node: Node) -> Complex | None:
    start: str | None = None
    body: Node | None = None
    for child in node.children:
        if child.type == "heredoc_start":
            start = child.text
        elif child.type == "heredoc_body":
            body = child
        elif child.type not in ("<<", "<<-", "heredoc_end", "file_descriptor"):
            return _complex(child)
    quoted = start is not None and ((start.startswith("'") and start.endswith("'")) or (start.startswith('"') and start.endswith('"')) or start.startswith("\\"))
    if not quoted:
        return _error("Heredoc with unquoted delimiter undergoes shell expansion", "heredoc_redirect")
    if body is not None:
        for child in body.children:
            if child.type != "heredoc_content":
                return _complex(child)
    return None


def _walkHerestringRedirect(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Complex | None:
    for child in node.children:
        if child.type == "<<<":
            continue
        content = _walkArgument(child, commands, scope)
        if not isinstance(content, str):
            return content
        if _NEWLINE_HASH.search(content):
            return _complex(child)
    return None


def _walkCommand(node: Node, extraRedirects: list[Redirect], commands: list[SimpleCommand], scope: dict[str, str]) -> Simple | Complex:
    argv: list[str] = []
    env: list[EnvVar] = []
    redirects = list(extraRedirects)
    for child in node.children:
        if child.type == "variable_assignment":
            value = _walkVariableAssignment(child, commands, scope)
            if "kind" in value:
                return cast(Complex, value)
            env.append({"name": value["name"], "value": value["value"]})
        elif child.type in ("command_name", "word", "number", "raw_string", "string", "concatenation", "arithmetic_expansion", "simple_expansion"):
            arg = _walkArgument(child.children[0] if child.type == "command_name" and child.children else child, commands, scope)
            if not isinstance(arg, str):
                return arg
            argv.append(arg)
        elif child.type == "file_redirect":
            redirect = _walkFileRedirect(child, commands, scope)
            if "kind" in redirect:
                return cast(Complex, redirect)
            redirects.append(redirect)
        elif child.type == "herestring_redirect":
            error = _walkHerestringRedirect(child, commands, scope)
            if error is not None:
                return error
        else:
            return _complex(child)
    text = node.text
    if re.search(r"\$[A-Za-z_]", text) or "\n" in text:
        text = " ".join("'" + arg.replace("'", "'\\''") + "'" if arg == "" or re.search(r'''["'\\ \t\n$`;|&<>(){}*?\[\]~#]''', arg) else arg for arg in argv)
    return {"kind": "simple", "commands": [{"argv": argv, "envVars": env, "redirects": redirects, "text": text}]}


def _collectCommandSubstitution(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Complex | None:
    local = dict(scope)
    for child in node.children:
        if child.type not in ("$(", "`", ")"):
            error = _collectCommands(child, commands, local)
            if error is not None:
                return error
    return None


def _walkArgument(node: Node | None, commands: list[SimpleCommand], scope: dict[str, str]) -> str | Complex:
    if node is None:
        return _error("Null argument node")
    if node.type == "word":
        if _BRACE.search(node.text):
            return _error("Word contains brace expansion syntax", "word")
        return re.sub(r"\\(.)", r"\1", node.text)
    if node.type == "number":
        if node.children:
            return _error("Number node contains expansion (NN# arithmetic base syntax)", node.children[0].type)
        return node.text
    if node.type == "raw_string":
        return node.text[1:-1]
    if node.type == "string":
        return _walkString(node, commands, scope)
    if node.type == "concatenation":
        if _BRACE.search(node.text):
            return _error("Brace expansion", "concatenation")
        result = ""
        for child in node.children:
            part = _walkArgument(child, commands, scope)
            if not isinstance(part, str):
                return part
            result += part
        return result
    if node.type == "arithmetic_expansion":
        error = _walkArithmetic(node)
        return node.text if error is None else error
    if node.type == "simple_expansion":
        return _resolveSimpleExpansion(node, scope, False)
    return _complex(node)


def _walkString(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> str | Complex:
    result, cursor = "", -1
    dynamic = literal = False
    for child in node.children:
        if cursor != -1 and child.startIndex > cursor and child.type != '"':
            result += "\n" * (child.startIndex - cursor)
            literal = True
        cursor = child.endIndex
        if child.type == '"':
            continue
        if child.type == "string_content":
            result += re.sub(r'''\\([$`"\\])''', r"\1", child.text)
            literal = True
        elif child.type == "$":
            result += "$"
            literal = True
        elif child.type == "command_substitution":
            body = _extractSafeCatHeredoc(child)
            if body == "DANGEROUS":
                return _complex(child)
            if body is not None:
                trimmed = re.sub(r"\n+$", "", body)
                if "\n" not in trimmed:
                    result += trimmed
                literal = True
                continue
            error = _collectCommandSubstitution(child, commands, scope)
            if error is not None:
                return error
            result += _CMDSUB
            dynamic = True
        elif child.type == "simple_expansion":
            value = _resolveSimpleExpansion(child, scope, True)
            if not isinstance(value, str):
                return value
            if value == _VAR:
                dynamic = True
            else:
                literal = True
            result += value
        elif child.type == "arithmetic_expansion":
            error = _walkArithmetic(child)
            if error is not None:
                return error
            result += child.text
            literal = True
        else:
            return _complex(child)
    if dynamic and not literal:
        return _complex(node)
    if not literal and not dynamic and len(node.text.encode("utf-16-le", errors="surrogatepass")) // 2 > 2:
        return _complex(node)
    return result


def _walkArithmetic(node: Node) -> Complex | None:
    for child in node.children:
        if not child.children:
            if not _ARITH_LEAF.search(child.text):
                return _error(f"Arithmetic expansion references variable or non-literal: {child.text}", "arithmetic_expansion")
        elif child.type in ("binary_expression", "unary_expression", "ternary_expression", "parenthesized_expression"):
            error = _walkArithmetic(child)
            if error is not None:
                return error
        else:
            return _complex(child)
    return None


def _extractSafeCatHeredoc(node: Node) -> str | None:
    statement: Node | None = None
    for child in node.children:
        if child.type in ("$(", ")"):
            continue
        if child.type == "redirected_statement" and statement is None:
            statement = child
        else:
            return None
    if statement is None:
        return None
    sawCat, body = False, None
    for child in statement.children:
        if child.type == "command":
            if len(child.children) != 1 or child.children[0].type != "command_name" or child.children[0].text != "cat":
                return None
            sawCat = True
        elif child.type == "heredoc_redirect":
            if _walkHeredocRedirect(child) is not None:
                return None
            for grandchild in child.children:
                if grandchild.type == "heredoc_body":
                    body = grandchild.text
        else:
            return None
    if not sawCat or body is None:
        return None
    if _PROC_ENVIRON.search(body) or re.search(r"\bsystem\s*\(", body, re.ASCII):
        return "DANGEROUS"
    return body


def _walkVariableAssignment(node: Node, commands: list[SimpleCommand], scope: dict[str, str]) -> Assignment | Complex:
    name: str | None = None
    value, append = "", False
    for child in node.children:
        if child.type == "variable_name":
            name = child.text
        elif child.type in ("=", "+="):
            append = child.type == "+="
        elif child.type == "command_substitution":
            error = _collectCommandSubstitution(child, commands, scope)
            if error is not None:
                return error
            value = _CMDSUB
        else:
            resolved = _resolveSimpleExpansion(child, scope, True) if child.type == "simple_expansion" else _walkArgument(child, commands, scope)
            if not isinstance(resolved, str):
                return resolved
            value = resolved
    if name is None:
        return _error("Variable assignment without name", "variable_assignment")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        return _error(f"Invalid variable name (bash treats as command): {name}", "variable_assignment")
    if name == "IFS":
        return _error("IFS assignment changes word-splitting — cannot model statically", "variable_assignment")
    if name == "PS4":
        if append:
            return _error("PS4 += cannot be statically verified — combine into a single PS4= assignment", "variable_assignment")
        if _containsPlaceholder(value):
            return _error("PS4 value derived from cmdsub/variable — runtime unknowable", "variable_assignment")
        if not re.fullmatch(r"[A-Za-z0-9 _+:./=\[\]-]*", re.sub(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}", "", value)):
            return _error("PS4 value outside safe charset — only ${VAR} refs and [A-Za-z0-9 _+:.=/[]-] allowed", "variable_assignment")
    if "~" in value:
        return _error("Tilde in assignment value — bash may expand at assignment time", "variable_assignment")
    return {"name": name, "value": value, "isAppend": append}


def _resolveSimpleExpansion(node: Node, scope: dict[str, str], insideString: bool) -> str | Complex:
    name: str | None = None
    special = False
    for child in node.children:
        if child.type in ("variable_name", "special_variable_name"):
            name, special = child.text, child.type == "special_variable_name"
            break
    if name is None:
        return _complex(node)
    if name in scope:
        value = scope[name]
        if _containsPlaceholder(value):
            return _VAR if insideString else _complex(node)
        if not insideString and (value == "" or re.search(r"[ \t\n*?\[]", value)):
            return _complex(node)
        return value
    if insideString and (name in _SAFE_ENV or (special and (name in _SPECIAL or re.fullmatch(r"[0-9]+", name)))):
        return _VAR
    return _complex(node)


_ZSH_BUILTINS = set("zmodload emulate sysopen sysread syswrite sysseek zpty ztcp zsocket zf_rm zf_mv zf_ln zf_chmod zf_chown zf_mkdir zf_rmdir zf_chgrp".split())
_EVAL_BUILTINS = set("eval source . exec command builtin fc coproc noglob nocorrect trap enable mapfile readarray hash bind complete compgen alias let".split())
_SUBSCRIPT_FLAGS = {
    "test": {"-v", "-R"}, "[": {"-v", "-R"}, "[[": {"-v", "-R"},
    "printf": {"-v"}, "read": {"-a"}, "unset": {"-v"}, "wait": {"-p"},
}
_READ_DATA_FLAGS = {"-p", "-d", "-n", "-N", "-t", "-u", "-i"}


def _semanticError(reason: str) -> SemanticCheckResult:
    return {"ok": False, "reason": reason}


def _unwrap(argv: list[str]) -> list[str] | SemanticCheckResult:
    a = argv
    while a:
        name = a[0]
        if name in ("time", "nohup"):
            a = a[1:]
        elif name == "timeout":
            index = 1
            while index < len(a):
                arg = a[index]
                nextArg = a[index + 1] if index + 1 < len(a) else ""
                if arg in ("--foreground", "--preserve-status", "--verbose") or re.fullmatch(r"--(?:kill-after|signal)=[A-Za-z0-9_.+-]+", arg):
                    index += 1
                elif arg in ("--kill-after", "--signal") and re.fullmatch(r"[A-Za-z0-9_.+-]+", nextArg):
                    index += 2
                elif arg.startswith("--"):
                    return _semanticError(f"timeout with {arg} flag cannot be statically analyzed")
                elif arg == "-v" or re.fullmatch(r"-[ks][A-Za-z0-9_.+-]+", arg):
                    index += 1
                elif arg in ("-k", "-s") and re.fullmatch(r"[A-Za-z0-9_.+-]+", nextArg):
                    index += 2
                elif arg.startswith("-"):
                    return _semanticError(f"timeout with {arg} flag cannot be statically analyzed")
                else:
                    break
            duration = a[index] if index < len(a) else ""
            if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?[smhd]?", duration):
                a = a[index + 1:]
            elif duration:
                return _semanticError(f"timeout duration '{duration}' cannot be statically analyzed")
            else:
                break
        elif name == "nice":
            arg = a[1] if len(a) > 1 else ""
            if arg == "-n" and len(a) > 2 and re.fullmatch(r"-?[0-9]+", a[2]):
                a = a[3:]
            elif re.fullmatch(r"-[0-9]+", arg):
                a = a[2:]
            elif re.search(r"[$(`]", arg):
                return _semanticError(f"nice argument '{arg}' contains expansion — cannot statically determine wrapped command")
            else:
                a = a[1:]
        elif name == "env":
            index = 1
            while index < len(a):
                arg = a[index]
                if "=" in arg and not arg.startswith("-") or arg in ("-i", "-0", "-v"):
                    index += 1
                elif arg == "-u" and index + 1 < len(a) and a[index + 1]:
                    index += 2
                elif arg.startswith("-"):
                    return _semanticError(f"env with {arg} flag cannot be statically analyzed")
                else:
                    break
            if index < len(a):
                a = a[index:]
            else:
                break
        elif name == "stdbuf":
            index = 1
            while index < len(a):
                arg = a[index]
                if re.fullmatch(r"-[ioe]", arg) and index + 1 < len(a) and a[index + 1]:
                    index += 2
                elif re.search(r"^-[ioe].", arg) or re.search(r"^--(input|output|error)=", arg):
                    index += 1
                elif arg.startswith("-"):
                    return _semanticError(f"stdbuf with {arg} flag cannot be statically analyzed")
                else:
                    break
            if 1 < index < len(a):
                a = a[index:]
            else:
                break
        else:
            break
    return a


def checkSemantics(commands: list[SimpleCommand]) -> SemanticCheckResult:
    from .bash_parser import SHELL_KEYWORDS

    for command in commands:
        unwrapped = _unwrap(command["argv"])
        if not isinstance(unwrapped, list):
            return unwrapped
        a = unwrapped
        if not a:
            continue
        name = a[0]
        if name == "":
            return _semanticError("Empty command name — argv[0] may not reflect what bash runs")
        if _containsPlaceholder(name):
            return _semanticError("Command name is runtime-determined (placeholder argv[0])")
        if name.startswith(("-", "|", "&")):
            return _semanticError("Command appears to be an incomplete fragment")
        dangerFlags = _SUBSCRIPT_FLAGS.get(name)
        if dangerFlags is not None:
            for index in range(1, len(a)):
                arg = a[index]
                nextArg = a[index + 1] if index + 1 < len(a) else ""
                if arg in dangerFlags and "[" in nextArg:
                    return _semanticError(f"'{name} {arg}' operand contains array subscript — bash evaluates $(cmd) in subscripts")
                if len(arg) > 2 and arg[0] == "-" and arg[1] != "-" and "[" not in arg:
                    for flag in dangerFlags:
                        if len(flag) == 2 and flag[1] in arg and "[" in nextArg:
                            return _semanticError(f"'{name} {flag}' (combined in '{arg}') operand contains array subscript — bash evaluates $(cmd) in subscripts")
                for flag in dangerFlags:
                    if len(flag) == 2 and arg.startswith(flag) and len(arg) > 2 and "[" in arg:
                        return _semanticError(f"'{name} {flag}' (fused) operand contains array subscript — bash evaluates $(cmd) in subscripts")
        if name == "[[":
            for index in range(2, len(a)):
                if a[index] in ("-eq", "-ne", "-lt", "-le", "-gt", "-ge") and ("[" in a[index - 1] or (index + 1 < len(a) and "[" in a[index + 1])):
                    return _semanticError(f"'[[ ... {a[index]} ... ]]' operand contains array subscript — bash arithmetically evaluates $(cmd) in subscripts")
        if name in ("read", "unset"):
            skip = False
            for arg in a[1:]:
                if skip:
                    skip = False
                    continue
                if arg.startswith("-"):
                    if name == "read":
                        if arg in _READ_DATA_FLAGS:
                            skip = True
                        elif len(arg) > 2 and arg[1] != "-":
                            for index in range(1, len(arg)):
                                if "-" + arg[index] in _READ_DATA_FLAGS:
                                    if index == len(arg) - 1:
                                        skip = True
                                    break
                    continue
                if "[" in arg:
                    return _semanticError(f"'{name}' positional NAME '{arg}' contains array subscript — bash evaluates $(cmd) in subscripts")
        if name in SHELL_KEYWORDS:
            return _semanticError(f"Shell keyword '{name}' as command name — tree-sitter mis-parse")
        for arg in command["argv"]:
            if "\n" in arg and _NEWLINE_HASH.search(arg):
                return _semanticError("Newline followed by # inside a quoted argument can hide arguments from path validation")
        for ev in command["envVars"]:
            if "\n" in ev["value"] and _NEWLINE_HASH.search(ev["value"]):
                return _semanticError("Newline followed by # inside an env var value can hide arguments from path validation")
        for redirect in command["redirects"]:
            if "\n" in redirect["target"] and _NEWLINE_HASH.search(redirect["target"]):
                return _semanticError("Newline followed by # inside a redirect target can hide arguments from path validation")
        if name == "jq":
            if any(re.search(r"\bsystem\s*\(", arg, re.ASCII) for arg in a):
                return _semanticError("jq command contains system() function which executes arbitrary commands")
            if any(re.search(r"^(?:-[fL](?:$|[^A-Za-z])|--(?:from-file|rawfile|slurpfile|library-path)(?:$|=))", arg) for arg in a):
                return _semanticError("jq command contains dangerous flags that could execute code or read arbitrary files")
        if name in _ZSH_BUILTINS:
            return _semanticError(f"Zsh builtin '{name}' can bypass security checks")
        if name in _EVAL_BUILTINS:
            if name == "command" and len(a) > 1 and a[1] in ("-v", "-V"):
                pass
            elif name == "fc" and not any(re.search(r"^-[^-]*[es]", arg) for arg in a[1:]):
                pass
            elif name == "compgen" and not any(re.search(r"^-[^-]*[CFW]", arg) for arg in a[1:]):
                pass
            else:
                return _semanticError(f"'{name}' evaluates arguments as shell code")
        if any("/proc/" in arg and _PROC_ENVIRON.search(arg) for arg in command["argv"]) or any("/proc/" in redirect["target"] and _PROC_ENVIRON.search(redirect["target"]) for redirect in command["redirects"]):
            return _semanticError("Accesses /proc/*/environ which may expose secrets")
    return {"ok": True}
