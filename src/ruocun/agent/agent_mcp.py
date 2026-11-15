"""按代理定义为子代理准备专属的命名 MCP 资源。连接和传输沿用公共实现，资源生命周期由本次子代理执行管理。"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from ..mcp.mcp import McpManager
from ..tools.registry import ToolRegistry
from ..tools.types import ToolContext
from .agent_defs import AgentDefinition


class AgentMcpRuntime:
    def __init__(self, registry: ToolRegistry, config: Mapping[str, Any], ctx: ToolContext,
                 env: Mapping[str, str], redact: Callable[[str], str] | None) -> None:
        self.config, self.env, self.redact = copy.deepcopy(dict(config)), dict(env), redact
        self.registry = registry
        self.lang = ctx.lang
        self.cwd = str(Path(ctx.cwd or ctx.workspaceRoot).resolve())
        self.manager = McpManager(registry, self.config, Path(ctx.cwd or ctx.workspaceRoot), env, redact=redact)
        self._opened = False
        self._closed = False
        self._expected: str | None = None
        self._visible: list[str] = []

    @property
    def definition_digest(self) -> str:
        material = json.dumps({"mcpServers": self.config.get("mcpServers", {}), "cwd": self.cwd},
                              sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(material.encode("utf-8", errors="backslashreplace")).hexdigest()

    def _schemas(self) -> str:
        prefixes = tuple(f"mcp__{name}__" for name in self.config.get("mcpServers", {}))
        tools = self.registry.toApiTools(lambda tool: tool.name.startswith(prefixes), self.lang)
        return json.dumps(sorted(tools, key=lambda tool: tool["function"]["name"]),
                          sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    async def open(self) -> None:
        if self._closed:
            raise ValueError("子代理 MCP 资源已关闭，必须由新 owner 重建。")
        if not self._opened:
            try:
                await self.manager.init()
                if self._expected is not None:
                    if self._schemas() != self._expected:
                        raise ValueError("原子代理 MCP 工具定义已变更，未交接执行。")
                    self.registry.restoreMcpVisibility(self._visible)
                self._opened = True
            except BaseException:
                await self.close()
                raise

    async def close(self) -> None:
        if not self._closed:
            await self.manager.close()
            self._closed = True

    def rebind(self, registry: ToolRegistry, ctx: ToolContext) -> AgentMcpRuntime:
        expected = self._schemas()
        prefixes = tuple(f"mcp__{name}__" for name in self.config.get("mcpServers", {}))
        visible = [tool["function"]["name"] for tool in self.registry.toApiTools(
            lambda tool: tool.name.startswith(prefixes) and self.registry.isMcpVisible(tool.name), self.lang)]
        for name in self.config.get("mcpServers", {}):
            registry.unregisterByPrefix(f"mcp__{name}__")
        rebound = AgentMcpRuntime(registry, self.config, ctx, self.env, self.redact)
        rebound._expected, rebound._visible = expected, visible
        return rebound


def createAgentMcpFactory(
    config: Mapping[str, Any], env: Mapping[str, str], *, redact: Callable[[str], str] | None = None,
) -> Callable[[AgentDefinition, ToolRegistry, ToolContext], AgentMcpRuntime | None]:
    frozen, environment = copy.deepcopy(dict(config)), dict(env)

    def create(definition: AgentDefinition, registry: ToolRegistry, ctx: ToolContext) -> AgentMcpRuntime | None:
        declared = frozen.get("mcpServers", {})
        selected = {name: copy.deepcopy(declared[name]) for name in definition.mcp_servers
                    if isinstance(declared, dict) and name in declared}
        return AgentMcpRuntime(registry, {"mcpServers": selected}, ctx, environment, redact) if selected else None

    return create
