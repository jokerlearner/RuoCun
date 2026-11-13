"""Run the supported Windows quality and package checks locally or in CI."""

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_ORIGIN = """\
import importlib.metadata, importlib.util, sys
from pathlib import Path
import ruocun
actual = Path(ruocun.__file__).resolve().parent
expected = Path(sys.prefix).resolve() / 'Lib' / 'site-packages' / 'ruocun'
assert actual == expected, (actual, expected)
assert ruocun.__version__ == importlib.metadata.version('ruocun')
print('Installed package:', actual, flush=True)
"""
_PURE = _ORIGIN + "assert importlib.util.find_spec('pytest') is None\n"
_WHEEL = _PURE + """\
from zipfile import ZipFile

metadata_suffixes = ('.dist-info/METADATA', '.dist-info/WHEEL')
distribution = importlib.metadata.distribution('ruocun')
installed_metadata = {
    str(path) for path in (distribution.files or ()) if str(path).endswith(metadata_suffixes)
}
installed_members = {
    path.relative_to(actual.parent).as_posix()
    for path in actual.rglob('*')
    if path.is_file() and '__pycache__' not in path.relative_to(actual).parts
}
with ZipFile(sys.argv[1]) as archive:
    names = archive.namelist()
    metadata = {name for name in names if name.endswith(metadata_suffixes)}
    members = {name for name in names if name.startswith('ruocun/') and not name.endswith('/')}
    if len(metadata) != 2 or metadata != installed_metadata or members != installed_members:
        raise SystemExit('Installed package does not match the supplied wheel member list.')
    for name in sorted(members | metadata):
        if (actual.parent / name).read_bytes() != archive.read(name):
            raise SystemExit(f'Installed package does not match the supplied wheel: {name}')
print(f'Installed wheel bytes verified: {len(members) + len(metadata)} members', flush=True)
"""
_PYTEST = _ORIGIN + """\
import os
git, managed, *pytest_args = sys.argv[1:]
os.environ['PATH'] = str(Path(git).parent) + os.pathsep + os.environ['PATH']
os.environ['ProgramData'] = managed
import pytest
import ruocun_acceptance
raise SystemExit(pytest.main(pytest_args))
"""


def _outside_checkout(path: Path) -> None:
    if any((directory / ".git").exists() for directory in (path, *path.parents)):
        raise ValueError(f"Use a temporary directory outside every Git checkout: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", "static", "package", "full"), default="all")
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--work", type=Path)
    parser.add_argument("--dev-python", type=Path)
    parser.add_argument("--installed-python", type=Path)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--git", type=Path)
    args = parser.parse_args()
    if sys.platform != "win32" or sys.version_info[:2] != (3, 11) or struct.calcsize("P") != 8:
        parser.error("The Windows gate requires CPython 3.11 x64 on Windows.")
    if args.installed_python and args.stage in {"all", "full"} and args.wheel is None:
        parser.error("Pass --wheel to bind the separate pytest installation to the same package.")
    state = args.state.resolve()
    state.mkdir(parents=True, exist_ok=True)
    wheelhouse = args.wheelhouse.resolve(strict=True) if args.wheelhouse else None
    if args.work:
        work = args.work.resolve()
        _outside_checkout(work)
        work.mkdir(parents=True, exist_ok=True)
    else:
        work = Path(tempfile.mkdtemp(prefix="ruocun-ci-")).resolve()
        _outside_checkout(work)

    def run(label, python, *arguments, cwd=REPO):
        cmd = [sys.executable, "-I", "-X", "utf8", REPO / "tools" / "run.py", "--label", label, "--state", state, "--cwd", cwd]
        if wheelhouse is not None:
            cmd += ["--wheelhouse", wheelhouse]
        cmd += ["--", python, "-I", "-X", "utf8", *arguments]
        subprocess.run([str(item) for item in cmd], cwd=REPO, check=True)

    def venv(name):
        destination = work / name
        if destination.exists():
            raise ValueError(f"Expected a fresh virtual environment: {destination}")
        run(f"{name}-venv", sys.executable, "-m", "venv", "--copies", destination, cwd=work)
        return destination / "Scripts" / "python.exe"

    def dependencies(python, lock, label):
        location = ["--no-index", "--find-links", wheelhouse] if wheelhouse else ["--index-url", "https://pypi.org/simple"]
        run(label, python, "-m", "pip", "install", *location, "--only-binary=:all:", "--require-hashes", "-r", REPO / lock)

    try:
        dev = args.dev_python.resolve(strict=True) if args.dev_python else None
        needs_dev = args.stage != "package" or (args.installed_python is None and args.wheel is None)
        if dev is None and needs_dev:
            dev = venv("development")
            dependencies(dev, "requirements-dev-win311.lock", "development-dependencies")
        if args.stage in {"all", "static"}:
            run("ruff", dev, "-m", "ruff", "check", ".")
            run("ruff-ci", dev, "-m", "ruff", "check", "--no-force-exclude", REPO / ".github" / "ci")
            run("mypy", dev, "-m", "mypy")
        if args.stage == "static":
            return 0
        installed = args.installed_python.resolve(strict=True) if args.installed_python else None
        wheel = args.wheel.resolve(strict=True) if args.wheel else None
        if installed is None:
            if wheel is None:
                dist = state / "dist"
                dist.mkdir()
                run("build-sdist-wheel", dev, "-m", "build", "--no-isolation", "--outdir", dist)
                wheel, = dist.glob("*.whl")
                sdist, = dist.glob("*.tar.gz")
                files = (wheel, sdist)
                (state / "SHA256SUMS").write_text("".join(
                    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files), encoding="ascii")
            installed = venv("installed")
            dependencies(installed, "requirements-runtime-win311.lock", "installed-dependencies")
            run("install-wheel", installed, "-m", "pip", "install", "--no-index", "--no-deps", wheel, cwd=work)
        run("pip-check", installed, "-m", "pip", "check", cwd=work)
        if wheel is None:
            run("installed-origin", installed, "-c", _PURE, cwd=work)
        else:
            run("installed-origin", installed, "-c", _WHEEL, wheel, cwd=work)
        run("installed-version", installed, "-m", "ruocun", "--version", cwd=work)
        run("installed-help", installed, "-m", "ruocun", "--help", cwd=work)
        if args.stage in {"all", "full"}:
            git = args.git or shutil.which("git.exe")
            if not git:
                parser.error("Pass the explicit Git executable to run the worktree and checkpoint tests.")
            git = Path(git).resolve(strict=True)
            # Tests start new isolated interpreters, so their dependencies must
            # be installed in the QA interpreter, separate from the pure smoke.
            qa = dev if args.dev_python is None else venv("qa")
            if args.dev_python is not None:
                dependencies(qa, "requirements-dev-win311.lock", "qa-dependencies")
            run("qa-wheel", qa, "-m", "pip", "install", "--no-index", "--no-deps", wheel, cwd=work)
            run("qa-support", qa, "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation",
                REPO / "tests" / "support", cwd=work)
            run("installed-pytest", qa, "-c", _PYTEST, git, work / "managed",
                "-q", "--basetemp", work / "pytest", "--junitxml", state / "windows-junit.xml")
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
