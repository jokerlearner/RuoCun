"""遍历已批准访问的目录，用 Python 正则匹配文件内容，并按请求输出路径、匹配片段或计数。"""

from __future__ import annotations

import asyncio
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .glob import globToRegExp, walkFiles
from .paths import approvedPath
from .schema import objectSchema
from .types import Tool, ToolContext, ToolRejected

_TYPES = {
    "js": [".js", ".jsx", ".mjs", ".cjs"], "ts": [".ts", ".tsx", ".mts", ".cts"],
    "py": [".py", ".pyw"], "go": [".go"], "rust": [".rs"], "java": [".java"],
    "c": [".c", ".h"], "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
    "rb": [".rb"], "php": [".php"], "swift": [".swift"], "kt": [".kt", ".kts"],
    "scala": [".scala", ".sc"], "sh": [".sh", ".bash", ".zsh"], "sql": [".sql"],
    "html": [".html", ".htm"], "css": [".css", ".scss", ".sass", ".less"], "json": [".json"],
    "yaml": [".yaml", ".yml"], "xml": [".xml"], "md": [".md", ".markdown"],
}


def _length(text: str) -> int:
    return len(text.encode("utf-16-le", errors="surrogatepass")) // 2


def _slice(text: str, start: int, end: int | None = None) -> str:
    return text.encode("utf-16-le", errors="surrogatepass")[
        start * 2:None if end is None else end * 2].decode("utf-16-le", errors="surrogatepass")


def _truncate(line: str, lang: str = "zh") -> str:
    length = _length(line)
    if length <= 300:
        return line
    note = (f"(line has {length} chars, truncated)" if lang == "en" else
            f"(该行共 {length} 字符,已截断)")
    return _slice(line, 0, 300) + "…" + note


