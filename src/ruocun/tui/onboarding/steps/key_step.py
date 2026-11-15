"""生成当前服务商的凭据输入提示，把验证失败转换为可显示的消息。"""

from ....config.profiles import Provider
from ....i18n.i18n import t

_REASONS = {"invalid", "unreachable", "http"}


def key_prompt(provider: Provider) -> str:
    return "\n".join((t("onboard.progress", 3, 4), t("onboard.key.title"), t("onboard.key.help." + provider)))


def validation_error(reason: object) -> str:
    name = reason if isinstance(reason, str) and reason in _REASONS else "fail"
    return "✗ " + t("validate.reason." + name)
