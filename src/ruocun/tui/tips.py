"""冻结tui/tips.ts（MIT）。"""

import random

from ..i18n.i18n import tips


def randomTip() -> str:
    values = tips()
    return random.choice(values) if values else ""