def _snippet(source: str, start: int, length: int, context: int, lang: str = "zh") -> str:
    matched = source[start:start + length]
    match_length = _length(matched)
    if match_length > 500:
        note = (f"(matched text is {match_length} chars, truncated)" if lang == "en" else
                f"(匹配文本共 {match_length} 字符,已截断)")
        return f"<<{_slice(matched, 0, 500)}…{note}>>"
    position = _length(source[:start])
    begin = max(0, position - context)
    end = min(_length(source), position + match_length + context)
    before = _slice(source, begin, position)
    after = _slice(source, position + match_length, end)
    prefix = "…" if begin else ""
    suffix = "…" if end < _length(source) else ""
    if _length(before) + match_length + _length(after) > 500:
        cap = max(0, (500 - match_length) // 2)
        note = "(context truncated)" if lang == "en" else "(上下文过长已截断)"
        return f"{prefix}{_slice(before, -cap)}<<{matched}>>{_slice(after, 0, cap)}…{note}"
    return f"{prefix}{before}<<{matched}>>{after}{suffix}"


def _clamp(text: str) -> str:
    length = _length(text)
    if length <= 16000:
        return text
    return (_slice(text, 0, 9600) + f"\n…(已省略中间 {length - 16000} 字符,共 {length} 字符;"
            "如需完整内容请用更精确的命令/grep 缩小范围)…\n" + _slice(text, -6400))


async def _grep(args: dict[str, Any], ctx: ToolContext) -> str:
    try:
        root = await approvedPath(ctx, args.get("path", "."))
    except ToolRejected:
        path = args.get("path", "undefined")
        return (f"Error: {path} is outside your workspace. Approve access in the permission prompt to search it."
                if ctx.lang == "en" else f"Error: {path} 在工作区之外，未获授权访问。可在权限提示中批准。")
    return await asyncio.to_thread(_search, root, args, ctx)


def _search(root: str, args: dict[str, Any], ctx: ToolContext) -> str:
    flags = re.IGNORECASE if args.get("ignore_case") else 0
    if args.get("multiline"):
        flags |= re.DOTALL
    try:
        regex = re.compile(args["pattern"], flags)
    except re.error as exc:
        raise ValueError(f"无效正则:{exc}。纯Python首版使用Python标准正则,不支持的JS专属语法请改写。") from exc
    name_regex = globToRegExp(args["glob"]) if args.get("glob") else None
    extensions = _TYPES.get(args.get("type", "").lower())
    mode = args.get("mode", "content")
    maximum = args.get("head_limit", 200)
    skip = args.get("offset", 0)
    before = max(args.get("before", 0), args.get("context", 0))
    after = max(args.get("after", 0), args.get("context", 0))
    only = args.get("only_matching", False)
    match_context = args.get("match_context", 0)
    out: list[str] = []
    truncated = False
    total = 0

    for scanned, (absolute, relative) in enumerate(walkFiles(root), 1):
        if ctx.signal.is_set():
            break
        if scanned > 50000:
            truncated = True
            break
        if name_regex and not name_regex.search(relative.rsplit("/", 1)[-1]):
            continue
        if extensions and not any(relative.endswith(extension) for extension in extensions):
            continue
        try:
            raw = Path(absolute).read_bytes().decode("utf-8", errors="replace")
        except OSError:
            continue
        if "\0" in raw:
            continue
        lines = raw.split("\n")
        def hits() -> Iterator[tuple[int, int, str, int, int]]:
            if args.get("multiline"):
                seen: set[int] = set()
                for match in regex.finditer(raw):
                    if not match[0]:
                        continue
                    index = raw[:match.start()].count("\n")
                    if index not in seen:
                        seen.add(index)
                        column = _length(raw[raw.rfind("\n", 0, match.start()) + 1:match.start()])
                        yield index, column, raw, match.start(), len(match[0])
            else:
                for index, line in enumerate(lines):
                    if only and mode == "content":
                        for match in regex.finditer(line):
                            if match[0]:
                                yield index, _length(line[:match.start()]), line, match.start(), len(match[0])
                    else:
                        line_match = regex.search(line)
                        if line_match is not None:
                            yield index, line_match.start(), line, line_match.start(), len(line_match[0])
        if mode == "files":
            if next(hits(), None) is not None:
                total += 1
                if total > skip:
                    out.append(relative)
        else:
            collected: set[int] = set()
            for index, column, source, start, length in hits():
                total += 1
                if total <= skip:
                    continue
                if only:
                    out.append(f"{relative}:{index + 1}:{column + 1}:{_snippet(source, start, length, match_context, ctx.lang)}")
                elif before or after:
                    if args.get("multiline"):
                        collected = set()
                    for number in range(max(0, index - before), min(len(lines), index + after + 1)):
                        if number not in collected:
                            collected.add(number)
                            marker = ">" if number == index else "-"
                            out.append(f"{relative}:{number + 1}:{marker} {_truncate(lines[number], ctx.lang)}")
                else:
                    out.append(f"{relative}:{index + 1}:{_truncate(lines[index], ctx.lang)}")
                if len(out) >= maximum:
                    truncated = True
                    break
        if len(out) >= maximum:
            truncated = True
            break
    if not out:
        scope = f"在 {args.get('path', '工作区根')} 内搜 /{args['pattern']}/"
        if args.get("glob"):
            scope += f",glob {args['glob']}"
        if args.get("type"):
            scope += f",type {args['type']}"
        if skip:
            scope += f",跳过前 {skip} 条"
        return f"(无匹配:{scope}。若确信存在,放宽 path 或检查 pattern/glob/type)"
    result = "\n".join(out)
    if truncated:
        result += f"\n…(已截断,超过 {maximum} 条)"
    if skip:
        result += f"\n(跳过前 {skip} 条,共 {total} 条匹配)"
    return _clamp(result)


_PROPERTIES: dict[str, Any] = {
    "pattern": {"type": "string", "description": "正则表达式(Python标准语法)"},
    "path": {"type": "string", "description": "搜索子目录或具体某个文件,默认工作区根"},
    "glob": {"type": "string", "description": "文件名 glob 过滤,如 *.ts"},
    "mode": {"type": "string", "enum": ["content", "files"], "description": "content(默认)或 files"},
    "ignore_case": {"type": "boolean", "description": "忽略大小写"},
    "before": {"type": "integer", "minimum": 0, "description": "匹配行前显示 N 行(参考 -B)"},
    "after": {"type": "integer", "minimum": 0, "description": "匹配行后显示 N 行(参考 -A)"},
    "context": {"type": "integer", "minimum": 0, "description": "匹配行前后各显示 N 行(参考 -C);与 before/after 取 max"},
    "head_limit": {"type": "integer", "minimum": 1, "description": "限制返回条数,默认 200"},
    "offset": {"type": "integer", "minimum": 0, "description": "跳过前 N 条结果(分页),默认 0"},
    "multiline": {"type": "boolean", "description": "跨行匹配(. 匹配换行符,模式可跨行)"},
    "type": {"type": "string", "description": "文件类型过滤(js/ts/py/go/rust/java/c/cpp/rb/php/swift/kt/scala/sh/sql/html/css/json/yaml/xml/md)"},
    "only_matching": {"type": "boolean", "description":
                      "用 <<...>> 显示命中的片段。适合定位长行中落在 300 字符预览范围之外的文本。"},
    "match_context": {"type": "integer", "minimum": 0, "maximum": 200,
                      "description": "仅 only_matching=true 时生效:匹配前后额外显示的字符数(非整行),默认 0"},
}

grepFilesTool = Tool(
    name="Grep", description=(
        "在工作区用 Python 正则找内容。mode=content 输出文件、行号和文本；mode=files 只列文件。path 可指定目录或单文件，也能用 "
        "glob、type 和 ignore_case 过滤。用 before、after 或 context 带上下文；head_limit 默认 200，offset "
        "跳过前面的结果。multiline 允许跨行；only_matching 把匹配内容标在 <<...>> 中，match_context "
        "额外显示附近字符，适合查看超长行。注意输出里的截断提示和搜索范围。"
    ),
    descriptionEn=(
        "Search workspace text with Python regular expressions. The content mode returns "
        "file, line number, and text; files mode returns paths. Scope a search with path, "
        "glob, and type, and set ignore_case when needed. Use before, after, or context for "
        "surrounding lines. head_limit defaults to 200 and offset skips results. Enable "
        "multiline for spans across lines. On a long line, use only_matching for the "
        "<<...>> match and match_context for nearby characters. Check the reported search "
        "scope and truncation."
    ), schema=objectSchema(_PROPERTIES, ["pattern"]),
    capability="read", approval="auto", handler=_grep,
)
