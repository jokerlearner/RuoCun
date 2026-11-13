"""Actual Windows SQLite runtime gate after importing the public store."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_importing_store_does_not_preload_uncontrolled_sqlite(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = (
        "import json,sys; "
        "from pathlib import Path; "
        "from ruocun.session.durable_store import DurableStore; "
        "from ruocun.session.runtime import verify_official_archive,verify_controlled_runtime; "
        "dll=verify_official_archive(Path(sys.argv[1]),Path(sys.argv[2])); "
        "record=verify_controlled_runtime(dll); "
        "print(json.dumps({'version':record.version,'gate':record.gate}))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(archive), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"version": "3.54.1", "gate": "met"}


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_existing_runtime_must_be_the_requested_dll(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = """
import sys
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.contract import RuntimeGateError
archive, root = Path(sys.argv[1]), Path(sys.argv[2])
first = verify_official_archive(archive, root / 'first')
second = verify_official_archive(archive, root / 'second')
verify_controlled_runtime(first)
try:
    verify_controlled_runtime(second)
except RuntimeGateError:
    pass
else:
    raise AssertionError('accepted a different DLL path as the loaded DLL')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(archive), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(sys.platform != "win32", reason="Windows SQLite runtime")
def test_store_revalidates_declared_runtime_path(tmp_path: Path) -> None:
    archive = Path(__file__).parent / "fixtures" / "sqlite-dll-win-x64-3540100.zip"
    code = """
import sys
from dataclasses import replace
from pathlib import Path
from ruocun.session.runtime import verify_official_archive, verify_controlled_runtime
from ruocun.session.durable_store import assert_runtime_gate
from ruocun.session.contract import RuntimeGateError
archive, root = Path(sys.argv[1]), Path(sys.argv[2])
first = verify_official_archive(archive, root / 'first')
second = verify_official_archive(archive, root / 'second')
record = verify_controlled_runtime(first)
try:
    assert_runtime_gate(replace(record, dll_path=str(second)))
except RuntimeGateError:
    pass
else:
    raise AssertionError('store accepted a manifest for a different loaded DLL')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", code, str(archive), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
