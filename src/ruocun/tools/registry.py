"""保存工具定义，生成模型可见的工具参数，并把已校验的调用交给对应处理器。

分叉时为本次已公布的工具及其派发定义建立快照。
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any

from ..client.types import ApiTool
from .schema import parseSchema, toJsonSchema
from .types import Tool, ToolContext


@dataclass(frozen=True)
class ToolSnapshot:
    api_tools: tuple[ApiTool, ...]
    definitions: tuple[Tool, ...]
    activated_deferred: frozenset[str]
    activated_mcp: frozenset[str]

    def copy_registry(self) -> ToolRegistry:
        child = ToolRegistry()
        child._tools = {tool.name: replace(tool, schema=copy.deepcopy(tool.schema),
                                           apiParameters=copy.deepcopy(tool.apiParameters))
                        for tool in self.definitions}
        child._activated_deferred = set(self.activated_deferred)
        child._activated_mcp = set(self.activated_mcp)
        return child


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._activated_deferred: set[str] = set()
        self._activated_mcp: set[str] = set()

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool
        if tool.name.startswith("mcp__") and len(self._activated_mcp) < 5:
            self._activated_mcp.add(tool.name)

    def filtered(self, predicate: Callable[[Tool], bool]) -> ToolRegistry:
        """按条件保留部分工具，构建可独立派发的注册表。"""
        child = ToolRegistry()
        for tool in self._tools.values():
            if predicate(tool):
                child.register(tool)
        return child

    def forkSnapshot(self, api_tools: Sequence[ApiTool]) -> ToolSnapshot | None:
        """冻结本次发送给模型的工具清单，并把其中每个工具与派发定义对应起来。"""
        definitions: dict[str, Tool] = {}
        for entry in api_tools:
            name = entry.get("function", {}).get("name")
            if not isinstance(name, str) or name not in self._tools:
                return None
            definitions[name] = self._tools[name]
        return ToolSnapshot(tuple(copy.deepcopy(api_tools)), tuple(definitions.values()),
                            frozenset(self._activated_deferred.intersection(definitions)),
                            frozenset(self._activated_mcp.intersection(definitions)))

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def unregisterByPrefix(self, prefix: str) -> list[str]:
        removed = [name for name in self._tools if name.startswith(prefix)]
        for name in removed:
            del self._tools[name]
            self._activated_mcp.discard(name)
        return removed

    def countByPrefix(self, prefix: str) -> int:
        return sum(name.startswith(prefix) for name in self._tools)

    def countMcpTools(self) -> int:
        return self.countByPrefix("mcp__")

    def searchAndActivateMcp(self, query: str) -> str:
        q = query.strip().lower()
        if not q:
            return "请提供搜索关键词。"
        hits = [tool for tool in self._tools.values() if tool.name.startswith("mcp__")
                and (q in tool.name.lower() or q in tool.description.lower())]
        if not hits:
            return f"没有 MCP 工具匹配「{query}」。"
        self._activated_mcp.update(tool.name for tool in hits)
        return "\n".join(f"{tool.name}: {tool.description}" for tool in hits) + (
            f"\n\n(以上 {len(hits)} 个工具已激活,从下一次工具调用起可直接调用它们。)")

    def isMcpVisible(self, name: str) -> bool:
        return not name.startswith("mcp__") or name in self._activated_mcp

    def restoreMcpVisibility(self, names: Sequence[str]) -> None:
        self._activated_mcp.update(name for name in names if name.startswith("mcp__") and name in self._tools)

    def toApiTools(
        self, predicate: Callable[[Tool], bool] | None = None, lang: str | None = None, *,
        hideUnactivatedDeferred: bool = False,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for tool in self._tools.values():
            if predicate is not None and not predicate(tool):
                continue
            deferred = tool.shouldDefer and tool.name not in self._activated_deferred
            if deferred and hideUnactivatedDeferred:
                continue
            description = tool.descriptionEn if lang == "en" and tool.descriptionEn else tool.description
            parameters = copy.deepcopy(tool.apiParameters) if tool.apiParameters is not None else toJsonSchema(tool.schema)
            if deferred:
                description = re.split(r"[。\n]", description)[0].encode(
                    "utf-16-le", errors="surrogatepass")[:160].decode("utf-16-le", errors="surrogatepass")
                parameters = {"type": "object", "properties": {}, "additionalProperties": False}
            result.append({"type": "function", "function": {
                "name": tool.name, "description": description, "parameters": parameters,
            }})
        return result

    def restoreDeferredVisibility(self, names: Sequence[str]) -> None:
        """按已验证的续接记录恢复延迟工具的可见性，只启用记录中的确切名称。"""
        self._activated_deferred.update(name for name in names
                                        if (tool := self.get(name)) is not None and tool.shouldDefer)

    def searchAndActivateDeferred(self, query: str, lang: str | None = None) -> str:
        q = query.strip().lower()
        if not q:
            return "请提供搜索关键词。"
        hits: list[str] = []
        for tool in self._tools.values():
            if not tool.shouldDefer or tool.name in self._activated_deferred:
                continue
            description = tool.descriptionEn if lang == "en" and tool.descriptionEn else tool.description
            if q not in tool.name.lower() and q not in description.lower():
                continue
            self._activated_deferred.add(tool.name)
            parameters = copy.deepcopy(tool.apiParameters) if tool.apiParameters is not None else toJsonSchema(tool.schema)
            hits.append(f"{tool.name}: {description}\n参数: " + json.dumps(
                parameters, ensure_ascii=False, separators=(",", ":")))
        if not hits:
            return f"没有延迟加载工具匹配「{query}」。"
        return "\n\n".join(hits) + f"\n\n(以上 {len(hits)} 个工具已激活,从下一次工具调用起可直接调用它们。)"

    def validate(self, name: str, rawArgs: str) -> dict[str, Any]:
        """解析和校验工具参数，可在审批以及记录执行意图之前调用。"""
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"unknown tool: {name}")
        try:
            args = json.loads(rawArgs, parse_constant=_reject_constant)
        except (ValueError, TypeError) as exc:
            hint = _truncated_hint(rawArgs)
            raise ValueError(f"invalid JSON arguments for {name}{hint}") from exc
        try:
            return parseSchema(tool.schema, args)
        except ValueError as exc:
            if tool.shouldDefer and name not in self._activated_deferred:
                raise ValueError(
                    f"{name} 尚未加载完整定义。先通过 ToolSearch 搜索「{name}」，"
                    "再按返回的参数说明重试。\n"
                    f"原始校验错误:{exc}") from exc
            props = tool.schema.get("properties", {})
            required = tool.schema.get("required", [])
            params = "; ".join(
                f"{key}({value.get('type', 'any')}, {'必填' if key in required else '可选'}"
                f"{', ' + value['description'] if value.get('description') else ''})"
                for key, value in props.items()
            ) or "(无参数)"
            message = str(exc)
            if message.startswith("缺少必填参数"):
                missing = [key for key in required if not isinstance(args, dict) or key not in args]
                keys = list(args) if isinstance(args, dict) else []
                field = missing[0] if missing else "(root)"
                hint = (f"你传了 [{', '.join(keys)}],但 {name} 需要参数「{field}」——参数名可能写错了。"
                        if keys else f"{name} 需要参数「{field}」,但你没传任何参数。")
                message += f"。{hint}"
            result = f"{name} {message} {name} 接受的参数:{params}"
            if message.startswith("缺少必填参数") and len(required) == 1:
                result += f' 最小调用示例:{name}({{"{required[0]}": "<值>"}})'
            raise ValueError(result) from exc

    async def dispatch(self, name: str, rawArgs: str, ctx: ToolContext) -> str:
        args = self.validate(name, rawArgs)
        tool = self._tools[name]
        if ctx.signal.is_set():
            raise InterruptedError("工具调用已取消")
        return await tool.handler(args, ctx)


def _reject_constant(value: str) -> None:
    raise ValueError("invalid JSON constant")


def _truncated_hint(raw: str) -> str:
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in raw:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]" and stack:
            stack.pop()
    repaired = raw + ('"' if in_string else "")
    repaired += "".join("}" if char == "{" else "]" for char in reversed(stack))
    try:
        partial = json.loads(repaired)
    except ValueError:
        return ""
    if not isinstance(partial, dict) or repaired == raw:
        return ""
    summary = "; ".join(
        f'{key}({len(value)} 字符,结尾"{value[-60:]}")' if isinstance(value, str)
        else f"{key}={json.dumps(value, ensure_ascii=False)}"
        for key, value in partial.items()
    )
    return f":参数可能被截断。{summary}。请拆成更小的几次调用;不执行不完整参数。"
