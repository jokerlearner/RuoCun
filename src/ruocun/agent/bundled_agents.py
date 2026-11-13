"""Build the standard RuoCun agents from packaged instructions."""
from __future__ import annotations

import json
from collections.abc import Mapping
from importlib.resources import files
from typing import Any

from ..config.compat import resolve_env
from ..config.model_selection import getAgentModel
from .agent_defs import AgentDefinition as AgentDefinition

_TEXT = json.loads(files("ruocun.agent").joinpath("resources/bundled-agents.json").read_text("utf-8"))
_FILE_WRITES = frozenset({"Agent", "Edit", "Write", "NotebookEdit"})


def _builtin(name: str, **fields: Any) -> AgentDefinition:
    text = _TEXT[name]
    return AgentDefinition(name, text["systemPrompt"], text["whenToUse"],
                           critical_system_reminder=text.get("criticalSystemReminder"), **fields)


def bundledAgentDefinitions(env: Mapping[str, str]) -> dict[str, AgentDefinition]:
    definitions = (
        _builtin("general-purpose", permission_mode="auto", memory="project"),
        _builtin("explore", model=(resolve_env("EXPLORE_MODEL", env) or "").strip() or "inherit",
                        disallowed_tools=_FILE_WRITES, omit_project_instructions=True),
        _builtin("plan", disallowed_tools=_FILE_WRITES | {"Bash", "BashOutput", "KillShell"},
                        omit_project_instructions=True),
        _builtin("verify", disallowed_tools=_FILE_WRITES, permission_mode="auto", background=True),
    )
    return {definition.agent_type: definition for definition in definitions}


def agentCatalog(
    env: Mapping[str, str], parent_model: str, *, definitions: Mapping[str, AgentDefinition] | None = None,
) -> str:
    available = definitions if definitions is not None else bundledAgentDefinitions(env)
    rows = [f"- {entry.agent_type} ({getAgentModel(entry.model, parent_model)})"
            f"{'（后台）' if entry.background else ''}"
            f"{'（本机工作树）' if entry.isolation else ''}: {entry.when_to_use}"
            for entry in available.values() if not entry.hooks and not entry.mcp_servers]
    return "\n\n## 可用子代理类型\n" + "\n".join(rows)
