"""Frozen memory/inject.test.ts selection and rendering assertions."""

from dataclasses import replace

from ruocun.memory.inject import (
    ValidatedMemory,
    buildIndexSection,
    buildMemorySection,
    selectForInjection,
    selectFullText,
    selectIndexNames,
)
from ruocun.memory.types import newMemory

TODAY = "2026-06-07"


def item(name, verdict="ok", **changes):
    memory = replace(newMemory(name=name, text=f"t-{name}", type="semantic", today=TODAY), **changes)
    return ValidatedMemory(memory, verdict)


def names(items):
    return [entry.mem.name for entry in items]


def test_memory_section_drops_stale_and_annotates_changed():
    text = buildMemorySection([
        item("a", text="事实A"), item("b", "changed", text="事实B"), item("c", "stale", text="事实C"),
    ])
    assert "事实A" in text
    assert "事实B(可能已过期" in text
    assert "事实C" not in text


def test_memory_section_empty_when_all_stale():
    assert buildMemorySection([item("c", "stale", text="事实C")]) == ""


def test_legacy_under_cap_keeps_live_order():
    items = [item("a"), item("b", "stale"), item("c", "changed")]
    assert names(selectForInjection(items, TODAY, 150)) == ["a", "c"]


def test_legacy_over_cap_keeps_user_and_high_retention():
    items = [item(f"user-{i}", type="user", importance=1) for i in range(5)]
    items += [item("vip", importance=10), item("junk", importance=1, lastUsed="2025-01-01")]
    items += [item(f"n-{i}", importance=5) for i in range(50)]
    selected = names(selectForInjection(items, TODAY, 10))
    assert len(selected) <= 10
    assert all(f"user-{i}" in selected for i in range(5))
    assert "vip" in selected and "junk" not in selected


def test_legacy_over_cap_keeps_feedback():
    items = [item("fb", type="feedback", importance=1, lastUsed="2025-01-01")]
    items += [item(f"n-{i}", importance=9) for i in range(50)]
    assert "fb" in names(selectForInjection(items, TODAY, 10))


def test_legacy_stale_items_do_not_use_the_cap():
    items = [item(f"s-{i}", "stale") for i in range(200)] + [item("live", importance=9)]
    assert names(selectForInjection(items, TODAY, 150)) == ["live"]


def test_full_text_prioritizes_user_feedback_locked_and_retention():
    items = [
        item("u", type="user", importance=1), item("fb", type="feedback", importance=1),
        item("lk", importance=1, locked=True), item("hi", importance=9),
        item("lo", importance=2, lastUsed="2025-01-01"),
    ]
    selected = names(selectFullText(items, TODAY, 4))
    assert all(name in selected for name in ("u", "fb", "lk", "hi"))
    assert "lo" not in selected and len(selected) <= 4


def test_full_text_filters_stale_protected_type():
    items = [item("a", type="user"), item("b", "stale", type="user")]
    assert names(selectFullText(items, TODAY)) == ["a"]


def test_index_excludes_full_names_and_stale_and_orders_remaining():
    items = [item("u", type="user"), item("x", importance=9), item("y", importance=3), item("z", "stale")]
    assert selectIndexNames(items, TODAY, selectFullText(items, TODAY, 1), 200) == ["x", "y"]


def test_index_caps_remaining_names():
    items = [item(f"n-{i}") for i in range(50)]
    assert len(selectIndexNames(items, TODAY, [], 10)) == 10


def test_index_rendering_lists_names_and_memory_read_hint():
    assert buildIndexSection([]) == ""
    result = buildIndexSection(["foo", "bar"])
    assert all(part in result for part in ("MemoryRead", "- foo", "- bar", "其余 2 条"))
