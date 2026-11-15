"""为纯文本欢迎横幅选取一句若存短句。"""

import math
import random
from collections.abc import Callable

from ..data.laozi_maxims import MAXIMS, Maxim


def randomMaxim(rng: Callable[[], float] = random.random) -> Maxim:
    return MAXIMS[min(len(MAXIMS) - 1, math.floor(rng() * len(MAXIMS)))]
