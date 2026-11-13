"""REC-12: product publication remains bound to its validated directory.

All race targets live under one fresh pytest sandbox. No native relative-name
APIs are used, and no pre-existing paths or historical probes are reused.
"""

from __future__ import annotations

import ctypes
import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun.platform.windows.durable_file as files
from ruocun.platform.file_contract import AtomicFileError


def _hold_junction(private: Path, alternate: Path) -> None:
    """Child-only fixture: one held synthetic directory, undone via that handle."""
    from ctypes import wintypes as W

    assert private.is_absolute() and alternate.is_absolute()
    assert private.parent == alternate.parent
    assert private.name == "private" and alternate.name == "alternate"
    assert not private.lstat().st_file_attributes & 0x400
    assert not alternate.lstat().st_file_attributes & 0x400
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.DeviceIoControl.argtypes = [W.HANDLE, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    kernel.DeviceIoControl.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
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
        print("READY", flush=True)
        assert sys.stdin.readline().strip() == "done"
    finally:
        if changed:
            removal = struct.pack("<IHH", 0xA0000003, 0, 0)
            assert kernel.DeviceIoControl(handle, 0x900AC, removal, len(removal), None, 0, ctypes.byref(W.DWORD()), None)
        kernel.CloseHandle(handle)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows directory sharing")
@pytest.mark.parametrize("swap_ancestor", [False, True])
def test_publication_cannot_be_redirected_by_parent_junction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, swap_ancestor: bool,
) -> None:
    sandbox = tmp_path.resolve()
    container, retired, alternate = (sandbox / x for x in ("container", "retired", "alternate"))
    assert not any(p.exists() for p in (container, retired, alternate))
    container.mkdir()
    private = container / "private"
    files.ensure_private_dir(private)
    files.ensure_private_dir(alternate)
    alternate_private = alternate / "private" if swap_ancestor else alternate
    if swap_ancestor:
        files.ensure_private_dir(alternate_private)
    target = alternate_private / "record"
    target.write_bytes(b"old-synthetic")
    replace = os.replace
    redirected = False

    def race(source: Path, destination: Path) -> None:
        nonlocal redirected
        assert source.parent == private and destination == private / "record"
        try:
            (container if swap_ancestor else private).rename(retired)
        except PermissionError:
            # A directory pin must reject rename before a junction can exist.
            replace(source, destination)
            return
        junction = container if swap_ancestor else private
        result = subprocess.run(
            [r"C:\Windows\System32\cmd.exe", "/c", "mklink", "/J", str(junction), str(alternate)],
            capture_output=True, timeout=10,
        )
        assert result.returncode == 0
        redirected = True
        (alternate_private / source.name).write_bytes(b"new-synthetic")
        replace(source, destination)

    monkeypatch.setattr(files.os, "replace", race)
    try:
        try:
            files.atomic_publish(private / "record", b"new-synthetic")
        except AtomicFileError:
            pass
        assert target.read_bytes() == b"old-synthetic", "publication followed a replacement junction"
    finally:
        if redirected:
            # Remove only the exact junction created above, never recurse into it.
            os.rmdir(container if swap_ancestor else private)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows reparse semantics")
