"""维护通用列表的当前选项，由调用方驱动移动和选取。"""

from collections.abc import Sequence
from typing import TypedDict


class SelectItem(TypedDict):
    label: str
    value: str


class Select:
    def __init__(self, items: Sequence[SelectItem], initialIndex: int = 0, *, wrap: bool = True) -> None:
        self.items = list(items)
        self.index = min(max(initialIndex, 0), max(0, len(self.items) - 1))
        self.wrap = wrap

    def move(self, distance: int) -> None:
        if self.items:
            self.index = ((self.index + distance) % len(self.items) if self.wrap else
                          min(max(0, self.index + distance), len(self.items) - 1))

    @property
    def value(self) -> str | None:
        return self.items[self.index]["value"] if self.items else None
