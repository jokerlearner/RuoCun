"""读取项目和用户的设置，修改仅写入原生用户设置。项目设置的覆盖关系由同一读取顺序决定。"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ..config.settings_store import MISSING, readSetting, setUserSetting
from .schema import objectSchema
from .types import Tool, ToolContext

_MODES = ("default", "auto", "bypassPermissions", "plan")


def _string(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return "[object Object]"
    if isinstance(value, list):
        return ",".join("" if v is None else _string(v) for v in value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def makeConfigTool(user_root: Path, *, user_files: Sequence[Path] = (),
                   project_files: Sequence[Path] = ()) -> Tool:
    async def handler(args: dict[str, Any], ctx: ToolContext) -> str:
        setting = args["setting"]
        if "value" not in args:
            # 优先读取项目设置。项目未给出可用值时，再读取用户设置。
            for tier, targets in enumerate((
                [*project_files, Path(ctx.workspaceRoot) / ".ruocun/settings.json"],
                [*user_files, user_root / "settings.json"],
            )):
                for target in reversed(targets):
                    value = await asyncio.to_thread(readSetting, target, setting)
                    if value is MISSING:
                        continue
                    if value is not None or tier == 1:
                        return _string(value)
                    break
            return f"(未设置:{setting})"
        value = args["value"]
        if setting == "permissions.defaultMode" and value not in _MODES:
            return "无效值。permissions.defaultMode 可选:" + "/".join(_MODES)
        if setting == "theme" and value not in ("light", "dark"):
            return "无效值。theme 可选:light/dark"
        if setting == "checkpoint.enabled" and not isinstance(value, bool):
            return "无效值。checkpoint.enabled 可选:true/false"
        await asyncio.to_thread(setUserSetting, user_root, setting, value)
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return f"已设置 {setting} = {encoded}(写入 {user_root / 'settings.json'})"

    return Tool(
        name="Config", capability="plan", approval="auto", shouldDefer=True, persistentEffect=True,
        description="读取或设置 RuoCun 配置项。不传 value 时返回当前值;传 value 时写入。"
                    "支持 setting: 'permissions.defaultMode'(default/auto/bypassPermissions/plan)、"
                    "'theme'(light/dark)、'checkpoint.enabled'(影子 git 快照/回滚,默认关闭)。"
                    "读取项目设置优先于用户设置；写入用户 settings.json。",
        descriptionEn="Read or set RuoCun configuration. Omit value to read; include value to write user settings. "
                      "Supports permissions.defaultMode, theme and checkpoint.enabled, plus dotted paths. "
                      "Reads project settings before user settings.",
        schema=objectSchema({
            "setting": {"type": "string", "description": "配置项键名,如 'permissions.defaultMode' 或 'theme'"},
            "value": {"anyOf": [{"type": "string"}, {"type": "boolean"}, {"type": "number"}],
                      "description": "新值;省略则读取当前值"},
        }, ["setting"]), handler=handler,
    )
