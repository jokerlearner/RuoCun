"""冻结project_doc.ts（MIT）的RUOCUN原生名称及D09显式只读兼容适配。"""

import os
from pathlib import Path

from .config.compat import DEFAULT_COMPATIBILITY, Compatibility


def _projectChain(start: Path) -> list[Path]:
    chain: list[Path] = []
    directory = start
    while True:
        chain.append(directory)
        if (directory / ".git").exists():
            return list(reversed(chain))
        if directory.parent == directory:
            return [start]
        directory = directory.parent


def loadProjectInstructions(
    workspaceRoot: str | Path, *, userRoot: Path | None = None,
    compatibility: Compatibility = DEFAULT_COMPATIBILITY,
    sourceStates: dict[str, str] | None = None,
) -> str:
    root = Path(os.path.abspath(workspaceRoot))
    user_root = userRoot if userRoot is not None else Path.home() / ".ruocun"
    parts: list[str] = []
    seen: set[str] = set()

    def read(label: str, file: Path, source_id: str | None = None) -> None:
        try:
            content = file.read_bytes().decode("utf-8", errors="replace").strip().strip("\ufeff").strip()
        except OSError:
            if sourceStates is not None and source_id is not None:
                sourceStates[source_id] = "缺失或不可读；该源未加载"
            return
        if content and content not in seen:
            seen.add(content)
            parts.append(f"### {label}\n{content}")
            state = "生效：内容已注入"
        else:
            state = "内容重复，已由先前来源提供" if content else "空内容，未注入"
        if sourceStates is not None and source_id is not None:
            sourceStates[source_id] = state

    sources = [source for source in compatibility.sources if source.resource == "instructions"]
    for source in sources:
        if source.scope == "user":
            read(f"兼容用户级({source.id}: {source.path})", Path(source.path), source.id)
    read("用户级(~/.ruocun/RUOCUN.md)", user_root / "RUOCUN.md")
    chain = _projectChain(root)
    for directory in chain:
        rel = os.path.relpath(directory, root)
        for source in sources:
            if (source.scope != "project" or source.workspace is None
                    or Path(source.workspace).resolve() != root.resolve()):
                continue
            parent = Path(os.path.abspath(source.path)).parent
            # 同链文件归实际层；显式链外文件绑定声明的当前workspace层。
            level = parent if parent in chain else root
            if level == directory:
                read(f"兼容项目级({source.id}: {source.path}) @ {rel}", Path(source.path), source.id)
        read(f"RUOCUN.md @ {rel}", directory / "RUOCUN.md")
        read(f"RUOCUN.local.md @ {rel}", directory / "RUOCUN.local.md")
    return "\n\n".join(parts)
