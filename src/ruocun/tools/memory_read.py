"""从当前执行明确绑定的记忆库读取内容，按精确名称或关键词返回相关记忆。"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from ..memory.store import MemoryStore
from ..memory.types import Memory
from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(files("ruocun.tools").joinpath("resources/memory-read.json").read_text("utf-8"))


def _full(memory: Memory) -> str:
    source = f"·来源 {memory.source}" if memory.source else ""
    return f"[{memory.type}·重{memory.importance}·命中{memory.uses}{source}]\n{memory.text}"


def makeMemoryReadTool(store: MemoryStore) -> Tool:
    async def read(args: dict[str, Any], ctx: ToolContext) -> str:
        memories = [entry.memory for entry in await store.load()]
        if not memories:
            return "(暂无记忆)"
        query: str = args["query"].strip()
        exact = next((memory for memory in memories if query in (memory.name, memory.title)), None)
        if exact is not None:
            return _full(exact)
        terms = query.lower().split()
        hits = []
        for memory in memories:
            haystack = f"{memory.name} {memory.title or ''} {memory.text}".lower()
            if all(term in haystack for term in terms):
                hits.append(memory)
                if len(hits) == args.get("limit", 6):
                    break
        if not hits:
            return f"(未找到记忆:{query})"
        if len(hits) == 1:
            return _full(hits[0])
        return "\n".join(f"- [{memory.type}·重{memory.importance}] {memory.title or memory.text}" for memory in hits)

    descriptions = _TEXT["parameters"]
    return Tool(
        name="MemoryRead", description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
        capability="read", approval="auto", handler=read,
        schema=objectSchema({
            "query": {"type": "string", "minLength": 1, "description": descriptions["query"]},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "description": descriptions["limit"]},
        }, ["query"]),
    )
