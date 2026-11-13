"""Frozen gc.test.ts assertions and the native delete receipt boundary."""

import asyncio
from dataclasses import replace

import pytest

from ruocun.config.compat import DEFAULT_COMPATIBILITY
from ruocun.memory.gc import (
    MemoryPruneUnconfirmed,
    daysBetween,
    gcMemories,
    retention,
    shouldPrune,
)
from ruocun.memory.store import MemoryStore
from ruocun.memory.types import newMemory

TODAY = "2026-06-07"
STALE = "2026-04-12"
OLD_CREATED = "2026-05-01"


def memory(name="a", **changes):
    return replace(newMemory(name=name, text=f"text-{name}", type="semantic", today=TODAY), **changes)


def test_days_between_is_unsigned_and_whole():
    assert daysBetween("2026-06-01", TODAY) == daysBetween(TODAY, "2026-06-01") == 6
    assert daysBetween(TODAY, TODAY) == 0


def test_days_between_returns_zero_on_bad_dates():
    assert daysBetween("garbage", TODAY) == daysBetween(TODAY, "") == 0


def test_legacy_tombstone_is_pruned_unless_locked():
    tombstone = memory("deleted", title="[DELETED]", text="已删除。", importance=10)
    assert shouldPrune(tombstone, TODAY)
    assert not shouldPrune(replace(tombstone, locked=True), TODAY)


def test_retention_is_monotonic_over_time():
    item = memory(uses=0)
    fresh = retention(replace(item, lastUsed=TODAY), TODAY)
    older = retention(replace(item, lastUsed="2026-05-08"), TODAY)
    oldest = retention(replace(item, lastUsed="2026-03-09"), TODAY)
    assert fresh == pytest.approx(1, abs=1e-5) and fresh > older > oldest


def test_retention_grows_with_confirmed_uses():
    last_used = "2026-03-09"
    assert retention(memory(uses=5, lastUsed=last_used), TODAY) > retention(memory(uses=0, lastUsed=last_used), TODAY)


def test_retention_threshold_source_calibration():
    assert retention(memory(uses=0, lastUsed=STALE), TODAY) < 0.3
    assert retention(memory(uses=0, lastUsed="2026-04-28"), TODAY) > 0.3


@pytest.mark.parametrize(("fields", "expected"), [
    ({"importance": 3, "type": "semantic", "lastUsed": STALE}, True),
    ({"importance": 3, "type": "user", "lastUsed": STALE}, False),
    ({"importance": 3, "type": "feedback", "lastUsed": STALE}, False),
    ({"importance": 3, "type": "semantic", "lastUsed": STALE, "locked": True}, False),
    ({"importance": 6, "type": "semantic", "lastUsed": STALE}, False),
    ({"importance": 3, "type": "semantic", "lastUsed": STALE, "uses": 10}, False),
    ({"type": "user", "importance": 5, "confidence": 0.4, "uses": 0, "lastUsed": STALE}, True),
    ({"type": "user", "importance": 5, "confidence": 0.4, "uses": 0, "lastUsed": TODAY}, False),
    ({"type": "user", "importance": 5, "confidence": 0.4, "uses": 1, "lastUsed": STALE}, False),
    ({"type": "user", "importance": 5, "confidence": 0.9, "uses": 0, "lastUsed": STALE}, False),
    ({"importance": 9, "type": "semantic", "status": "superseded", "validUntil": "2026-06-03"}, False),
])
def test_source_retention_protection_and_expiry(fields, expected):
    assert shouldPrune(memory(**fields), TODAY) is expected


def test_superseded_grace_expiry_preserves_locked_entry():
    item = memory(importance=9, status="superseded", validUntil="2026-05-20")
    assert shouldPrune(item, TODAY)
    assert not shouldPrune(replace(item, locked=True), TODAY)


@pytest.mark.parametrize(("fields", "expected"), [
    ({}, True),
    ({"uses": 1}, False),
    ({"created": TODAY}, False),
    ({"importance": 7}, False),
    ({"confidence": 0.9}, False),
    ({"type": "feedback"}, False),
])
def test_source_provisional_window(fields, expected):
    provisional = memory(uses=0, importance=5, confidence=0.5, created=OLD_CREATED, lastUsed=TODAY)
    assert shouldPrune(replace(provisional, **fields), TODAY) is expected
    if not fields:
        assert not shouldPrune(provisional, TODAY, provisionalDays=37.5)


def test_gc_missing_directory_returns_empty(tmp_path):
    store = MemoryStore(tmp_path / "workspace", tmp_path / "user", DEFAULT_COMPATIBILITY)
    assert asyncio.run(gcMemories(store, "project", TODAY)) == []
    assert not (tmp_path / "workspace").exists()


def test_gc_removes_dead_native_file_and_keeps_live_file(tmp_path):
    store = MemoryStore(tmp_path, tmp_path / "user", DEFAULT_COMPATIBILITY)

    async def scenario():
        await store.publishExpected("project", memory("dead", importance=2, lastUsed=STALE), None)
        await store.publishExpected("project", memory("alive", importance=8, lastUsed=STALE), None)
        assert await gcMemories(store, "project", TODAY) == ["dead"]
        assert [entry.path.name for entry in await store.loadNative("project")] == ["alive.md"]

    asyncio.run(scenario())


def test_gc_unconfirmed_receipt_stops_scope_and_reports_only_confirmed_deletes(tmp_path, monkeypatch):
    from ruocun.memory import store as store_module

    store = MemoryStore(tmp_path, tmp_path / "user", DEFAULT_COMPATIBILITY)
    real_sync = store_module.sync_directory
    calls = 0

    def sync(directory):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic directory receipt failure")
        return real_sync(directory)

    async def scenario():
        for name in ("first", "second", "third"):
            await store.publishExpected("project", memory(name, importance=2, lastUsed=STALE), None)
        first, unconfirmed, untouched = await store.loadNative("project")
        monkeypatch.setattr(store_module, "sync_directory", sync)
        with pytest.raises(MemoryPruneUnconfirmed) as outcome:
            await gcMemories(store, "project", TODAY)
        assert outcome.value.pruned == (first.memory.name,)
        assert not first.path.exists() and not unconfirmed.path.exists()
        assert untouched.path.is_file() and calls == 2

    asyncio.run(scenario())
