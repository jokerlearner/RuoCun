"""冻结 adapt.test.ts 与 convert.test.ts 的十三个行为。"""

import asyncio
import hashlib
import os
import subprocess

import pytest

from ruocun.skills.adapt import isForeignSkill
from ruocun.skills.convert import convertSystemPrompt, makeSkillAdapter

TOOLS = {"Read", "Write", "Edit", "Bash", "Grep", "AskUserQuestion"}
CATALOG = "Read — 读文件\nEdit — 改文件\nBash — 跑命令"
FOREIGN = "use the `WebFetch` tool then `MultiEdit`"


@pytest.mark.parametrize(("bodies", "expected"), [
    ([FOREIGN, "call WebFetch tool to grab it"], True),
    (["emit an `apply_patch` block", "use run_shell_command tool to build"], True),
    (["then use superpowers:test-driven-development"], True),
    (["先 `Read` 再 `Edit`,跑 `Bash` 验证", "用 Read 工具读配置,再 Grep 工具搜符号"], False),
    (["Read the docs and edit your notes carefully"], False),
    (["see https://example.com at 12:30 for details"], False),
])
def test_foreign_skill_detection(bodies, expected):
    assert all(isForeignSkill(body, TOOLS) == expected for body in bodies)


def test_prompt_inherits_current_model_without_provider_ids():
    prompt = convertSystemPrompt("Read — 读文件")
    assert "deepseek-v4-flash" not in prompt and "deepseek-v4-pro" not in prompt
    assert "继承当前主模型" in prompt and any(tier in prompt for tier in ("haiku", "sonnet", "opus"))


def test_prompt_explains_agent_for_independent_context_when_available():
    prompt = convertSystemPrompt("Read — 读文件")
    assert "agent" in prompt and ("独立上下文" in prompt or "子代理" in prompt)


def test_prompt_retains_main_loop_intent_without_invented_model_switch():
    prompt = convertSystemPrompt("Read — 读文件")
    assert "主流程" in prompt or "主循环" in prompt
    assert "子代理" in prompt or "agent" in prompt
    assert "DAO 的核心优化" not in prompt


def test_legacy_body_only_cache_is_not_reused(tmp_path):
    directory = tmp_path / "skill-adapted"
    directory.mkdir()
    old_hash = hashlib.sha256(FOREIGN.encode()).hexdigest()[:16]
    (directory / f"{old_hash}.md").write_text("model: deepseek-v4-flash", encoding="utf-8")

    async def flash(system, user):
        return "使用 agent 并继承主模型"

    adapt = makeSkillAdapter(toolNames=TOOLS, catalog=CATALOG, userRoot=tmp_path, callFlash=flash)
    assert asyncio.run(adapt(FOREIGN)) == "使用 agent 并继承主模型"


def test_native_body_is_preserved_without_auxiliary_request(tmp_path):
    async def flash(system, user):
        pytest.fail("本地原生技能不应请求辅助模型")

    adapt = makeSkillAdapter(toolNames=TOOLS, catalog=CATALOG, userRoot=tmp_path, callFlash=flash)
    body = "先 `Read` 再 `Edit`"
    assert asyncio.run(adapt(body)) == body


def test_foreign_body_converts_once_then_uses_hash_cache(tmp_path):
    calls = []

    async def flash(system, user):
        calls.append((system, user))
        return "用 Read 读、Bash 跑"

    adapt = makeSkillAdapter(toolNames=TOOLS, catalog=CATALOG, userRoot=tmp_path, callFlash=flash)
    assert asyncio.run(adapt(FOREIGN)) == "用 Read 读、Bash 跑"
    assert asyncio.run(adapt(FOREIGN)) == "用 Read 读、Bash 跑"
    assert len(calls) == 1 and calls[0][1] == FOREIGN
    if os.name == "nt":
        cache = tmp_path / "skill-adapted"
        outside = tmp_path / "external-cache"
        cache.rename(outside)
        outside_entry = next(outside.glob("*.md"))
        outside_entry.write_bytes(b"synthetic external entry")
        subprocess.run([os.environ["COMSPEC"], "/d", "/c", "mklink", "/J", str(cache), str(outside)],
                       check=True, capture_output=True)
        try:
            assert asyncio.run(adapt(FOREIGN)) == "用 Read 读、Bash 跑"
            assert len(calls) == 2 and outside_entry.read_bytes() == b"synthetic external entry"
        finally:
            cache.rmdir()


def test_auxiliary_failure_returns_original_body_with_general_note(tmp_path):
    async def flash(system, user):
        raise RuntimeError("offline")

    adapt = makeSkillAdapter(toolNames=TOOLS, catalog=CATALOG, userRoot=tmp_path, callFlash=flash)
    out = asyncio.run(adapt("call `WebFetch` tool"))
    assert "本平台适配" in out and "call `WebFetch` tool" in out and "deepseek-v4" not in out
