"""Choose a RuoCun welcome line for the plain terminal banner."""

import math
import random
from collections.abc import Callable

from ..data.laozi_maxims import MAXIMS, Maxim


def randomMaxim(rng: Callable[[], float] = random.random) -> Maxim:
    return MAXIMS[min(len(MAXIMS) - 1, math.floor(rng() * len(MAXIMS)))]
