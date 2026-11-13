"""Check the source adapters on POSIX without claiming a POSIX product install."""

import ast
import os
import sys
import threading
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "src"
sys.path.insert(0, str(SOURCE))


def main() -> int:
    from ruocun import __version__
    from ruocun.cli import main as cli
    from ruocun.platform.process_tree import run_foreground_plan
    from ruocun.platform.sandbox import sandboxSpawn
    from ruocun.platform.shell_plan import buildShellPlan

    assert sys.platform in {"linux", "darwin"} and sys.version_info[:2] >= (3, 11)
    paths = sorted((SOURCE / "ruocun").rglob("*.py"))
    for path in paths:
        tree = ast.parse(path.read_bytes(), filename=str(path), feature_version=(3, 11))
        compile(tree, str(path), "exec")
    package = tomllib.loads((REPO / "pyproject.toml").read_text("utf-8"))
    assert package["project"]["requires-python"] == "==3.11.*"
    assert '"py311-none-win_amd64"' in (REPO / "hatch_build.py").read_text("utf-8")
    assert cli(["--version"]) == cli(["--help"]) == 0
    with TemporaryDirectory(prefix="ruocun-posix-design-") as tmp:
        value = "合成 POSIX 🙂"
        plan = buildShellPlan("printf '%s\\n' \"$SYNTHETIC_VALUE\"", tmp,
                              environ={"HOME": tmp, "PATH": "/usr/bin:/bin", "SYNTHETIC_VALUE": value})
        result = run_foreground_plan(plan, threading.Event())
        assert result.code == 0 and result.stdout == value + "\n" and not result.stderr
        selected = sandboxSpawn("ls", tmp, platform=sys.platform, exists=lambda _: True,
                                environ={"RUOCUN_SANDBOX": "1", "RUOCUN_SANDBOX_NO_NET": "1"})
        assert selected and "file" in selected and selected["args"][-3:] == ["/bin/sh", "-c", "ls"]
        expected = "--unshare-net" if sys.platform == "linux" else "(deny network*)"
        assert expected in " ".join(selected["args"])
    print(f"{sys.platform} / Python {sys.version.split()[0]}: {len(paths)} files passed Python 3.11 grammar and compile.")
    print(f"Source CLI {__version__}; native POSIX shell passed.")
    print("Windows x64 wheel tag checked; POSIX package install and product runtime are outside this design check.")
    assert not os.environ.get("PYTHONPATH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
