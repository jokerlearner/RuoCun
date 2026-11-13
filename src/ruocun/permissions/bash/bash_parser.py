"""冻结bash_parser.ts的纯Python迁移（MIT），产出tree-sitter-bash兼容节点。

游标使用Python代码点；节点位置始终为UTF-8字节。命令UTF-16长度门由wrapper掌管。
"""

from __future__ import annotations

import bisect
import re
import time
from dataclasses import dataclass, field

from .types import Node

PARSE_TIMEOUT_MS = 50
MAX_NODES = 50_000
SPECIAL_VARS = set("?$@*#-!_")
DECL_KEYWORDS = {"export", "declare", "typeset", "readonly", "local"}
SHELL_KEYWORDS = {"if", "then", "elif", "else", "fi", "while", "until", "for", "in",
                  "do", "done", "case", "esac", "function", "select"}


@dataclass
class Token:
    type: str
    value: str
    start: int
    end: int


@dataclass
class HeredocPending:
    delim: str
    stripTabs: bool
    quoted: bool
    bodyStart: int = 0
    bodyEnd: int = 0
    endStart: int = 0
    endEnd: int = 0


@dataclass
class Lexer:
    src: str
    i: int = 0
    b: int = 0
    heredocs: list[HeredocPending] = field(default_factory=list)
    byteTable: list[int] | None = None

    @property
    def len(self) -> int:
        return len(self.src)


@dataclass
class ParseState:
    L: Lexer
    src: str
    srcBytes: int
    isAscii: bool
    deadline: float
    nodeCount: int = 0
    aborted: bool = False
    inBacktick: int = 0
    stopToken: str | None = None


def advance(L: Lexer) -> None:
    c = L.src[L.i]
    L.i += 1
    L.b += len(c.encode("utf-8", errors="surrogatepass"))


def peek(L: Lexer, off: int = 0) -> str:
    return L.src[L.i + off] if 0 <= L.i + off < L.len else ""


def byteAt(L: Lexer, charIdx: int) -> int:
    if L.byteTable is None:
        table, b = [0], 0
        for char in L.src:
            b += len(char.encode("utf-8", errors="surrogatepass"))
            table.append(b)
        L.byteTable = table
    return L.byteTable[charIdx]


def isWordChar(c: str) -> bool:
    return bool(c) and ("a" <= c <= "z" or "A" <= c <= "Z" or "0" <= c <= "9"
                        or c in "_/.-+:@%,~^?*!=[]")


def isWordStart(c: str) -> bool:
    return isWordChar(c) or c == "\\"


def isIdentStart(c: str) -> bool:
    return bool(c) and ("a" <= c <= "z" or "A" <= c <= "Z" or c == "_")


def isIdentChar(c: str) -> bool:
    return isIdentStart(c) or isDigit(c)


def isDigit(c: str) -> bool:
    return "0" <= c <= "9"


def isHexDigit(c: str) -> bool:
    return isDigit(c) or "a" <= c <= "f" or "A" <= c <= "F"


def isBaseDigit(c: str) -> bool:
    return isIdentChar(c) or c == "@"


def isHeredocDelimChar(c: str) -> bool:
    return bool(c) and c not in " \t\n<>|&;()'\"`\\"


def skipBlanks(L: Lexer) -> None:
    while L.i < L.len:
        c = peek(L)
        if c in {" ", "\t", "\r"}:
            advance(L)
        elif c == "\\":
            nx = peek(L, 1)
            if nx == "\n" or nx == "\r" and peek(L, 2) == "\n":
                advance(L)
                advance(L)
                if nx == "\r":
                    advance(L)
            elif nx in {" ", "\t"}:
                advance(L)
                advance(L)
            else:
                break
        else:
            break


def nextToken(L: Lexer, ctx: str = "arg") -> Token:
    skipBlanks(L)
    start = L.b
    if L.i >= L.len:
        return Token("EOF", "", start, start)
    c, c1 = peek(L), peek(L, 1)
    if c == "\n":
        advance(L)
        return Token("NEWLINE", "\n", start, L.b)
    if c == "#":
        si = L.i
        while L.i < L.len and peek(L) != "\n":
            advance(L)
        return Token("COMMENT", L.src[si:L.i], start, L.b)
    for op in ("&&", "||", "|&", ";;&", ";;", ";&", ">>", ">&-", ">&", ">|",
               "&>>", "&>", "<<<", "<<-", "<<", "<&-", "<&", "<(", ">(", "((", "))"):
        if L.src.startswith(op, L.i):
            for _ in op:
                advance(L)
            typ = "LT_PAREN" if op == "<(" else "GT_PAREN" if op == ">(" else "OP"
            return Token(typ, op, start, L.b)
    if c in "|&;><()":
        advance(L)
        return Token("OP", c, start, L.b)
    if ctx == "cmd":
        op = ("[[" if c == "[" and c1 == "[" else "[" if c == "[" else
              "{" if c == "{" and c1 in {" ", "\t", "\n"} else
              "}" if c == "}" else "!" if c == "!" and c1 in {" ", "\t"} else "")
        if op:
            for _ in op:
                advance(L)
            return Token("OP", op, start, L.b)
    if c == '"':
        advance(L)
        return Token("DQUOTE", c, start, L.b)
    if c == "'":
        si = L.i
        advance(L)
        while L.i < L.len and peek(L) != "'":
            advance(L)
        if L.i < L.len:
            advance(L)
        return Token("SQUOTE", L.src[si:L.i], start, L.b)
    if c == "$":
        for prefix, typ in (("$((", "DOLLAR_DPAREN"), ("$(", "DOLLAR_PAREN"),
                            ("${", "DOLLAR_BRACE")):
            if L.src.startswith(prefix, L.i):
                for _ in prefix:
                    advance(L)
                return Token(typ, prefix, start, L.b)
        if c1 == "'":
            si = L.i
            advance(L)
            advance(L)
            while L.i < L.len and peek(L) != "'":
                if peek(L) == "\\" and L.i + 1 < L.len:
                    advance(L)
                advance(L)
            if L.i < L.len:
                advance(L)
            return Token("ANSI_C", L.src[si:L.i], start, L.b)
        advance(L)
        return Token("DOLLAR", "$", start, L.b)
    if c == "`":
        advance(L)
        return Token("BACKTICK", c, start, L.b)
    if isDigit(c):
        j = L.i
        while j < L.len and isDigit(L.src[j]):
            j += 1
        after = L.src[j] if j < L.len else ""
        if after in {">", "<"}:
            si = L.i
            while L.i < j:
                advance(L)
            return Token("WORD", L.src[si:L.i], start, L.b)
    if isWordStart(c) or c in {"{", "}"}:
        si = L.i
        while L.i < L.len:
            ch = peek(L)
            if ch == "\\":
                if L.i + 1 >= L.len:
                    break
                advance(L)
                advance(L)
                continue
            if not isWordChar(ch) and ch not in {"{", "}"}:
                break
            advance(L)
        if L.i > si:
            value = L.src[si:L.i]
            return Token("NUMBER" if re.fullmatch(r"-?\d+", value, re.ASCII) else "WORD",
                         value, start, L.b)
    advance(L)
    return Token("WORD", c, start, L.b)


def parseSource(source: str, timeoutMs: float = PARSE_TIMEOUT_MS) -> Node | None:
    L = Lexer(source)
    P = ParseState(L, source, len(source.encode("utf-8", errors="surrogatepass")),
                   source.isascii(), time.perf_counter() + timeoutMs / 1000)
    try:
        program = parseProgram(P)
        return None if P.aborted else program
    except Exception:
        return None


def checkBudget(P: ParseState) -> None:
    P.nodeCount += 1
    if P.nodeCount > MAX_NODES or P.nodeCount & 0x7F == 0 and time.perf_counter() > P.deadline:
        P.aborted = True
        raise RuntimeError("parser budget")


def sliceBytes(P: ParseState, startByte: int, endByte: int) -> str:
    if P.isAscii:
        return P.src[startByte:endByte]
    byteAt(P.L, 0)
    assert P.L.byteTable is not None
    return P.src[bisect.bisect_left(P.L.byteTable, startByte):bisect.bisect_left(P.L.byteTable, endByte)]


def mk(P: ParseState, type: str, start: int, end: int, children: list[Node]) -> Node:
    checkBudget(P)
    return Node(type, sliceBytes(P, start, end), start, end, children)


def leaf(P: ParseState, type: str, tok: Token) -> Node:
    return mk(P, type, tok.start, tok.end, [])


def saveLex(L: Lexer) -> tuple[int, int]:
    return L.i, L.b


def restoreLex(L: Lexer, s: tuple[int, int]) -> None:
    L.i, L.b = s


def parseProgram(P: ParseState) -> Node:
    children: list[Node] = []
    skipBlanks(P.L)
    while True:
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type == "NEWLINE":
            skipBlanks(P.L)
            continue
        restoreLex(P.L, save)
        break
    progStart = P.L.b
    while P.L.i < P.L.len:
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type == "EOF":
            break
        if t.type == "NEWLINE":
            continue
        if t.type == "COMMENT":
            children.append(leaf(P, "comment", t))
            continue
        restoreLex(P.L, save)
        stmts = parseStatements(P, None)
        children.extend(stmts)
        if not stmts:
            err = nextToken(P.L, "cmd")
            if err.type == "EOF":
                break
            if err.type == "OP" and err.value == ";;" and children:
                continue
            children.append(mk(P, "ERROR", err.start, err.end, []))
    return mk(P, "program", progStart, P.srcBytes if children else progStart, children)


def parseStatements(P: ParseState, terminator: str | None) -> list[Node]:
    out: list[Node] = []
    while True:
        skipBlanks(P.L)
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type == "EOF":
            restoreLex(P.L, save)
            break
        if t.type == "NEWLINE":
            if P.L.heredocs:
                scanHeredocBodies(P)
            continue
        if t.type == "COMMENT":
            out.append(leaf(P, "comment", t))
            continue
        if ((terminator and t.type == "OP" and t.value == terminator)
                or t.type == "OP" and t.value in {")", "}", ";;", ";&", ";;&", "))", "]]", "]"}
                or t.type == "BACKTICK" and P.inBacktick > 0
                or t.type == "WORD" and t.value in {"then", "elif", "else", "fi", "do", "done", "esac"}):
            restoreLex(P.L, save)
            break
        restoreLex(P.L, save)
        stmt = parseAndOr(P)
        if not stmt:
            break
        out.append(stmt)
        skipBlanks(P.L)
        save2 = saveLex(P.L)
        sep = nextToken(P.L, "cmd")
        if sep.type == "OP" and sep.value in {";", "&"}:
            save3 = saveLex(P.L)
            after = nextToken(P.L, "cmd")
            restoreLex(P.L, save3)
            out.append(leaf(P, sep.value, sep))
            if (after.type == "EOF" or after.type == "OP" and after.value in {")", "}", ";;", ";&", ";;&"}
                    or after.type == "WORD" and after.value in {"then", "elif", "else", "fi", "do", "done", "esac"}):
                continue
        elif sep.type == "NEWLINE":
            if P.L.heredocs:
                scanHeredocBodies(P)
            continue
        else:
            restoreLex(P.L, save2)
    return out


