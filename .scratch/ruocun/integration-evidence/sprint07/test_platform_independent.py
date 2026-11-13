"""Win32 source-derived checks, using a second process and fresh synthetic paths.

No relative native file APIs. Reparse changes target only a freshly created
directory handle; any change is undone using that same handle before return.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes as W
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

import pytest
import ruocun.platform.windows.durable_file as port


def kernel_api():
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.DeviceIoControl.argtypes = [W.HANDLE, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    kernel.DeviceIoControl.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.CloseHandle.restype = W.BOOL
    return kernel


def child_metadata(private: Path, alternate: Path, access: int) -> None:
    # Explicitly reject non-sibling paths and pre-existing reparse points.
    assert private.is_absolute() and alternate.is_absolute()
    assert private.parent == alternate.parent
    assert private.name == "private" and alternate.name == "alternate"
    assert not private.lstat().st_file_attributes & 0x400
    assert not alternate.lstat().st_file_attributes & 0x400
    kernel = kernel_api()
    handle = kernel.CreateFileW(str(private), access, 7, None, 3, 0x02200000, None)
    if handle in (None, 0, ctypes.c_void_p(-1).value):
        print(json.dumps({"opened": False, "open_error": ctypes.get_last_error()}))
        return
    substitute = ("\\??\\" + str(alternate)).encode("utf-16-le")
    printable = str(alternate).encode("utf-16-le")
    names = substitute + b"\0\0" + printable + b"\0\0"
    payload = struct.pack("<IHHHHHH", 0xA0000003, len(names) + 8, 0, 0, len(substitute), len(substitute) + 2, len(printable)) + names
    changed = False
    try:
        returned = W.DWORD()
        changed = bool(kernel.DeviceIoControl(handle, 0x900A4, payload, len(payload), None, 0, ctypes.byref(returned), None))
        error = ctypes.get_last_error()
        print(json.dumps({"opened": True, "changed": changed, "set_error": error}))
    finally:
        if changed:
            removal = struct.pack("<IHH", 0xA0000003, 0, 0)
            assert kernel.DeviceIoControl(handle, 0x900AC, removal, len(removal), None, 0, ctypes.byref(W.DWORD()), None)
        assert kernel.CloseHandle(handle)


def attempt(private: Path, alternate: Path, access: int) -> dict:
    child = subprocess.run([sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--metadata", str(private), str(alternate), str(access)],
                           capture_output=True, text=True, timeout=10)
    assert child.returncode == 0, child.stderr
    return json.loads(child.stdout)


@pytest.mark.parametrize("readonly", [False, True])
@pytest.mark.parametrize("access", [0, 0x100, 0x40000000])
def test_held_directory_resists_second_process_reparse(tmp_path: Path, readonly: bool, access: int) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    alternate.mkdir()
    port.ensure_private_dir(private)
    with port.PrivateDirectory(private, readonly=readonly):
        result = attempt(private, alternate, access)
        assert not result.get("changed", False), result
    assert not private.lstat().st_file_attributes & 0x400
    assert list(private.iterdir()) == []
    assert list(alternate.iterdir()) == []


def test_second_process_rename_blocked_through_publication(tmp_path: Path) -> None:
    private = tmp_path / "private"
    alternate = tmp_path / "alternate"
    alternate.mkdir()
    port.ensure_private_dir(private)
    with port.PrivateDirectory(private):
        child = subprocess.run([sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--rename", str(private)], capture_output=True, text=True, timeout=10)
        assert child.returncode == 0, child.stderr
        assert json.loads(child.stdout) == {"denied": True}
    assert private.is_dir() and not (tmp_path / "retired").exists()


@pytest.mark.parametrize("access", [0x100, 0x40000000])
def test_empty_to_guard_exclusive_handle_blocks_metadata(tmp_path: Path, access: int) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    alternate.mkdir()
    port.ensure_private_dir(private)
    handle = port._open_directory_pin(private, exclusive_write=True)
    try:
        result = attempt(private, alternate, access)
        assert not result.get("changed", False), result
    finally:
        assert kernel_api().CloseHandle(handle)
    assert not private.lstat().st_file_attributes & 0x400


@pytest.mark.parametrize("access", [0x100, 0x40000000])
def test_readonly_nonempty_directory_resists_metadata(tmp_path: Path, access: int) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    alternate.mkdir()
    port.ensure_private_dir(private)
    marker = private / "synthetic-db"
    marker.write_bytes(b"synthetic-existing-data")
    with port.PrivateDirectory(private, readonly=True):
        result = attempt(private, alternate, access)
        assert not result.get("changed", False), result
    assert marker.read_bytes() == b"synthetic-existing-data"
    assert not private.lstat().st_file_attributes & 0x400


def child_hold_metadata(private: Path, alternate: Path, ready: Path, done: Path) -> None:
    assert private.is_absolute() and alternate.is_absolute()
    assert private.parent == alternate.parent == ready.parent == done.parent
    assert private.name == "private" and alternate.name == "alternate"
    assert ready.name == "ready" and done.name == "done"
    assert not private.lstat().st_file_attributes & 0x400
    assert not alternate.lstat().st_file_attributes & 0x400
    kernel = kernel_api()
    handle = kernel.CreateFileW(str(private), 0x100, 7, None, 3, 0x02200000, None)
    assert handle not in (None, 0, ctypes.c_void_p(-1).value)
    substitute = ("\\??\\" + str(alternate)).encode("utf-16-le")
    printable = str(alternate).encode("utf-16-le")
    names = substitute + b"\0\0" + printable + b"\0\0"
    payload = struct.pack("<IHHHHHH", 0xA0000003, len(names) + 8, 0, 0, len(substitute), len(substitute) + 2, len(printable)) + names
    changed = False
    try:
        changed = bool(kernel.DeviceIoControl(handle, 0x900A4, payload, len(payload), None, 0, ctypes.byref(W.DWORD()), None))
        assert changed, ctypes.get_last_error()
        ready.write_text("synthetic-ready", encoding="ascii")
        deadline = time.monotonic() + 5
        while not done.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert done.exists(), "synthetic scheduling deadline"
    finally:
        if changed:
            removal = struct.pack("<IHH", 0xA0000003, 0, 0)
            assert kernel.DeviceIoControl(handle, 0x900AC, removal, len(removal), None, 0, ctypes.byref(W.DWORD()), None)
        assert kernel.CloseHandle(handle)


def test_guard_creation_remains_bound_during_metadata_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pause only the guard CreateFileW call; all native operations remain real."""
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    ready, done = tmp_path / "ready", tmp_path / "done"
    port.ensure_private_dir(private)
    port.ensure_private_dir(alternate)
    kernel = port._kernel()
    fired = False

    class ScheduledKernel:
        def __getattr__(self, name):
            return getattr(kernel, name)

        def CreateFileW(self, name, *args):
            nonlocal fired
            path = Path(name)
            if not fired and path.parent == private and path.name.startswith(".ruocun-guard-"):
                fired = True
                child = subprocess.Popen([sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--hold-metadata", str(private), str(alternate), str(ready), str(done)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                try:
                    deadline = time.monotonic() + 5
                    while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                        time.sleep(0.01)
                    assert ready.exists(), "second-process metadata setup failed"
                    return kernel.CreateFileW(name, *args)
                finally:
                    done.write_text("synthetic-done", encoding="ascii")
                    _out, err = child.communicate(timeout=10)
                    assert child.returncode == 0, err
            return kernel.CreateFileW(name, *args)

    monkeypatch.setattr(port, "_kernel", lambda: ScheduledKernel())
    with port.PrivateDirectory(private):
        assert fired
        result = attempt(private, alternate, 0x100)
        assert not result.get("changed", False), {
            "second_process": result,
            "private_entries": [p.name for p in private.iterdir()],
            "alternate_guard_count": len(list(alternate.iterdir())),
        }
    assert list(private.iterdir()) == list(alternate.iterdir()) == []


if __name__ == "__main__":
    if sys.argv[1] == "--metadata":
        child_metadata(Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]))
    elif sys.argv[1] == "--hold-metadata":
        child_hold_metadata(*(Path(p) for p in sys.argv[2:6]))
    elif sys.argv[1] == "--rename":
        source = Path(sys.argv[2])
        assert source.is_absolute() and source.name == "private"
        destination = source.parent / "retired"
        assert not destination.exists()
        try:
            source.rename(destination)
        except PermissionError:
            print(json.dumps({"denied": True}))
        else:
            destination.rename(source)
            print(json.dumps({"denied": False}))
