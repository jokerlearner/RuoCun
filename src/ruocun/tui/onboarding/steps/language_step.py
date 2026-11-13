"""冻结 LanguageStep.tsx (MIT) 的语言选项与默认值。"""

from ....i18n.i18n import t
from ..select import SelectItem

LANGUAGES: tuple[SelectItem, ...] = ({"label": "中文", "value": "zh"}, {"label": "English", "value": "en"})


def language_prompt() -> str:
    return t("onboard.progress", 1, 4) + "\n" + t("onboard.lang.title")
