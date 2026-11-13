"""冻结 todo_write.ts 的整表 TodoWrite（MIT）；清单按上下文隔离。"""

from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from typing import Any

from .schema import objectSchema
from .todo_store import formatTodos
from .types import Tool, ToolContext, ToolRejected

_METADATA = json.loads(files("ruocun.tools").joinpath("resources/todo-write.json").read_text("utf-8"))


async def _todo(args: dict[str, Any], ctx: ToolContext) -> str:
    todos = args["todos"]
    count = sum(todo["status"] == "in_progress" for todo in todos)
    if count > 1:
        raise ToolRejected(f"同一时刻最多一个 in_progress,当前有 {count} 个")
    ctx.todos = deepcopy(todos)
    if not todos:
        return "(任务清单已清空)"
    out = formatTodos(todos)
    if len(todos) >= 3 and all(todo["status"] == "completed" for todo in todos):
        out += ("\n\n（所有待办已标为完成。交付前回到用户的原始要求，逐条检查实际证据。"
                "涉及实质改动时，安排 verify 子代理独立核验。）")
    return out


todoWriteTool = Tool(
    name="TodoWrite", description=_METADATA["description"], descriptionEn=_METADATA["descriptionEn"],
    schema=objectSchema({"todos": {"type": "array", "description": "完整任务列表", "items": objectSchema({
        "content": {"type": "string", "description": "祈使式描述,如 'Run tests'"},
        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
        "activeForm": {"type": "string", "description": "进行式描述(参考),如 'Running tests';省略时用 content"},
    }, ["content", "status"]) }}, ["todos"]), capability="plan", approval="auto", handler=_todo,
)
