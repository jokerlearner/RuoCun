"""在调用方明确提供旧、新目录时尝试移动旧目录。

发现新目录已经存在时视为迁移已处理过，保留目标中现有的数据。
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

MigrateResult = Literal["migrated", "skipped", "absent"]


def migrateLegacyDir(old_dir: str | Path, new_dir: str | Path) -> MigrateResult:
    old, new = Path(old_dir), Path(new_dir)
    if not old.is_dir():
        return "absent"
    if new.exists():
        return "skipped"  # 目标存在表示已处理过，保留目标目录中的数据。
    old.rename(new)
    return "migrated"
