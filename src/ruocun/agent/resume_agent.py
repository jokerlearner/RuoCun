"""Ordinary durable checkpoint continuation from frozen resume_agent.ts (MIT)."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlsplit

from ..session.contract import ArchiveImport, RunRecord, task_inbox_messages
from ..session.recovery import AgentContinuation, repairToolPairs
from ..tools.tools_for_mode import apiToolsForMode
from .worktree import directory_identity

if TYPE_CHECKING:
    from ..session.conversation import Conversation
    from .run_agent import PreparedAgentRun


def agentRecoveryMaterial(prepared: PreparedAgentRun, messages: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cwd = Path(prepared.ctx.cwd or prepared.ctx.workspaceRoot).resolve(strict=True)
    workspace = Path(prepared.ctx.workspaceRoot).resolve(strict=True)
    identity = directory_identity(cwd)
    endpoint = prepared.options.get("baseUrl", "")
    location = urlsplit(endpoint)
    # A credential-bearing endpoint cannot be reproduced from safe material.
    endpoint_safe = (location.scheme in {"https", "http"} and bool(location.hostname)
                     and not any((location.username, location.password, location.query, location.fragment)))
    mode = prepared.permission.getMode()
    tools = (list(prepared.exact_tools.api_tools) if prepared.exact_tools is not None else
             apiToolsForMode(prepared.registry, "plan" if mode == "plan" else "normal", prepared.ctx.lang))
    effective_tools = json.dumps(tools, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return {
        "format": 1, "model": prepared.session.model, "agentType": prepared.definition.agent_type,
        "definitionVersion": prepared.definition.version,
        "worktree": str(cwd), "worktreeIdentity": list(identity),
        "workspaceRoot": str(workspace), "workspaceIdentity": list(directory_identity(workspace)),
        "provider": prepared.options.get("provider", ""), "baseUrl": endpoint if endpoint_safe else None,
        "permissions": {"mode": mode, "rules": copy.deepcopy(prepared.permission.getRules())},
        "externalPolicy": prepared.parent_permissions.externalAgentPolicy(), "requestedMode": prepared.requested_mode,
        "toolRoster": [entry["function"]["name"] for entry in tools],
        "toolRosterDigest": hashlib.sha256(effective_tools.encode("utf-8")).hexdigest(),
        "mcpConfigDigest": (prepared.mcp_runtime.definition_digest if prepared.mcp_runtime is not None else
                            prepared.ctx.mcpConfigDigest if any(entry["function"]["name"].startswith("mcp__") for entry in tools)
                            else None),
        "budget": prepared.session.budgetCNY, "turnLimit": prepared.max_turns, "turnsRemaining": prepared.max_turns,
        "reasoningEffort": prepared.reasoning_effort,
        "toolPolicy": "background" if prepared.is_async else "synchronous",
        "messages": copy.deepcopy(prepared.session.messages if messages is None else messages),
    }


def agentCheckpointSnapshot(
    snapshot: dict[str, Any], messages: list[dict[str, Any]], material: dict[str, Any],
    turns_remaining: int, inbox_messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stage transcript, recovery budget and inbox consumption in one candidate.

    Owners validate their identity/budget policy before staging, and publish the
    candidate before consuming inbox messages or changing their live state.
    The material is freshly built recovery data, never the saved checkpoint.
    """
    material["turnsRemaining"] = turns_remaining
    if isinstance(snapshot.get("archive_scope"), str):
        material["archive_scope"] = snapshot["archive_scope"]
    if type(snapshot.get("output_raw_offset")) is int:
        material["output_raw_offset"] = snapshot["output_raw_offset"]
    candidate = {**snapshot, "messages": messages, "recovery_material": material}
    if inbox_messages:
        candidate["task_inbox"] = []
    return candidate


async def agentOutputMessages(conversation: Conversation, record: RunRecord) -> list[dict[str, Any]]:
    """Read admitted child activity by original-message position, never compacted indices."""
    offset = record.snapshot.get("output_raw_offset", record.snapshot.get("output_start", 0))
    if type(offset) is not int or offset < 0:
        raise ValueError("子代理原文输出边界无效。")
    messages: list[dict[str, Any]] = []
    while True:
        page = await conversation.worker.archive_export(record.run_ref.run_id, offset=offset, limit=100)
        messages.extend(page["messages"])
        following = page["next_offset"]
        if following is None:
            return messages
        if type(following) is not int or following <= offset:
            raise RuntimeError("子代理原文分页没有前进，停止读取。")
        offset = following