def parseAndOr(P: ParseState) -> Node | None:
    left = parsePipeline(P)
    if not left:
        return None
    while True:
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type != "OP" or t.value not in {"&&", "||"}:
            restoreLex(P.L, save)
            break
        op = leaf(P, t.value, t)
        skipNewlines(P)
        right = parsePipeline(P)
        if not right:
            left = mk(P, "list", left.startIndex, op.endIndex, [left, op])
            break
        if right.type == "redirected_statement" and len(right.children) >= 2:
            inner, redirs = right.children[0], right.children[1:]
            node = mk(P, "list", left.startIndex, inner.endIndex, [left, op, inner])
            left = mk(P, "redirected_statement", node.startIndex, redirs[-1].endIndex, [node, *redirs])
        else:
            left = mk(P, "list", left.startIndex, right.endIndex, [left, op, right])
    return left


def skipNewlines(P: ParseState) -> None:
    while True:
        save = saveLex(P.L)
        if nextToken(P.L, "cmd").type != "NEWLINE":
            restoreLex(P.L, save)
            break


def parsePipeline(P: ParseState) -> Node | None:
    first = parseCommand(P)
    if not first:
        return None
    parts = [first]
    while True:
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type != "OP" or t.value not in {"|", "|&"}:
            restoreLex(P.L, save)
            break
        op = leaf(P, t.value, t)
        skipNewlines(P)
        nxt = parseCommand(P)
        if not nxt:
            parts.append(op)
            break
        if nxt.type == "redirected_statement" and len(nxt.children) >= 2 and parts:
            inner, redirs = nxt.children[0], nxt.children[1:]
            pipe = mk(P, "pipeline", parts[0].startIndex, inner.endIndex, [*parts, op, inner])
            parts = [mk(P, "redirected_statement", pipe.startIndex, redirs[-1].endIndex, [pipe, *redirs])]
        else:
            parts.extend([op, nxt])
    return parts[0] if len(parts) == 1 else mk(P, "pipeline", parts[0].startIndex, parts[-1].endIndex, parts)


def parseCommand(P: ParseState) -> Node | None:
    skipBlanks(P.L)
    save = saveLex(P.L)
    t = nextToken(P.L, "cmd")
    if t.type == "EOF":
        restoreLex(P.L, save)
        return None
    if t.type == "OP" and t.value == "!":
        bang = leaf(P, "!", t)
        inner = parseCommand(P)
        if not inner:
            restoreLex(P.L, save)
            return None
        if inner.type == "redirected_statement" and len(inner.children) >= 2:
            cmd, redirs = inner.children[0], inner.children[1:]
            neg = mk(P, "negated_command", bang.startIndex, cmd.endIndex, [bang, cmd])
            return mk(P, "redirected_statement", neg.startIndex, redirs[-1].endIndex, [neg, *redirs])
        return mk(P, "negated_command", bang.startIndex, inner.endIndex, [bang, inner])
    if t.type == "OP" and t.value in {"(", "{", "(("}:
        openNode = leaf(P, t.value, t)
        closer = {"(": ")", "{": "}", "((": "))"}[t.value]
        body = parseArithCommaList(P, closer, "var") if t.value == "((" else parseStatements(P, closer)
        closeTok = nextToken(P.L, "cmd")
        close = (leaf(P, closer, closeTok) if closeTok.value == closer else
                 mk(P, closer, openNode.endIndex, openNode.endIndex, []))
        node = mk(P, "subshell" if t.value == "(" else "compound_statement",
                  openNode.startIndex, close.endIndex, [openNode, *body, close])
        return node if t.value == "((" else maybeRedirect(P, node)
    if t.type == "OP" and t.value in {"[", "[["}:
        openNode = leaf(P, t.value, t)
        closer = "]" if t.value == "[" else "]]"
        exprSave = saveLex(P.L)
        expr = parseTestExpr(P, closer)
        skipBlanks(P.L)
        if t.value == "[" and peek(P.L) != "]":
            restoreLex(P.L, exprSave)
            prevStop, P.stopToken = P.stopToken, "]"
            rstmt = parseCommand(P)
            P.stopToken = prevStop
            if rstmt and rstmt.type == "redirected_statement":
                expr = rstmt
            else:
                restoreLex(P.L, exprSave)
                expr = parseTestExpr(P, closer)
            skipBlanks(P.L)
        closeTok = nextToken(P.L, "arg")
        close = (leaf(P, closer, closeTok) if closeTok.value == closer else
                 mk(P, closer, openNode.endIndex, openNode.endIndex, []))
        return mk(P, "test_command", openNode.startIndex, close.endIndex,
                  [openNode, expr, close] if expr else [openNode, close])
    if t.type == "WORD":
        if t.value == "if":
            return maybeRedirect(P, parseIf(P, t), True)
        if t.value in {"while", "until"}:
            return maybeRedirect(P, parseWhile(P, t), True)
        if t.value in {"for", "select"}:
            return maybeRedirect(P, parseFor(P, t), True)
        if t.value == "case":
            return maybeRedirect(P, parseCase(P, t), True)
        if t.value == "function":
            return parseFunction(P, t)
        if t.value in DECL_KEYWORDS:
            return maybeRedirect(P, parseDeclaration(P, t))
        if t.value in {"unset", "unsetenv"}:
            return maybeRedirect(P, parseUnset(P, t))
    restoreLex(P.L, save)
    return parseSimpleCommand(P)


def parseSimpleCommand(P: ParseState) -> Node | None:
    start = P.L.b
    assignments: list[Node] = []
    preRedirects: list[Node] = []
    while True:
        skipBlanks(P.L)
        a = tryParseAssignment(P)
        if a:
            assignments.append(a)
            continue
        r = tryParseRedirect(P)
        if r:
            preRedirects.append(r)
            continue
        break
    skipBlanks(P.L)
    save = saveLex(P.L)
    nameTok = nextToken(P.L, "cmd")
    if (nameTok.type in {"EOF", "NEWLINE", "COMMENT"}
            or nameTok.type == "OP" and nameTok.value not in {"{", "[", "[["}
            or nameTok.type == "WORD" and nameTok.value in SHELL_KEYWORDS and nameTok.value != "in"):
        restoreLex(P.L, save)
        if len(assignments) == 1 and not preRedirects:
            return assignments[0]
        if preRedirects and not assignments:
            return mk(P, "redirected_statement", preRedirects[0].startIndex, preRedirects[-1].endIndex, preRedirects)
        if len(assignments) > 1 and not preRedirects:
            return mk(P, "variable_assignments", assignments[0].startIndex, assignments[-1].endIndex, assignments)
        if assignments or preRedirects:
            allNodes = [*assignments, *preRedirects]
            return mk(P, "command", start, allNodes[-1].endIndex, allNodes)
        return None
    restoreLex(P.L, save)
    fnSave = saveLex(P.L)
    nm = parseWord(P, "cmd")
    if nm and nm.type == "word":
        skipBlanks(P.L)
        if peek(P.L) == "(" and peek(P.L, 1) == ")":
            oParen = leaf(P, "(", nextToken(P.L, "cmd"))
            cParen = leaf(P, ")", nextToken(P.L, "cmd"))
            skipBlanks(P.L)
            skipNewlines(P)
            body = parseCommand(P)
            if body:
                bodyKids = [body]
                if (body.type == "redirected_statement" and len(body.children) >= 2
                        and body.children[0].type == "compound_statement"):
                    bodyKids = body.children
                return mk(P, "function_definition", nm.startIndex, bodyKids[-1].endIndex,
                          [nm, oParen, cParen, *bodyKids])
    restoreLex(P.L, fnSave)
    nameArg = parseWord(P, "cmd")
    if not nameArg:
        return assignments[0] if len(assignments) == 1 else None
    cmdName = mk(P, "command_name", nameArg.startIndex, nameArg.endIndex, [nameArg])
    args: list[Node] = []
    redirects: list[Node] = []
    heredocRedirect: Node | None = None
    while True:
        skipBlanks(P.L)
        r = tryParseRedirect(P, True)
        if r:
            if r.type == "heredoc_redirect":
                heredocRedirect = r
            elif r.type == "herestring_redirect":
                args.append(r)
            else:
                redirects.append(r)
            continue
        if redirects or P.stopToken == "]" and peek(P.L) == "]":
            break
        save2 = saveLex(P.L)
        pk = nextToken(P.L, "arg")
        if (pk.type in {"EOF", "NEWLINE", "COMMENT"} or pk.type == "OP"
                and pk.value in {"|", "|&", "&&", "||", ";", ";;", ";&", ";;&", "&", ")", "}", "))"}):
            restoreLex(P.L, save2)
            break
        restoreLex(P.L, save2)
        arg = parseWord(P, "arg")
        if not arg:
            if peek(P.L) == "(":
                openNode = leaf(P, "(", nextToken(P.L, "cmd"))
                subshellBody = parseStatements(P, ")")
                cTok = nextToken(P.L, "cmd")
                close = (leaf(P, ")", cTok) if cTok.type == "OP" and cTok.value == ")" else
                         mk(P, ")", openNode.endIndex, openNode.endIndex, []))
                args.append(mk(P, "subshell", openNode.startIndex, close.endIndex, [openNode, *subshellBody, close]))
                continue
            break
        if (arg.type == "word" and arg.text == "=" or arg.type in {"word", "concatenation"}
                and peek(P.L) == "(" and P.L.b == arg.endIndex):
            args.append(mk(P, "ERROR", arg.startIndex, arg.endIndex, [arg]))
        else:
            args.append(arg)
    cmdChildren = [*assignments, *preRedirects, cmdName, *args]
    cmd = mk(P, "command", cmdChildren[0].startIndex, cmdChildren[-1].endIndex, cmdChildren)
    if heredocRedirect:
        scanHeredocBodies(P)
        hd = P.L.heredocs.pop(0) if P.L.heredocs else None
        if hd and len(heredocRedirect.children) >= 2:
            bodyNode = mk(P, "heredoc_body", hd.bodyStart, hd.bodyEnd,
                          [] if hd.quoted else parseHeredocBodyContent(P, hd.bodyStart, hd.bodyEnd))
            endNode = mk(P, "heredoc_end", hd.endStart, hd.endEnd, [])
            heredocRedirect.children.extend([bodyNode, endNode])
            heredocRedirect.endIndex = hd.endEnd
            heredocRedirect.text = sliceBytes(P, heredocRedirect.startIndex, hd.endEnd)
        allR = [*preRedirects, heredocRedirect, *redirects]
        rStart = min(cmd.startIndex, preRedirects[0].startIndex) if preRedirects else cmd.startIndex
        return mk(P, "redirected_statement", rStart, heredocRedirect.endIndex, [cmd, *allR])
    if redirects:
        return mk(P, "redirected_statement", cmd.startIndex, redirects[-1].endIndex, [cmd, *redirects])
    return cmd


