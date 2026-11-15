"""将任务管理器中的子代理任务显示为可选列表。面板只读取任务状态，选择结果交回调用者处理。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from time import time_ns
from typing import TYPE_CHECKING

from ...i18n.i18n import getLang
from .app import panel_line

if TYPE_CHECKING:
    from ...agent.tasks import BgTask


class AgentTasksPanel:
    def __init__(self, tasks: Callable[[], Sequence[BgTask]]) -> None:
        self._tasks = tasks
        self.selected: str | None = None
        self.offset = 0
        self._entry_key: tuple[str, int, int] | None = None
        self._entries: list[str] = []
        self._tool_count = 0

    def _selection(self) -> tuple[list[BgTask], int, BgTask | None]:
        tasks = [task for task in self._tasks() if task.kind in {"agent", "fork"}]
        index = next((i for i, task in enumerate(tasks) if task.id == self.selected), 0)
        return tasks, index, tasks[index] if tasks else None

    def _load_entries(self, task: BgTask) -> None:
        messages = task.messages
        key = (task.runId, len(messages), id(messages[-1]) if messages else 0)
        if key == self._entry_key:
            return
        entries, count = [], 0
        for message in messages:
            content = message.get("content")
            if message.get("role") == "assistant":
                if isinstance(content, str) and content:
                    entries.append(content)
                for call in message.get("tool_calls") or []:
                    function = call.get("function") or {}
                    entries.append(f"{function.get('name', '')} {function.get('arguments', '')}")
                    count += 1
            elif message.get("role") == "tool":
                if isinstance(content, list):
                    content = " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
                entries.append(f"↳ {content if isinstance(content, str) else ''}")
        self._entry_key, self._entries, self._tool_count = key, entries, count

    @staticmethod
    def _sizes(rows: int, count: int) -> tuple[int, int]:
        shown = min(5, count, max(1, rows - 7))
        return shown, max(1, min(12, rows - shown - 8))

    def handle(self, key: str, rows: int) -> None:
        tasks, index, task = self._selection()
        if task is None:
            return
        if key in {"up", "down"}:
            index = max(0, min(len(tasks) - 1, index + (1 if key == "down" else -1)))
            self.selected, self.offset = tasks[index].id, 0
        elif key in {"pageup", "pagedown"}:
            self._load_entries(task)
            _, page = self._sizes(rows, len(tasks))
            self.offset = max(0, min(len(self._entries) - page, self.offset + (page if key == "pageup" else -page)))

    def render(self, columns: int, rows: int) -> str:
        tasks, index, task = self._selection()
        zh = getLang() == "zh"
        title = ("子 agent 执行情况" if zh else "Subagent activity") + f" ({len(tasks)})"
        lines = [title, "↑↓ 选择 · PgUp/PgDn 历史 · Ctrl+T / Esc 关闭" if zh else
                 "↑↓ select · PgUp/PgDn history · Ctrl+T / Esc close"]
        if task is None:
            lines.append("暂无子 agent 任务" if zh else "No subagent tasks")
        else:
            shown, page = self._sizes(rows, len(tasks))
            start = max(0, min(index - 2, len(tasks) - shown))
            lines.extend(f"{'❯ ' if i == index else '  '}{entry.id} · {entry.status} · {entry.description}"
                         for i, entry in enumerate(tasks[start:start + shown], start))
            self._load_entries(task)
            end = len(self._entries) - min(self.offset, max(0, len(self._entries) - page))
            elapsed = "—" if task.startedAt is None else f"{max(0, ((task.endedAt or time_ns() // 1_000_000) - task.startedAt) // 1000)}s"
            mode = ("历史消息" if self.offset else "实时更新") if zh else ("history" if self.offset else "live")
            lines.append(f"{elapsed} · {self._tool_count} {'次工具调用' if zh else 'tool calls'} · {mode}")
            log = self._entries[max(0, end - page):end]
            lines.extend(log or ["暂无中间输出" if zh else "No intermediate output yet"])
            lines.extend(value for value in (task.summary, task.error or task.result) if value)
        return "\n".join(panel_line(line, columns) for line in lines[:max(1, rows - 4)])