async def prepareAgentArchive(conversation: Conversation, prepared: PreparedAgentRun) -> ArchiveImport | None:
    """Copy only a trusted visible prefix; the new task is an explicit appended suffix."""
    if prepared.archive_source_scope is None:
        return None
    imported = await conversation.worker.archive_branch(prepared.archive_source_scope,
                                                         indices=prepared.archive_source_indices)
    by_id = {record["id"]: record for record in imported.records}
    prefix = [by_id[identity]["message"] for identity in imported.lineage]
    if prepared.session.messages[:len(prefix)] != prefix:
        raise ValueError("子代理继承材料与可信归档前缀不一致，未启动。")
    return imported


def agentOutputOffset(messages: list[dict[str, Any]], imported: ArchiveImport | None) -> int:
    if imported is None:
        return len(messages)
    raw_count = len({record["raw_seq"] for record in imported.records if record.get("kind") == "raw"})
    return raw_count + len(messages) - len(imported.lineage)


def continuationToolPolicy(continuation: AgentContinuation) -> Literal["synchronous", "background"]:
    if continuation.previous.kind != "agent":
        raise ValueError("仅支持具有完整普通代理材料的继续运行。")
    policy = continuation.material.get("toolPolicy")
    if policy == "synchronous":
        return "synchronous"
    if policy == "background":
        return "background"
    if "toolPolicy" not in continuation.material and continuation.material.get("format") == 1:
        # The first background checkpoint format did not write a policy field.
        previous = continuation.previous
        snapshot = previous.snapshot
        execution = snapshot.get("background_execution")
        epoch = snapshot.get("background_agent_epoch")
        if (snapshot.get("foreground") is None and type(epoch) is int and epoch > 0
                and isinstance(execution, dict) and execution.get("kind") == "agent"
                and execution.get("background") is True
                and execution.get("taskId") == previous.run_ref.task_id
                and execution.get("runId") == previous.run_ref.run_id):
            return "background"
    raise ValueError("原代理的工具裁剪策略无法核实，未授权继续。")


def restorePreparedContinuation(prepared: PreparedAgentRun, continuation: AgentContinuation) -> None:
    """Rebuild mutable visibility and mode on the private child before authorizing continuation."""
    saved = continuation.material
    permissions, roster = saved.get("permissions"), saved.get("toolRoster")
    if not isinstance(permissions, dict) or not isinstance(roster, list) or not all(isinstance(name, str) for name in roster):
        raise ValueError("原代理权限模式或工具目录无法核实，未授权继续。")
    if permissions.get("mode") == "plan":
        prepared.permission.setMode("plan")
    prepared.registry.restoreDeferredVisibility(roster)
    prepared.registry.restoreMcpVisibility(roster)
    validatePreparedContinuation(prepared, continuation)


def validatePreparedContinuation(prepared: PreparedAgentRun, continuation: AgentContinuation) -> None:
    saved = continuation.material
    if saved.get("archive_scope", continuation.previous.run_ref.run_id) != continuation.previous.run_ref.run_id:
        raise ValueError("原代理归档范围与持久执行身份不一致，未授权继续。")
    if continuation.previous.snapshot.get("archive_scope", continuation.previous.run_ref.run_id) != continuation.previous.run_ref.run_id:
        raise ValueError("原代理检查点归档范围不可信，未授权继续。")
    if (continuation.previous.kind != "agent" or saved.get("format") != 1
            or saved.get("agentType") in {"explore", "plan"}):
        raise ValueError("仅支持具有完整普通代理材料的继续运行。")
    fresh = agentRecoveryMaterial(prepared)
    fields = ("model", "agentType", "definitionVersion", "worktree", "worktreeIdentity", "workspaceRoot", "workspaceIdentity",
              "provider", "baseUrl", "permissions", "externalPolicy", "requestedMode", "toolRoster", "toolRosterDigest", "budget",
              "turnLimit", "reasoningEffort", "mcpConfigDigest")
    if (continuationToolPolicy(continuation) != fresh["toolPolicy"] or not saved.get("provider")
            or not saved.get("baseUrl") or any(saved.get(key) != fresh[key] for key in fields)):
        raise ValueError("原代理模型、定义、工具、端点、工作区或权限已变更，未授权继续。")
    remaining = saved.get("turnsRemaining")
    if type(remaining) is not int or not 0 < remaining <= prepared.max_turns:
        raise ValueError("原代理剩余轮次预算不足或无法核实，未授权继续。")
    original = saved.get("messages")
    if (not isinstance(original, list) or not original or not isinstance(original[0], dict)
            or not prepared.session.messages or prepared.session.messages[0] != original[0]):
        raise ValueError("无法核实继续时的原代理系统提示。")


async def continuationMessages(conversation: Conversation, continuation: AgentContinuation) -> list[dict[str, Any]]:
    view = await conversation.background_view()
    original = continuation.material["messages"]
    messages = repairToolPairs(original, view.tool_records, continuation.previous.run_ref.run_id)
    pending = task_inbox_messages(continuation.previous.snapshot.get("task_inbox", []))
    return [*messages, *pending, {"role": "user", "content": continuation.instruction}]
