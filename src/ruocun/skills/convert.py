"""生成外部技能正文的适配文本，并缓存已经生成的结果。

转换由调用方提供的模型接口完成。适配文本可以直接用于本次执行，缓存只是为了后续复用。
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Awaitable, Callable
from collections.abc import Set as AbstractSet
from pathlib import Path

from ..platform.file_contract import AtomicFileError
from ..platform.windows.durable_file import PrivateDirectory, atomic_publish
from .adapt import isForeignSkill

FlashCall = Callable[[str, str], Awaitable[str]]

_AGENT = (
    "外部技能若希望隔离上下文、降低开销或让主流程改用其他模型，优先用可用的 agent 工具把该步骤交给子代理。"
    "子代理默认继承当前主模型。只有用户给出当前网关支持的完整模型 ID 时才填写 model。"
    "未提供子代理工具时，在现有能力内完成同一任务，缺少必要能力时请用户决定。"
)


def convertSystemPrompt(catalog: str) -> str:
    return f"""把用户提供的技能正文转换为若存可直接使用的版本。保留原来的任务、步骤、例子和语气，只改必须适配的调用。

当前工具目录：
{catalog}

先按功能查目录，例如文件读取、命令执行、文件编辑和代码搜索。使用目录中的实际名称，缺少对应项时写出所需动作。带命名空间的技能引用改用裸名，例如 superpowers:example 写成 example。
haiku、sonnet、opus、mini、flash 等档位只在原平台有意义。{_AGENT}

直接返回完整正文，无需解释或另加代码围栏。若当前目录已支持正文中的用法，原样返回。"""


_GENERIC_NOTE = (
    "## 本平台适配\n"
    "这份正文来自另一种运行环境。将读写、搜索和命令操作映射到若存当前提供的工具，"
    "技能引用使用裸名（例如 superpowers:example 写成 example）。"
    "外部模型档位不提供可直接使用的模型 ID。"
    + _AGENT + "\n\n"
)


def _read_cache(file: Path) -> str:
    try:
        with PrivateDirectory(file.parent, readonly=True, anchor_file=file.name):
            return file.read_text(encoding="utf-8")
    except (OSError, AtomicFileError, UnicodeError):
        return ""


def _save_cache(file: Path, body: str) -> None:
    try:
        atomic_publish(file, body.encode("utf-8"), require_durability=False)
    except (OSError, AtomicFileError, UnicodeError):
        pass  # 缓存发布失败时仍返回本次生成的适配文本。


def makeSkillAdapter(
    *, toolNames: AbstractSet[str], catalog: str, callFlash: FlashCall, userRoot: Path,
) -> Callable[[str], Awaitable[str]]:
    cache_dir = userRoot / "skill-adapted"
    prompt = convertSystemPrompt(catalog)

    async def adapt(body: str) -> str:
        if not isForeignSkill(body, toolNames):
            return body
        content = f"inherit-model-v2\n{catalog}\n{body}".encode("utf-8", errors="replace")
        file = cache_dir / f"{hashlib.sha256(content).hexdigest()[:16]}.md"
        cached = await asyncio.to_thread(_read_cache, file)
        if cached:
            return cached
        try:
            converted = (await callFlash(prompt, body)).strip()
        except Exception:
            converted = ""
        if not converted:
            return _GENERIC_NOTE + body
        await asyncio.to_thread(_save_cache, file, converted)
        return converted

    return adapt
