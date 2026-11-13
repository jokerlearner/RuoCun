"""Source fixture/report redaction without printing user state."""

from collections.abc import Mapping
from pathlib import Path

from ruocun.memory.secrets import redactSecrets


def redactText(text: str, *, home: str | None = None, name_map: Mapping[str, str] | None = None,
               known_secret: str = "") -> str:
    if known_secret:
        text = text.replace(known_secret, "[REDACTED]")
    text = redactSecrets(text)
    base = str(Path.home()) if home is None else home
    if base:
        text = text.replace(base, "~").replace(base.replace("\\", "/"), "~")
    for raw, masked in sorted((name_map or {}).items(), key=lambda item: -len(item[0])):
        if raw:
            text = text.replace(raw, masked)
    return text
