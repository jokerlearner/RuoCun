"""Verify an installed package can load the ordinary Agent SQLite runtime."""

import subprocess
import sys
import tempfile

_BOOTSTRAP = """
import sys
from importlib.resources import as_file, files
from pathlib import Path
from ruocun.session.runtime import verify_controlled_runtime, verify_official_archive

with as_file(files('ruocun').joinpath('resources/runtime/sqlite-dll-win-x64-3540100.zip')) as archive:
    dll = verify_official_archive(archive, Path(sys.argv[1]))
verify_controlled_runtime(dll)
"""


def main() -> int:
    if sys.platform != "win32" or sys.maxsize <= 2**32:
        return 2
    # A fresh child preloads the DLL before sqlite3 and releases it before cleanup.
    try:
        with tempfile.TemporaryDirectory(prefix="rc-runtime-") as directory:
            result = subprocess.run([sys.executable, "-I", "-c", _BOOTSTRAP, directory],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return 2
    return 0 if result.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
