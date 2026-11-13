"""旧目录改名纯函数（来源冻结 ``src/config/migrate_dirs.ts``，MIT）。

CFG-09 / ADR-0005 / D09:9：RuoCun 使用独立原生根，**不自动**移动、改名或写回
旧目录，不接管旧会话。本模块保留来源 ``migrateLegacyDir`` 纯函数语义供
隔离验证；产品启动路径不调用它去接管其它应用目录。
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
        return "skipped"  # 新目录已存在说明已迁移过，不动旧目录，避免覆盖
    old.rename(new)
    return "migrated"
