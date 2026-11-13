"""Frozen memory/audit.test.ts plus the TTY command's store boundary."""

import asyncio
from dataclasses import replace

import pytest

from ruocun.config.compat import (
    DEFAULT_COMPATIBILITY,
    Compatibility,
    CompatibilitySource,
)
from ruocun.memory.audit import AuditRow, assessMemory, formatAudit
from ruocun.memory.command import isMutatingMemoryCommand, memoryCommand
from ruocun.memory.store import MemoryStore
from ruocun.memory.types import newMemory

TODAY = "2026-06-07"


def memory(**updates):
    return replace(newMemory(name="m", text="某条记忆", type="semantic", today=TODAY), **updates)


@pytest.mark.parametrize(("fields", "flag"), [
    ({"status": "superseded", "supersededBy": "x"}, "superseded"),
    ({"text": "用户使用 test-driven-development 技能进行测试", "type": "user"}, "noise"),
    ({"text": "也许用户喜欢深色主题", "type": "user", "confidence": 0.4, "uses": 0, "importance": 5}, "lowvalue"),
    ({"type": "semantic", "importance": 3, "lastUsed": "2026-04-12"}, "stale"),
    ({"type": "semantic", "importance": 7, "lastUsed": TODAY}, "ok"),
])
def test_audit_flags_preserve_frozen_priority(fields, flag):
    assert assessMemory(memory(**fields), TODAY).flag == flag


def test_audit_empty_report():
    assert "为空" in formatAudit([], TODAY)


def test_audit_report_groups_noise_and_suggests_deletion():
    rows = [
        AuditRow("用户", memory(name="noise1", text="用户使用 Grep 工具", type="user"), "noise", "x"),
        AuditRow("项目", memory(name="good1", type="semantic", importance=8), "ok", ""),
    ]
    report = formatAudit(rows, TODAY)
    assert all(text in report for text in ("共 2 条", "noise1", "/memory delete", "建议清理 1 条"))


def test_tty_memory_query_and_valid_delete_share_native_store(tmp_path):
    assert not isMutatingMemoryCommand("/memory")
    assert not isMutatingMemoryCommand("/memory delete")
    assert not isMutatingMemoryCommand("/memory forget ../outside")
    assert isMutatingMemoryCommand("/memory rm good1")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    user = tmp_path / "user"
    store = MemoryStore(workspace, user, DEFAULT_COMPATIBILITY, today=lambda: TODAY)

    async def scenario():
        await store.upsert("project", memory(name="good1"))
        report = await memoryCommand("/memory", store)
        assert "good1" in report and "项目" in report
        assert "用法" in await memoryCommand("/memory delete", store)
        assert "用法" in await memoryCommand("/memory delete ../outside", store)
        assert len(await store.load()) == 1
        await store.upsert("user", memory(name="held"))
        # A configured source aliases the user folder after its native note
        # already exists. Deleting that note is a known refusal.
        source = CompatibilitySource("alias", "user", "memory", str(user / "memory"))
        guarded = MemoryStore(workspace, user, Compatibility(1, (source,)), today=lambda: TODAY)
        output = await memoryCommand("/memory rm good1 held", guarded)
        assert output.startswith("已删除:good1\n")
        assert "未删除:held" in output and "只读兼容来源" in output
        assert (user / "memory" / "held.md").exists()
        assert await memoryCommand("/memory forget good1", store) == "未找到:good1"

    asyncio.run(scenario())
