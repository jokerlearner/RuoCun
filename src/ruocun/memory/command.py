"""The foreground /memory audit and deletion branch from frozen index.ts."""

from ..tools.types import ToolRejected
from .audit import formatAudit, gatherAudit
from .store import MemoryStore, isMemoryName

_DELETE = {"delete", "rm", "forget"}
_USAGE = "用法:/memory delete <名> [名…](名见 /memory 审核报告)"


def _targets(text: str) -> list[str] | None:
    parts = text.split()
    if len(parts) >= 2 and parts[0] == "/memory" and parts[1] in _DELETE:
        return parts[2:]
    return None


def isMutatingMemoryCommand(text: str) -> bool:
    targets = _targets(text)
    return bool(targets and all(isMemoryName(target) for target in targets))


async def memoryCommand(text: str, store: MemoryStore) -> str | None:
    parts = text.split()
    if not parts or parts[0] != "/memory":
        return None
    targets = _targets(text)
    if targets is None:
        today = store.today()
        return formatAudit(await gatherAudit(store, today), today)
    if not targets or not all(isMemoryName(target) for target in targets):
        return _USAGE
    done, missing, readonly, locked = [], [], [], []
    refusals = []
    for target in targets:
        try:
            result = await store.delete(target, exactName=True)
        except ToolRejected as exc:
            refusals.append(f"未删除:{target}。{exc}")
            continue
        if result.removed:
            done.append(target)
        elif result.readOnly:
            readonly.append(target)
        elif result.locked:
            locked.append(target)
        else:
            missing.append(target)
    groups = (("已删除", done), ("未找到", missing), ("只读兼容来源已保留", readonly), ("锁定记忆已保留", locked))
    lines = [f"{label}:{', '.join(names)}" for label, names in groups if names]
    return "\n".join(lines + refusals) or "无操作"
