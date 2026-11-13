"""58旧候选最小复现与D09 Windows私有文件适配。"""

import json

import pytest

from ruocun.config import credential, profiles_store
from ruocun.platform.windows.durable_file import ensure_private_dir, verify_private_file

META = {"provider": "openai", "baseUrl": "http://127.0.0.1:1/v1", "model": "synthetic"}


def test_duplicate_profile_is_rejected_before_system_write():
    old = "synthetic-existing-key"
    store = credential.MemoryKeychain({("ruocun-api-key", "ruocun/work"): old})
    cfg = {"version": 2, "activeProfile": "work", "profiles": {"work": {**META, "keyRef": "keychain:ruocun/work"}}}
    with pytest.raises(ValueError, match="账户已存在"):
        credential.persistKey(cfg, "work", META, "synthetic-new-key", store, prefer_keychain=True)
    assert store.secrets[("ruocun-api-key", "ruocun/work")] == old
    assert store.calls == []


def test_fallback_file_is_private_atomic_and_preserves_unknown_fields(tmp_path):
    native = tmp_path / "native"
    path = native / "config.json"
    cfg, stored = credential.persistKey(
        {"version": 2, "activeProfile": "default", "profiles": {}, "theme": "dark"},
        "work", META, "synthetic-file-key", credential.UnavailableKeychain(), prefer_keychain=True,
    )
    profiles_store.saveProfiles(path, cfg)
    assert stored == "file" and verify_private_file(path)
    actual = json.loads(path.read_text(encoding="utf-8"))
    assert actual["profiles"]["work"]["key"] == "synthetic-file-key" and actual["theme"] == "dark"


def test_corrupt_saved_profiles_are_preserved_on_save_failure(tmp_path):
    native = tmp_path / "native"
    ensure_private_dir(native)
    path = native / "config.json"
    original = b"{unconfirmed synthetic original"
    path.write_bytes(original)
    with pytest.raises(ValueError):
        profiles_store.saveProfiles(path, {"version": 2, "activeProfile": "default", "profiles": {}})
    assert path.read_bytes() == original