def maybeRedirect(P: ParseState, node: Node, allowHerestring: bool = False) -> Node:
    redirects: list[Node] = []
    while True:
        skipBlanks(P.L)
        save = saveLex(P.L)
        r = tryParseRedirect(P)
        if not r:
            break
        if r.type == "herestring_redirect" and not allowHerestring:
            restoreLex(P.L, save)
            break
        redirects.append(r)
    return (mk(P, "redirected_statement", node.startIndex, redirects[-1].endIndex, [node, *redirects])
            if redirects else node)


def tryParseAssignment(P: ParseState) -> Node | None:
    save = saveLex(P.L)
    skipBlanks(P.L)
    startB = P.L.b
    if not isIdentStart(peek(P.L)):
        restoreLex(P.L, save)
        return None
    while isIdentChar(peek(P.L)):
        advance(P.L)
    nameEnd = subEnd = P.L.b
    if peek(P.L) == "[":
        advance(P.L)
        depth = 1
        while P.L.i < P.L.len and depth > 0:
            c = peek(P.L)
            depth += 1 if c == "[" else -1 if c == "]" else 0
            advance(P.L)
        subEnd = P.L.b
    c, c1 = peek(P.L), peek(P.L, 1)
    if c == "=" and c1 != "=":
        op = "="
    elif c == "+" and c1 == "=":
        op = "+="
    else:
        restoreLex(P.L, save)
        return None
    lhs = mk(P, "variable_name", startB, nameEnd, [])
    if subEnd > nameEnd:
        lhs = mk(P, "subscript", startB, subEnd, [
            lhs, mk(P, "[", nameEnd, nameEnd + 1, []),
            parseSubscriptIndex(P, nameEnd + 1, subEnd - 1), mk(P, "]", subEnd - 1, subEnd, [])])
    opStart = P.L.b
    advance(P.L)
    if op == "+=":
        advance(P.L)
    opNode = mk(P, op, opStart, P.L.b, [])
    val: Node | None = None
    if peek(P.L) == "(":
        aOpen = leaf(P, "(", nextToken(P.L, "cmd"))
        elems = [aOpen]
        while True:
            skipBlanks(P.L)
            if peek(P.L) == ")":
                break
            e = parseWord(P, "arg")
            if not e:
                break
            elems.append(e)
        acTok = nextToken(P.L, "cmd")
        aClose = (leaf(P, ")", acTok) if acTok.value == ")" else
                  mk(P, ")", aOpen.endIndex, aOpen.endIndex, []))
        elems.append(aClose)
        val = mk(P, "array", aOpen.startIndex, aClose.endIndex, elems)
    elif peek(P.L) and peek(P.L) not in {" ", "\t", "\n", ";", "&", "|", ")", "}"}:
        val = parseWord(P, "arg")
    return mk(P, "variable_assignment", startB, val.endIndex if val else opNode.endIndex,
              [lhs, opNode, val] if val else [lhs, opNode])


def parseSubscriptIndexInline(P: ParseState) -> Node | None:
    skipBlanks(P.L)
    c = peek(P.L)
    if c in {"@", "*"} and peek(P.L, 1) == "]":
        s = P.L.b
        advance(P.L)
        return mk(P, "word", s, P.L.b, [])
    if c == "(" and peek(P.L, 1) == "(":
        s = P.L.b
        advance(P.L)
        advance(P.L)
        openNode = mk(P, "((", s, P.L.b, [])
        inner = parseArithExpr(P, "))", "var")
        skipBlanks(P.L)
        cs = P.L.b
        if peek(P.L) == ")" and peek(P.L, 1) == ")":
            advance(P.L)
            advance(P.L)
        close = mk(P, "))", cs, P.L.b, [])
        return mk(P, "compound_statement", s, close.endIndex,
                  [openNode, inner, close] if inner else [openNode, close])
    return parseArithExpr(P, "]", "word")


def parseSubscriptIndex(P: ParseState, startB: int, endB: int) -> Node:
    text = sliceBytes(P, startB, endB)
    if re.fullmatch(r"\d+", text, re.ASCII):
        return mk(P, "number", startB, endB, [])
    if re.fullmatch(r"\$([a-zA-Z_]\w*)", text, re.ASCII):
        return mk(P, "simple_expansion", startB, endB, [mk(P, "$", startB, startB + 1, []),
                  mk(P, "variable_name", startB + 1, endB, [])])
    if len(text) == 2 and text[0] == "$" and text[1] in SPECIAL_VARS:
        return mk(P, "simple_expansion", startB, endB, [mk(P, "$", startB, startB + 1, []),
                  mk(P, "special_variable_name", startB + 1, endB, [])])
    return mk(P, "word", startB, endB, [])


def isRedirectLiteralStart(P: ParseState) -> bool:
    c = peek(P.L)
    if c in {"", "\n", "|", "&", ";", "(", ")", "}"}:
        return False
    if c in {"<", ">"}:
        return peek(P.L, 1) == "("
    if isDigit(c):
        j = P.L.i
        while j < P.L.len and isDigit(P.L.src[j]):
            j += 1
        if j < P.L.len and P.L.src[j] in {"<", ">"}:
            return False
    return not (P.stopToken == "]" and c == "]")


def tryParseRedirect(P: ParseState, greedy: bool = False) -> Node | None:
    save = saveLex(P.L)
    skipBlanks(P.L)
    fd: Node | None = None
    if isDigit(peek(P.L)):
        s, j = P.L.b, P.L.i
        while j < P.L.len and isDigit(P.L.src[j]):
            j += 1
        if j < P.L.len and P.L.src[j] in {">", "<"}:
            while P.L.i < j:
                advance(P.L)
            fd = mk(P, "file_descriptor", s, P.L.b, [])
    t = nextToken(P.L, "arg")
    if t.type != "OP":
        restoreLex(P.L, save)
        return None
    v = t.value
    if v == "<<<":
        op = leaf(P, v, t)
        skipBlanks(P.L)
        target = parseWord(P, "arg")
        kids = [op, target] if target else [op]
        return mk(P, "herestring_redirect", fd.startIndex if fd else op.startIndex,
                  target.endIndex if target else op.endIndex, [fd, *kids] if fd else kids)
    if v in {"<<", "<<-"}:
        op = leaf(P, v, t)
        skipBlanks(P.L)
        dStart, quoted, delim, dc = P.L.b, False, "", peek(P.L)
        if dc in {"'", '"'}:
            quoted = True
            advance(P.L)
            while P.L.i < P.L.len and peek(P.L) != dc:
                delim += peek(P.L)
                advance(P.L)
            if P.L.i < P.L.len:
                advance(P.L)
        elif dc == "\\":
            quoted = True
            advance(P.L)
            if P.L.i < P.L.len and peek(P.L) != "\n":
                delim += peek(P.L)
                advance(P.L)
            while P.L.i < P.L.len and isIdentChar(peek(P.L)):
                delim += peek(P.L)
                advance(P.L)
        else:
            while P.L.i < P.L.len and isHeredocDelimChar(peek(P.L)):
                delim += peek(P.L)
                advance(P.L)
        startNode = mk(P, "heredoc_start", dStart, P.L.b, [])
        P.L.heredocs.append(HeredocPending(delim, v == "<<-", quoted))
        kids = [fd, op, startNode] if fd else [op, startNode]
        startIdx = fd.startIndex if fd else op.startIndex
        while True:
            skipBlanks(P.L)
            tc = peek(P.L)
            if tc in {"\n", ""} or P.L.i >= P.L.len:
                break
            if tc in {">", "<"} or isDigit(tc):
                rSave = saveLex(P.L)
                r = tryParseRedirect(P)
                if r and r.type == "file_redirect":
                    kids.append(r)
                    continue
                restoreLex(P.L, rSave)
            if tc == "|" and peek(P.L, 1) != "|":
                advance(P.L)
                skipBlanks(P.L)
                pipeCmds: list[Node] = []
                while True:
                    cmd = parseCommand(P)
                    if not cmd:
                        break
                    pipeCmds.append(cmd)
                    skipBlanks(P.L)
                    if peek(P.L) == "|" and peek(P.L, 1) != "|":
                        ps = P.L.b
                        advance(P.L)
                        pipeCmds.append(mk(P, "|", ps, P.L.b, []))
                        skipBlanks(P.L)
                        continue
                    break
                if pipeCmds:
                    kids.append(mk(P, "pipeline", pipeCmds[0].startIndex, pipeCmds[-1].endIndex, pipeCmds))
                continue
            if tc == "&" and peek(P.L, 1) == "&" or tc == "|" and peek(P.L, 1) == "|":
                advance(P.L)
                advance(P.L)
                skipBlanks(P.L)
                rhs = parseCommand(P)
                if rhs:
                    kids.append(rhs)
                continue
            if tc in {"&", ";", "(", ")"}:
                eStart = P.L.b
                while P.L.i < P.L.len and peek(P.L) != "\n":
                    advance(P.L)
                kids.append(mk(P, "ERROR", eStart, P.L.b, []))
                break
            w = parseWord(P, "arg")
            if w:
                kids.append(w)
                continue
            eStart = P.L.b
            while P.L.i < P.L.len and peek(P.L) != "\n":
                advance(P.L)
            if P.L.b > eStart:
                kids.append(mk(P, "ERROR", eStart, P.L.b, []))
            break
        return mk(P, "heredoc_redirect", startIdx, P.L.b, kids)
    if v in {"<&-", ">&-"}:
        op = leaf(P, v, t)
        kids = [fd, op] if fd else [op]
        skipBlanks(P.L)
        dSave = saveLex(P.L)
        dest = parseWord(P, "arg") if isRedirectLiteralStart(P) else None
        if dest:
            kids.append(dest)
        else:
            restoreLex(P.L, dSave)
        return mk(P, "file_redirect", fd.startIndex if fd else op.startIndex,
                  dest.endIndex if dest else op.endIndex, kids)
    if v in {">", ">>", ">&", ">|", "&>", "&>>", "<", "<&"}:
        op = leaf(P, v, t)
        kids = [fd, op] if fd else [op]
        end, taken = op.endIndex, 0
        while True:
            skipBlanks(P.L)
            if not isRedirectLiteralStart(P) or not greedy and taken >= 1:
                break
            target = (parseProcessSub(P) if peek(P.L) in {"<", ">"} and peek(P.L, 1) == "("
                      else parseWord(P, "arg"))
            if not target:
                break
            kids.append(target)
            end, taken = target.endIndex, taken + 1
        return mk(P, "file_redirect", fd.startIndex if fd else op.startIndex, end, kids)
    restoreLex(P.L, save)
    return None


def parseProcessSub(P: ParseState) -> Node | None:
    c = peek(P.L)
    if c not in {"<", ">"} or peek(P.L, 1) != "(":
        return None
    start = P.L.b
    advance(P.L)
    advance(P.L)
    openNode = mk(P, c + "(", start, P.L.b, [])
    body = parseStatements(P, ")")
    skipBlanks(P.L)
    cs = P.L.b
    if peek(P.L) == ")":
        advance(P.L)
    close = mk(P, ")", cs, P.L.b, [])
    return mk(P, "process_substitution", start, close.endIndex, [openNode, *body, close])


