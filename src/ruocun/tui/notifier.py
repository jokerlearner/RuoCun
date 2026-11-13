"""MM-772/W6：终端内 best-effort 提示；不调用来源桌面通知后端。"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping

from .app.app import clean_text


def cleanNotificationText(text: str) -> str:
    return re.sub(r"[\x7f-\x9f]", "", clean_text(text))


def notify(title: str, message: str, *, write: Callable[[str], None] | None = None,
           env: Mapping[str, str] | None = None) -> bool:
    """True 只代表提示已交给 owner，不代表用户已看到。"""
    actual_env = os.environ if env is None else env
    disabled = actual_env.get("RUOCUN_NO_NOTIFY")
    if disabled == "1" or write is None:
        return False
    title, message = cleanNotificationText(title), cleanNotificationText(message)
    try:
        write(f"{title}: {message}" if title else message)
        return True
    except Exception:
        return False
