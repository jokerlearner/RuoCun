"""Frozen agent_memory.ts layout, adapted to the native RuoCun state root (MIT)."""
from pathlib import Path, PureWindowsPath

_NOTES = {
    "user": "- 用户范围。只留在其它项目中也成立的事实。",
    "project": "- 项目范围。文件由版本控制共享，内容限于本项目。",
    "local": "- 本地范围。内容只用于当前检出，不进入版本控制。",
}


def agentMemoryPrompt(agent_type: str, scope: str, workspace: Path, user_root: Path) -> str:
    name = agent_type.replace(":", "-")
    if (not name or name in {".", ".."} or name.rstrip(". ") != name
            or any(ord(char) < 32 or char in '/\\<>"|?*' for char in name) or PureWindowsPath(name).is_reserved()):
        raise ValueError("代理名称无法安全用作记忆目录。")
    if scope not in _NOTES:
        raise ValueError("代理记忆范围无效，应为 user、project 或 local。")
    directory = (user_root if scope == "user" else workspace / ".ruocun") / "agents" / "memory" / name
    if scope == "local":
        directory /= "local"
    memory_file = directory / "memory.md"
    return f"""## 子代理长期记录

文件为 {memory_file}。用 Read 查看，获得当前权限后可用 Write 或 Edit 更新。

每行留一条将来可用的发现，例如稳定的目录约定、决定的理由、复现后确认的修复或用户明确的偏好。省去临时进度和从当前文件一眼可查的内容。
{_NOTES[scope]}"""
