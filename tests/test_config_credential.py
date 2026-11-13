"""CFG-04: 凭据优先级、keyRef 精确只读、provenance 与状态区分。

预期独立来源：
- 冻结 src/config/credential.ts:1-46 及 .test.ts:23-84
- 冻结 src/config/keychain.ts:8-18（旧服务 dao-api-key）
- D09「环境别名与凭据范围」:152-156（新写 ruocun-api-key / ruocun/<profile>、
  旧 keychain:<account> 按原 account 精确只读 dao-api-key、_ruocun.credentialOrigins、
  stored=system/file、not-found/refused/timeout-unconfirmed 明确区分、不读真实现存密钥）
按 S/D/R 改写：服务名/账户名按 D09 已确认 INTENTIONAL-DELTA 更新。
"""

from __future__ import annotations

import pytest

from ruocun.config import credential

DS_META: dict = {
    "provider": "deepseek", "baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-pro",
}


def _cfg(profile: dict, name: str = "work") -> dict:
    return {"version": 2, "activeProfile": name, "profiles": {name: profile}}


# ---------------------------------------------------------------------------
# resolveCredential (冻结 credential.test.ts:23-53)
# ---------------------------------------------------------------------------


def test_inline_key_wins_over_keyref_and_does_not_touch_keychain():
    # frozen credential.test.ts:24-32 + CFG-04「inline 优先」
    cfg = _cfg({**DS_META, "key": "sk-inline", "keyRef": "keychain:dao/work"})
    kc = credential.MemoryKeychain({("dao-api-key", "dao/work"): "sk-secret"})
    r = credential.resolveCredential(cfg, kc)
    assert r is not None and r["key"] == "sk-inline" and r["source"] == "profile:work"
    assert kc.calls == []  # 内联非空优先，不查钥匙串


def test_previous_service_keyref_does_not_query_system():
    cfg = _cfg({**DS_META, "keyRef": "keychain:dao/work"})
    kc = credential.MemoryKeychain({("dao-api-key", "dao/work"): "sk-from-keychain"})
    assert credential.resolveCredential(cfg, kc) is None
    assert kc.calls == []


def test_missing_secret_returns_null():
    # frozen credential.test.ts:46-53
    cfg = _cfg({**DS_META, "keyRef": "keychain:ruocun/work"})
    assert credential.resolveCredential(cfg, credential.MemoryKeychain()) is None


def test_missing_key_does_not_auto_pick_account_from_generic_env():
    # CFG-04「缺 key 不靠 OPENAI_API_KEY 等通用环境变量自动挑账户」
    cfg = _cfg({**DS_META})  # 无 key / 无 keyRef
    kc = credential.MemoryKeychain({("dao-api-key", "dao/work"): "sk-secret"})
    assert credential.resolveCredential(cfg, kc) is None
    assert kc.calls == []  # 连 keychain 都不查，更不读环境


def test_native_reference_must_match_the_active_account_name():
    cfg = _cfg({**DS_META, "keyRef": "keychain:ruocun/other"})
    kc = credential.MemoryKeychain({("ruocun-api-key", "ruocun/other"): "sk-other"})
    assert credential.resolveCredential(cfg, kc) is None
    assert kc.calls == []


def test_native_new_keyref_maps_to_new_service():
    # D09:152-154「原生无来源标记时，新 keychain:ruocun/ 映射新服务」
    cfg = _cfg({**DS_META, "keyRef": "keychain:ruocun/work"})
    kc = credential.MemoryKeychain({("ruocun-api-key", "ruocun/work"): "sk-new"})
    r = credential.resolveCredential(cfg, kc)
    assert r is not None and r["key"] == "sk-new"
    assert ("get", "ruocun-api-key", "ruocun/work") in kc.calls


def test_unknown_non_keychain_prefix_has_no_credential():
    cfg = _cfg({**DS_META, "keyRef": "vault:somewhere"})
    assert credential.resolveCredential(cfg, credential.MemoryKeychain()) is None


