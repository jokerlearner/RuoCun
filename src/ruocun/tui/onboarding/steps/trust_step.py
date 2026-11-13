"""冻结 TrustStep.tsx (MIT) 的当前目录提示，说明 RuoCun 原生作用范围。"""

from ....i18n.i18n import getLang, t
from ...notifier import cleanNotificationText


def trust_prompt(root: str) -> str:
    body = (
        "信任后允许加载此目录的项目配置，包括 .ruocun/settings.json、settings.local.json 和 hooks.json。"
        "兼容配置仅在已启用且被配置来源规则选中时适用。请仅信任你自己编写或已审阅的目录。"
        if getLang() == "zh" else
        "Trust allows loading project configuration in this folder, including .ruocun/settings.json, settings.local.json and hooks.json. "
        "Compatibility configuration applies when enabled and selected by configuration source rules. Only trust folders you wrote or reviewed."
    )
    path = cleanNotificationText(root).replace("\n", " ").replace("\t", " ")
    return "\n".join((t("onboard.progress", 4, 4), t("onboard.trust.title"), path, body, "[y/N]"))
