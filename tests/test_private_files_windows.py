"""Windows private-directory and atomic publication behaviour (REC-12)."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ruocun.platform.windows.durable_file as durable_file
from ruocun.platform.file_contract import AtomicFileError
from ruocun.platform.windows.durable_file import (
    PublishDurabilityError,
    atomic_publish,
    ensure_private_dir,
)


def _sddl(path: Path) -> str:
    ps = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
    result = subprocess.run(
        [str(ps), "-NoProfile", "-NonInteractive", "-Command", "(Get-Acl -LiteralPath $env:RUOCUN_TEST_ACL_PATH).Sddl"],
        env={**os.environ, "RUOCUN_TEST_ACL_PATH": str(path)},
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    return result.stdout.strip()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_existing_unmanaged_directory_acl_is_never_modified(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    before = _sddl(existing)
    with pytest.raises(AtomicFileError):
        ensure_private_dir(existing)
    assert _sddl(existing) == before


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_new_directory_and_published_file_are_private_and_reusable(tmp_path: Path) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    original_acl = _sddl(directory)
    assert "D:P" in original_acl
    assert "OICI" in original_acl
    ensure_private_dir(directory)
    result = atomic_publish(directory / "credentials.json", b"synthetic-value")
    assert result.replaced and result.durability == "confirmed"
    assert (directory / "credentials.json").read_bytes() == b"synthetic-value"
    assert _sddl(directory) == original_acl
    child_acl = _sddl(directory / "credentials.json")
    assert "(A;ID;FA;;;" in child_acl
    assert child_acl.count("(A;") == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_paged_export_publication_preserves_old_file_when_source_fails(tmp_path: Path) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "archive.json"
    atomic_publish(target, b"old confirmed export")
    def broken_pages():
        yield b"first synthetic page"
        raise ValueError("synthetic source read failed")
    with pytest.raises(AtomicFileError):
        atomic_publish(target, broken_pages())
    assert target.read_bytes() == b"old confirmed export"
    receipt = atomic_publish(target, iter((b"first ", b"second")))
    assert target.read_bytes() == b"first second"
    assert receipt.bytes_written == 12 and receipt.durability == "confirmed"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native long paths")
def test_long_run_directory_preserves_private_atomic_publication(tmp_path: Path) -> None:
    # Ordinary session/run nesting can exceed MAX_PATH without a long component.
    parent = tmp_path / ("s" * max(1, 240 - len(str(tmp_path)) - 1))
    parent.mkdir(parents=True)
    directory = parent / "12345678-1234-1234-1234-123456789abc"
    ensure_private_dir(directory)
    ensure_private_dir(directory)
    target = durable_file.local_path(directory / "bootstrap.json")
    receipt = atomic_publish(target, b"synthetic-runner-bootstrap")
    assert receipt.replaced and receipt.durability == "confirmed"
    assert target.read_bytes() == b"synthetic-runner-bootstrap"
    durable_file.verify_private_file(target)
    assert durable_file.local_path(target) == target
    assert durable_file.local_path(tmp_path) == tmp_path
    with pytest.raises(AtomicFileError):
        durable_file.local_path(Path(r"\\?\UNC\synthetic-host\share\run"))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
@pytest.mark.parametrize("error_type", [AtomicFileError, OSError, RuntimeError])
def test_directory_sync_failure_reports_visible_but_unconfirmed(
    tmp_path: Path, error_type: type[Exception],
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"

    def fail_sync(_path: Path) -> str:
        raise error_type("synthetic directory sync failure")

    with pytest.raises(PublishDurabilityError) as caught:
        atomic_publish(target, b"synthetic-new-value", sync_directory_fn=fail_sync)
    assert caught.value.receipt.replaced
    assert caught.value.receipt.durability == "unconfirmed"
    assert target.read_bytes() == b"synthetic-new-value"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit])
def test_post_replace_interrupt_preserves_exception_and_attaches_receipt(
    tmp_path: Path, error_type: type[BaseException],
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"

    def interrupt(_path: Path) -> str:
        raise error_type("synthetic interruption")

    with pytest.raises(error_type) as caught:
        atomic_publish(target, b"synthetic-new-value", sync_directory_fn=interrupt)
    receipt = caught.value.publish_receipt  # type: ignore[attr-defined]
    assert receipt.replaced and receipt.durability == "unconfirmed"
    assert target.read_bytes() == b"synthetic-new-value"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows sharing semantics")
def test_locked_destination_preserves_previous_value(tmp_path: Path) -> None:
    from ctypes import wintypes as W

    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"
    atomic_publish(target, b"old")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        W.LPCWSTR, W.DWORD, W.DWORD, ctypes.c_void_p, W.DWORD, W.DWORD, W.HANDLE
    ]
    kernel.CreateFileW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.CreateFileW(str(target), 0x80000000, 0x1 | 0x2, None, 3, 0, None)
    assert handle not in (None, 0, ctypes.c_void_p(-1).value)
    try:
        with pytest.raises(AtomicFileError):
            atomic_publish(target, b"new")
        assert target.read_bytes() == b"old"
        assert sorted(p.name for p in directory.iterdir()) == ["record"]
    finally:
        kernel.CloseHandle(handle)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows reparse points")
def test_reparse_directory_is_rejected_before_writing(tmp_path: Path) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    link = tmp_path / "link"
    result = subprocess.run(
        [r"C:\Windows\System32\cmd.exe", "/c", "mklink", "/J", str(link), str(directory)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    with pytest.raises(AtomicFileError):
        atomic_publish(link / "record", b"synthetic-value")
    assert not (directory / "record").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_replace_and_temporary_cleanup_failures_are_both_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"
    atomic_publish(target, b"old")
    original_unlink = Path.unlink

    def deny_replace(_source: object, _target: object) -> None:
        raise PermissionError("synthetic replace failure")

    def deny_temporary_cleanup(path: Path, *args: object, **kwargs: object) -> None:
        if path.parent == directory and path.name.endswith(".tmp"):
            raise PermissionError("synthetic cleanup failure")
        original_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(durable_file.os, "replace", deny_replace)
    monkeypatch.setattr(Path, "unlink", deny_temporary_cleanup)
    with pytest.raises(AtomicFileError) as caught:
        atomic_publish(target, b"synthetic-new-value")
    error = caught.value
    assert isinstance(error.__cause__, PermissionError)
    assert isinstance(error.cleanup_error, PermissionError)  # type: ignore[attr-defined]
    retained = Path(error.retained_path)  # type: ignore[attr-defined]
    assert retained.parent == directory and retained.read_bytes() == b"synthetic-new-value"
    assert target.read_bytes() == b"old"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_untrusted_or_unreadable_owner_rejects_private_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    original_acl = _sddl(directory)
    # Inject an operating-system owner result: this does not claim a live
    # cross-account test or change the host's owner or privileges.
    monkeypatch.setattr(durable_file, "_read_owner_sid", lambda _path: "S-1-5-18", raising=False)
    with pytest.raises(AtomicFileError):
        ensure_private_dir(directory)
    assert _sddl(directory) == original_acl

    def unavailable(_path: Path) -> str:
        raise AtomicFileError("synthetic owner lookup failure")

    monkeypatch.setattr(durable_file, "_read_owner_sid", unavailable)
    with pytest.raises(AtomicFileError):
        ensure_private_dir(directory)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
@pytest.mark.parametrize("deny_cleanup", [False, True])
def test_interruption_before_replace_cleans_or_reports_retained_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, deny_cleanup: bool,
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"
    atomic_publish(target, b"old")
    original_unlink = Path.unlink

    def interrupted_fsync(_fd: int) -> None:
        raise KeyboardInterrupt("synthetic fsync interruption")

    def maybe_deny_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if deny_cleanup and path.parent == directory and path.name.endswith(".tmp"):
            raise PermissionError("synthetic unlink failure")
        original_unlink(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(durable_file.os, "fsync", interrupted_fsync)
    monkeypatch.setattr(Path, "unlink", maybe_deny_unlink)
    with pytest.raises(KeyboardInterrupt) as caught:
        atomic_publish(target, b"synthetic-new-value")
    error = caught.value
    assert not error.replacement_uncertain  # type: ignore[attr-defined]
    assert target.read_bytes() == b"old"
    if deny_cleanup:
        assert isinstance(error.cleanup_error, PermissionError)  # type: ignore[attr-defined]
        retained = Path(error.retained_path)  # type: ignore[attr-defined]
        assert retained.read_bytes() == b"synthetic-new-value"
    else:
        assert error.retained_path is None  # type: ignore[attr-defined]


@pytest.mark.skipif(sys.platform != "win32", reason="Windows private ACL")
def test_replace_interruption_reports_possibly_published_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / "private"
    ensure_private_dir(directory)
    target = directory / "record"
    atomic_publish(target, b"old")
    replace = durable_file.os.replace

    def replace_then_interrupt(src: object, dst: object) -> None:
        replace(src, dst)  # type: ignore[arg-type]
        raise KeyboardInterrupt("synthetic after-rename interruption")

    monkeypatch.setattr(durable_file.os, "replace", replace_then_interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        atomic_publish(target, b"new")
    assert target.read_bytes() == b"new"
    assert caught.value.replacement_uncertain  # type: ignore[attr-defined]
    receipt = caught.value.publish_receipt  # type: ignore[attr-defined]
    assert receipt.replaced is None and receipt.durability == "unconfirmed"
