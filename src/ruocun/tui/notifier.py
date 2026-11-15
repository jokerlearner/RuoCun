"""清理提示文字并交给终端界面。通知尝试独立于业务执行结果。"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping

from .app.app import clean_text


def cleanNotificationText(text: str) -> str:
    return re.sub(r"[\x7f-\x9f]", "", clean_text(text))


def notify(title: str, message: str, *, write: Callable[[str], None] | None = None,
           env: Mapping[str, str] | None = None) -> bool:
    """返回真值表示提示已交给终端展示入口，用户是否看到由实际终端状态决定。"""
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
