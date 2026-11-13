"""冻结config/auth_wizard.ts（MIT）；校验/输入注入，密钥存储复用58。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypedDict

from ..i18n.i18n import t
from .credential import KeychainPort, persistKey
from .profiles import Profile, ProfilesConfig, ResolvedCredential


@dataclass
class WizardDeps:
    cfg: ProfilesConfig
    name: str
    meta: Profile
    ask: Callable[[str], Awaitable[str]]
    write: Callable[[str], None]
    validate: Callable[[dict[str, str]], Awaitable[dict[str, Any]]]
    kc: KeychainPort
    preferKeychain: bool


class WizardResult(TypedDict):
    cfg: ProfilesConfig
    resolved: ResolvedCredential


async def runKeyWizard(deps: WizardDeps) -> WizardResult | None:
    while True:
        key = (await deps.ask(t("wizard.paste"))).strip()
        if not key:
            deps.write(t("wizard.abandoned") + "\n")
            return None
        deps.write(t("wizard.validating") + "\n")
        validated = await deps.validate({"baseUrl": deps.meta["baseUrl"], "key": key})
        if not validated.get("ok"):
            reason = validated.get("reason")
            reason = reason if reason in {"invalid", "unreachable", "http"} else "fail"
            deps.write(t("wizard.retry", t("validate.reason." + reason)) + "\n")
            continue
        # persistKey保留58的不明写入显式异常，不捕捉后重试；cfg由组合根保存。
        cfg, stored = persistKey(deps.cfg, deps.name, deps.meta, key, deps.kc, prefer_keychain=deps.preferKeychain)
        deps.write(t("wizard.storedKeychain" if stored == "system" else "wizard.storedFile") + "\n")
        return {"cfg": cfg, "resolved": {"key": key, "provider": deps.meta["provider"],
                                          "baseUrl": deps.meta["baseUrl"], "model": deps.meta["model"],
                                          "source": "profile:" + deps.name}}
