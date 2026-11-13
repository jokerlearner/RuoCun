"""冻结 skills/adapt.ts（MIT）的外来技能结构识别。"""

from __future__ import annotations

import re
from collections.abc import Set as AbstractSet

_NAMESPACE = re.compile(r"(^|[\s`(])[a-z][a-z0-9_-]*:[a-z][a-z0-9-]{2,}(?![A-Za-z0-9_])")
_TOOL = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`|(?<![A-Za-z0-9_])([A-Z][a-zA-Z]+|[a-z]+_[a-z_]+)"
                   r"(?![A-Za-z0-9_])\s*(?:tool|工具)")


def isForeignSkill(body: str, toolNames: AbstractSet[str]) -> bool:
    if _NAMESPACE.search(body):
        return True
    for match in _TOOL.finditer(body):
        token = match[1] or match[2]
        if token not in toolNames and ("_" in token or token[0].isupper()):
            return True
    return False
