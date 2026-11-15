"""将 Markdown 转换为适合终端显示的文本和样式，按显示列宽折叠表格。"""

import re
from io import StringIO

from .width import displayWidth, padEnd


def _inline(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    for index, part in enumerate(parts):
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            parts[index] = "\x1b[36m" + part[1:-1] + "\x1b[39m"
        else:
            parts[index] = re.sub(r"\*(.+?)\*", "\x1b[3m" + r"\1" + "\x1b[23m",
                                  re.sub(r"\*\*(.+?)\*\*", "\x1b[1m" + r"\1" + "\x1b[22m", part))
    return "".join(parts)


def _wrap_cell(text: str, width: int) -> list[str]:
    width = max(1, width)
    lines: list[str] = []
    current: list[str] = []
    current_width, last_space = 0, -1
    for char in text:
        if char == "\n":
            lines.append("".join(current))
            current, current_width, last_space = [], 0, -1
            continue
        char_width = displayWidth(char)
        if current_width + char_width > width and current:
            if 0 <= last_space < len(current) - 1:
                lines.append("".join(current[:last_space]))
                current = current[last_space + 1:]
            else:
                lines.append("".join(current))
                current = []
            current_width = displayWidth("".join(current))
            last_space = max((i for i, value in enumerate(current) if value == " "), default=-1)
        current.append(char)
        current_width += char_width
        if char == " ":
            last_space = len(current) - 1
    lines.append("".join(current))
    return lines


def _table(rows: list[list[str]], maximum: int) -> str:
    header, body = rows[0] if rows else [], rows[2:]
    cols = len(header)
    if not cols:
        return ""
    natural = [max(1, displayWidth(header[col]), *(displayWidth(row[col] if col < len(row) else "") for row in body))
               for col in range(cols)]
    budget, total = max(cols * 3, (maximum or 80) - (3 * cols + 1)), sum(natural)
    widths = natural[:]
    if total > budget:
        minimum = min(8, max(3, budget // cols))
        widths = [max(minimum, width * budget // total) for width in natural]
        over = sum(widths) - budget
        while over > 0 and max(widths) > minimum:
            index = widths.index(max(widths))
            widths[index] -= 1
            over -= 1

    def bar(left: str, middle: str, right: str) -> str:
        return left + middle.join("─" * (width + 2) for width in widths) + right

    def row(cells: list[str], bold: bool = False) -> str:
        wrapped = [_wrap_cell(cells[col] if col < len(cells) else "", width) for col, width in enumerate(widths)]
        result = []
        for height in range(max(1, *(len(cell) for cell in wrapped))):
            parts = [padEnd(cell[height] if height < len(cell) else "", widths[col]) for col, cell in enumerate(wrapped)]
            if bold:
                parts = ["\x1b[1m" + part + "\x1b[22m" for part in parts]
            result.append("│ " + " │ ".join(parts) + " │")
        return "\n".join(result)

    return "\n".join([bar("┌", "┬", "┐"), row(header, True), bar("├", "┼", "┤"),
                      *(row(cells) for cells in body), bar("└", "┴", "┘")])


def _highlight(code: str, language: str) -> str:
    # Rich 只在内存中生成高亮文本，终端读写继续由输入代理统一管理。
    try:
        from pygments.lexers import get_lexer_by_name  # type: ignore[import-untyped]
        from rich.console import Console
        from rich.syntax import Syntax
        get_lexer_by_name(language)
        captured = StringIO()
        columns = max([80, *(displayWidth(line) + 1 for line in code.split("\n"))])
        console = Console(file=captured, force_terminal=True, color_system="truecolor", width=columns,
                          legacy_windows=False, highlight=False)
        console.print(Syntax(code, language, theme="ansi_dark", background_color="default", word_wrap=False), end="")
        value = captured.getvalue()
        return value.removesuffix("\n") if not code.endswith("\n") else value
    except Exception:
        return "\x1b[2m" + code + "\x1b[22m"


def renderMarkdown(md: str, width: int | None = None) -> str:
    table_width = max(20, (width or 80) - 2)
    lines, index = md.split("\n"), 0
    result: list[str] = []
    while index < len(lines):
        line = lines[index]
        fence = re.match(r"^\s*```(\w+)?", line)
        if fence:
            language = fence[1] or ""
            index += 1
            code = []
            while index < len(lines) and not re.match(r"^\s*```", lines[index]):
                code.append(lines[index])
                index += 1
            index += 1
            result.extend("  " + value for value in _highlight("\n".join(code), language).split("\n"))
            continue
        if re.match(r"^\s*\|", line) and index + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$", lines[index + 1]):
            table = []
            while index < len(lines) and re.match(r"^\s*\|", lines[index]):
                table.append([part.strip() for part in lines[index].strip().removeprefix("|").removesuffix("|").split("|")])
                index += 1
            result.append(_table(table, table_width))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        quote = re.match(r"^>\s?(.*)$", line)
        bullet = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        numbered = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if heading:
            result.append("\x1b[1m\x1b[36m" + _inline(heading[2]) + "\x1b[0m")
        elif re.match(r"^(-{3,}|\*{3,}|_{3,})\s*$", line):
            result.append("\x1b[2m" + "─" * 40 + "\x1b[22m")
        elif quote:
            result.append("\x1b[2m│\x1b[22m " + _inline(quote[1]))
        elif bullet:
            result.append(bullet[1] + "• " + _inline(bullet[2]))
        elif numbered:
            result.append(numbered[1] + numbered[2] + ". " + _inline(numbered[3]))
        else:
            result.append(_inline(line) if line.strip() else "")
        index += 1
    return "\n".join(result)