def scanHeredocBodies(P: ParseState) -> None:
    while P.L.i < P.L.len and peek(P.L) != "\n":
        advance(P.L)
    if P.L.i < P.L.len:
        advance(P.L)
    for hd in P.L.heredocs:
        hd.bodyStart = P.L.b
        delimLen = len(hd.delim)
        while P.L.i < P.L.len:
            lineStartB, checkI = P.L.b, P.L.i
            if hd.stripTabs:
                while checkI < P.L.len and P.L.src[checkI] == "\t":
                    checkI += 1
            if (P.L.src.startswith(hd.delim, checkI) and (checkI + delimLen >= P.L.len
                    or P.L.src[checkI + delimLen] in {"\n", "\r"})):
                hd.bodyEnd = lineStartB
                while P.L.i < checkI:
                    advance(P.L)
                hd.endStart = P.L.b
                for _ in hd.delim:
                    advance(P.L)
                hd.endEnd = P.L.b
                if P.L.i < P.L.len and peek(P.L) == "\n":
                    advance(P.L)
                return
            while P.L.i < P.L.len and peek(P.L) != "\n":
                advance(P.L)
            if P.L.i < P.L.len:
                advance(P.L)
        hd.bodyEnd = hd.endStart = hd.endEnd = P.L.b


def restoreLexToByte(P: ParseState, targetByte: int) -> None:
    byteAt(P.L, 0)
    assert P.L.byteTable is not None
    P.L.i = bisect.bisect_left(P.L.byteTable, targetByte)
    P.L.b = targetByte


def parseHeredocBodyContent(P: ParseState, start: int, end: int) -> list[Node]:
    saved = saveLex(P.L)
    restoreLexToByte(P, start)
    out: list[Node] = []
    contentStart, sawExpansion = P.L.b, False
    while P.L.b < end:
        c = peek(P.L)
        if c == "\\":
            nxt = peek(P.L, 1)
            advance(P.L)
            if nxt in {"$", "`", "\\"}:
                advance(P.L)
            continue
        if c in {"$", "`"}:
            preB = P.L.b
            exp = parseDollarLike(P)
            if exp and exp.type in {"simple_expansion", "expansion", "command_substitution", "arithmetic_expansion"}:
                if sawExpansion and preB > contentStart:
                    out.append(mk(P, "heredoc_content", contentStart, preB, []))
                out.append(exp)
                contentStart, sawExpansion = P.L.b, True
            continue
        advance(P.L)
    if sawExpansion:
        out.append(mk(P, "heredoc_content", contentStart, end, []))
    restoreLex(P.L, saved)
    return out


def parseWord(P: ParseState, _ctx: str) -> Node | None:
    skipBlanks(P.L)
    parts: list[Node] = []
    while P.L.i < P.L.len:
        c = peek(P.L)
        if c in {" ", "\t", "\n", "\r", "", "|", "&", ";", "(", ")"}:
            break
        if c in {"<", ">"}:
            if peek(P.L, 1) == "(":
                ps = parseProcessSub(P)
                if ps:
                    parts.append(ps)
                continue
            break
        if c == '"':
            parts.append(parseDoubleQuoted(P))
            continue
        if c == "'":
            parts.append(leaf(P, "raw_string", nextToken(P.L, "arg")))
            continue
        if c == "$":
            c1 = peek(P.L, 1)
            if c1 == "'":
                parts.append(leaf(P, "ansi_c_string", nextToken(P.L, "arg")))
                continue
            if c1 == '"':
                dTok = Token("DOLLAR", "$", P.L.b, P.L.b + 1)
                advance(P.L)
                parts.append(leaf(P, "$", dTok))
                parts.append(parseDoubleQuoted(P))
                continue
            if c1 == "`":
                advance(P.L)
                continue
            exp = parseDollarLike(P)
            if exp:
                parts.append(exp)
            continue
        if c == "`":
            if P.inBacktick > 0:
                break
            bt = parseBacktick(P)
            if bt:
                parts.append(bt)
            continue
        if c == "{":
            be = tryParseBraceExpr(P)
            if be:
                parts.append(be)
                continue
            if peek(P.L, 1) in {";", "|", "&", "\n", "", ")", " ", "\t"}:
                s = P.L.b
                advance(P.L)
                parts.append(mk(P, "word", s, P.L.b, []))
                continue
            cat = tryParseBraceLikeCat(P)
            if cat:
                parts.extend(cat)
                continue
        if c in {"}", "[", "]"}:
            s = P.L.b
            advance(P.L)
            parts.append(mk(P, "word", s, P.L.b, []))
            continue
        frag = parseBareWord(P)
        if not frag:
            break
        if (frag.type == "word" and re.fullmatch(r"-?(0x)?[0-9]+#", frag.text)
                and peek(P.L) == "$" and peek(P.L, 1) in {"{", "("}):
            exp = parseDollarLike(P)
            if exp:
                parts.append(mk(P, "number", frag.startIndex, exp.endIndex, [exp]))
                continue
        parts.append(frag)
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else mk(P, "concatenation", parts[0].startIndex, parts[-1].endIndex, parts)


def parseBareWord(P: ParseState) -> Node | None:
    start, startI = P.L.b, P.L.i
    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\\":
            if P.L.i + 1 >= P.L.len:
                break
            nx = peek(P.L, 1)
            if nx == "\n" or nx == "\r" and peek(P.L, 2) == "\n":
                break
            advance(P.L)
            advance(P.L)
            continue
        if c in {" ", "\t", "\n", "\r", "", "|", "&", ";", "(", ")", "<", ">", '"', "'", "$", "`", "{", "}", "[", "]"}:
            break
        advance(P.L)
    if P.L.b == start:
        return None
    text = P.src[startI:P.L.i]
    return mk(P, "number" if re.fullmatch(r"-?\d+", text, re.ASCII) else "word", start, P.L.b, [])


def tryParseBraceExpr(P: ParseState) -> Node | None:
    save = saveLex(P.L)
    if peek(P.L) != "{":
        return None
    oStart = P.L.b
    advance(P.L)
    oEnd = p1Start = P.L.b
    while isDigit(peek(P.L)) or isIdentStart(peek(P.L)):
        advance(P.L)
    p1End = P.L.b
    if p1End == p1Start or peek(P.L) != "." or peek(P.L, 1) != ".":
        restoreLex(P.L, save)
        return None
    dotStart = P.L.b
    advance(P.L)
    advance(P.L)
    dotEnd = p2Start = P.L.b
    while isDigit(peek(P.L)) or isIdentStart(peek(P.L)):
        advance(P.L)
    p2End = P.L.b
    if p2End == p2Start or peek(P.L) != "}":
        restoreLex(P.L, save)
        return None
    cStart = P.L.b
    advance(P.L)
    p1Text, p2Text = sliceBytes(P, p1Start, p1End), sliceBytes(P, p2Start, p2End)
    p1IsNum = bool(re.fullmatch(r"\d+", p1Text, re.ASCII))
    p2IsNum = bool(re.fullmatch(r"\d+", p2Text, re.ASCII))
    if p1IsNum != p2IsNum or not p1IsNum and (len(p1Text) != 1 or len(p2Text) != 1):
        restoreLex(P.L, save)
        return None
    return mk(P, "brace_expression", oStart, P.L.b, [mk(P, "{", oStart, oEnd, []),
              mk(P, "number" if p1IsNum else "word", p1Start, p1End, []),
              mk(P, "..", dotStart, dotEnd, []),
              mk(P, "number" if p2IsNum else "word", p2Start, p2End, []),
              mk(P, "}", cStart, P.L.b, [])])


def tryParseBraceLikeCat(P: ParseState) -> list[Node] | None:
    if peek(P.L) != "{":
        return None
    oStart = P.L.b
    advance(P.L)
    inner = [mk(P, "word", oStart, P.L.b, [])]
    stops = {"}", "\n", ";", "|", "&", " ", "\t", "<", ">", "(", ")"}
    while P.L.i < P.L.len:
        bc = peek(P.L)
        if bc in stops:
            break
        if bc in {"[", "]"}:
            s = P.L.b
            advance(P.L)
            inner.append(mk(P, "word", s, P.L.b, []))
            continue
        midStart = P.L.b
        while P.L.i < P.L.len and peek(P.L) not in stops | {"[", "]"}:
            advance(P.L)
        if P.L.b <= midStart:
            break
        typ = "number" if re.fullmatch(r"-?\d+", sliceBytes(P, midStart, P.L.b), re.ASCII) else "word"
        inner.append(mk(P, typ, midStart, P.L.b, []))
    if peek(P.L) == "}":
        s = P.L.b
        advance(P.L)
        inner.append(mk(P, "word", s, P.L.b, []))
    return inner


def parseDoubleQuoted(P: ParseState) -> Node:
    qStart = P.L.b
    advance(P.L)
    parts = [mk(P, '"', qStart, P.L.b, [])]
    contentStart, contentStartI = P.L.b, P.L.i

    def flushContent() -> None:
        if P.L.b > contentStart and not re.fullmatch(r"[ \t]+", P.src[contentStartI:P.L.i]):
            parts.append(mk(P, "string_content", contentStart, P.L.b, []))

    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == '"':
            break
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c == "\n":
            flushContent()
            advance(P.L)
            contentStart, contentStartI = P.L.b, P.L.i
            continue
        if c == "$":
            c1 = peek(P.L, 1)
            if c1 in {"(", "{"} or isIdentStart(c1) or c1 in SPECIAL_VARS or isDigit(c1):
                flushContent()
                exp = parseDollarLike(P)
                if exp:
                    parts.append(exp)
                contentStart, contentStartI = P.L.b, P.L.i
                continue
            if c1 not in {'"', ""}:
                flushContent()
                s = P.L.b
                advance(P.L)
                parts.append(mk(P, "$", s, P.L.b, []))
                contentStart, contentStartI = P.L.b, P.L.i
                continue
        if c == "`":
            flushContent()
            bt = parseBacktick(P)
            if bt:
                parts.append(bt)
            contentStart, contentStartI = P.L.b, P.L.i
            continue
        advance(P.L)
    flushContent()
    cs = P.L.b
    if peek(P.L) == '"':
        advance(P.L)
    close = mk(P, '"', cs, P.L.b, [])
    parts.append(close)
    return mk(P, "string", qStart, close.endIndex, parts)


