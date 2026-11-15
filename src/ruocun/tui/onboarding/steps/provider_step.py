"""按首次引导的预定顺序生成服务商选项。"""

from ....config.profiles import Provider
from ....i18n.i18n import t
from ..select import SelectItem

PROVIDERS: tuple[Provider, ...] = ("deepseek", "volcengine", "qianfan", "zhipu")


def provider_options() -> list[SelectItem]:
    return [{"label": t("onboard.provider." + provider), "value": provider} for provider in PROVIDERS]


def provider_prompt() -> str:
    return t("onboard.progress", 2, 4) + "\n" + t("onboard.provider.title")
