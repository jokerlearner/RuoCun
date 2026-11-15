"""生成纯文本入口的欢迎横幅。交互会话的欢迎卡由 welcome 模块生成。"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypedDict

from .brand import DISPLAY_NAME
from .capabilities import Capabilities
from .maxim import randomMaxim
from .notifier import cleanNotificationText
from .taiji import TAIJI_WIDTH, renderTaiji
from .theme import paint
from .width import displayWidth


class WelcomeInfo(TypedDict, total=False):
    model: str
    thinking: str
    cwd: str
    version: str
    branch: str
    obs: str


def buildWelcome(
    info: Mapping[str, str], caps: Capabilities, rng: Callable[[], float] | None = None, bg: str = "dark"
) -> str:
    def field(key: str) -> str:
        return cleanNotificationText(info.get(key, "")).replace("\n", " ").replace("\t", " ")

    def padding(width: int) -> str:
        return " " * max(0, (caps.columns - width) // 2)

    def render(*parts: tuple[str, str], width: int | None = None) -> str:
        if width is None:
            width = displayWidth("".join(text for text, _ in parts))
        return padding(width) + "".join(paint(text, tone, caps, bg) if tone else text for text, tone in parts)

    directory = field("cwd")
    directories = [part for part in directory.split("/") if part]
    if len(directories) > 3:
        directory = "…/" + "/".join(directories[-3:])
    workdir = [("目录", "dim"), (" ", ""), (directory, "ink")]
    branch = field("branch")
    if branch:
        workdir.extend((("   ", ""), (f"⎇ {branch}", "jade")))
    model = [
        ("模型", "dim"), (" ", ""), (field("model"), "ink"), (" ", ""), ("·", "dim"), (" ", ""),
        (field("thinking"), "ink"), (" ", ""), ("·", "dim"), (" ", ""), ("1M 上下文", "ink"),
    ]
    details_width = max(displayWidth("".join(text for text, _ in parts)) for parts in (model, workdir))
    version = field("version")
    maxim = randomMaxim() if rng is None else randomMaxim(rng)
    divider = "╌" * min(max(40, caps.columns - 8), 100)
    emblem = [padding(TAIJI_WIDTH(caps)) + row for row in renderTaiji(caps, bg)]
    return "\n".join([
        "", *emblem, "",
        render((DISPLAY_NAME, "jade"), ("  ", ""), ("·", "dim"), ("  ", ""), (f"v{version}", "dim")),
        render((f"「{maxim['text']}」", "jade")), "",
        render(*model, width=details_width), render(*workdir, width=details_width), "",
        render((divider, "dim")),
        render(("输入消息开始 · /help 命令 · @ 引用文件 · Esc 打断", "dim")), "",
    ])