def parseDollarLike(P: ParseState) -> Node | None:
    c1, dStart = peek(P.L, 1), P.L.b
    if c1 == "(" and peek(P.L, 2) == "(" or c1 == "[":
        opener, closer = ("$((", "))") if c1 == "(" else ("$[", "]")
        for _ in opener:
            advance(P.L)
        openNode = mk(P, opener, dStart, P.L.b, [])
        exprs = parseArithCommaList(P, closer, "var")
        skipBlanks(P.L)
        cs = P.L.b
        if P.L.src.startswith(closer, P.L.i):
            for _ in closer:
                advance(P.L)
        close = mk(P, closer, cs, P.L.b, [])
        return mk(P, "arithmetic_expansion", dStart, close.endIndex, [openNode, *exprs, close])
    if c1 == "(":
        advance(P.L)
        advance(P.L)
        openNode = mk(P, "$(", dStart, P.L.b, [])
        body = parseStatements(P, ")")
        skipBlanks(P.L)
        cs = P.L.b
        if peek(P.L) == ")":
            advance(P.L)
        close = mk(P, ")", cs, P.L.b, [])
        if (len(body) == 1 and body[0].type == "redirected_statement" and len(body[0].children) == 1
                and body[0].children[0].type == "file_redirect"):
            body = body[0].children
        return mk(P, "command_substitution", dStart, close.endIndex, [openNode, *body, close])
    if c1 == "{":
        advance(P.L)
        advance(P.L)
        openNode = mk(P, "${", dStart, P.L.b, [])
        inner = parseExpansionBody(P)
        cs = P.L.b
        if peek(P.L) == "}":
            advance(P.L)
        close = mk(P, "}", cs, P.L.b, [])
        return mk(P, "expansion", dStart, close.endIndex, [openNode, *inner, close])
    advance(P.L)
    dollar = mk(P, "$", dStart, P.L.b, [])
    nc = peek(P.L)
    if nc == "_" and not isIdentChar(peek(P.L, 1)):
        typ, count = "special_variable_name", 1
    elif isIdentStart(nc):
        typ, count = "variable_name", 0
    elif isDigit(nc):
        typ, count = "variable_name", 1
    elif nc in SPECIAL_VARS:
        typ, count = "special_variable_name", 1
    else:
        return dollar
    s = P.L.b
    if count:
        advance(P.L)
    else:
        while isIdentChar(peek(P.L)):
            advance(P.L)
    vn = mk(P, typ, s, P.L.b, [])
    return mk(P, "simple_expansion", dStart, P.L.b, [dollar, vn])


def parseBacktick(P: ParseState) -> Node | None:
    start = P.L.b
    advance(P.L)
    openNode = mk(P, "`", start, P.L.b, [])
    P.inBacktick += 1
    body: list[Node] = []
    while True:
        skipBlanks(P.L)
        if peek(P.L) in {"`", ""}:
            break
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type in {"EOF", "BACKTICK"}:
            restoreLex(P.L, save)
            break
        if t.type == "NEWLINE":
            continue
        restoreLex(P.L, save)
        stmt = parseAndOr(P)
        if not stmt:
            break
        body.append(stmt)
        skipBlanks(P.L)
        if peek(P.L) == "`":
            break
        save2 = saveLex(P.L)
        sep = nextToken(P.L, "cmd")
        if sep.type == "OP" and sep.value in {";", "&"}:
            body.append(leaf(P, sep.value, sep))
        elif sep.type != "NEWLINE":
            restoreLex(P.L, save2)
    P.inBacktick -= 1
    cs = P.L.b
    if peek(P.L) == "`":
        advance(P.L)
    close = mk(P, "`", cs, P.L.b, [])
    return mk(P, "command_substitution", start, close.endIndex, [openNode, *body, close]) if body else None


def parseExpansionBody(P: ParseState) -> list[Node]:
    out: list[Node] = []
    skipBlanks(P.L)
    c0, c1 = peek(P.L), peek(P.L, 1)
    if c0 == "#" and c1 == "!" and peek(P.L, 2) == "}":
        advance(P.L)
        advance(P.L)
        return out
    if c0 == "!" and c1 == "#":
        j = 2
        if peek(P.L, j) == "#":
            j += 1
        if peek(P.L, j) == " ":
            j += 1
        if peek(P.L, j) == "}":
            for _ in range(j):
                advance(P.L)
            return out
    if peek(P.L) == "#":
        s = P.L.b
        advance(P.L)
        out.append(mk(P, "#", s, P.L.b, []))
    pc = peek(P.L)
    if pc in {"!", "=", "~"} and (isIdentStart(peek(P.L, 1)) or isDigit(peek(P.L, 1))):
        s = P.L.b
        advance(P.L)
        out.append(mk(P, pc, s, P.L.b, []))
    skipBlanks(P.L)
    s = P.L.b
    if isIdentStart(peek(P.L)):
        while isIdentChar(peek(P.L)):
            advance(P.L)
        out.append(mk(P, "variable_name", s, P.L.b, []))
    elif isDigit(peek(P.L)):
        while isDigit(peek(P.L)):
            advance(P.L)
        out.append(mk(P, "variable_name", s, P.L.b, []))
    elif peek(P.L) in SPECIAL_VARS:
        advance(P.L)
        out.append(mk(P, "special_variable_name", s, P.L.b, []))
    if peek(P.L) == "[":
        varNode = out[-1] if out else None
        brOpen = P.L.b
        advance(P.L)
        brOpenNode = mk(P, "[", brOpen, P.L.b, [])
        idx = parseSubscriptIndexInline(P)
        skipBlanks(P.L)
        brClose = P.L.b
        if peek(P.L) == "]":
            advance(P.L)
        brCloseNode = mk(P, "]", brClose, P.L.b, [])
        if varNode:
            kids = [varNode, brOpenNode, idx, brCloseNode] if idx else [varNode, brOpenNode, brCloseNode]
            out[-1] = mk(P, "subscript", varNode.startIndex, P.L.b, kids)
    skipBlanks(P.L)
    tc = peek(P.L)
    if tc in {"*", "@"} and peek(P.L, 1) == "}":
        s = P.L.b
        advance(P.L)
        out.append(mk(P, tc, s, P.L.b, []))
        return out
    if tc == "@" and isIdentStart(peek(P.L, 1)):
        s = P.L.b
        advance(P.L)
        out.append(mk(P, "@", s, P.L.b, []))
        while isIdentChar(peek(P.L)):
            advance(P.L)
        return out
    c = peek(P.L)
    if c == ":":
        c1 = peek(P.L, 1)
        if c1 in {"\n", "}"}:
            advance(P.L)
            while peek(P.L) == "\n":
                advance(P.L)
            return out
        if c1 not in {"-", "=", "?", "+"}:
            advance(P.L)
            skipBlanks(P.L)
            off: Node | None
            if peek(P.L) == "-" and isDigit(peek(P.L, 1)):
                ns = P.L.b
                advance(P.L)
                while isDigit(peek(P.L)):
                    advance(P.L)
                off = mk(P, "number", ns, P.L.b, [])
            else:
                off = parseArithExpr(P, ":}", "var")
            if off:
                out.append(off)
            skipBlanks(P.L)
            if peek(P.L) == ":":
                advance(P.L)
                skipBlanks(P.L)
                length: Node | None
                if peek(P.L) == "-" and isDigit(peek(P.L, 1)):
                    ns = P.L.b
                    advance(P.L)
                    while isDigit(peek(P.L)):
                        advance(P.L)
                    length = mk(P, "number", ns, P.L.b, [])
                else:
                    length = parseArithExpr(P, "}", "var")
                if length:
                    out.append(length)
            return out
    if c not in {":", "#", "%", "/", "^", ",", "-", "=", "?", "+"}:
        return out
    s, c1, op = P.L.b, peek(P.L, 1), c
    if c == ":" and c1 in {"-", "=", "?", "+"} or c in {"#", "%", "/", "^", ","} and c1 == c:
        advance(P.L)
        advance(P.L)
        op = c + c1
    else:
        advance(P.L)
    out.append(mk(P, op, s, P.L.b, []))
    isPattern = op in {"#", "##", "%", "%%", "/", "//", "^", "^^", ",", ",,"}
    if op in {"/", "//"}:
        ac = peek(P.L)
        if ac in {"#", "%"}:
            s = P.L.b
            advance(P.L)
            out.append(mk(P, ac, s, P.L.b, []))
        if peek(P.L) == '"':
            out.append(parseDoubleQuoted(P))
        regex = parseExpansionRest(P, "regex", True)
        if regex:
            out.append(regex)
        if peek(P.L) == "/":
            s = P.L.b
            advance(P.L)
            out.append(mk(P, "/", s, P.L.b, []))
            repl = parseExpansionRest(P, "replword", False)
            if repl:
                if repl.type == "concatenation" and len(repl.children) == 2 and repl.children[0].type == "command_substitution":
                    out.extend(repl.children)
                else:
                    out.append(repl)
    elif op in {"#", "##", "%", "%%"}:
        out.extend(parseExpansionRegexSegmented(P))
    else:
        rest = parseExpansionRest(P, "regex" if isPattern else "word", False)
        if rest:
            out.append(rest)
    return out


def parseExpansionRest(P: ParseState, nodeType: str, stopAtSlash: bool) -> Node | None:
    start = P.L.b
    if nodeType == "word" and peek(P.L) == "(":
        advance(P.L)
        elems = [mk(P, "(", start, P.L.b, [])]
        while P.L.i < P.L.len:
            skipBlanks(P.L)
            if peek(P.L) in {")", "}", "\n", ""}:
                break
            ws = P.L.b
            while P.L.i < P.L.len and peek(P.L) not in {")", "}", " ", "\t", "\n", ""}:
                advance(P.L)
            if P.L.b > ws:
                elems.append(mk(P, "word", ws, P.L.b, []))
            else:
                break
        if peek(P.L) == ")":
            cs = P.L.b
            advance(P.L)
            elems.append(mk(P, ")", cs, P.L.b, []))
        while peek(P.L) == "\n":
            advance(P.L)
        return mk(P, "array", start, P.L.b, elems)
    if nodeType == "regex":
        braceDepth = 0
        while P.L.i < P.L.len:
            c = peek(P.L)
            if c == "\n" or braceDepth == 0 and (c == "}" or stopAtSlash and c == "/"):
                break
            if c == "\\" and P.L.i + 1 < P.L.len:
                advance(P.L)
                advance(P.L)
                continue
            if c in {'"', "'"}:
                advance(P.L)
                while P.L.i < P.L.len and peek(P.L) != c:
                    if peek(P.L) == "\\" and P.L.i + 1 < P.L.len:
                        advance(P.L)
                    advance(P.L)
                if peek(P.L) == c:
                    advance(P.L)
                continue
            if c == "$" and peek(P.L, 1) in {"{", "("}:
                opener = peek(P.L, 1)
                closer = "}" if opener == "{" else ")"
                advance(P.L)
                advance(P.L)
                depth = 1
                while P.L.i < P.L.len and depth > 0:
                    nc = peek(P.L)
                    depth += 1 if nc == opener else -1 if nc == closer else 0
                    advance(P.L)
                continue
            braceDepth += 1 if c == "{" else -1 if c == "}" and braceDepth > 0 else 0
            advance(P.L)
        end = P.L.b
        while peek(P.L) == "\n":
            advance(P.L)
        return None if end == start else mk(P, "regex", start, end, [])
    parts: list[Node] = []
    segStart, braceDepth = P.L.b, 0

    def flushSeg() -> None:
        if P.L.b > segStart:
            parts.append(mk(P, "word", segStart, P.L.b, []))

    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\n" or braceDepth == 0 and (c == "}" or stopAtSlash and c == "/"):
            break
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        c1 = peek(P.L, 1)
        if c == "$":
            if c1 in {"{", "(", "["} or isIdentStart(c1) or isDigit(c1) or c1 in SPECIAL_VARS:
                flushSeg()
                exp = parseDollarLike(P)
                if exp:
                    parts.append(exp)
                segStart = P.L.b
                continue
            if c1 == "'":
                flushSeg()
                aStart = P.L.b
                advance(P.L)
                advance(P.L)
                while P.L.i < P.L.len and peek(P.L) != "'":
                    if peek(P.L) == "\\" and P.L.i + 1 < P.L.len:
                        advance(P.L)
                    advance(P.L)
                if peek(P.L) == "'":
                    advance(P.L)
                parts.append(mk(P, "ansi_c_string", aStart, P.L.b, []))
                segStart = P.L.b
                continue
        if c == '"':
            flushSeg()
            parts.append(parseDoubleQuoted(P))
            segStart = P.L.b
            continue
        if c == "'":
            flushSeg()
            rStart = P.L.b
            advance(P.L)
            while P.L.i < P.L.len and peek(P.L) != "'":
                advance(P.L)
            if peek(P.L) == "'":
                advance(P.L)
            parts.append(mk(P, "raw_string", rStart, P.L.b, []))
            segStart = P.L.b
            continue
        if c in {"<", ">"} and c1 == "(" or c == "`":
            flushSeg()
            sub = parseBacktick(P) if c == "`" else parseProcessSub(P)
            if sub:
                parts.append(sub)
            segStart = P.L.b
            continue
        braceDepth += 1 if c == "{" else -1 if c == "}" and braceDepth > 0 else 0
        advance(P.L)
    flushSeg()
    while peek(P.L) == "\n":
        advance(P.L)
    if len(parts) > 1 and parts[0].type == "word" and re.fullmatch(r"[ \t]+", parts[0].text):
        parts.pop(0)
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else mk(P, "concatenation", parts[0].startIndex, parts[-1].endIndex, parts)