def test_explicit_previous_service_record_does_not_use_a_same_name_native_secret():
    cfg = _cfg({**DS_META, "keyRef": "keychain:ruocun/work"})
    cfg["_ruocun"] = {"credentialOrigins": {
        "work": {"keyRef": "keychain:ruocun/work", "service": "dao-api-key"},
    }}
    kc = credential.MemoryKeychain({("dao-api-key", "ruocun/work"): "sk-old",
                                    ("ruocun-api-key", "ruocun/work"): "sk-other"})
    assert credential.resolveCredential(cfg, kc) is None
    assert kc.calls == []


# ---------------------------------------------------------------------------
# 状态区分与不泄漏秘密 (D09:152-156)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kwargs,status,seed", [
    ({}, "not-found", {}),  # not-found 的真值：该账户没有 secret
    ({"refuse": True}, "refused",
     {("ruocun-api-key", "ruocun/work"): "sk-SECRET-VALUE"}),
    ({"timeout_unconfirmed": True}, "timeout-unconfirmed",
     {("ruocun-api-key", "ruocun/work"): "sk-SECRET-VALUE"}),
])
def test_keychain_failure_states_are_distinct_and_never_leak_secret(kwargs, status, seed):
    cfg = _cfg({**DS_META, "keyRef": "keychain:ruocun/work"})
    kc = credential.MemoryKeychain(seed, **kwargs)
    assert credential.resolveCredential(cfg, kc) is None
    assert kc.last_lookup is not None and kc.last_lookup.status == status
    text = credential.describeFailure(kc.last_lookup)
    assert status in text
    assert "sk-SECRET-VALUE" not in text  # fallback 准确显示且不泄漏秘密


# ---------------------------------------------------------------------------
# persistKey (冻结 credential.test.ts:56-84 + D09 新写服务)
# ---------------------------------------------------------------------------


def test_persist_key_writes_new_service_and_leaves_only_keyref():
    # D09:152「新写服务名 ruocun-api-key，账户 ruocun/<profile原始名称>」
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    kc = credential.MemoryKeychain()
    cfg, stored = credential.persistKey(
        base, "work", DS_META, "sk-secret", kc, prefer_keychain=True)
    assert stored == "system"
    assert ("ruocun-api-key", "ruocun/work") in kc.secrets
    assert cfg["profiles"]["work"].get("key") is None
    assert cfg["profiles"]["work"]["keyRef"] == "keychain:ruocun/work"
    assert cfg["activeProfile"] == "work"
    # provenance 记录不含秘密
    origins = cfg["_ruocun"]["credentialOrigins"]["work"]
    assert origins == {"keyRef": "keychain:ruocun/work", "service": "ruocun-api-key"}
    assert "sk-secret" not in str(origins)


def test_persist_key_falls_back_to_inline_file_when_system_write_fails():
    # frozen credential.test.ts:69-75 + D09:156「明确失败按原格式文件 fallback，真实显示 file」
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    kc = credential.MemoryKeychain(refuse=True)
    cfg, stored = credential.persistKey(
        base, "work", DS_META, "sk-secret", kc, prefer_keychain=True)
    assert stored == "file"
    assert cfg["profiles"]["work"]["key"] == "sk-secret"
    assert cfg["profiles"]["work"].get("keyRef") is None


def test_persist_key_without_preference_uses_inline_file():
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    kc = credential.MemoryKeychain()
    cfg, stored = credential.persistKey(
        base, "p", DS_META, "sk", kc, prefer_keychain=False)
    assert stored == "file"
    assert cfg["profiles"]["p"]["key"] == "sk"
    assert kc.secrets == {}


def test_persist_key_never_deletes_legacy_service_secret():
    # D09:156「删除 RuoCun 账户不得删除旧服务的 secret，即使 profile 同名」
    base: dict = {"version": 2, "activeProfile": "default", "profiles": {}}
    kc = credential.MemoryKeychain({("dao-api-key", "dao/work"): "sk-old-legacy"})
    credential.persistKey(base, "work", DS_META, "sk-new", kc, prefer_keychain=True)
    assert ("dao-api-key", "dao/work") in kc.secrets  # 旧 secret 保留
    assert not any(call[0] == "delete" for call in kc.calls)  # 未删除任何旧凭据
