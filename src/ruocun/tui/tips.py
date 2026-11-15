"""从当前终端语言的提示库中选择一条快捷用法。"""

import random

from ..i18n.i18n import tips


def randomTip() -> str:
    values = tips()
    return random.choice(values) if values else ""
