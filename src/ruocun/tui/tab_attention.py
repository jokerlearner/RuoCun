"""根据任务状态生成终端标签页标题和提醒。标题序列通过注入的终端写入口发送。"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping
from typing import Literal

from .brand import DISPLAY_NAME

TabAttentionKind = Literal["attention", "completed"]


def _clean_title(title: str) -> str:
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", re.sub(r"\s+", " ", title)).strip()


def formatTabTitle(_cwd: str, name: str | None = None) -> str:
    task = _clean_title(name or "")
    if len(task) > 24:
        task = task[:24] + "…"
    return f"{task} · {DISPLAY_NAME}" if task and task != DISPLAY_NAME else DISPLAY_NAME


class TabAttention:
    def __init__(self, title: str, write: Callable[[str], None], enabled: bool) -> None:
        self._write, self._enabled = write, enabled
        self._base = _clean_title(title) or DISPLAY_NAME
        self._marked: TabAttentionKind | None = None
        self._disposed = False
        self._emit("\x1b[22;0t")
        self._title(self._base)
        self._emit("\x1b[?1004h")

    def _emit(self, value: str) -> None:
        if self._enabled:
            try:
                self._write(value)
            except Exception:
                pass  # 终端标签页更新失败时保留已经得到的任务结果。

    def _title(self, value: str) -> None:
        self._emit(f"\x1b]0;{value}\x1b\\")

    def _render(self) -> None:
        prefix = "🟢 " if self._marked == "completed" else "🟡 " if self._marked else ""
        self._title(prefix + self._base)

    def mark(self, kind: TabAttentionKind = "attention") -> None:
        if not self._disposed and self._marked != kind:
            self._marked = kind
            self._render()

    def clear(self) -> None:
        if not self._disposed and self._marked is not None:
            self._marked = None
            self._render()

    def setTitle(self, title: str) -> None:
        value = _clean_title(title) or DISPLAY_NAME
        if not self._disposed and value != self._base:
            self._base = value
            self._render()

    def dispose(self) -> None:
        if self._disposed:
            return
        if self._marked:
            self._title(self._base)
        self._emit("\x1b[?1004l\x1b[23;0t")
        self._disposed = True


def createTabAttention(title: str, *, write: Callable[[str], None], isTTY: bool = False,
                       env: Mapping[str, str] | None = None) -> TabAttention:
    actual_env = os.environ if env is None else env
    return TabAttention(title, write, isTTY and actual_env.get("TERM") != "dumb")
