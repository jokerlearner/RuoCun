"""从启动参数、环境与区域设置解析终端语言，按语言格式化消息，并持久化用户的语言选择。"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, cast

from ..platform.windows.durable_file import local_path
from .messages.en import en, enTips
from .messages.zh import zh, zhTips

Lang = Literal["zh", "en"]
_current: Lang = "en"
_write_lock = threading.RLock()


def _explicit(value: str | None) -> Lang | None:
    text = (value or "").lower()
    return "zh" if text.startswith("zh") else "en" if text.startswith("en") else None


def resolveLang(env: Mapping[str, str], settingsLang: str | None = None) -> Lang:
    explicit = env.get("RUOCUN_LANG")
    locale = env.get("LC_ALL") or env.get("LC_MESSAGES") or env.get("LANG", "")
    return _explicit(explicit) or _explicit(settingsLang) or ("zh" if locale.lower().startswith("zh") else "en")


def setLang(lang: str) -> None:
    if lang not in ("zh", "en"):
        raise ValueError("lang must be zh or en")
    global _current
    _current = cast(Lang, lang)


def getLang() -> Lang:
    return _current


def t(key: str, *args: str | int | float) -> str:
    raw = (zh if _current == "zh" else en).get(key, key)
    return re.sub(r"\{(\d+)\}", lambda match: str(args[int(match[1])]) if int(match[1]) < len(args) else match[0], raw)


def tips() -> list[str]:
    return list(zhTips if _current == "zh" else enTips)


def _file(userRoot: Path | None) -> Path:
    path = (userRoot if userRoot is not None else Path.home() / ".ruocun") / "settings.json"
    return local_path(path) if sys.platform == "win32" else path.absolute()


def readUserLang(*, userRoot: Path | None = None) -> str | None:
    try:
        value = json.loads(_file(userRoot).read_text(encoding="utf-8"))
        lang = value.get("lang") if isinstance(value, dict) else None
        return lang if isinstance(lang, str) else None
    except (OSError, ValueError, UnicodeError):
        return None


def writeUserLang(lang: str, *, userRoot: Path | None = None) -> None:
    if lang not in ("zh", "en"):
        raise ValueError("lang must be zh or en")
    file = _file(userRoot)
    with _write_lock:
        try:
            value = json.loads(file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            value = {}
        if not isinstance(value, dict):
            raise ValueError("现有语言设置不是对象，保留原文件")
        value["lang"] = lang
        file.parent.mkdir(parents=True, exist_ok=True)
        temporary = file.with_name(f".{file.name}.{uuid.uuid4().hex}.tmp")
        if sys.platform == "win32":
            temporary = local_path(temporary)
        try:
            with temporary.open("xb") as stream:
                stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, file)
        finally:
            temporary.unlink(missing_ok=True)


def switchLang(lang: str, *, userRoot: Path | None = None) -> None:
    writeUserLang(lang, userRoot=userRoot)
    setLang(lang)
