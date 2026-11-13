"""Frozen agent_defs.ts frontmatter and D09 native/explicit-compatible discovery (MIT)."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from ..config.compat import Compatibility

DefinitionSource = Literal["built-in", "userSettings", "projectSettings"]
_DISK_SOURCE = Literal["userSettings", "projectSettings"]
_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


@dataclass(frozen=True)
class AgentDefinition:
    agent_type: str
    system_prompt: str
    when_to_use: str = ""
    source: DefinitionSource = "built-in"
    filename: str | None = None
    model: str | None = None
    disallowed_tools: frozenset[str] = frozenset()
    tools: tuple[str, ...] | None = None
    permission_mode: str | None = None
    omit_project_instructions: bool = False
    background: bool = False
    memory: str | None = None
    max_turns: int | None = None
    effort: str | None = None
    skills: tuple[str, ...] = ()
    initial_prompt: str | None = None
    critical_system_reminder: str | None = None
    isolation: Literal["worktree", "remote"] | None = None
    color: str | None = None
    hooks: dict[str, tuple[str, ...]] = field(default_factory=dict)
    mcp_servers: tuple[str, ...] = ()

    @property
    def version(self) -> str:
        data = asdict(self)
        data.pop("filename")
        data["disallowed_tools"] = sorted(self.disallowed_tools)
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _comma_list(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _section(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*\n(.*?)(?=^\S|\Z)", text, re.MULTILINE | re.DOTALL)
    return match[1] if match is not None else ""


def _command_hooks(text: str) -> dict[str, tuple[str, ...]]:
    block = _section(text, "hooks")
    hooks: dict[str, tuple[str, ...]] = {}
    for event in ("SubagentStart", "SubagentStop"):
        event_block = re.search(rf"^  {event}:[ \t]*\n(.*?)(?=^  \S|\Z)", block, re.MULTILINE | re.DOTALL)
        if event_block is None:
            continue
        commands = tuple(match[1] for line in event_block[1].splitlines()
                         if (match := re.fullmatch(r'\s*-\s*command:\s*"?(.+?)"?\s*', line)))
        if commands:
            hooks[event] = commands
    return hooks


def parseAgentDefinition(filename: str, raw: str, source: _DISK_SOURCE = "userSettings") -> AgentDefinition | None:
    match = _FRONTMATTER.match(raw.replace("\r\n", "\n"))
    if match is None:
        return None
    metadata, body = match[1], match[2].strip()
    values = {}
    for line in metadata.splitlines():
        key, separator, value = line.partition(":")
        if key and separator:
            values[key.strip().lower()] = re.sub(r'''^["']|["']$''', "", value.strip())
    name = values.get("name", "").strip()
    if not name or not body:
        return None
    tokens = _comma_list(values.get("tools", values.get("allowed-tools", values.get("allowedtools", ""))))
    includes = tuple(token for token in tokens if token != "*" and not token.startswith("!"))
    excludes = tuple(token[1:].strip() for token in tokens if token.startswith("!") and token[1:].strip())
    model = values.get("model", "").strip()
    max_turns = re.match(r"^[+-]?[0-9]+", values.get("maxturns", "").lstrip())
    isolation = values.get("isolation")
    return AgentDefinition(
        name, body, values.get("description", ""), source=source, filename=filename,
        model="inherit" if model.lower() == "inherit" else model or None,
        tools=includes if includes and "*" not in tokens else None,
        disallowed_tools=frozenset(excludes or _comma_list(values.get("disallowedtools", ""))),
        permission_mode=values.get("permissionmode") or None,
        omit_project_instructions=values.get("omitclaudemd") == "true",
        background=values.get("background") == "true", memory=values.get("memory") or None,
        max_turns=(int(max_turns[0]) or None) if max_turns is not None and len(max_turns[0]) <= 32 else None,
        effort=values.get("effort") or None, skills=_comma_list(values.get("skills", "")),
        initial_prompt=values.get("initialprompt") or None,
        critical_system_reminder=values.get("criticalsystemreminder") or None,
        isolation="worktree" if isolation == "worktree" else "remote" if isolation == "remote" else None,
        color=values.get("color") or None, hooks=_command_hooks(metadata),
        mcp_servers=tuple(match[1] for line in _section(metadata, "mcpServers").splitlines()
                          if (match := re.fullmatch(r"\s*-\s+(\S+)\s*", line))),
    )


def _load_directory(directory: Path, source: _DISK_SOURCE) -> list[AgentDefinition]:
    try:
        entries = list(directory.iterdir())
    except OSError:
        return []
    definitions = []
    for file in entries:
        if file.suffix != ".md":
            continue
        try:
            definition = parseAgentDefinition(file.stem, file.read_text(encoding="utf-8"), source)
        except (OSError, UnicodeError):
            continue
        if definition is not None:
            definitions.append(definition)
    return definitions


async def loadAgentDefinitions(
    cwd: Path, user_root: Path, compatibility: Compatibility, *, env: Mapping[str, str], disabled: bool = False,
) -> dict[str, AgentDefinition]:
    from .bundled_agents import bundledAgentDefinitions

    builtins = bundledAgentDefinitions(env)
    if disabled:
        return builtins
    sources = [source for source in compatibility.sources if source.resource == "agents"]
    user = [Path(source.path) for source in sources if source.scope == "user"]
    project = [Path(source.path) for source in sources if source.scope == "project" and source.workspace is not None
               and Path(source.workspace).resolve() == cwd.resolve()]
    groups = await asyncio.gather(
        *(asyncio.to_thread(_load_directory, directory, "userSettings") for directory in [*user, user_root / "agents"]),
        *(asyncio.to_thread(_load_directory, directory, "projectSettings") for directory in [*project, cwd / ".ruocun" / "agents"]),
    )
    disk = {definition.agent_type: definition for group in groups for definition in group}
    return {**disk, **{name: definition for name, definition in builtins.items() if name not in disk}}
