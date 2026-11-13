"""Frozen repomap/extract.ts: definitions, import references and signatures (MIT)."""

from __future__ import annotations

import asyncio
import re
import threading
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser

from .languages import LangDef
from .loader import loadGrammar


@dataclass
class SymbolDef:
    name: str
    kind: str
    startLine: int
    signature: str


@dataclass
class FileExtract:
    defs: list[SymbolDef]
    refs: list[str]
    importSources: list[str]


_LOCK = threading.RLock()
_PARSER: Parser | None = None


def _text(node: Node) -> str:
    return (node.text or b"").decode("utf-8", errors="replace")


def _definition(node: Node, how: str) -> str | None:
    if how in {"name", "type"}:
        name = node.child_by_field_name(how)
        return _text(name) if name is not None else None
    for child in node.named_children:
        if how == "spec" and child.type == "type_spec":
            return _definition(child, "name")
        if how == "declarator" and child.type == "variable_declarator":
            value = child.child_by_field_name("value")
            if value is not None and value.type in {"arrow_function", "function_expression", "generator_function"}:
                return _definition(child, "name")
    return None


def _signature(node: Node, lines: list[str]) -> str:
    start = node.start_point.row
    body = node.child_by_field_name("body")
    end = (body.start_point.row if body.start_point.row > start else start + 1) if body else min(node.end_point.row + 1, start + 3)
    return "\n".join(lines[start:min(end, start + 8)]).rstrip()


def _refs(node: Node, language: LangDef, refs: dict[str, None], sources: dict[str, None]) -> None:
    grammar = language.grammar
    if "typescript" in grammar or "javascript" in grammar:
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "string":
                    source = _text(child).strip("\"'")
                    if source.startswith(("./", "../")):
                        sources[source] = None
                    if name := source.split("/")[-1]:
                        refs[name] = None
                elif child.type == "import_clause":
                    for item in child.named_children:
                        if item.type == "named_imports":
                            for spec in item.named_children:
                                if spec.type == "import_specifier":
                                    name_node = spec.child_by_field_name("name") or next(iter(spec.named_children), None)
                                    if name_node is not None:
                                        refs[_text(name_node)] = None
                        elif item.type == "namespace_import":
                            if match := re.search(r"as\s+(\w+)", _text(item), re.ASCII):
                                refs[match[1]] = None
                        elif item.type == "identifier":
                            refs[_text(item)] = None
        elif node.type == "export_statement":
            source_node = node.child_by_field_name("source")
            if source_node is not None and source_node.type == "string":
                source = _text(source_node).strip("\"'")
                if source.startswith(("./", "../")):
                    sources[source] = None
    elif "python" in grammar and node.type in {"import_statement", "import_from_statement"}:
        module = node.child_by_field_name("module_name")
        if module is not None:
            refs.update(dict.fromkeys(filter(None, _text(module).split("."))))
            if _text(module).startswith("."):
                sources[_text(module)] = None
        for child in node.named_children:
            if child.type in {"dotted_name", "aliased_import"}:
                text = re.sub(r"\s+as\s+\w+", "", _text(child), flags=re.ASCII)
                refs.update(dict.fromkeys(filter(None, text.split("."))))
    elif "go" in grammar and node.type == "import_spec":
        path = node.child_by_field_name("path")
        if path is not None and (name := _text(path).strip('"').split("/")[-1]):
            refs[name] = None
    elif "rust" in grammar and node.type == "use_declaration":
        text = re.sub(r"^use\s*", "", _text(node)).removesuffix(";")
        refs.update(dict.fromkeys(filter(None, (part.strip() for part in re.split(r"::|\{|\}|,|\s+", text)))))
    elif "java" in grammar and node.type == "import_declaration":
        text = re.sub(r"^import\s+(static\s+)?", "", _text(node)).removesuffix(";")
        if name := text.split(".")[-1]:
            refs[name] = None


def extractFileSync(absPath: str | Path, lang: LangDef | None, *, signal: threading.Event | None = None) -> FileExtract | None:
    global _PARSER
    if lang is None:
        return None
    language = loadGrammar(lang.grammar)
    if language is None:
        return None
    try:
        source = Path(absPath).read_text("utf-8", errors="replace")
    except OSError:
        return None
    if not source.strip():
        return None
    with _LOCK:
        if _PARSER is None:
            _PARSER = Parser()
        _PARSER.language = language
        tree = _PARSER.parse(source.encode("utf-8"))
        lines = source.split("\n")
        definitions: list[SymbolDef] = []
        refs: dict[str, None] = {}
        sources: dict[str, None] = {}
        stack = [tree.root_node]
        while stack:
            if signal is not None and signal.is_set():
                raise InterruptedError("代码地图构建已取消。")
            node = stack.pop()
            if (how := lang.defNodes.get(node.type)) and (name := _definition(node, how)):
                definitions.append(SymbolDef(name, node.type, node.start_point.row + 1, _signature(node, lines)))
            _refs(node, lang, refs, sources)
            stack.extend(reversed(node.children))
        # Only plain values escape this frame; neither cached results nor callers own AST nodes.
        return FileExtract(definitions, list(refs), list(sources))


async def extractFile(absPath: str | Path, lang: LangDef | None, *, signal: threading.Event | None = None) -> FileExtract | None:
    return await asyncio.to_thread(extractFileSync, absPath, lang, signal=signal)
