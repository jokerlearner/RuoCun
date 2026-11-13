"""Frozen repomap/languages.ts grammar and definition-node coverage (MIT)."""

from dataclasses import dataclass
from pathlib import PurePath


@dataclass(frozen=True)
class LangDef:
    grammar: str
    extensions: tuple[str, ...]
    defNodes: dict[str, str]


_TS = {"class_declaration": "name", "abstract_class_declaration": "name", "function_declaration": "name",
       "method_definition": "name", "interface_declaration": "name", "type_alias_declaration": "name",
       "enum_declaration": "name", "lexical_declaration": "declarator"}
LANGUAGES = (
    LangDef("tree-sitter-typescript.wasm", (".ts", ".mts", ".cts"), _TS),
    LangDef("tree-sitter-tsx.wasm", (".tsx",), _TS),
    LangDef("tree-sitter-javascript.wasm", (".js", ".jsx", ".mjs", ".cjs"), {
        key: value for key, value in _TS.items() if key not in {"interface_declaration", "type_alias_declaration", "enum_declaration"}}),
    LangDef("tree-sitter-python.wasm", (".py",), {"class_definition": "name", "function_definition": "name"}),
    LangDef("tree-sitter-go.wasm", (".go",), {
        "function_declaration": "name", "method_declaration": "name", "type_declaration": "spec"}),
    LangDef("tree-sitter-rust.wasm", (".rs",), {
        **dict.fromkeys(("function_item", "struct_item", "enum_item", "trait_item", "mod_item"), "name"), "impl_item": "type"}),
    LangDef("tree-sitter-java.wasm", (".java",), dict.fromkeys((
        "class_declaration", "interface_declaration", "enum_declaration", "record_declaration", "method_declaration"), "name")),
)
_EXTENSIONS = {extension: language for language in LANGUAGES for extension in language.extensions}


def langForFile(relPath: str) -> LangDef | None:
    return _EXTENSIONS.get(PurePath(relPath).suffix.lower())
