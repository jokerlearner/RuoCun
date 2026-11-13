"""Frozen repomap/render.ts folded signatures and UTF16 character/3 estimate (MIT)."""

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
