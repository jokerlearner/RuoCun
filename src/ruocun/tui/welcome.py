"""冻结 Welcome.tsx (MIT) 卡片/图像留白布局；终端I/O仍由InputBroker持有。"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import TypedDict

from ..i18n.i18n import t
from .brand import DISPLAY_NAME, WELCOME_MOTTO
from .capabilities import Capabilities
from .mascot_frames import renderStaticMascot
from .notifier import cleanNotificationText
from .theme import paint
from .width import displayWidth


class WelcomeMascotLayout(TypedDict):
    columns: float
    rows: float


class WelcomeLayout(TypedDict):
    cardWidth: int
    cardLeft: int
    imageColumns: int
    imageLeft: int
    imageTop: int
    cardHeight: int
    imageRows: int
    sideBySide: bool


def getWelcomeLayout(columns: float, mascot: WelcomeMascotLayout | None = None, *,
                     terminalRows: int | None = None) -> WelcomeLayout:
    width = max(1, math.floor(columns))
    card = min(width, 146)
    left = (width - card) // 2
    valid = mascot is not None and all(math.isfinite(mascot[k]) and mascot[k] > 0 for k in ("columns", "rows"))
    image_columns = math.ceil(mascot["columns"]) if valid and mascot else 0
    image_rows = max(13, math.ceil(mascot["rows"])) if valid and mascot else 0
    # The live card can use a shorter text column, reserving five rows for input/status.
    beside = (valid and card >= image_columns + (79 if terminalRows is None else 46)
              and (terminalRows is None or terminalRows >= image_rows + 9))
    rows = image_rows if beside else 0
    return {"cardWidth": card, "cardLeft": left, "imageColumns": image_columns if beside else 0,
            "imageLeft": left + 3, "imageTop": 2, "cardHeight": rows + 4 if beside else 0,
            "imageRows": rows, "sideBySide": beside}


def _truncate(text: str, columns: int) -> str:
    out, size = "", 0
    for char in text:
        size += displayWidth(char)
        if size > columns:
            break
        out += char
    return out


def Welcome(info: Mapping[str, str], caps: Capabilities, bg: str = "dark", *,
            maxim: object = None, skipFooter: bool = False,
            mascot: WelcomeMascotLayout | None = None, terminalRows: int | None = None) -> str:
    box = getWelcomeLayout(caps.columns, mascot if bg == "dark" else None, terminalRows=terminalRows)
    width = box["cardWidth"]
    native_beside = box["sideBySide"]
    compact_beside = not native_beside and width >= 64
    picture_columns = 0
    picture: list[str] = []
    if caps.isTTY and terminalRows is not None and terminalRows >= 22:
        if native_beside and mascot is not None:
            # Keep the still within full cells of the Sixel image that may replace it.
            picture_columns, picture = renderStaticMascot(box["imageColumns"] - 1, math.ceil(mascot["rows"]) - 1, caps.tier)
        elif compact_beside:
            picture_columns, picture = renderStaticMascot(width - 39, terminalRows - 9, caps.tier)
        elif width >= 18:
            picture_columns, picture = renderStaticMascot(width - 6, terminalRows - 19, caps.tier)
    clean = {key: cleanNotificationText(value).replace("\n", " ").replace("\t", " ") for key, value in info.items()}
    fields = [(DISPLAY_NAME, "jade"), (f"「{WELCOME_MOTTO}」", "jade")]
    footer = [(t("welcome.model") + clean.get("model", "") + " · " + clean.get("thinking", "") + " · " + t("welcome.ctx"), "ink"),
              (t("welcome.dir") + clean.get("cwd", ""), "dim")]
    obs = clean.get("obs", "")
    if obs:
        footer.append((obs, "vermilion" if "降级" in obs else "dim"))
    body: list[tuple[str, str]]
    offset = 0
    beside = native_beside or (compact_beside and bool(picture))
    if beside:
        body = [("", "dim")] * (box["imageRows"] if native_beside else max(13, len(picture)))
        body[1], body[3] = fields
        if not skipFooter:
            for index, field in enumerate(footer):
                body[6 + index] = field
            if native_beside:
                body[11] = (t("welcome.quickstart") + " · " + t("welcome.hint"), "dim")
            else:
                body[10], body[11] = (t("welcome.quickstart"), "dim"), (t("welcome.hint"), "dim")
        offset = box["imageColumns"] + 5 if native_beside else picture_columns + 3
    else:
        body = fields
        if not skipFooter:
            body = [*body, ("", "dim"), *footer, ("", "dim"), (t("welcome.quickstart"), "dim"), (t("welcome.hint"), "dim")]
    if width < 6:
        return "\n".join(_truncate(text, width) for text, _ in body if text)
    indent = " " * box["cardLeft"]
    inner = width - 6
    def edge(text: str) -> str:
        return indent + paint(text, "jade", caps, bg)
    def row(text: str = "", sem: str = "dim", lead: str = "", lead_width: int = 0) -> str:
        raw = _truncate(text, inner - lead_width)
        return (edge("│  ") + lead + paint(raw, sem, caps, bg) + " " * (inner - lead_width - displayWidth(raw))
                + edge("  │").removeprefix(indent))
    rows = [edge("╭" + "─" * (width - 2) + "╮"), row()]
    if beside:
        for index, (text, sem) in enumerate(body):
            lead = picture[index] + " " * (offset - picture_columns) if index < len(picture) else " " * offset
            rows.append(row(text, sem, lead, offset))
    else:
        if picture:
            margin = (inner - picture_columns) // 2
            rows.extend(row(lead=" " * margin + line, lead_width=margin + picture_columns) for line in picture)
        rows.extend(row(text, sem) for text, sem in body)
    rows.extend([row(), edge("╰" + "─" * (width - 2) + "╯")])
    return "\n".join(rows)
