"""Optional, failure-isolated observation (MIT)."""

from .backend import closeObs, flushObs, isObsOn, observationScope, obsStatus, spanScope
from .init import initObs

__all__ = ["closeObs", "flushObs", "initObs", "isObsOn", "observationScope", "obsStatus", "spanScope"]