def parseExpansionRegexSegmented(P: ParseState) -> list[Node]:
    out: list[Node] = []
    segStart = P.L.b

    def flushRegex() -> None:
        if P.L.b > segStart:
            out.append(mk(P, "regex", segStart, P.L.b, []))

    while P.L.i < P.L.len:
        c = peek(P.L)
        if c in {"}", "\n"}:
            break
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c == '"':
            flushRegex()
            out.append(parseDoubleQuoted(P))
            segStart = P.L.b
            continue
        if c == "'":
            flushRegex()
            s = P.L.b
            advance(P.L)
            while P.L.i < P.L.len and peek(P.L) != "'":
                advance(P.L)
            if peek(P.L) == "'":
                advance(P.L)
            out.append(mk(P, "raw_string", s, P.L.b, []))
            segStart = P.L.b
            continue
        if c == "$" and peek(P.L, 1) in {"{", "("}:
            opener = peek(P.L, 1)
            closer = "}" if opener == "{" else ")"
            advance(P.L)
            advance(P.L)
            depth = 1
            while P.L.i < P.L.len and depth > 0:
                nc = peek(P.L)
                depth += 1 if nc == opener else -1 if nc == closer else 0
                advance(P.L)
            continue
        advance(P.L)
    flushRegex()
    while peek(P.L) == "\n":
        advance(P.L)
    return out


def consumeKeyword(P: ParseState, name: str, kids: list[Node]) -> None:
    skipNewlines(P)
    save = saveLex(P.L)
    t = nextToken(P.L, "cmd")
    if t.type == "WORD" and t.value == name:
        kids.append(leaf(P, name, t))
    else:
        restoreLex(P.L, save)


def parseIf(P: ParseState, ifTok: Token) -> Node:
    ifKw = leaf(P, "if", ifTok)
    kids = [ifKw, *parseStatements(P, None)]
    consumeKeyword(P, "then", kids)
    kids.extend(parseStatements(P, None))
    while True:
        save = saveLex(P.L)
        t = nextToken(P.L, "cmd")
        if t.type == "WORD" and t.value == "elif":
            eKw = leaf(P, "elif", t)
            eKids = [eKw, *parseStatements(P, None)]
            consumeKeyword(P, "then", eKids)
            eKids.extend(parseStatements(P, None))
            kids.append(mk(P, "elif_clause", eKw.startIndex, eKids[-1].endIndex, eKids))
        elif t.type == "WORD" and t.value == "else":
            elKw = leaf(P, "else", t)
            elBody = parseStatements(P, None)
            kids.append(mk(P, "else_clause", elKw.startIndex,
                           elBody[-1].endIndex if elBody else elKw.endIndex, [elKw, *elBody]))
        else:
            restoreLex(P.L, save)
            break
    consumeKeyword(P, "fi", kids)
    return mk(P, "if_statement", ifKw.startIndex, kids[-1].endIndex, kids)


def parseWhile(P: ParseState, kwTok: Token) -> Node:
    kw = leaf(P, kwTok.value, kwTok)
    kids = [kw, *parseStatements(P, None)]
    dg = parseDoGroup(P)
    if dg:
        kids.append(dg)
    return mk(P, "while_statement", kw.startIndex, kids[-1].endIndex, kids)


def parseFor(P: ParseState, forTok: Token) -> Node:
    forKw = leaf(P, forTok.value, forTok)
    skipBlanks(P.L)
    if forTok.value == "for" and peek(P.L) == "(" and peek(P.L, 1) == "(":
        s = P.L.b
        advance(P.L)
        advance(P.L)
        kids = [forKw, mk(P, "((", s, P.L.b, [])]
        for k in range(3):
            skipBlanks(P.L)
            kids.extend(parseArithCommaList(P, ";" if k < 2 else "))", "assign"))
            if k < 2 and peek(P.L) == ";":
                s = P.L.b
                advance(P.L)
                kids.append(mk(P, ";", s, P.L.b, []))
        skipBlanks(P.L)
        if peek(P.L) == ")" and peek(P.L, 1) == ")":
            s = P.L.b
            advance(P.L)
            advance(P.L)
            kids.append(mk(P, "))", s, P.L.b, []))
        save = saveLex(P.L)
        sep = nextToken(P.L, "cmd")
        if sep.type == "OP" and sep.value == ";":
            kids.append(leaf(P, ";", sep))
        elif sep.type != "NEWLINE":
            restoreLex(P.L, save)
        dg = parseDoGroup(P)
        if dg:
            kids.append(dg)
        else:
            skipNewlines(P)
            skipBlanks(P.L)
            if peek(P.L) == "{":
                s = P.L.b
                advance(P.L)
                brace = mk(P, "{", s, P.L.b, [])
                body = parseStatements(P, "}")
                cs = P.L.b
                if peek(P.L) == "}":
                    advance(P.L)
                close = mk(P, "}", cs, P.L.b, [])
                kids.append(mk(P, "compound_statement", s, close.endIndex, [brace, *body, close]))
        return mk(P, "c_style_for_statement", forKw.startIndex, kids[-1].endIndex, kids)
    kids = [forKw]
    varTok = nextToken(P.L, "arg")
    kids.append(mk(P, "variable_name", varTok.start, varTok.end, []))
    skipBlanks(P.L)
    save = saveLex(P.L)
    inTok = nextToken(P.L, "arg")
    if inTok.type == "WORD" and inTok.value == "in":
        kids.append(leaf(P, "in", inTok))
        while True:
            skipBlanks(P.L)
            if peek(P.L) in {";", "\n", ""}:
                break
            w = parseWord(P, "arg")
            if not w:
                break
            kids.append(w)
    else:
        restoreLex(P.L, save)
    save2 = saveLex(P.L)
    sep = nextToken(P.L, "cmd")
    if sep.type == "OP" and sep.value == ";":
        kids.append(leaf(P, ";", sep))
    elif sep.type != "NEWLINE":
        restoreLex(P.L, save2)
    dg = parseDoGroup(P)
    if dg:
        kids.append(dg)
    return mk(P, "for_statement", forKw.startIndex, kids[-1].endIndex, kids)


def parseDoGroup(P: ParseState) -> Node | None:
    skipNewlines(P)
    save = saveLex(P.L)
    doTok = nextToken(P.L, "cmd")
    if doTok.type != "WORD" or doTok.value != "do":
        restoreLex(P.L, save)
        return None
    doKw = leaf(P, "do", doTok)
    kids = [doKw, *parseStatements(P, None)]
    consumeKeyword(P, "done", kids)
    return mk(P, "do_group", doKw.startIndex, kids[-1].endIndex, kids)


def parseCase(P: ParseState, caseTok: Token) -> Node:
    caseKw = leaf(P, "case", caseTok)
    kids = [caseKw]
    skipBlanks(P.L)
    word = parseWord(P, "arg")
    if word:
        kids.append(word)
    skipBlanks(P.L)
    consumeKeyword(P, "in", kids)
    skipNewlines(P)
    while True:
        skipBlanks(P.L)
        skipNewlines(P)
        save = saveLex(P.L)
        t = nextToken(P.L, "arg")
        if t.type == "WORD" and t.value == "esac":
            kids.append(leaf(P, "esac", t))
            break
        if t.type == "EOF":
            break
        restoreLex(P.L, save)
        item = parseCaseItem(P)
        if not item:
            break
        kids.append(item)
    return mk(P, "case_statement", caseKw.startIndex, kids[-1].endIndex, kids)


def parseCaseItem(P: ParseState) -> Node | None:
    skipBlanks(P.L)
    start = P.L.b
    kids: list[Node] = []
    if peek(P.L) == "(":
        s = P.L.b
        advance(P.L)
        kids.append(mk(P, "(", s, P.L.b, []))
    isFirstAlt = True
    while True:
        skipBlanks(P.L)
        if peek(P.L) in {")", ""}:
            break
        pats = parseCasePattern(P)
        if not pats:
            break
        if not isFirstAlt and len(pats) > 1:
            rewritten = [mk(P, "word", p.startIndex, p.endIndex, []) if p.type == "extglob_pattern" else p for p in pats]
            kids.append(mk(P, "concatenation", rewritten[0].startIndex, rewritten[-1].endIndex, rewritten))
        else:
            kids.extend(pats)
        isFirstAlt = False
        skipBlanks(P.L)
        if peek(P.L) == "\\" and peek(P.L, 1) == "\n":
            advance(P.L)
            advance(P.L)
            skipBlanks(P.L)
        if peek(P.L) != "|":
            break
        s = P.L.b
        advance(P.L)
        kids.append(mk(P, "|", s, P.L.b, []))
        if peek(P.L) == "\\" and peek(P.L, 1) == "\n":
            advance(P.L)
            advance(P.L)
    if peek(P.L) == ")":
        s = P.L.b
        advance(P.L)
        kids.append(mk(P, ")", s, P.L.b, []))
    body = parseStatements(P, None)
    kids.extend(body)
    save = saveLex(P.L)
    term = nextToken(P.L, "cmd")
    if term.type == "OP" and term.value in {";;", ";&", ";;&"}:
        kids.append(leaf(P, term.value, term))
    else:
        restoreLex(P.L, save)
    if not kids:
        return None
    if not body:
        for i, node in enumerate(kids):
            if node.type == "extglob_pattern":
                text = sliceBytes(P, node.startIndex, node.endIndex)
                if re.match(r"^[-+?*@!][a-zA-Z]", text) and not re.search(r"[*?(]", text):
                    kids[i] = mk(P, "word", node.startIndex, node.endIndex, [])
    return mk(P, "case_item", start, kids[-1].endIndex, kids)


