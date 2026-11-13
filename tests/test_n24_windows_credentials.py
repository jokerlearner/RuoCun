"""58既有433d980候选的最小窄端口回归，不运行旧demo。"""

from __future__ import annotations

import pytest

from ruocun.config import credential as cred
from ruocun.platform.windows import credentials as wincred


def test_factory_respects_existing_env_switch_and_keeps_single_lookup_for_diagnosis():
    backend = wincred.InjectedBackend(read_override=wincred.NativeResult("refused", winerror=5))
    store = cred.createKeychain({}, backend=backend)
    cfg = {"version": 2, "activeProfile": "work", "profiles": {"work": {"keyRef": "keychain:ruocun/work"}}}
    assert cred.resolveCredential(cfg, store) is None
    assert "refused" in cred.describeFailure(store.last_lookup)
    assert len(backend.calls) == 1
    disabled = cred.createKeychain({"RUOCUN_USE_KEYCHAIN": "off", "DAO_USE_KEYCHAIN": "1"}, backend=backend)
    assert isinstance(disabled, cred.UnavailableKeychain)


def test_non_native_service_is_blocked_even_through_direct_port():
    backend = wincred.InjectedBackend()
    store = wincred.WindowsCredentialStore(backend)
    assert store.get("dao-api-key", "dao/work").status == "refused"
    with pytest.raises(ValueError, match="若存凭据服务"):
        store.set("dao-api-key", "dao/work", "synthetic-protected-key")
    with pytest.raises(ValueError, match="若存凭据服务"):
        store.delete("dao-api-key", "dao/work")
    assert backend.calls == []

def test_target_name_preserves_account_case_via_utf8_hex():
    # D17 probe.py:24-26；D09:152「保留 Profile/profile 区别；不依赖系统 TargetName 大小写敏感」
    upper = wincred.targetName("ruocun-api-key", "ruocun/Profile")
    lower = wincred.targetName("ruocun-api-key", "ruocun/profile")
    assert upper != lower


def test_target_name_is_service_plus_reversible_hex():
    # D09:152「TargetName 以服务名及原账户 UTF-8 hex 编码」；D17 中文账户实测。
    t = wincred.targetName("dao-api-key", "dao/中文账户")
    assert t.startswith("dao-api-key/")
    hex_part = t.split("/", 1)[1]
    assert hex_part == hex_part.lower()
    assert bytes.fromhex(hex_part).decode("utf-8") == "dao/中文账户"


@pytest.mark.parametrize("native_status,raw,winerror,expected,has_secret", [
    ("ok", b"sk-FROM-SYSTEM", None, "found", True),
    ("not-found", None, 1168, "not-found", False),
    ("refused", None, 5, "refused", False),
    ("timeout-unconfirmed", None, None, "timeout-unconfirmed", False),
    ("error-unconfirmed", None, None, "error-unconfirmed", False),
])
def test_get_maps_native_status_and_never_leaks_secret_on_failure(
    native_status, raw, winerror, expected, has_secret,
):
    # D09:152 准确区分 not-found/refused/timeout-unconfirmed；秘密只在 found 带出。
    backend = wincred.InjectedBackend(
        read_override=wincred.NativeResult(native_status, raw, winerror))
    lookup = wincred.WindowsCredentialStore(backend).get("ruocun-api-key", "ruocun/work")
    assert lookup.status == expected
    assert (lookup.secret is not None) is has_secret
    if has_secret:
        assert lookup.secret == "sk-FROM-SYSTEM"
    else:
        assert lookup.secret is None


@pytest.mark.parametrize("native_status,winerror,stored,status", [
    ("ok", None, "system", "stored"),
    ("refused", 5, "file", "refused"),
    ("timeout-unconfirmed", None, "unknown", "timeout-unconfirmed"),
    ("error-unconfirmed", None, "unknown", "error-unconfirmed"),
    ("error", None, "unknown", "error-unconfirmed"),
])
def test_set_reports_system_only_on_confirmed_ok(native_status, winerror, stored, status):
    # WIN-05「失败不误报系统保存」；D09:152「系统写结果不明不伪报已存」。
    backend = wincred.InjectedBackend(
        write_override=wincred.NativeResult(native_status, winerror=winerror))
    result = wincred.WindowsCredentialStore(backend).set(
        "ruocun-api-key", "ruocun/work", "sk-synthetic")
    assert result.stored == stored
    assert result.status == status


def test_delete_targets_exact_own_target_and_keeps_legacy_service_secret():
    # D09:156「删除 RuoCun 账户不得删除旧服务的 secret，即使 profile 同名」。
    legacy = wincred.targetName("dao-api-key", "dao/work")
    own = wincred.targetName("ruocun-api-key", "ruocun/work")
    backend = wincred.InjectedBackend(store={legacy: b"sk-OLD-LEGACY", own: b"sk-NEW"})
    wincred.WindowsCredentialStore(backend).delete("ruocun-api-key", "ruocun/work")
    assert backend.calls == [("delete", own)]  # 只一次、精确目标、不枚举其它账户
    assert backend.store[legacy] == b"sk-OLD-LEGACY"  # 旧服务 secret 保留
    assert own not in backend.store


DS_META = {
    "provider": "deepseek", "baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-pro",
}


SECRET = "sk-synthetic-NOT-A-REAL-KEY"


