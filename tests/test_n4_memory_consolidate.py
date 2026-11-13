"""Frozen memory/consolidate.test.ts plan, gate and request assertions."""

import asyncio
import json
import sys
from dataclasses import replace

import pytest

from ruocun.config.compat import DEFAULT_COMPATIBILITY
from ruocun.memory import store as store_module
from ruocun.memory.consolidate import (
    applyConsolidationPlan,
    buildConsolidatePrompt,
    consolidate,
    consolidationCfg,
    maybeConsolidate,
    parseConsolidationPlan,
    shouldConsolidate,
)
from ruocun.memory.store import MemoryStore
from ruocun.memory.types import newMemory
from ruocun.platform.windows.durable_file import PublishDurabilityError

DAY = 86_400_000
TODAY = "2026-06-07"
GROUP = {"canonical": {"title": "A", "text": "规范记忆", "type": "user", "importance": 8},
         "supersede": ["old1", "old2"], "reason": "重叠"}


def test_parse_consolidation_groups():
    assert parseConsolidationPlan(json.dumps({"groups": [GROUP]})) == {"groups": [GROUP]}


def test_parse_consolidation_extracts_fence():
    body = "```json\n" + json.dumps({"groups": [GROUP]}) + "\n```"
    assert parseConsolidationPlan(body)["groups"] == [GROUP]


def test_parse_bad_json_returns_empty_plan():
    assert parseConsolidationPlan("无效") == {"groups": []}


def test_parse_skips_groups_without_text_or_supersede_array():
    bad = [{"canonical": {"title": "A"}, "supersede": ["a"]},
           {"canonical": {"text": "x"}, "supersede": "bad"}]
    assert parseConsolidationPlan(json.dumps({"groups": [*bad, GROUP]}))["groups"] == [GROUP]


@pytest.mark.parametrize(("last", "count", "now", "expected"), [
    (DAY, 20, 2 * DAY, False), (DAY, 10, 5 * DAY, False),
    (DAY, 20, 5 * DAY, True), (0, 20, 100 * DAY, True),
])
def test_consolidation_gate(last, count, now, expected):
    assert shouldConsolidate(last, count, now, consolidationCfg("user")) is expected


def test_consolidation_scope_thresholds_and_force():
    configs = [consolidationCfg(scope) for scope in ("user", "knowledge", "project")]
    assert [(cfg.days, cfg.min, cfg.force) for cfg in configs] == [
        (3, 12, "aggressive"), (3, 15, "medium"), (3, 20, "conservative"),
    ]


def test_project_consolidation_prompt_is_conservative():
    memory = newMemory(name="m", text="项目事实", type="semantic", today=TODAY, source="main.py")
    prompt = buildConsolidatePrompt("project", [memory])
    assert "保守" in prompt and "明确冗余" in prompt and "source=main.py" in prompt


def test_consolidate_sends_scope_memories_and_parses_plan():
    sent = []

    async def call(options):
        sent.append(options)
        return json.dumps({"groups": [GROUP]})

    memory = newMemory(name="old1", text="项目事实", type="semantic", today=TODAY)
    plan = asyncio.run(consolidate("project", [memory], options={"model": "synthetic"}, call=call))
    assert plan["groups"] == [GROUP]
    assert "name=old1" in sent[0]["messages"][0]["content"]
    assert sent[0]["extra"] == {"thinking": {"type": "disabled"}, "temperature": 0}


def test_consolidate_unparseable_model_returns_empty_plan():
    async def call(options):
        return "乱码"

    assert asyncio.run(consolidate("user", [], options={"model": "synthetic"}, call=call)) == {"groups": []}


@pytest.fixture
def store(tmp_path):
    if sys.platform != "win32":
        pytest.skip("真实 Windows 原生 Markdown 发布")
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    return MemoryStore(cwd, tmp_path / "user", DEFAULT_COMPATIBILITY)


async def _seed(store, count):
    for i in range(count):
        memory = newMemory(name=f"m{i}", title=f"T{i}", text=f"t{i}", type="user", today=TODAY)
        assert await store.publishExpected("user", memory, None)


