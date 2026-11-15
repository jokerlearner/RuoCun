"""通过绑定的记忆库保存或删除条目。写入前检查凭据、确定存储范围，并为附带出处的条目记录来源指纹。"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any, cast

from ..memory.secrets import findSecrets
from ..memory.store import MemoryStore, projectIdOf, routeScope, slug
from ..memory.types import MemoryType, Scope, newMemory
from ..memory.validate import hashMemorySource
from .schema import objectSchema
from .types import Tool, ToolContext

_TEXT: dict[str, Any] = json.loads(files("ruocun.tools").joinpath("resources/memory-write.json").read_text("utf-8"))
_LABELS = {"project": "项目级", "user": "用户级", "knowledge": "知识库"}


def makeMemoryWriteTool(store: MemoryStore) -> Tool:
    async def write(args: dict[str, Any], ctx: ToolContext) -> str:
        text: str = args.get("text", "")
        title: str = args.get("title", "")
        if args.get("delete"):
            key = (title or text).strip()
            if not key:
                return "删除失败:需提供 title 或 text 来定位要删除的记忆。"
            result = await store.delete(key, signal=ctx.signal)
            if result.removed:
                message = f"已删除记忆(共 {len(result.removed)} 条):{'、'.join(result.removed)}"
                if result.readOnly:
                    message += "\n同名只读兼容记忆已保留。"
                return message
            if result.readOnly:
                return "删除失败:匹配记忆来自只读兼容来源。"
            return f"未找到匹配记忆:{key}"
        if not text.strip():
            return "写入失败:text 必填(删除请用 delete: true)。"
        source: str | None = args.get("source")
        secrets: dict[str, None] = {}
        for value in (text, title, source):
            if value:
                secrets.update(dict.fromkeys(findSecrets(value)))
        if secrets:
            return f"拒绝写入记忆:疑似含密钥({'、'.join(secrets)})。请勿把凭据写进记忆;如需记录,改写成不含密钥的描述。"
        kind = cast(MemoryType, args.get("type", "semantic"))
        scope = cast(Scope, args.get("scope", routeScope(kind)))
        source_hash = await hashMemorySource(store.cwd, source) if source else None
        item = newMemory(
            name=slug(title or text), title=title, text=text, type=kind, today=store.today(),
            importance=args.get("importance", 5), confidence=args.get("confidence"),
            source=source, sourceHash=source_hash, origin=projectIdOf(store.cwd) if scope == "knowledge" else None,
        )
        saved = await store.upsert(scope, item, signal=ctx.signal)
        if ctx.memoryAudit is not None:
            ctx.memoryAudit.wrote(kind, saved.action == "updated")
        prefix = "已更新" if saved.action == "updated" else "已记住"
        return f"{prefix}({_LABELS[scope]}):{text.strip()}"

    descriptions = _TEXT["parameters"]
    fields: dict[str, dict[str, Any]] = {
        "text": {"type": "string"},
        "title": {"type": "string"},
        "type": {"type": "string", "enum": ["user", "feedback", "semantic", "procedural", "episodic"]},
        "importance": {"type": "integer", "minimum": 1, "maximum": 10},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "source": {"type": "string"},
        "scope": {"type": "string", "enum": ["project", "user", "knowledge"]},
        "delete": {"type": "boolean"},
    }
    return Tool(
        name="MemoryWrite", description=_TEXT["description"], descriptionEn=_TEXT["descriptionEn"],
        capability="plan", approval="auto", persistentEffect=True, handler=write,
        schema=objectSchema({name: {**field, "description": descriptions[name]} for name, field in fields.items()}, []),
    )
