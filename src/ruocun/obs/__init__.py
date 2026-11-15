"""可选的运行观测接口。采集和导出失败由观测层消化，业务调用独立完成。"""

from .backend import closeObs, flushObs, isObsOn, observationScope, obsStatus, spanScope
from .init import initObs

__all__ = ["closeObs", "flushObs", "initObs", "isObsOn", "observationScope", "obsStatus", "spanScope"]
