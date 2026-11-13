"""Frozen unified_reflect and reflect_persist public pipeline, synthetic model only."""

import asyncio
import json
from dataclasses import replace


def test_source_unified_fork_tail_all_titles_filters_and_cold_request():
    from ruocun.agent.unified_reflect import reflect

    async def scenario():
        sent = []
        async def call(options):
            sent.append(options)
            return json.dumps({"onTrack": False, "advisory": "反复改foo.ts", "memories": [
                {"title": "偏好中文", "text": "用户偏好中文", "type": "user", "importance": 8},
                {"title": "key", "text": "我的AWS key是AKIA1234567890ABCDEF", "type": "user", "importance": 9},
                {"title": "琐碎", "text": "随口一句", "type": "episodic", "importance": 2},
                {"title": "别mock", "text": "测试必须真实数据库", "type": "feedback", "importance": 9}]})
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "干活"}]
        options = {"baseUrl": "http://127.0.0.1:1", "apiKey": "synthetic", "model": "synthetic",
                   "tools": [{"type": "function", "function": {"name": "Read"}}]}
        existing = [{"title": f"偏好{i}", "text": f"正文内容-{i}"} for i in range(35)]
        result = await reflect(messages, options=options, call=call, existing=existing, fork=True)
        assert not result["onTrack"] and "foo.ts" in result["advisory"]
        assert [memory["title"] for memory in result["memories"]] == ["偏好中文"]
        tail = sent[-1]["messages"][-1]["content"]
        assert "偏好34" in tail and "正文内容-0" in tail and "正文内容-34" not in tail
        assert sent[-1]["tools"] and sent[-1]["extra"] == {"reasoning_effort": "max"}
        await reflect(messages, options=options, call=call, fork=False)
        assert "tools" not in sent[-1] and sent[-1]["extra"] == {"thinking": {"type": "disabled"}, "temperature": 0}
        assert len(messages) == 2
    asyncio.run(scenario())


def test_source_apply_scope_merge_corrections_locked_and_confirmed(tmp_path):
    from ruocun.agent.reflect_persist import applyReflectResult, reflectMemToCand
    from ruocun.config.compat import Compatibility
    from ruocun.memory.store import MemoryStore, routeScope
    from ruocun.memory.types import newMemory

    async def scenario():
        workspace, home = tmp_path / "workspace", tmp_path / "home"
        workspace.mkdir()
        home.mkdir()
        store = MemoryStore(workspace, home, Compatibility(1, ()))
        original = newMemory(name="old", title="旧事实", text="old", type="semantic", today="2026-06-25")
        await store.upsert("project", original)
        locked = replace(original, name="locked", title="锁定", locked=True)
        assert await store.publishExpected("project", locked, None)
        candidate = reflectMemToCand({"title": "增强", "text": "expanded", "type": "user", "mergeInto": "旧事实"},
                                     [original], "2026-06-26")
        assert candidate.name == "old" and candidate.type == "semantic"
        result = {"onTrack": False, "advisory": "check", "memories": [
            {"title": "中文偏好", "text": "用户偏好中文", "type": "user", "importance": 8}],
            "corrections": [{"target": "旧事实", "action": "revise", "newText": "new fact", "reason": "verified"},
                            {"target": "锁定", "action": "supersede", "reason": "must skip"}], "confirmed": ["旧事实", "锁定"]}
        applied = await applyReflectResult(result, store, today="2026-06-26")
        assert applied["added"] == 1 and len(applied["corrections"]) == 1 and applied["confirmed"] == 2
        entries = await store.load()
        assert next(entry.memory for entry in entries if entry.memory.name == "old").text == "new fact"
        assert next(entry.memory for entry in entries if entry.memory.name == "old").lastUsed == "2026-06-26"
        assert next(entry.memory for entry in entries if entry.memory.name == "locked").status == "active"
        assert next(entry.memory for entry in entries if entry.memory.name == "locked").lastUsed == "2026-06-26"
        assert next(entry.scope for entry in entries if entry.memory.title == "中文偏好") == routeScope("user")
    asyncio.run(scenario())
