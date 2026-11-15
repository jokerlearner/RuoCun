"""首次遇到某种语言时加载对应的 Tree-sitter 解析语法。"""

from functools import lru_cache
from importlib import import_module

from tree_sitter import Language


@lru_cache(maxsize=None)
def loadGrammar(grammarFile: str) -> Language | None:
    name = grammarFile.removeprefix("tree-sitter-").removesuffix(".wasm")
    module = "typescript" if name == "tsx" else name
    function = "language_tsx" if name == "tsx" else "language_typescript" if name == "typescript" else "language"
    try:
        return Language(getattr(import_module("tree_sitter_" + module), function)())
    except (ImportError, AttributeError, ValueError):
        return None


def resetRepomapRuntimeForTest() -> None:
    loadGrammar.cache_clear()
