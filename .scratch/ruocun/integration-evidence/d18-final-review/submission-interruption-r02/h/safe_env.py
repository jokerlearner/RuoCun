"""Explicit OS-only child environment; never inherit model/service credentials."""
import os


def child_env(**overrides):
    allowed = ("SystemRoot", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
               "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA", "PROGRAMFILES",
               "PROGRAMFILES(X86)", "SYSTEMDRIVE")
    values = {name: os.environ[name] for name in allowed if name in os.environ}
    values.update(PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    values.update(overrides)
    return values