def test_pinned_empty_directory_cannot_become_a_junction(tmp_path: Path) -> None:
    """One named sandbox; metadata changes target only its held directory handle."""
    from ctypes import wintypes as W

    private, alternate = tmp_path / "private", tmp_path / "alternate"
    alternate.mkdir()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.DeviceIoControl.argtypes = [W.HANDLE, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD), ctypes.c_void_p]
    kernel.DeviceIoControl.restype = W.BOOL
    kernel.CloseHandle.argtypes = [W.HANDLE]
    substitute = ("\\??\\" + str(alternate.resolve())).encode("utf-16-le")
    printable = str(alternate.resolve()).encode("utf-16-le")
    names = substitute + b"\0\0" + printable + b"\0\0"
    payload = struct.pack("<IHHHHHH", 0xA0000003, len(names) + 8, 0, 0, len(substitute), len(substitute) + 2, len(printable)) + names
    with files.PrivateDirectory(private):
        handle = kernel.CreateFileW(str(private), 0x40000000, 7, None, 3, 0x02200000, None)
        assert handle not in (None, 0, ctypes.c_void_p(-1).value)
        changed = False
        try:
            returned = W.DWORD()
            changed = bool(kernel.DeviceIoControl(handle, 0x900A4, payload, len(payload), None, 0, ctypes.byref(returned), None))
            error = ctypes.get_last_error()
            assert not changed and error == 145, "pinned private directory accepted reparse metadata"
        finally:
            if changed:
                # Undo only our own tag via the same handle; never traverse it.
                removal = struct.pack("<IHH", 0xA0000003, 0, 0)
                assert kernel.DeviceIoControl(handle, 0x900AC, removal, len(removal), None, 0, ctypes.byref(W.DWORD()), None)
            kernel.CloseHandle(handle)
    assert list(private.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native name parsing")
@pytest.mark.parametrize("readonly", [False, True])
def test_guard_native_open_rejects_second_process_reparse_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, readonly: bool,
) -> None:
    private, alternate = tmp_path / "private", tmp_path / "alternate"
    files.ensure_private_dir(private)
    files.ensure_private_dir(alternate)
    anchor = private / "session.db"
    if readonly:
        anchor.write_bytes(b"synthetic-existing-data")
    win_dll = ctypes.WinDLL
    fired = False

    class ScheduledCall:
        def __init__(self, call: object) -> None:
            object.__setattr__(self, "call", call)

        def __setattr__(self, key: str, value: object) -> None:
            setattr(self.call, key, value)

        def __call__(self, *args: object) -> object:
            nonlocal fired
            if fired:
                return self.call(*args)
            fired = True
            if readonly:
                anchor.unlink()
            child = subprocess.Popen(
                [sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--hold-junction", str(private), str(alternate)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                assert child.stdout is not None and child.stdout.readline().strip() == "READY"
                return self.call(*args)
            finally:
                _out, error = child.communicate("done\n", timeout=10)
                assert child.returncode == 0, error

    class ScheduledLibrary:
        def __init__(self, library: object) -> None:
            self.NtCreateFile = ScheduledCall(library.NtCreateFile)

    def scheduled_dll(name: str, *args: object, **kwargs: object) -> object:
        library = win_dll(name, *args, **kwargs)
        return ScheduledLibrary(library) if name == "ntdll" else library

    monkeypatch.setattr(ctypes, "WinDLL", scheduled_dll)
    with pytest.raises(AtomicFileError):
        with files.PrivateDirectory(private, readonly=readonly, anchor_file="session.db" if readonly else None):
            raise AssertionError("guard setup followed the replacement junction")
    assert fired
    assert list(private.iterdir()) == list(alternate.iterdir()) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Windows readonly namespace")
def test_readonly_requires_and_holds_existing_private_file_anchor(tmp_path: Path) -> None:
    private = tmp_path / "private"
    files.ensure_private_dir(private)
    with pytest.raises(AtomicFileError):
        with files.PrivateDirectory(private, readonly=True):
            pass
    assert list(private.iterdir()) == []
    anchor = private / "session.db"
    anchor.write_bytes(b"synthetic-existing-data")
    with files.PrivateDirectory(private, readonly=True, anchor_file="session.db"):
        with pytest.raises(PermissionError):
            anchor.unlink()
        assert list(private.iterdir()) == [anchor]
    assert anchor.read_bytes() == b"synthetic-existing-data"
    with files.PrivateDirectory(private):
        guards = list(private.glob(".ruocun-guard-*.tmp"))
        assert len(guards) == 1
        with pytest.raises(PermissionError):
            guards[0].unlink()


if __name__ == "__main__" and sys.argv[1] == "--hold-junction":
    _hold_junction(Path(sys.argv[2]), Path(sys.argv[3]))

