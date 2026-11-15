"""组织首次启动的语言、账户和目录信任选择，校验通过后由启动入口注入的函数保存结果。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol, TypedDict

from ...config.profiles import DEFAULTS, Provider, ResolvedCredential
from ...i18n.i18n import getLang, t
from .select import SelectItem
from .steps.key_step import key_prompt, validation_error
from .steps.language_step import LANGUAGES, language_prompt
from .steps.provider_step import PROVIDERS, provider_options, provider_prompt
from .steps.trust_step import trust_prompt


class OnboardingUI(Protocol):
    async def show_welcome(self, info: Mapping[str, str], *, skip_footer: bool = False) -> None: ...

    async def select(self, title: str, items: Sequence[SelectItem], *, initial_index: int = 0,
                     wrap: bool = False) -> str | None: ...

    def set_language(self, lang: str) -> None: ...

    async def ask_secret_validated(self, prompt: str, submit: Callable[[str], Awaitable[bool]], *,
                                   validating: str) -> str | None: ...

    async def ask_trust(self, prompt: str) -> bool | None: ...

    async def write(self, text: str) -> None: ...


class OnboardingResult(TypedDict):
    resolved: ResolvedCredential
    lang: str
    trusted: bool


async def Onboarding(ui: OnboardingUI, *, welcome: Mapping[str, str], detectedLang: str,
                     validate: Callable[[Mapping[str, Any]], Awaitable[Mapping[str, Any]]],
                     persist: Callable[[Provider, dict[str, str], str], Awaitable[ResolvedCredential]],
                     writeLang: Callable[[str], Awaitable[None]], trustCurrent: Callable[[], Awaitable[None]],
                     workspaceRoot: str) -> OnboardingResult | None:
    await ui.show_welcome(welcome, skip_footer=True)
    lang = await ui.select(language_prompt(), LANGUAGES, initial_index=int(detectedLang == "en"), wrap=True)
    if lang is None or lang not in {"zh", "en"}:
        return None
    ui.set_language(lang)
    picked = await ui.select(provider_prompt(), provider_options(), wrap=True)
    if picked not in PROVIDERS:
        return None
    provider = picked
    meta = dict(DEFAULTS[provider])
    resolved: ResolvedCredential | None = None

    async def submit(key: str) -> bool:
        nonlocal resolved
        result = await validate({"baseUrl": meta["baseUrl"], "key": key, "provider": provider})
        if result.get("ok") is not True:
            await ui.write(validation_error(result.get("reason")))
            return False
        resolved = await persist(provider, meta, key)
        return True

    try:
        key = await ui.ask_secret_validated(key_prompt(provider), submit, validating=t("onboard.key.validating"))
        if key is None or resolved is None:
            return None
        trusted = await ui.ask_trust(trust_prompt(workspaceRoot))
        if trusted is None:
            return None
        await writeLang(lang)
        if trusted:
            await trustCurrent()
    except Exception:
        # 写入结果未知时提示检查已保存状态。自动重试可能重复写入，底层错误也可能带出凭据。
        await ui.write("✗ " + ("保存失败，已退出。请先检查已保存的账户和设置。" if getLang() == "zh" else
                              "Save failed; exiting. Check the saved account and settings before retrying."))
        return None
    return {"resolved": resolved, "lang": lang, "trusted": trusted}
