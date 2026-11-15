"""按预算把已排序的定义渲染为简明代码库地图。

折叠缺省的代码段，只保留需要展示的签名，按 UTF-16 长度粗估其 token 开销。
"""

import math
from dataclasses import dataclass

from .extract import SymbolDef


@dataclass
class RenderedFile:
    rel: str
    defs: list[SymbolDef]


def _tokens(text: str) -> int:
    return math.ceil(len(text.encode("utf-16-le", errors="surrogatepass")) / 6)


def renderRepoMap(files: list[RenderedFile], tokenBudget: int) -> str:
    blocks: list[str] = []
    used = 0
    for file in files:
        file_used = _tokens(file.rel + ":\n")
        if used + file_used > tokenBudget - 120:
            break
        lines: list[str] = []
        truncated = False
        for definition in file.defs:
            signature = "│" + definition.signature.replace("\n", "\n│")
            tokens = _tokens(signature + "\n") + 6
            if used + file_used + tokens > tokenBudget - 120:
                truncated = True
                break
            lines.extend(("⋮...", signature))
            file_used += tokens
        if not lines:
            continue
        if truncated:
            lines.append("⋮...")
        used += file_used
        blocks.append(file.rel + ":\n" + "\n".join(lines))
    return "\n\n".join(blocks)
