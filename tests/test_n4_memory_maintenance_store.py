"""Minimal maintenance composition checks for the native store."""

import asyncio
from dataclasses import replace

import pytest

from ruocun.config.compat import Compatibility, CompatibilitySource
from ruocun.memory.frontmatter import serializeMemory
from ruocun.memory.store import MemoryStore
from ruocun.memory.types import newMemory
from ruocun.platform.windows.durable_file import PublishDurabilityError
from ruocun.tools.types import ToolRejected

TODAY = "2026-06-07"


def test_maintenance_checks_raw_snapshot_and_preserves_compatible_and_locked(tmp_path):
    cwd = tmp_path / "repo"
    cwd.mkdir()
    old = tmp_path / "old"
    old.mkdir()
    candidate = newMemory(name="memory", text="原生记录", type="semantic", today=TODAY)
    old_file = old / "memory.md"
    old_bytes = serializeMemory(replace(candidate, text="兼容原件")).encode("utf-8")
    old_file.write_bytes(old_bytes)
    source = CompatibilitySource("legacy", "project", "memory", str(old), str(cwd))
    store = MemoryStore(cwd, tmp_path / "user", Compatibility(1, (source,)))

    async def scenario():
        assert await store.loadNative("project") == []
        legacy, = await store.load()
        assert not await store.publishExpected("project", candidate, legacy)
        assert not await store.deleteExpected(legacy)
        assert await store.publishExpected("project", candidate, None)
        entry, = await store.loadNative("project")
        edited = entry.path.read_bytes() + b"\n"
        entry.path.write_bytes(edited)  # Same parsed values, different hand-edited original.
        changed = replace(candidate, text="更新", locked=True)
        assert not await store.publishExpected("project", changed, entry)
        assert not await store.deleteExpected(entry)
        assert not await store.publishExpected("project", changed, None)
        assert entry.path.read_bytes() == edited
        current, = await store.loadNative("project")
        assert await store.publishExpected("project", changed, current, preserveOriginal=True)
        assert not list(current.path.parent.glob("*.bak"))
        locked, = await store.loadNative("project")
        assert locked.memory == changed
        assert not await store.deleteExpected(locked)
        assert not await store.publishExpected("project", candidate, locked)
        assert old_file.read_bytes() == old_bytes

    asyncio.run(scenario())


def test_consolidation_marker_uses_native_file_and_preserves_malformed_original(tmp_path):
    cwd = tmp_path / "repo"
    cwd.mkdir()
    user = tmp_path / "user"
    store = MemoryStore(cwd, user, Compatibility(1, ()))
    marker = user / "knowledge" / ".last-consolidation"

    async def scenario():
        assert await store.readConsolidationMarker("knowledge") == 0
        assert not user.exists()
        await store.writeConsolidationMarker("knowledge", 1780790400000)
        assert marker.read_bytes() == b"1780790400000"
        assert await store.readConsolidationMarker("knowledge") == 1780790400000
        marker.write_bytes(b"not-a-receipt")
        with pytest.raises(ToolRejected, match="标记"):
            await store.readConsolidationMarker("knowledge")
        with pytest.raises(ToolRejected, match="标记"):
            await store.writeConsolidationMarker("knowledge", 1780790400001)
        assert marker.read_bytes() == b"not-a-receipt"

    asyncio.run(scenario())


def test_maintenance_keeps_original_bytes_after_visible_replacement_with_unknown_sync(tmp_path, monkeypatch):
    from ruocun.memory import store as store_module

    store = MemoryStore(tmp_path, tmp_path / "user", Compatibility(1, ()))
    old = newMemory(name="canonical", text="原正文", type="semantic", today=TODAY)
    new = replace(old, text="合并后的正文")
    real_publish = store_module.atomic_publish

    async def scenario():
        assert await store.publishExpected("project", old, None)
        entry, = await store.loadNative("project")
        raw = entry.path.read_bytes().replace(b"\n", b"\r\n") + b"\r\n"
        entry.path.write_bytes(raw)
        entry, = await store.loadNative("project")

        def fail_sync(_directory):
            raise OSError("synthetic directory synchronization failure after replacement")

        def publish(file, data):
            if file == entry.path:
                return real_publish(file, data, sync_directory_fn=fail_sync)
            return real_publish(file, data)

        monkeypatch.setattr(store_module, "atomic_publish", publish)
        with pytest.raises(PublishDurabilityError) as outcome:
            await store.publishExpected("project", new, entry, preserveOriginal=True)
        assert outcome.value.receipt.replaced is True
        current, = await store.loadNative("project")
        assert current.memory.text == new.text
        backups = list(entry.path.parent.glob(".canonical.*.bak"))
        assert len(backups) == 1
        assert backups[0].read_bytes() == raw

    asyncio.run(scenario())
