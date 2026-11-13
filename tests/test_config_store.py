"""原生账户配置读写、格式迁移与独立目录边界。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from ruocun.config import migrate_dirs, profiles_store
from ruocun.platform.windows.durable_file import ensure_private_dir

# ---------------------------------------------------------------------------
# profiles_store 来源行为 (profiles_store.test.ts)
# ---------------------------------------------------------------------------


def test_load_profiles_missing_file_returns_fresh_empty(tmp_path):
    cfg = profiles_store.loadProfiles(tmp_path / ".dao" / "config.json")
    assert cfg["version"] == 2
    assert cfg["profiles"] == {}


def test_load_profiles_migrates_legacy_apikey(tmp_path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"apiKey": "sk-legacy", "model": "m1"}), encoding="utf-8")
    cfg = profiles_store.loadProfiles(f)
    assert cfg["profiles"]["default"]["key"] == "sk-legacy"
    assert cfg["profiles"]["default"]["model"] == "m1"


def test_load_profiles_bad_json_returns_empty_archive(tmp_path):
    f = tmp_path / "config.json"
    f.write_text("{ not json", encoding="utf-8")
    cfg = profiles_store.loadProfiles(f)
    assert cfg["version"] == 2
    assert cfg["profiles"] == {}
    assert cfg["activeProfile"] == "default"


def test_save_and_reload_v2(tmp_path):
    f = tmp_path / ".ruocun" / "config.json"
    cfg = profiles_store.addProfile(profiles_store.loadProfiles(f), "work", {
        "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
        "model": "deepseek-v4-pro", "key": "sk-work",
    })
    profiles_store.saveProfiles(f, cfg)
    reloaded = profiles_store.loadProfiles(f)
    assert reloaded["profiles"]["work"]["key"] == "sk-work"
    assert reloaded["activeProfile"] == "work"


def test_save_preserves_unrelated_top_level_fields(tmp_path):
    # frozen profiles_store.test.ts:47-55
    native = tmp_path / ".ruocun"
    if sys.platform == "win32":
        ensure_private_dir(native)
    else:
        native.mkdir()
    f = native / "config.json"
    f.write_text(json.dumps({"apiKey": "sk-x", "theme": "dark"}), encoding="utf-8")
    cfg = profiles_store.loadProfiles(f)
    profiles_store.saveProfiles(f, cfg)
    obj = json.loads(f.read_text(encoding="utf-8"))
    assert obj["theme"] == "dark"
    assert obj["version"] == 2


def test_profile_mutations_are_pure_and_active_switches():
    # frozen profiles_store.test.ts:61-79
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    cfg = profiles_store.addProfile(base, "work", {
        "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "k",
    })
    assert cfg["profiles"]["work"]["key"] == "k"
    assert cfg["activeProfile"] == "work"
    assert base["profiles"] == {}  # 纯函数，不改原对象
    cfg2 = profiles_store.addProfile(cfg, "a", {
        "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "1",
    })
    assert profiles_store.setActive(cfg2, "work")["activeProfile"] == "work"
    with pytest.raises(ValueError):
        profiles_store.setActive(cfg2, "missing")


def test_add_profile_rejects_existing_name_one_account_one_key():
    # frozen profiles_store.test.ts:81-85
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    cfg = profiles_store.addProfile(base, "work", {
        "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "old",
    })
    with pytest.raises(ValueError):
        profiles_store.addProfile(cfg, "work", {
            "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "new",
        })
    assert cfg["profiles"]["work"]["key"] == "old"


def test_remove_active_profile_repoints_to_remaining():
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    cfg = profiles_store.addProfile(base, "a", {
        "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "1",
    })
    cfg = profiles_store.addProfile(cfg, "b", {
        "provider": "deepseek", "baseUrl": "b", "model": "m", "key": "2",
    })
    out = profiles_store.removeProfile(cfg, "b")
    assert "b" not in out["profiles"]
    assert out["activeProfile"] == "a"


# ---------------------------------------------------------------------------
# D09 整份选择 / 写回 (CFG-01/09)
# ---------------------------------------------------------------------------


def _v2_file(path: Path, key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "version": 2, "activeProfile": "p",
        "profiles": {"p": {"provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                           "model": "deepseek-v4-pro", "key": key}},
        "theme": "dark",  # 未知顶层字段
    }), encoding="utf-8")


def test_saving_one_explicit_account_file_keeps_the_other(tmp_path):
    native = tmp_path / "home" / ".ruocun" / "config.json"
    other = tmp_path / "other-config.json"
    _v2_file(other, "sk-other")
    before = other.read_bytes()
    cfg = profiles_store.addProfile(profiles_store.loadProfiles(native), "work", {
        "provider": "deepseek", "baseUrl": "https://api.deepseek.com",
        "model": "deepseek-v4-pro", "key": "sk-native",
    })
    profiles_store.saveProfiles(native, cfg)
    assert other.read_bytes() == before
    assert profiles_store.loadProfiles(native)["profiles"]["work"]["key"] == "sk-native"


def test_writeback_strips_legacy_apikey_keeps_v2_and_unknown_fields(tmp_path):
    directory = tmp_path / ".ruocun"
    if sys.platform == "win32":
        ensure_private_dir(directory)
    else:
        directory.mkdir()
    native = directory / "config.json"
    native.write_text(json.dumps({
        "apiKey": "sk-legacy", "baseUrl": "https://x", "model": "m", "theme": "dark",
    }), encoding="utf-8")
    cfg = profiles_store.loadProfiles(native)
    profiles_store.saveProfiles(native, cfg)
    obj = json.loads(native.read_text(encoding="utf-8"))
    assert "apiKey" not in obj  # 去旧 apiKey
    assert obj["version"] == 2  # 保留 v2
    assert obj["theme"] == "dark"  # 未知顶层字段


# ---------------------------------------------------------------------------
# migrate_dirs 来源纯函数 (migrate_dirs.test.ts) + CFG-09 产品边界
# ---------------------------------------------------------------------------


def test_migrate_renames_old_dir_with_contents(tmp_path):
    old, new = tmp_path / ".codeds", tmp_path / ".dao"
    (old / "memory").mkdir(parents=True)
    (old / "config.json").write_text("{}", encoding="utf-8")
    (old / "memory" / "a.md").write_text("fact", encoding="utf-8")
    assert migrate_dirs.migrateLegacyDir(old, new) == "migrated"
    assert (new / "config.json").read_text(encoding="utf-8") == "{}"
    assert (new / "memory" / "a.md").read_text(encoding="utf-8") == "fact"
    assert not old.exists()


def test_migrate_absent_when_old_dir_missing(tmp_path):
    assert migrate_dirs.migrateLegacyDir(tmp_path / ".codeds", tmp_path / ".dao") == "absent"
    assert not (tmp_path / ".dao").exists()


def test_migrate_skipped_leaves_both_when_new_exists(tmp_path):
    old, new = tmp_path / ".codeds", tmp_path / ".dao"
    old.mkdir()
    new.mkdir()
    (old / "old.txt").write_text("old", encoding="utf-8")
    (new / "new.txt").write_text("new", encoding="utf-8")
    assert migrate_dirs.migrateLegacyDir(old, new) == "skipped"
    assert (old / "old.txt").read_text(encoding="utf-8") == "old"
    assert (new / "new.txt").read_text(encoding="utf-8") == "new"


def test_migrate_absent_when_old_is_a_file(tmp_path):
    (tmp_path / ".codeds").write_text("not a dir", encoding="utf-8")
    assert migrate_dirs.migrateLegacyDir(tmp_path / ".codeds", tmp_path / ".dao") == "absent"


def test_ruocun_does_not_auto_takeover_old_dao_directory(tmp_path):
    # CFG-09 + ADR-0005：格式兼容不等于自动接管旧 DAO 目录；不自动移动/改名/写回。
    old_dao = tmp_path / ".dao"
    old_dao.mkdir()
    (old_dao / "config.json").write_text(json.dumps({
        "version": 2, "activeProfile": "p",
        "profiles": {"p": {"provider": "deepseek", "baseUrl": "https://api.deepseek.com",
                           "model": "deepseek-v4-pro", "key": "sk-old"}},
    }), encoding="utf-8")
    user_root = tmp_path / "home" / ".ruocun"
    user_root.mkdir(parents=True)
    native = user_root / "config.json"
    assert profiles_store.loadProfiles(native)["profiles"] == {}
    # 旧目录与内容原样保留，无新目录、无写回
    assert (old_dao / "config.json").exists()
    assert json.loads((old_dao / "config.json").read_text(encoding="utf-8"))["profiles"]["p"]["key"] == "sk-old"
    assert not native.exists()