def parseCasePattern(P: ParseState) -> list[Node]:
    skipBlanks(P.L)
    save = saveLex(P.L)
    start, startI, parenDepth = P.L.b, P.L.i, 0
    hasDollar = hasBracketOutsideParen = hasQuote = False
    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c in {'"', "'"}:
            hasQuote = True
            advance(P.L)
            while P.L.i < P.L.len and peek(P.L) != c:
                if peek(P.L) == "\\" and P.L.i + 1 < P.L.len:
                    advance(P.L)
                advance(P.L)
            if peek(P.L) == c:
                advance(P.L)
            continue
        if c == "(":
            parenDepth += 1
            advance(P.L)
            continue
        if parenDepth > 0:
            if c == ")":
                parenDepth -= 1
                advance(P.L)
                continue
            if c == "\n":
                break
            advance(P.L)
            continue
        if c in {")", "|", " ", "\t", "\n"}:
            break
        hasDollar = hasDollar or c == "$"
        hasBracketOutsideParen = hasBracketOutsideParen or c == "["
        advance(P.L)
    if P.L.b == start:
        return []
    text = P.src[startI:P.L.i]
    hasExtglobParen = bool(re.search(r"[*?+@!]\(", text))
    if hasQuote and not hasExtglobParen:
        restoreLex(P.L, save)
        return parseCasePatternSegmented(P)
    if not hasExtglobParen and (hasDollar or hasBracketOutsideParen):
        restoreLex(P.L, save)
        w = parseWord(P, "arg")
        return [w] if w else []
    typ = "extglob_pattern" if hasExtglobParen or re.search(r"[*?]|^[-+?*@!][a-zA-Z]", text) else "word"
    return [mk(P, typ, start, P.L.b, [])]


def parseCasePatternSegmented(P: ParseState) -> list[Node]:
    parts: list[Node] = []
    segStart, segStartI = P.L.b, P.L.i

    def flushSeg() -> None:
        if P.L.i > segStartI:
            typ = "extglob_pattern" if re.search(r"[*?]", P.src[segStartI:P.L.i]) else "word"
            parts.append(mk(P, typ, segStart, P.L.b, []))

    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c == '"':
            flushSeg()
            parts.append(parseDoubleQuoted(P))
            segStart, segStartI = P.L.b, P.L.i
            continue
        if c == "'":
            flushSeg()
            parts.append(leaf(P, "raw_string", nextToken(P.L, "arg")))
            segStart, segStartI = P.L.b, P.L.i
            continue
        if c in {")", "|", " ", "\t", "\n"}:
            break
        advance(P.L)
    flushSeg()
    return parts


def parseFunction(P: ParseState, fnTok: Token) -> Node:
    fnKw = leaf(P, "function", fnTok)
    skipBlanks(P.L)
    nameTok = nextToken(P.L, "arg")
    kids = [fnKw, mk(P, "word", nameTok.start, nameTok.end, [])]
    skipBlanks(P.L)
    if peek(P.L) == "(" and peek(P.L, 1) == ")":
        kids.append(leaf(P, "(", nextToken(P.L, "cmd")))
        kids.append(leaf(P, ")", nextToken(P.L, "cmd")))
    skipBlanks(P.L)
    skipNewlines(P)
    body = parseCommand(P)
    if body:
        if (body.type == "redirected_statement" and len(body.children) >= 2
                and body.children[0].type == "compound_statement"):
            kids.extend(body.children)
        else:
            kids.append(body)
    return mk(P, "function_definition", fnKw.startIndex, kids[-1].endIndex, kids)


def parseDeclaration(P: ParseState, kwTok: Token) -> Node:
    kw = leaf(P, kwTok.value, kwTok)
    kids = [kw]
    while True:
        skipBlanks(P.L)
        c = peek(P.L)
        if c in {"", "\n", ";", "&", "|", ")", "<", ">"}:
            break
        a = tryParseAssignment(P)
        if a:
            kids.append(a)
            continue
        if c in {'"', "'", "$"}:
            w = parseWord(P, "arg")
            if w:
                kids.append(w)
                continue
            break
        save = saveLex(P.L)
        tok = nextToken(P.L, "arg")
        if tok.type not in {"WORD", "NUMBER"}:
            restoreLex(P.L, save)
            break
        typ = "variable_name" if not tok.value.startswith("-") and isIdentStart(tok.value[:1]) else "word"
        kids.append(mk(P, typ, tok.start, tok.end, []))
    return mk(P, "declaration_command", kw.startIndex, kids[-1].endIndex, kids)


def parseUnset(P: ParseState, kwTok: Token) -> Node:
    kw = leaf(P, "unset", kwTok)
    kids = [kw]
    while True:
        skipBlanks(P.L)
        if peek(P.L) in {"", "\n", ";", "&", "|", ")", "<", ">"}:
            break
        arg = parseWord(P, "arg")
        if not arg:
            break
        if arg.type == "word" and not arg.text.startswith("-"):
            kids.append(mk(P, "variable_name", arg.startIndex, arg.endIndex, []))
        else:
            kids.append(arg)
    return mk(P, "unset_command", kw.startIndex, kids[-1].endIndex, kids)


def parseTestExpr(P: ParseState, closer: str) -> Node | None:
    return parseTestOr(P, closer)


def parseTestOr(P: ParseState, closer: str) -> Node | None:
    left = parseTestAnd(P, closer)
    if not left:
        return None
    while True:
        skipBlanks(P.L)
        save = saveLex(P.L)
        if peek(P.L) != "|" or peek(P.L, 1) != "|":
            break
        s = P.L.b
        advance(P.L)
        advance(P.L)
        op = mk(P, "||", s, P.L.b, [])
        right = parseTestAnd(P, closer)
        if not right:
            restoreLex(P.L, save)
            break
        left = mk(P, "binary_expression", left.startIndex, right.endIndex, [left, op, right])
    return left


def parseTestAnd(P: ParseState, closer: str) -> Node | None:
    left = parseTestUnary(P, closer)
    if not left:
        return None
    while True:
        skipBlanks(P.L)
        if peek(P.L) != "&" or peek(P.L, 1) != "&":
            break
        s = P.L.b
        advance(P.L)
        advance(P.L)
        op = mk(P, "&&", s, P.L.b, [])
        right = parseTestUnary(P, closer)
        if not right:
            break
        left = mk(P, "binary_expression", left.startIndex, right.endIndex, [left, op, right])
    return left


def parseTestUnary(P: ParseState, closer: str) -> Node | None:
    skipBlanks(P.L)
    if peek(P.L) != "(":
        return parseTestBinary(P, closer)
    s = P.L.b
    advance(P.L)
    openNode = mk(P, "(", s, P.L.b, [])
    inner = parseTestOr(P, closer)
    skipBlanks(P.L)
    cs = P.L.b
    if peek(P.L) == ")":
        advance(P.L)
    close = mk(P, ")", cs, P.L.b, [])
    return mk(P, "parenthesized_expression", openNode.startIndex, close.endIndex,
              [openNode, inner, close] if inner else [openNode, close])


def parseTestNegatablePrimary(P: ParseState, closer: str) -> Node | None:
    skipBlanks(P.L)
    c = peek(P.L)
    if c == "!":
        s = P.L.b
        advance(P.L)
        bang = mk(P, "!", s, P.L.b, [])
        inner = parseTestNegatablePrimary(P, closer)
        return mk(P, "unary_expression", s, inner.endIndex, [bang, inner]) if inner else bang
    if c == "-" and isIdentStart(peek(P.L, 1)):
        s = P.L.b
        advance(P.L)
        while isIdentChar(peek(P.L)):
            advance(P.L)
        op = mk(P, "test_operator", s, P.L.b, [])
        skipBlanks(P.L)
        arg = parseTestPrimary(P, closer)
        return mk(P, "unary_expression", s, arg.endIndex, [op, arg]) if arg else op
    return parseTestPrimary(P, closer)


def parseTestBinary(P: ParseState, closer: str) -> Node | None:
    skipBlanks(P.L)
    left = parseTestNegatablePrimary(P, closer)
    if not left:
        return None
    skipBlanks(P.L)
    c, c1, os = peek(P.L), peek(P.L, 1), P.L.b
    op: Node | None = None
    if c + c1 in {"==", "!=", "=~"}:
        advance(P.L)
        advance(P.L)
        op = mk(P, c + c1, os, P.L.b, [])
    elif c == "=" and c1 != "=" or c == "<" and c1 != "<" or c == ">" and c1 != ">":
        advance(P.L)
        op = mk(P, c, os, P.L.b, [])
    elif c == "-" and isIdentStart(c1):
        advance(P.L)
        while isIdentChar(peek(P.L)):
            advance(P.L)
        op = mk(P, "test_operator", os, P.L.b, [])
    if not op:
        return left
    skipBlanks(P.L)
    if closer == "]]":
        if op.type == "=~":
            skipBlanks(P.L)
            rc = peek(P.L)
            rhs: Node | None = None
            if rc in {'"', "'"}:
                save = saveLex(P.L)
                quoted = parseDoubleQuoted(P) if rc == '"' else leaf(P, "raw_string", nextToken(P.L, "arg"))
                j = P.L.i
                while j < P.L.len and P.src[j] in {" ", "\t"}:
                    j += 1
                nc, nc1 = P.src[j:j + 1], P.src[j + 1:j + 2]
                if nc + nc1 in {"]]", "&&", "||"} or nc in {"\n", ""}:
                    rhs = quoted
                else:
                    restoreLex(P.L, save)
            if not rhs:
                rhs = parseTestRegexRhs(P)
            return mk(P, "binary_expression", left.startIndex, rhs.endIndex, [left, op, rhs]) if rhs else left
        if op.type == "=":
            rhs = parseTestRegexRhs(P)
            return mk(P, "binary_expression", left.startIndex, rhs.endIndex, [left, op, rhs]) if rhs else left
        if op.type in {"==", "!="}:
            parts = parseTestExtglobRhs(P)
            return mk(P, "binary_expression", left.startIndex, parts[-1].endIndex, [left, op, *parts]) if parts else left
    right = parseTestPrimary(P, closer)
    return mk(P, "binary_expression", left.startIndex, right.endIndex, [left, op, right]) if right else left


