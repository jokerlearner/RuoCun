"""解析显式账户配置并通过原生系统端口保存凭据。"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Mapping, Protocol, cast

from .compat import use_keychain_enabled
from .profiles import ProfilesConfig, ResolvedCredential
from .profiles_store import addProfile

if TYPE_CHECKING:
    from ..platform.windows.credentials import CredentialBackend

KEYREF_PREFIX = "keychain:"
NEW_KEYCHAIN_SERVICE = "ruocun-api-key"

LookupStatus = Literal["found", "not-found", "refused", "timeout-unconfirmed", "error-unconfirmed"]
StoredKind = Literal["system", "file"]


@dataclass(frozen=True)
class SecretLookup:
    status: LookupStatus
    secret: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class SecretStoreResult:
    stored: Literal["system", "file", "unknown"]
    status: Literal["stored", "refused", "timeout-unconfirmed", "error-unconfirmed"] = "stored"


class CredentialWriteUnconfirmed(RuntimeError):
    """系统写入尚未确认，调用者不得将其视为失败或自动重复写入。"""


class KeychainPort(Protocol):
    def get(self, service: str, account: str) -> SecretLookup: ...

    def set(self, service: str, account: str, secret: str) -> SecretStoreResult: ...

    def delete(self, service: str, account: str) -> None: ...


@dataclass
class MemoryKeychain:
    """合成内存钥匙串：仅测试/演示用；不接系统后端、不读真实密钥。"""

    secrets: dict[tuple[str, str], str] = field(default_factory=dict, repr=False)
    calls: list[tuple[str, str, str]] = field(default_factory=list)
    last_lookup: SecretLookup | None = None
    refuse: bool = False
    timeout_unconfirmed: bool = False

    def get(self, service: str, account: str) -> SecretLookup:
        self.calls.append(("get", service, account))
        lookup = self._lookup(service, account)
        self.last_lookup = lookup
        return lookup

    def _lookup(self, service: str, account: str) -> SecretLookup:
        if self.timeout_unconfirmed:
            return SecretLookup("timeout-unconfirmed")
        if self.refuse:
            return SecretLookup("refused")
        value = self.secrets.get((service, account))
        return SecretLookup("found", value) if value is not None else SecretLookup("not-found")

    def set(self, service: str, account: str, secret: str) -> SecretStoreResult:
        self.calls.append(("set", service, account))
        if self.timeout_unconfirmed:
            return SecretStoreResult("unknown", "timeout-unconfirmed")
        if self.refuse:
            return SecretStoreResult("file", "refused")
        self.secrets[(service, account)] = secret
        return SecretStoreResult("system", "stored")

    def delete(self, service: str, account: str) -> None:
        self.calls.append(("delete", service, account))
        self.secrets.pop((service, account), None)


@dataclass
class UnavailableKeychain:
    """系统凭据后端不可用（本票不实现）：明确 not-found / file fallback。"""

    def get(self, service: str, account: str) -> SecretLookup:
        return SecretLookup("not-found")

    def set(self, service: str, account: str, secret: str) -> SecretStoreResult:
        return SecretStoreResult("file", "refused")

    def delete(self, service: str, account: str) -> None:
        return None


_FAILURE_TEXT: dict[str, str] = {
    "not-found": "系统凭据未找到（not-found），请重新配置账户",
    "refused": "系统凭据访问被拒绝（refused），请检查权限后重新配置",
    "timeout-unconfirmed": "系统凭据查询超时、结果未确认（timeout-unconfirmed），请重新配置或稍后重试",
    "error-unconfirmed": "系统凭据查询出错、结果未确认（error-unconfirmed），请重新配置或稍后重试",
}


def describeFailure(lookup: SecretLookup) -> str:
    """准确显示失败状态，绝不回显任何 secret 值。"""
    return _FAILURE_TEXT.get(lookup.status, "")


def account_for(profile_name: str) -> str:
    return f"ruocun/{profile_name}"


def key_ref_for(profile_name: str) -> str:
    return f"{KEYREF_PREFIX}{account_for(profile_name)}"


def _native_account(cfg: ProfilesConfig, name: str, key_ref: object) -> str | None:
    if not name or key_ref != key_ref_for(name):
        return None
    ruocun_meta = cfg.get("_ruocun")
    origins: Any = (
        ruocun_meta.get("credentialOrigins", {}) if isinstance(ruocun_meta, dict) else {}
    )
    record = origins.get(name) if isinstance(origins, dict) else None
    if (isinstance(record, dict) and record.get("keyRef") == key_ref
            and record.get("service") != NEW_KEYCHAIN_SERVICE):
        return None
    return account_for(name)


def resolveCredential(
    cfg: ProfilesConfig,
    kc: KeychainPort,
) -> ResolvedCredential | None:
    name = cfg.get("activeProfile")
    profiles = cfg.get("profiles")
    if not isinstance(name, str) or not isinstance(profiles, dict):
        return None
    p = profiles.get(name)
    if not isinstance(p, dict):
        return None
    key = p.get("key")
    if isinstance(key, str) and key:
        return cast(ResolvedCredential, {
            "key": key, "provider": p.get("provider"),
            "baseUrl": p.get("baseUrl"), "model": p.get("model"),
            "source": f"profile:{name}",
        })
    account = _native_account(cfg, name, p.get("keyRef"))
    if account is None:
        return None
    lookup = kc.get(NEW_KEYCHAIN_SERVICE, account)
    if lookup.status != "found" or not lookup.secret:
        return None
    return cast(ResolvedCredential, {
        "key": lookup.secret, "provider": p.get("provider"),
        "baseUrl": p.get("baseUrl"), "model": p.get("model"),
        "source": f"profile:{name}",
    })


def persistKey(
    cfg: ProfilesConfig,
    name: str,
    meta: Mapping[str, Any],
    key: str,
    kc: KeychainPort,
    *,
    prefer_keychain: bool,
) -> tuple[ProfilesConfig, StoredKind]:
    """系统保存成功后只写引用与来源；明确失败时写入原生配置文件。"""
    account = account_for(name)
    key_ref = key_ref_for(name)
    if prefer_keychain:
        # 使用与最终新增相同的重名检查，在可能覆盖系统凭据之前拒绝无效请求。
        new_cfg = addProfile(cfg, name, {**meta, "keyRef": key_ref})
        result = kc.set(NEW_KEYCHAIN_SERVICE, account, key)
        if result.status in ("timeout-unconfirmed", "error-unconfirmed"):
            raise CredentialWriteUnconfirmed(
                f"系统凭据写入结果未知（{result.status}），请确认后再操作")
        if result.status == "stored" and result.stored == "system":
            ruocun_meta = new_cfg.get("_ruocun")
            origins: dict[str, Any] = (
                dict(ruocun_meta.get("credentialOrigins", {}))
                if isinstance(ruocun_meta, dict) and isinstance(
                    ruocun_meta.get("credentialOrigins", {}), dict)
                else {}
            )
            origins[name] = {"keyRef": key_ref, "service": NEW_KEYCHAIN_SERVICE}
            rest = dict(ruocun_meta) if isinstance(ruocun_meta, dict) else {}
            rest["credentialOrigins"] = origins
            return {**new_cfg, "_ruocun": rest}, "system"
    return addProfile(cfg, name, {**meta, "key": key}), "file"


RECONFIGURE_HINT = "请重新配置账户（提供内联 key 或有效的若存系统凭据引用）"


def diagnoseCredential(
    cfg: ProfilesConfig,
    kc: KeychainPort,
) -> str:
    """报告当前账户的凭据状态，输出不含密钥。"""
    name = cfg.get("activeProfile")
    profiles = cfg.get("profiles")
    if not isinstance(name, str) or not isinstance(profiles, dict):
        return f"无有效激活账户；{RECONFIGURE_HINT}"
    p = profiles.get(name)
    if not isinstance(p, dict):
        return f"激活账户 {name} 无有效 profile；{RECONFIGURE_HINT}"
    key = p.get("key")
    if isinstance(key, str) and key:
        return "激活账户使用内联 key（stored=file），无需系统凭据"
    account = _native_account(cfg, name, p.get("keyRef"))
    if account is None:
        return f"未配置可用凭据；{RECONFIGURE_HINT}"
    lookup = kc.get(NEW_KEYCHAIN_SERVICE, account)
    if lookup.status == "found" and lookup.secret:
        return f"系统凭据可用（stored=system，service={NEW_KEYCHAIN_SERVICE}）"
    failure = describeFailure(lookup)
    return f"{failure}；请重新配置账户或稍后重试"


def createKeychain(
    environ: Mapping[str, str], *, backend: CredentialBackend | None = None,
    timeout_seconds: float = 8.0,
) -> KeychainPort:
    if sys.platform != "win32" or not use_keychain_enabled(environ):
        return UnavailableKeychain()
    from ..platform.windows.credentials import (
        Win32CredentialBackend,
        WindowsCredentialStore,
    )

    try:
        selected = backend if backend is not None else Win32CredentialBackend()
    except OSError:
        return UnavailableKeychain()
    return WindowsCredentialStore(selected, timeout_seconds=timeout_seconds)
