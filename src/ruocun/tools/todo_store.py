"""为当前工具上下文提供任务清单存储，以及工具和界面共用的清单文本格式。"""

from __future__ import annotations

from copy import deepcopy

ICON = {"pending": "☐", "in_progress": "▶", "completed": "☑"}


class TodoStore:
    def __init__(self) -> None:
        self.todos: list[dict[str, str]] = []

    def set(self, todos: list[dict[str, str]]) -> None:
        self.todos = deepcopy(todos)

    def get(self) -> list[dict[str, str]]:
        return deepcopy(self.todos)

    def reset(self) -> None:
        self.todos = []


def formatTodos(todos: list[dict[str, str]]) -> str:
    return "\n".join(f"{ICON[todo['status']]} {todo.get('activeForm', todo['content'])}" for todo in todos)