def test_apply_consolidation_writes_canonical_then_supersedes_same_source(store):
    async def scenario():
        family = newMemory(name="家长", title="为2岁孩子做游戏的家长", text="持续做儿童游戏,懂认知边界",
                           type="user", today=TODAY, importance=8, source="evidence.md#fact", sourceHash="abc")
        technology = replace(family, name="swiftui-spritekit", title="偏好 SwiftUI+SpriteKit 做儿童游戏",
                             text="用 SwiftUI+SpriteKit", importance=5)
        other = replace(technology, name="foreign", title="其它事实", source="other.md")
        locked = replace(technology, name="locked", title="锁定事实", locked=True)
        for memory in (family, technology, other, locked):
            assert await store.publishExpected("user", memory, None)
        entries = await store.loadNative("user")
        original = {entry.memory.name: entry.path.read_bytes() for entry in entries}
        plan = {"groups": [
            {"canonical": {"title": "新条目", "text": "跨来源或锁定不能合并"},
             "supersede": ["swiftui-spritekit", conflict], "reason": "被保护"}
            for conflict in ("foreign", "locked")
        ]}
        plan["groups"].append({
            "canonical": {"title": family.title, "text": "持续做儿童游戏,懂认知边界;技术上用 SwiftUI+SpriteKit",
                          "type": "user", "importance": 8, "confidence": 0.85, "source": "inferred"},
            "supersede": ["swiftui-spritekit"], "reason": "家长画像已涵盖技术偏好",
        })
        result = await applyConsolidationPlan(store, "user", plan, entries, "2026-06-29")
        assert (result.merged, result.superseded) == (1, 1)
        live = {entry.memory.name: entry for entry in await store.loadNative("user")}
        assert live.keys() == {"家长", "foreign", "locked"}
        assert "SwiftUI" in live["家长"].memory.text
        assert (live["家长"].memory.source, live["家长"].memory.sourceHash) == (family.source, family.sourceHash)
        for name in ("foreign", "locked"):
            assert live[name].path.read_bytes() == original[name]
        entries = {entry.memory.name: entry for entry in await store.loadNative("user", includeSuperseded=True)}
        assert entries["swiftui-spritekit"].memory.supersededBy == "家长"
        assert entries["swiftui-spritekit"].memory.text == technology.text
    asyncio.run(scenario())


def test_apply_consolidation_unknown_names_skip_without_throwing(store):
    plan = {"groups": [{"canonical": {"title": "T", "text": "X", "type": "user", "source": "inferred"},
                        "supersede": ["不存在"], "reason": "r"}]}
    result = asyncio.run(applyConsolidationPlan(store, "user", plan, [], TODAY))
    assert (result.merged, result.superseded) == (1, 0)
    entry, = asyncio.run(store.loadNative("user"))
    assert entry.memory.text == "X" and entry.memory.source is None and entry.memory.sourceHash is None


def test_maybe_consolidate_small_scope_skips_request_and_marker(store):
    async def scenario():
        await _seed(store, 1)

        async def call(options):
            pytest.fail("门槛未达不应请求模型")

        await maybeConsolidate(store, "user", today=TODAY, now=30 * DAY, options={}, call=call)
        assert await store.readConsolidationMarker("user") == 0
    asyncio.run(scenario())


def test_maybe_consolidate_gated_run_writes_and_audits(store, monkeypatch):
    async def scenario():
        await _seed(store, 13)
        events = []

        async def call(options):
            return json.dumps({"groups": [{"canonical": {"title": "T0", "text": "merged", "type": "user"},
                                           "supersede": ["m1"], "reason": "r"}]})

        await maybeConsolidate(store, "user", today="2026-06-29", now=30 * DAY, options={}, call=call,
                               onAudit=events.append)
        assert events == [{"scope": "user", "groups": 1, "superseded": 1, "reasons": ["r"]}]
        assert await store.readConsolidationMarker("user") == 30 * DAY
        entries = {entry.memory.name: entry.memory for entry in await store.loadNative("user", includeSuperseded=True)}
        assert entries["m0"].text == "merged" and entries["m1"].status == "superseded"

        # 独立原生根触发真实 replace 后未知，成功路径不重用这组现场。
        failed = MemoryStore(store.cwd, store.cwd.parent / "unconfirmed-user", DEFAULT_COMPATIBILITY)
        await _seed(failed, 13)
        events.clear()
        before = {entry.memory.name: entry.path for entry in await failed.loadNative("user")}
        target = before["m0"]
        original = target.read_bytes()
        old_target = before["m1"].read_bytes()
        real_publish = store_module.atomic_publish

        def fail_sync(directory):
            raise OSError("synthetic directory synchronization failure after replacement")

        def publish(file, data):
            if file == target:
                return real_publish(file, data, sync_directory_fn=fail_sync)
            return real_publish(file, data)

        with monkeypatch.context() as patch:
            patch.setattr(store_module, "atomic_publish", publish)
            with pytest.raises(PublishDurabilityError) as outcome:
                await maybeConsolidate(failed, "user", today="2026-06-29", now=30 * DAY, options={}, call=call,
                                       onAudit=events.append)
        assert outcome.value.receipt.replaced is True
        assert target.read_bytes() != original
        backup, = target.parent.glob(".m0.*.bak")
        assert backup.read_bytes() == original
        assert before["m1"].read_bytes() == old_target
        assert await failed.readConsolidationMarker("user") == 0 and not events
    asyncio.run(scenario())


def test_maybe_consolidate_recent_marker_skips_request(store):
    async def scenario():
        await _seed(store, 13)
        await store.writeConsolidationMarker("user", 29 * DAY)

        async def call(options):
            pytest.fail("间隔未达不应请求模型")

        await maybeConsolidate(store, "user", today=TODAY, now=30 * DAY, options={}, call=call)
        assert await store.readConsolidationMarker("user") == 29 * DAY
    asyncio.run(scenario())