def parseTestRegexRhs(P: ParseState) -> Node | None:
    skipBlanks(P.L)
    start, parenDepth, bracketDepth = P.L.b, 0, 0
    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c == "\n":
            break
        if parenDepth == 0 and bracketDepth == 0:
            if c == "]" and peek(P.L, 1) == "]":
                break
            if c in {" ", "\t"}:
                j = P.L.i
                while j < P.L.len and P.L.src[j] in {" ", "\t"}:
                    j += 1
                if P.L.src[j:j + 2] in {"]]", "&&", "||"}:
                    break
                advance(P.L)
                continue
        if c == "(":
            parenDepth += 1
        elif c == ")" and parenDepth > 0:
            parenDepth -= 1
        elif c == "[":
            bracketDepth += 1
        elif c == "]" and bracketDepth > 0:
            bracketDepth -= 1
        advance(P.L)
    return None if P.L.b == start else mk(P, "regex", start, P.L.b, [])


def parseTestExtglobRhs(P: ParseState) -> list[Node]:
    skipBlanks(P.L)
    parts: list[Node] = []
    segStart, segStartI, parenDepth = P.L.b, P.L.i, 0

    def flushSeg() -> None:
        if P.L.i > segStartI:
            typ = "number" if re.fullmatch(r"\d+", P.src[segStartI:P.L.i], re.ASCII) else "extglob_pattern"
            parts.append(mk(P, typ, segStart, P.L.b, []))

    while P.L.i < P.L.len:
        c = peek(P.L)
        if c == "\\" and P.L.i + 1 < P.L.len:
            advance(P.L)
            advance(P.L)
            continue
        if c == "\n":
            break
        if parenDepth == 0:
            if c == "]" and peek(P.L, 1) == "]":
                break
            if c in {" ", "\t"}:
                j = P.L.i
                while j < P.L.len and P.L.src[j] in {" ", "\t"}:
                    j += 1
                if P.L.src[j:j + 2] in {"]]", "&&", "||"}:
                    break
                advance(P.L)
                continue
        if c == "$":
            c1 = peek(P.L, 1)
            if c1 in {"(", "{"} or isIdentStart(c1) or c1 in SPECIAL_VARS:
                flushSeg()
                exp = parseDollarLike(P)
                if exp:
                    parts.append(exp)
                segStart, segStartI = P.L.b, P.L.i
                continue
        if c == '"':
            flushSeg()
            parts.append(parseDoubleQuoted(P))
            segStart, segStartI = P.L.b, P.L.i
            continue
        if c == "'":
            flushSeg()
            parts.append(leaf(P, "raw_string", nextToken(P.L, "arg")))
            segStart, segStartI = P.L.b, P.L.i
            continue
        parenDepth += 1 if c == "(" else -1 if c == ")" and parenDepth > 0 else 0
        advance(P.L)
    flushSeg()
    return parts


def parseTestPrimary(P: ParseState, closer: str) -> Node | None:
    skipBlanks(P.L)
    if closer == "]" and peek(P.L) == "]" or closer == "]]" and peek(P.L) == "]" and peek(P.L, 1) == "]":
        return None
    return parseWord(P, "arg")


ARITH_PREC = {
    "=": 2, "+=": 2, "-=": 2, "*=": 2, "/=": 2, "%=": 2, "<<=": 2, ">>=": 2,
    "&=": 2, "^=": 2, "|=": 2, "||": 4, "&&": 5, "|": 6, "^": 7, "&": 8,
    "==": 9, "!=": 9, "<": 10, ">": 10, "<=": 10, ">=": 10, "<<": 11, ">>": 11,
    "+": 12, "-": 12, "*": 13, "/": 13, "%": 13, "**": 14,
}
ARITH_RIGHT_ASSOC = {"=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=", "&=", "^=", "|=", "**"}


def parseArithExpr(P: ParseState, stop: str, mode: str = "var") -> Node | None:
    return parseArithTernary(P, stop, mode)


def parseArithCommaList(P: ParseState, stop: str, mode: str = "var") -> list[Node]:
    out: list[Node] = []
    while True:
        e = parseArithTernary(P, stop, mode)
        if e:
            out.append(e)
        skipBlanks(P.L)
        if peek(P.L) == "," and not isArithStop(P, stop):
            advance(P.L)
            continue
        break
    return out


def parseArithTernary(P: ParseState, stop: str, mode: str) -> Node | None:
    cond = parseArithBinary(P, stop, 0, mode)
    if not cond:
        return None
    skipBlanks(P.L)
    if peek(P.L) != "?":
        return cond
    qs = P.L.b
    advance(P.L)
    q = mk(P, "?", qs, P.L.b, [])
    t = parseArithBinary(P, ":", 0, mode)
    skipBlanks(P.L)
    cs = P.L.b
    if peek(P.L) == ":":
        advance(P.L)
    colon = mk(P, ":", cs, P.L.b, [])
    f = parseArithTernary(P, stop, mode)
    kids = [cond, q]
    if t:
        kids.append(t)
    kids.append(colon)
    if f:
        kids.append(f)
    return mk(P, "ternary_expression", cond.startIndex, f.endIndex if f else colon.endIndex, kids)


def scanArithOp(P: ParseState) -> tuple[str, int] | None:
    for op in ("<<=", ">>=", "**", "<<", ">>", "==", "!=", "<=", ">=", "&&", "||",
               "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|="):
        if P.L.src.startswith(op, P.L.i):
            return op, len(op)
    c, c1 = peek(P.L), peek(P.L, 1)
    if c == "+" and c1 == "+" or c == "-" and c1 == "-":
        return None
    return (c, 1) if c in {"+", "-", "*", "/", "%", "<", ">", "&", "|", "^", "="} else None


def parseArithBinary(P: ParseState, stop: str, minPrec: int, mode: str) -> Node | None:
    left = parseArithUnary(P, stop, mode)
    if not left:
        return None
    while True:
        skipBlanks(P.L)
        if isArithStop(P, stop) or peek(P.L) == ",":
            break
        opInfo = scanArithOp(P)
        if not opInfo:
            break
        opText, opLen = opInfo
        prec = ARITH_PREC.get(opText)
        if prec is None or prec < minPrec:
            break
        os = P.L.b
        for _ in range(opLen):
            advance(P.L)
        op = mk(P, opText, os, P.L.b, [])
        right = parseArithBinary(P, stop, prec if opText in ARITH_RIGHT_ASSOC else prec + 1, mode)
        if not right:
            break
        left = mk(P, "binary_expression", left.startIndex, right.endIndex, [left, op, right])
    return left


def parseArithUnary(P: ParseState, stop: str, mode: str) -> Node | None:
    skipBlanks(P.L)
    if isArithStop(P, stop):
        return None
    c, c1 = peek(P.L), peek(P.L, 1)
    if c + c1 in {"++", "--"}:
        s = P.L.b
        advance(P.L)
        advance(P.L)
        op = mk(P, c + c1, s, P.L.b, [])
        inner = parseArithUnary(P, stop, mode)
        return mk(P, "unary_expression", s, inner.endIndex, [op, inner]) if inner else op
    if c in {"-", "+", "!", "~"}:
        if mode != "var" and c == "-" and isDigit(c1):
            s = P.L.b
            advance(P.L)
            while isDigit(peek(P.L)):
                advance(P.L)
            return mk(P, "number", s, P.L.b, [])
        s = P.L.b
        advance(P.L)
        op = mk(P, c, s, P.L.b, [])
        inner = parseArithUnary(P, stop, mode)
        return mk(P, "unary_expression", s, inner.endIndex, [op, inner]) if inner else op
    return parseArithPostfix(P, stop, mode)


def parseArithPostfix(P: ParseState, stop: str, mode: str) -> Node | None:
    prim = parseArithPrimary(P, stop, mode)
    if not prim:
        return None
    c, c1 = peek(P.L), peek(P.L, 1)
    if c + c1 in {"++", "--"}:
        s = P.L.b
        advance(P.L)
        advance(P.L)
        op = mk(P, c + c1, s, P.L.b, [])
        return mk(P, "postfix_expression", prim.startIndex, op.endIndex, [prim, op])
    return prim


def parseArithPrimary(P: ParseState, stop: str, mode: str) -> Node | None:
    skipBlanks(P.L)
    if isArithStop(P, stop):
        return None
    c = peek(P.L)
    if c == "(":
        s = P.L.b
        advance(P.L)
        openNode = mk(P, "(", s, P.L.b, [])
        inners = parseArithCommaList(P, ")", mode)
        skipBlanks(P.L)
        cs = P.L.b
        if peek(P.L) == ")":
            advance(P.L)
        close = mk(P, ")", cs, P.L.b, [])
        return mk(P, "parenthesized_expression", s, close.endIndex, [openNode, *inners, close])
    if c == '"':
        return parseDoubleQuoted(P)
    if c == "$":
        return parseDollarLike(P)
    if isDigit(c):
        s = P.L.b
        while isDigit(peek(P.L)):
            advance(P.L)
        if P.L.b - s == 1 and c == "0" and peek(P.L) in {"x", "X"}:
            advance(P.L)
            while isHexDigit(peek(P.L)):
                advance(P.L)
        elif peek(P.L) == "#":
            advance(P.L)
            while isBaseDigit(peek(P.L)):
                advance(P.L)
        return mk(P, "number", s, P.L.b, [])
    if isIdentStart(c):
        s = P.L.b
        while isIdentChar(peek(P.L)):
            advance(P.L)
        nc = peek(P.L)
        if mode == "assign":
            skipBlanks(P.L)
            if peek(P.L) == "=" and peek(P.L, 1) != "=":
                vn = mk(P, "variable_name", s, P.L.b, [])
                es = P.L.b
                advance(P.L)
                eq = mk(P, "=", es, P.L.b, [])
                val = parseArithTernary(P, stop, mode)
                return mk(P, "variable_assignment", s, val.endIndex if val else eq.endIndex,
                          [vn, eq, val] if val else [vn, eq])
        if nc == "[":
            vn = mk(P, "variable_name", s, P.L.b, [])
            brS = P.L.b
            advance(P.L)
            brOpen = mk(P, "[", brS, P.L.b, [])
            idx = parseArithTernary(P, "]", "var") or parseDollarLike(P)
            skipBlanks(P.L)
            cs = P.L.b
            if peek(P.L) == "]":
                advance(P.L)
            brClose = mk(P, "]", cs, P.L.b, [])
            return mk(P, "subscript", s, brClose.endIndex,
                      [vn, brOpen, idx, brClose] if idx else [vn, brOpen, brClose])
        return mk(P, "variable_name" if mode == "var" else "word", s, P.L.b, [])
    return None


def isArithStop(P: ParseState, stop: str) -> bool:
    c = peek(P.L)
    if stop == "))":
        return c == ")" and peek(P.L, 1) == ")"
    if stop in {")", ";", ":", "]", "}"}:
        return c == stop
    if stop == ":}":
        return c in {":", "}"}
    return c in {"", "\n"}
