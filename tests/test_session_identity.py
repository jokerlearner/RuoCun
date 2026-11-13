"""Cross-process identity behaviour from REC-09 and frozen process_identity tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest

import ruocun.session.process_identity as identity_module
from ruocun.session.contract import CrossHostError, IdentityQueryError, ProcessIdentity
from ruocun.session.process_identity import identity_alive, process_identity


@pytest.mark.skipif(sys.platform != "win32", reason="Windows identity path")
def test_live_child_is_recognized_across_processes() -> None:
    code = (
        "import json,sys; from dataclasses import asdict; "
        "from ruocun.session.process_identity import process_identity; "
        "print(json.dumps(asdict(process_identity())), flush=True); sys.stdin.read()"
    )
    for _ in range(12):
        child = subprocess.Popen(
            [sys.executable, "-I", "-X", "utf8", "-c", code],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert child.stdout is not None
            first = child.stdout.readline()
            assert first, "child did not report its identity"
            identity = ProcessIdentity(**json.loads(first))
            assert identity_alive(identity), "a live child on this boot must not be mistaken for dead"
        finally:
            child.communicate(timeout=15)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows identity path")
def test_real_process_identity_fences_start_boot_and_other_host() -> None:
    identity = process_identity(os.getpid())
    assert identity is not None
    assert identity_alive(identity)
    assert not identity_alive(replace(identity, start=identity.start + "-different"))
    assert not identity_alive(replace(identity, boot=identity.boot + "-different"))
    with pytest.raises(CrossHostError):
        identity_alive(replace(identity, host=identity.host + "-different"))


@pytest.mark.skipif(sys.platform != "win32", reason="Windows identity path")
def test_identity_query_failure_is_not_treated_as_dead(monkeypatch: pytest.MonkeyPatch) -> None:
    identity = process_identity(os.getpid())
    assert identity is not None

    def denied(_pid: int) -> ProcessIdentity | None:
        raise IdentityQueryError("synthetic denied identity query")

    monkeypatch.setattr(identity_module, "process_identity", denied)
    with pytest.raises(IdentityQueryError):
        identity_alive(identity)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows identity path")
def test_exited_child_is_dead_while_parent_retains_its_process_handle() -> None:
    child = subprocess.Popen(
        [sys.executable, "-I", "-c", "import sys; print('READY', flush=True); sys.stdin.read()"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert child.stdout is not None and child.stdout.readline().strip() == "READY"
        identity = process_identity(child.pid)
        assert identity is not None and identity_alive(identity)
        child.communicate(timeout=15)
        # Popen's process handle remains held here: the exited kernel object can
        # still be queried, but must not fence a legitimate recovery owner.
        assert not identity_alive(identity)
    finally:
        if child.poll() is None:
            child.communicate(timeout=15)
