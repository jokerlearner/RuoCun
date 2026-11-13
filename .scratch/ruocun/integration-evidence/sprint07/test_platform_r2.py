"""Close the two confirmed REC-12 counterexamples, without new guarantees."""

from __future__ import annotations

import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest
from ruocun.platform.file_contract import AtomicFileError
import ruocun.platform.windows.durable_file as port

from test_platform_independent import attempt


@pytest.mark.parametrize("access", [0x100, 0x40000000])
@pytest.mark.parametrize("readonly", [False, True])
def test_established_namespace_resists_real_metadata_process(tmp_path: Path, access: int, readonly: bool) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    alternate.mkdir()
    port.ensure_private_dir(private)
    anchor = private / "anchor.db"
    if readonly:
        anchor.write_bytes(b"synthetic-existing-data")
    before = sorted(p.name for p in private.iterdir())
    with port.PrivateDirectory(private, readonly=readonly, anchor_file="anchor.db" if readonly else None):
        result = attempt(private, alternate, access)
        assert not result.get("changed", False), result
    assert sorted(p.name for p in private.iterdir()) == before
    assert list(alternate.iterdir()) == []


def test_readonly_empty_directory_fails_closed(tmp_path: Path) -> None:
    private = tmp_path / "private"
    port.ensure_private_dir(private)
    for anchor in (None, "absent.db", "../anchor", ".", ".."):
        with pytest.raises(AtomicFileError):
            with port.PrivateDirectory(private, readonly=True, anchor_file=anchor):
                raise AssertionError("unprotected empty readonly directory was accepted")
        assert list(private.iterdir()) == []


@pytest.mark.parametrize("readonly", [False, True])
def test_native_open_window_rejects_real_second_process_junction(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, readonly: bool) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    ready, done = tmp_path / "ready", tmp_path / "done"
    port.ensure_private_dir(private)
    port.ensure_private_dir(alternate)
    anchor = private / "anchor.db"
    if readonly:
        anchor.write_bytes(b"synthetic-existing-data")
    real_dll = ctypes.WinDLL
    fired = False

    class ScheduledCall:
        def __init__(self, call):
            object.__setattr__(self, "call", call)

        def __setattr__(self, key, value):
            setattr(self.call, key, value)

        def __call__(self, *args):
            nonlocal fired
            assert not fired
            fired = True
            attributes = args[2]._obj
            assert attributes.RootDirectory is None
            assert attributes.Length == 48 and attributes.Attributes & 0x1000
            assert args[8] & 0x20 and args[1] & 0x100000
            assert attributes.ObjectName.contents.Buffer.startswith("\\??\\" + str(private))
            if readonly:
                anchor.unlink()  # Only this test's own anchor, before native open.
            child = subprocess.Popen([sys.executable, "-I", "-X", "utf8", str(Path(__file__).with_name("test_platform_independent.py").resolve()), "--hold-metadata", str(private), str(alternate), str(ready), str(done)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.01)
                assert ready.exists(), "synthetic metadata child failed to start"
                return self.call(*args)
            finally:
                done.write_text("synthetic-done", encoding="ascii")
                _out, error = child.communicate(timeout=10)
                assert child.returncode == 0, error

    class NativeProxy:
        def __init__(self, native):
            self.NtCreateFile = ScheduledCall(native.NtCreateFile)

    def scheduled_library(name, *args, **kwargs):
        library = real_dll(name, *args, **kwargs)
        return NativeProxy(library) if name == "ntdll" else library

    monkeypatch.setattr(ctypes, "WinDLL", scheduled_library)
    with pytest.raises(AtomicFileError):
        with port.PrivateDirectory(private, readonly=readonly, anchor_file="anchor.db" if readonly else None):
            raise AssertionError("native open followed a replacement junction")
    assert fired
    assert list(private.iterdir()) == list(alternate.iterdir()) == []


@pytest.mark.parametrize("readonly", [False, True])
def test_nonempty_anchor_is_not_removable_by_second_process(tmp_path: Path, readonly: bool) -> None:
    private = tmp_path / "private"
    port.ensure_private_dir(private)
    anchor = private / "anchor.db"
    if readonly:
        anchor.write_bytes(b"synthetic-existing-data")
    with port.PrivateDirectory(private, readonly=readonly, anchor_file="anchor.db" if readonly else None):
        target = anchor if readonly else next(private.glob(".ruocun-guard-*.tmp"))
        child = subprocess.run([sys.executable, "-I", "-X", "utf8", "-c", "import sys,json; from pathlib import Path; p=Path(sys.argv[1]); assert p.is_absolute(); assert p.parent.name=='private';\ntry: p.unlink()\nexcept PermissionError: print(json.dumps({'denied':True}))\nelse: print(json.dumps({'denied':False}))", str(target)], capture_output=True, text=True, timeout=10)
        assert child.returncode == 0, child.stderr
        assert json.loads(child.stdout) == {"denied": True}
    if readonly:
        assert anchor.read_bytes() == b"synthetic-existing-data"
    else:
        assert list(private.iterdir()) == []
