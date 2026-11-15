"""从指定文件读取和追加长期允许的工具名。

读取失败时按空集合处理。追加前重新核对文件，保留无法解析或格式有误的原始数据。
"""
import json
from pathlib import Path


def _rejectConstant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


async def loadAlwaysApproved(file: str | Path) -> set[str]:
    try:
        values = json.loads(Path(file).read_text(encoding="utf-8"), parse_constant=_rejectConstant)
        return {value for value in values if isinstance(value, str)} if isinstance(values, list) else set()
    except (OSError, ValueError, UnicodeError):
        return set()


async def appendAlwaysApproved(file: str | Path, toolName: str) -> None:
    path = Path(file)
    try:
        values = json.loads(path.read_text(encoding="utf-8"), parse_constant=_rejectConstant)
    except FileNotFoundError:
        values = []
    # 原文件已经存在时，只有合法的字符串列表才能继续写入，避免用新列表覆盖损坏记录。
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError(f"{path}: 审批记录不是数组，保留原文件")
    current = list(dict.fromkeys(value for value in values if isinstance(value, str)))
    if toolName in current:
        return
    current.append(toolName)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