def test_system_roundtrip_persist_then_resolve_via_windows_port():
    # 冻结 credential.test.ts:59-67/34-44 + D09:152 新服务/provenance。
    store = wincred.WindowsCredentialStore(wincred.InjectedBackend())
    base = {"version": 2, "activeProfile": "default", "profiles": {}}
    cfg, stored = cred.persistKey(base, "work", DS_META, SECRET, store, prefer_keychain=True)
    assert stored == "system"
    assert cfg["profiles"]["work"]["keyRef"] == "keychain:ruocun/work"
    assert cfg["profiles"]["work"].get("key") is None
    assert cfg["_ruocun"]["credentialOrigins"]["work"]["service"] == "ruocun-api-key"
    resolved = cred.resolveCredential(cfg, store)
    assert resolved is not None and resolved["key"] == SECRET
    assert resolved["source"] == "profile:work"


def test_case_collision_profiles_do_not_overwrite_or_misdelete():
    # D17 e/cred.json case_safe_profiles；WIN-05「case collision 可区分」。
    store = wincred.WindowsCredentialStore(wincred.InjectedBackend())
    assert store.set("ruocun-api-key", "ruocun/Profile", "sk-UPPER").stored == "system"
    assert store.set("ruocun-api-key", "ruocun/profile", "sk-LOWER").stored == "system"
    assert store.get("ruocun-api-key", "ruocun/Profile").secret == "sk-UPPER"
    assert store.get("ruocun-api-key", "ruocun/profile").secret == "sk-LOWER"
    store.delete("ruocun-api-key", "ruocun/Profile")
    assert store.get("ruocun-api-key", "ruocun/Profile").status == "not-found"
    assert store.get("ruocun-api-key", "ruocun/profile").secret == "sk-LOWER"


def test_unresponsive_system_write_returns_unconfirmed_without_claiming_success():
    from threading import Event

    release = Event()
    finished = Event()

    class SlowSystem(wincred.InjectedBackend):
        def write(self, target, secret):
            try:
                release.wait(2)
                return super().write(target, secret)
            finally:
                finished.set()

    store = wincred.WindowsCredentialStore(SlowSystem(), timeout_seconds=0.05)
    try:
        result = store.set("ruocun-api-key", "ruocun/slow", "synthetic-secret")
        assert result.status == "timeout-unconfirmed"
        assert result.stored != "system"
    finally:
        release.set()
        assert finished.wait(2)


def test_late_system_write_remains_unknown_without_fallback_or_replay():
    from threading import Event

    release = Event()
    finished = Event()

    class SlowSystem(wincred.InjectedBackend):
        def write(self, target, secret):
            try:
                release.wait(2)
                return super().write(target, secret)
            finally:
                finished.set()

    backend = SlowSystem()
    store = wincred.WindowsCredentialStore(backend, timeout_seconds=0.05)
    base = {"version": 2, "activeProfile": "default", "profiles": {}}
    try:
        with pytest.raises(cred.CredentialWriteUnconfirmed):
            cred.persistKey(base, "work", DS_META, SECRET, store, prefer_keychain=True)
        assert base["profiles"] == {}
    finally:
        release.set()
        assert finished.wait(2)
    lookup = store.get("ruocun-api-key", "ruocun/work")
    assert lookup.status == "found" and lookup.secret == SECRET
    assert len([call for call in backend.calls if call[0] == "write"]) == 1


def test_system_write_then_exception_does_not_fall_back_or_retry():
    class WriteThenRaise(wincred.InjectedBackend):
        def write(self, target, secret):
            super().write(target, secret)
            raise OSError(secret.decode())  # 合成值，确认底层异常文本不会传播。

    backend = WriteThenRaise()
    store = wincred.WindowsCredentialStore(backend)
    base = {"version": 2, "activeProfile": "default", "profiles": {}}
    with pytest.raises(cred.CredentialWriteUnconfirmed) as error:
        cred.persistKey(base, "work", DS_META, SECRET, store, prefer_keychain=True)
    assert "error-unconfirmed" in str(error.value)
    assert SECRET not in str(error.value)
    assert base["profiles"] == {}
    assert len([call for call in backend.calls if call[0] == "write"]) == 1
    assert store.get("ruocun-api-key", "ruocun/work").secret == SECRET


def test_secret_bearing_credential_objects_do_not_expose_secret_in_repr():
    sample = "synthetic-value-for-repr-check"
    objects = [
        cred.SecretLookup("found", sample),
        cred.MemoryKeychain({("service", "account"): sample}),
        wincred.NativeResult("ok", sample.encode()),
        wincred.InjectedBackend(store={"target": sample.encode()}),
    ]
    for value in objects:
        assert sample not in repr(value)
        assert sample not in str(value)


def test_duplicate_profile_rejected_before_system_credential_is_overwritten():
    account = "ruocun/work"
    target = wincred.targetName("ruocun-api-key", account)
    old_secret = "synthetic-old-key"
    backend = wincred.InjectedBackend(store={target: old_secret.encode()})
    store = wincred.WindowsCredentialStore(backend)
    base = {
        "version": 2,
        "activeProfile": "work",
        "profiles": {"work": {"keyRef": "keychain:ruocun/work"}},
    }
    with pytest.raises(ValueError) as error:
        cred.persistKey(base, "work", DS_META, "synthetic-new-key", store,
                        prefer_keychain=True)
    assert str(error.value) == "账户已存在:work(先 /account rm work 再新建)"
    assert backend.calls == []
    assert store.get("ruocun-api-key", account).secret == old_secret


