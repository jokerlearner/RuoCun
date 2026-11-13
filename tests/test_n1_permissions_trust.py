"""DAO config/trust.test.ts; native .ruocun and explicit synthetic user root."""
import asyncio
import os

import pytest

from ruocun.config.trust import (
    addTrusted,
    hasProjectConfig,
    isTrusted,
    shouldTrustProject,
)


def test_no_config(tmp_path):
    root, user = tmp_path / "project", tmp_path / "user"
    assert not hasProjectConfig(root)
    assert asyncio.run(shouldTrustProject(root, userRoot=user, environ={}))


def test_trust_project(tmp_path):
    root, user = tmp_path / "project", tmp_path / "user"
    (root / ".ruocun").mkdir(parents=True)
    (root / ".ruocun" / "hooks.json").write_text("{}", encoding="utf-8")
    assert hasProjectConfig(root)
    assert not asyncio.run(isTrusted(root, userRoot=user))
    assert not asyncio.run(shouldTrustProject(root, userRoot=user, environ={}))
    asyncio.run(addTrusted(root, userRoot=user))
    assert asyncio.run(isTrusted(root, userRoot=user))
    assert asyncio.run(shouldTrustProject(root, userRoot=user, environ={}))


def test_headless_override(tmp_path):
    root, user = tmp_path / "project", tmp_path / "user"
    (root / ".ruocun").mkdir(parents=True)
    (root / ".ruocun" / "settings.json").write_text("{}", encoding="utf-8")
    assert asyncio.run(shouldTrustProject(root, userRoot=user, environ={"RUOCUN_TRUST": "1"}))


def test_trust_publish_failure_preserves_previous_receipt(tmp_path, monkeypatch):
    user = tmp_path / "user"
    asyncio.run(addTrusted(tmp_path / "prior", userRoot=user))
    old = (user / "trusted.json").read_bytes()

    def failed_replace(*args):
        raise OSError("synthetic trust publication failure")

    monkeypatch.setattr(os, "replace", failed_replace)
    with pytest.raises(OSError, match="synthetic trust publication failure"):
        asyncio.run(addTrusted(tmp_path / "candidate", userRoot=user))
    assert (user / "trusted.json").read_bytes() == old
    assert not list(user.glob(".trusted.json.*.tmp"))
