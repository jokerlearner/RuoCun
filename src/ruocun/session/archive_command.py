"""处理用户的 /archive 查询，通过当前会话的存储线程分页读归档。

用户命令可显式选择范围；模型工具由其调用入口绑定可读范围。
"""

from __future__ import annotations

import json

from .contract import StoreError
from .storage_worker import StorageWorker


async def archiveCommand(worker: StorageWorker, arguments: list[str]) -> str:
    usage = "用法：/archive list [--scope 范围] [--offset N --limit N]；/archive read <id> [--scope 范围] [--offset N --limit N]"
    try:
        command = arguments[0] if arguments else "list"
        rest = arguments[1:]
        identity = rest.pop(0) if command == "read" and rest else None
        values: dict[str, str] = {}
        if len(rest) % 2:
            return usage
        for key, value in zip(rest[::2], rest[1::2], strict=True):
            if key not in {"--scope", "--offset", "--limit"} or key in values:
                return usage
            values[key] = value
        scope = values.get("--scope", "main")
        offset = int(values.get("--offset", "0"))
        limit = int(values.get("--limit", "4096" if command == "read" else "20"))
        if command == "list":
            page = await worker.archive_list(scope, offset=offset, limit=limit)
        elif command == "read" and identity is not None:
            page = await worker.archive_read(identity, scope, offset=offset, limit=limit)
        else:
            return usage
        return json.dumps(page, ensure_ascii=False, indent=2)
    except (ValueError, TypeError):
        return usage
    except StoreError as error:
        return f"归档读取已拒绝：{error}"
