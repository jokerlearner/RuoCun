"""把文件之间的相对引用和符号引用转换成图，再为地图计算文件排序。

排序用于优先展示可能被其他位置依赖的文件。
"""

import posixpath
import threading
from dataclasses import dataclass

from .extract import FileExtract

_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".py", ".go", ".rs", ".java")


@dataclass
class FileEntry:
    rel: str
    extract: FileExtract


@dataclass
class GraphResult:
    ranks: dict[str, float]
    edges: dict[str, set[str]]


def _resolve(source_file: str, source: str, known: set[str]) -> str | None:
    base = "/".join(part for part in source.split("/") if part != ".")
    candidates = [base, *(base + extension for extension in _EXTENSIONS), base + "/index",
                  *(base + "/index" + extension for extension in _EXTENSIONS)]
    for candidate in candidates:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_file), candidate))
        if resolved in known:
            return resolved
    return None


def buildGraph(entries: list[FileEntry], *, signal: threading.Event | None = None) -> GraphResult:
    nodes = list(dict.fromkeys(entry.rel for entry in entries))
    known = set(nodes)
    definitions: dict[str, set[str]] = {}
    for entry in entries:
        if signal is not None and signal.is_set():
            raise InterruptedError("代码地图构建已取消。")
        for symbol in entry.extract.defs:
            definitions.setdefault(symbol.name, set()).add(entry.rel)
    edges: dict[str, set[str]] = {}
    for entry in entries:
        if signal is not None and signal.is_set():
            raise InterruptedError("代码地图构建已取消。")
        targets = {target for source in entry.extract.importSources if (target := _resolve(entry.rel, source, known))}
        for name in entry.extract.refs:
            targets.update(definitions.get(name, ()))
        targets.discard(entry.rel)
        if targets:
            edges[entry.rel] = targets
    count = len(nodes)
    if not count:
        return GraphResult({}, edges)
    rank = dict.fromkeys(nodes, 1 / count)
    node_order = {node: position for position, node in enumerate(nodes)}
    ordered_edges = {origin: sorted(targets, key=node_order.__getitem__) for origin, targets in edges.items()}
    for _ in range(30):
        if signal is not None and signal.is_set():
            raise InterruptedError("代码地图构建已取消。")
        dangling = .85 * sum(value for node, value in rank.items() if not edges.get(node)) / count
        updated = dict.fromkeys(nodes, (1 - .85) / count + dangling)
        for origin, ordered_targets in ordered_edges.items():
            share = .85 * rank[origin] / len(ordered_targets)
            for target in ordered_targets:
                updated[target] += share
        rank = updated
    return GraphResult(rank, edges)
