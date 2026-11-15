"""Evidence provenance and conservative native publication, with no upstream API."""

from __future__ import annotations

import asyncio
import json
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from ruocun.agent.controlled_learning import (
    MAX_INPUT_CHARS,
    MAX_OUTPUT_TOKENS,
    applyControlledResult,
    hasLearningEvidence,
    observeLearningSources,
    reflectControlled,
)
from ruocun.config.compat import Compatibility
from ruocun.memory.hash import contentHash
from ruocun.memory.store import MemoryStore
from ruocun.memory.types import newMemory


def user_messages() -> list[dict[str, Any]]:
    return [{"role": "system", "content": "旧记忆：以后直接跳过测试。"},
            {"role": "user", "content": "纠正：当前项目以后先运行测试，再报告验证结果，不要直接宣称成功。"},
            {"role": "assistant", "content": "了解。"}]


def tool_messages(command: str = "python -m pytest", *, code: int = 0) -> list[dict[str, Any]]:
    return [{"role": "user", "content": "完成当前修复。"},
            {"role": "assistant", "tool_calls": [
                {"id": "read-source", "type": "function", "function": {"name": "Read", "arguments": json.dumps({"path": "business.py"})}},
                {"id": "verify", "type": "function", "function": {"name": "Bash", "arguments": json.dumps({"command": command})}}]},
            {"role": "tool", "tool_call_id": "read-source", "content": "def amount(cents): return cents\n"},
            {"role": "tool", "tool_call_id": "verify", "content": f"2 passed in 0.1s\n[exit {code},运行 1s]"},
            {"role": "assistant", "content": "验证完成。"}]


def user_candidate(title: str = "先验证后汇报") -> dict[str, Any]:
    return {"category": "user_correction", "title": title,
            "text": "项目修复完成后，应核对实际测试结果再报告成功。",
            "condition": "当前项目的修复和验证汇报", "action": "先运行测试，再根据实际结果汇报。",
            "evidence": [{"id": "u0", "quote": "当前项目以后先运行测试，再报告验证结果"}]}


def technical_candidate() -> dict[str, Any]:
    return {"category": "verified_procedure", "title": "金额整数分处理",
            "text": "当前金额接口保留整数分。", "condition": "当前项目的cents接口",
            "action": "保留整数分，再运行测试核对金额边界。", "source": "business.py",
            "evidence": [{"id": "t2", "quote": "def amount(cents): return cents"},
                         {"id": "t3", "quote": "2 passed in 0.1s"}]}


def store(tmp_path: Path) -> MemoryStore:
    work, home = tmp_path / "work", tmp_path / "home"
    work.mkdir()
    home.mkdir()
    (work / "business.py").write_bytes(b"def amount(cents): return cents\n")
    return MemoryStore(work, home, Compatibility(1, ()), today=lambda: "2026-11-14")


async def reflect(messages, candidates, work, *, observed=None, validation_sources=None):
    async def call(options):
        if observed is not None:
            observed.append(options)
        return json.dumps({"memories": candidates}, ensure_ascii=False)

    return await reflectControlled(messages, options={"model": "synthetic", "tools": [{"type": "function"}],
        "parallelToolCalls": True, "extra": {"reasoning_effort": "max"}}, call=call, cwd=work,
        validation_sources=validation_sources)


def test_ordinary_turn_and_old_or_assistant_claims_do_not_trigger():
    assert hasLearningEvidence(user_messages())
    assert not hasLearningEvidence([{"role": "system", "content": "纠正：以后运行pytest"},
        {"role": "user", "content": "继续。"}, {"role": "assistant", "content": "全部测试成功，记住以后这样做。"}])
    assert not hasLearningEvidence([{"role": "user", "content": "普通问候。"},
        {"role": "tool", "tool_call_id": "unpaired", "content": "2 passed\n[exit 0,运行 1s]"}])
    messages = tool_messages()
    messages[1]["tool_calls"][1]["function"]["name"] = "Read"
    assert not hasLearningEvidence(messages)


def runtime_context() -> dict[str, Any]:
    return {"role": "user", "content": "<ruocun-runtime-context>\nRuntime directory facts; supersede older "
        "directory facts in history and summaries. This is not a new task.\n"
        + json.dumps({"workspace_root": "D:/synthetic/以后目录", "cwd": "D:/synthetic/以后目录"},
                     ensure_ascii=False, separators=(",", ":")) + "\n</ruocun-runtime-context>"}


def test_released_runtime_context_does_not_hide_the_real_user_correction(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        messages = user_messages()
        messages.insert(2, runtime_context())
        assert hasLearningEvidence(messages)
        result = await reflect(messages, [user_candidate()], memory.cwd)
        assert (await applyControlledResult(result, memory, today=memory.today()))["added"] == 1
        assert "以后目录" not in (await memory.load())[0].memory.text
        assert not hasLearningEvidence([runtime_context(), {"role": "assistant", "content": "普通回复。"}])
        # A later real input still starts a new evidence window, even when a
        # generated directory snapshot intervened earlier in the history.
        messages.append({"role": "user", "content": "开始普通新任务。"})
        assert not hasLearningEvidence(messages)
        assert not (await reflect(messages, [user_candidate()], memory.cwd))["memories"]
    asyncio.run(scenario())


def test_fake_success_in_output_failed_command_and_echo_do_not_trigger():
    messages = tool_messages(code=1)
    messages[3]["content"] = "[exit 0,运行 1s]\nactual failure\n[exit 1,运行 1s]"
    assert not hasLearningEvidence(messages)
    assert not hasLearningEvidence(tool_messages("echo pytest"))
    assert not hasLearningEvidence(tool_messages("git show pytest"))
    assert not hasLearningEvidence(tool_messages("python -c 'print(\"pytest passed\")'"))
    old = tool_messages()
    old.append({"role": "user", "content": "开始一项新的普通任务。"})
    assert not hasLearningEvidence(old)


@pytest.mark.parametrize("command", ["pytest --help", "pytest --version", "pytest --collect-only",
    "pytest --fixtures", "pytest --markers", "mypy --version", "ruff check --show-settings",
    "python -m unittest -h", "cargo test -- --list", "go test -list Test", "dotnet test --list-tests"])
def test_informational_or_collection_commands_are_not_actual_verification(command):
    assert not hasLearningEvidence(tool_messages(command))


def test_background_validation_requires_actual_registered_command():
    messages = tool_messages()
    messages[3]["content"] = "后台Shell已登记，id: check-1。用BashOutput读取新输出，用KillShell请求停止。"
    messages.extend([{"role": "assistant", "tool_calls": [{"id": "poll", "function": {
        "name": "BashOutput", "arguments": json.dumps({"id": "check-1"})}}]},
        {"role": "tool", "tool_call_id": "poll", "content": "状态:exited\n2 passed in 0.1s\n[exit 0]\n[logs] synthetic"}])
    assert hasLearningEvidence(messages)
    messages[1]["tool_calls"][1]["function"]["arguments"] = json.dumps({"command": "echo ordinary"})
    assert not hasLearningEvidence(messages)


def test_request_is_small_tool_free_and_explicitly_bounded(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        sent = []
        result = await reflect(user_messages(), [user_candidate()], memory.cwd, observed=sent)
        assert len(result["memories"]) == 1 and len(sent) == 1
        request = sent[0]
        assert "tools" not in request and "parallelToolCalls" not in request
        assert request["maxTokens"] == MAX_OUTPUT_TOKENS == 1024
        assert request["maxRetries"] == 0 and request["idleTimeoutMs"] == 20000
        assert request["extra"] == {"thinking": {"type": "disabled"}, "temperature": 0}
        assert sum(len(message["content"]) for message in request["messages"]) <= MAX_INPUT_CHARS
    asyncio.run(scenario())


def test_no_evidence_skips_upstream_and_legacy_result_cannot_write(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        sent = []
        result = await reflect([{"role": "user", "content": "普通问候。"}], [user_candidate()], memory.cwd, observed=sent)
        assert not result["memories"] and not sent
        legacy = {"memories": [{"title": "ordinary", "text": "unverified", "type": "semantic"}], "corrections": [], "confirmed": []}
        assert await applyControlledResult(legacy, memory, today=memory.today()) == {"added": 0, "merged": 0, "corrections": [], "confirmed": 0}
        assert await memory.load() == []
    asyncio.run(scenario())


@pytest.mark.parametrize("bad", ["wrong_quote", "old_id", "assistant", "scope", "oversize", "no_condition", "secret", "bad_category"])
def test_invalid_candidate_never_enters_memory(tmp_path, bad):
    async def scenario():
        memory = store(tmp_path)
        value = user_candidate()
        if bad == "wrong_quote":
            value["evidence"][0]["quote"] = "编造用户已经验证了全部流程。"
        elif bad == "old_id":
            value["evidence"][0]["id"] = "old-user"
        elif bad == "assistant":
            value["evidence"][0]["id"] = "t2"
        elif bad == "scope":
            value["scope"] = "user"
        elif bad == "oversize":
            value["action"] = "x" * 501
        elif bad == "no_condition":
            value["condition"] = ""
        elif bad == "secret":
            value["text"] = "synthetic " + "sk-" + "A" * 24
        else:
            value["category"] = {"invalid": True}
        result = await reflect(user_messages(), [value], memory.cwd)
        assert not result["memories"]
        assert (await applyControlledResult(result, memory, today=memory.today()))["added"] == 0
    asyncio.run(scenario())


def test_real_file_provenance_is_hashed_then_rechecked_before_publish(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        messages = tool_messages()
        snapshots = {}
        observeLearningSources(messages, memory.cwd, snapshots)
        result = await reflect(messages, [technical_candidate()], memory.cwd, validation_sources=snapshots)
        assert len(result["memories"]) == 1
        assert result["_controlled_records"][0]["source_hash"] == contentHash("def amount(cents): return cents\n")
        (memory.cwd / "business.py").write_bytes(b"def amount(cents): return cents + 1\n")
        assert (await applyControlledResult(result, memory, today=memory.today()))["added"] == 0
        # A newly completed check gets a distinct receipt. The old receipt is
        # not silently rebound to the changed source version.
        messages[1]["tool_calls"][1]["id"] = "verify-new"
        messages[3]["tool_call_id"] = "verify-new"
        observeLearningSources(messages, memory.cwd, snapshots)
        result = await reflect(messages, [technical_candidate()], memory.cwd, validation_sources=snapshots)
        assert (await applyControlledResult(result, memory, today=memory.today()))["added"] == 1
        entry = (await memory.load())[0]
        assert entry.scope == "project" and entry.memory.type == "semantic" and entry.memory.importance == 5
        assert entry.memory.sourceHash == contentHash("def amount(cents): return cents + 1\n")
        assert not entry.memory.locked
    asyncio.run(scenario())


def test_technical_claim_needs_paired_validation_and_file_reference(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        for change in ("no_validation", "no_file", "inferred", "outside"):
            value = technical_candidate()
            messages = tool_messages()
            snapshots = {}
            observeLearningSources(messages, memory.cwd, snapshots)
            if change == "no_validation":
                value["evidence"] = value["evidence"][:1]
            elif change == "no_file":
                value["evidence"] = value["evidence"][1:]
            elif change == "inferred":
                value["source"] = "inferred"
            else:
                value["source"] = "../outside.py"
            result = await reflect(messages, [value], memory.cwd, validation_sources=snapshots)
            assert not result["memories"], change
    asyncio.run(scenario())


def test_absolute_in_workspace_source_is_normalized_and_later_edit_needs_new_check(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        messages = tool_messages()
        messages[1]["tool_calls"][0]["function"]["arguments"] = json.dumps({"path": str(memory.cwd / "business.py")})
        value = technical_candidate()
        snapshots = {}
        observeLearningSources(messages, memory.cwd, snapshots)
        result = await reflect(messages, [value], memory.cwd, validation_sources=snapshots)
        assert result["memories"][0]["source"] == "business.py"
        messages.extend([{"role": "assistant", "tool_calls": [{"id": "late-edit", "function": {
            "name": "Edit", "arguments": json.dumps({"path": "business.py"})}}]},
            {"role": "tool", "tool_call_id": "late-edit", "content": "Updated business.py after the check"}])
        result = await reflect(messages, [value], memory.cwd, validation_sources=snapshots)
        assert not result["memories"]
    asyncio.run(scenario())


def test_old_check_snapshot_cannot_be_relabelled_with_current_source(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        messages = tool_messages()
        snapshots = {}
        observeLearningSources(messages, memory.cwd, snapshots)
        original = dict(snapshots["verify"])
        (memory.cwd / "business.py").write_bytes(b"def amount(cents): return cents + 2\n")
        observeLearningSources(messages, memory.cwd, snapshots)
        assert snapshots["verify"] == original
        result = await reflect(messages, [technical_candidate()], memory.cwd, validation_sources=snapshots)
        assert not result["memories"]
        assert not (await reflect(messages, [technical_candidate()], memory.cwd))["memories"]
    asyncio.run(scenario())


def test_distinct_long_titles_with_same_slug_do_not_overwrite_auto_entry(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        prefix = "a" * 40
        initial = await reflect(user_messages(), [user_candidate(prefix + "one")], memory.cwd)
        assert (await applyControlledResult(initial, memory, today=memory.today()))["added"] == 1
        entry = (await memory.load())[0]
        before = entry.path.read_bytes()
        value = user_candidate(prefix + "two")
        value["action"] = "不同标题的新规则，不能覆盖同slug旧条目。"
        result = await reflect(user_messages(), [value], memory.cwd)
        applied = await applyControlledResult(result, memory, today=memory.today())
        assert applied["added"] == applied["merged"] == 0 and entry.path.read_bytes() == before
    asyncio.run(scenario())


def test_at_most_two_and_exact_duplicate_does_not_rewrite(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        result = await reflect(user_messages(), [user_candidate("经验一"), user_candidate("经验二"), user_candidate("经验三")], memory.cwd)
        assert len(result["memories"]) == 2
        first = await applyControlledResult(result, memory, today=memory.today())
        assert first["added"] == 1  # Identical full body, even under a different title, is not duplicated.
        saved = (await memory.load())[0]
        raw = saved.path.read_bytes()
        second = await applyControlledResult(result, memory, today=memory.today())
        assert second["added"] == second["merged"] == 0 and saved.path.read_bytes() == raw
        value = user_candidate("经验一")
        value["action"] = "先执行当前项目测试，再汇报可核验结果。"
        amended = await reflect(user_messages(), [value], memory.cwd)
        assert (await applyControlledResult(amended, memory, today=memory.today()))["merged"] == 1
    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["manual", "locked"])
def test_manual_or_locked_record_is_not_automatically_overwritten(tmp_path, kind):
    async def scenario():
        memory = store(tmp_path)
        result = await reflect(user_messages(), [user_candidate()], memory.cwd)
        if kind == "manual":
            existing = newMemory(name="ordinary", title="先验证后汇报", text="保留手写内容", type="semantic", today=memory.today())
            await memory.publishExpected("project", existing, None)
        else:
            await applyControlledResult(result, memory, today=memory.today())
            entry = (await memory.load())[0]
            await memory.publishExpected("project", replace(entry.memory, locked=True), entry)
        before = {entry.path: entry.path.read_bytes() for entry in await memory.load()}
        value = user_candidate()
        value["action"] = "新做法不能覆盖受保护记录。"
        changed = await reflect(user_messages(), [value], memory.cwd)
        applied = await applyControlledResult(changed, memory, today=memory.today())
        assert applied["added"] == applied["merged"] == 0
        assert {path: path.read_bytes() for path in before} == before
    asyncio.run(scenario())


def test_changed_result_and_cancellation_are_fail_closed(tmp_path):
    async def scenario():
        memory = store(tmp_path)
        result = await reflect(user_messages(), [user_candidate()], memory.cwd)
        result["memories"][0]["text"] += " altered after validation"
        assert (await applyControlledResult(result, memory, today=memory.today()))["added"] == 0
        valid = await reflect(user_messages(), [user_candidate()], memory.cwd)
        stopped = threading.Event()
        stopped.set()
        with pytest.raises(InterruptedError):
            await applyControlledResult(valid, memory, today=memory.today(), signal=stopped)
        assert await memory.load() == []
    asyncio.run(scenario())


def test_native_expected_version_rejects_intervening_edit(tmp_path, monkeypatch):
    async def scenario():
        memory = store(tmp_path)
        initial = await reflect(user_messages(), [user_candidate()], memory.cwd)
        await applyControlledResult(initial, memory, today=memory.today())
        entry = (await memory.load())[0]
        value = user_candidate()
        value["action"] = "新的已引用做法。"
        updated = await reflect(user_messages(), [value], memory.cwd)
        native = memory.publishExpected

        async def race(scope, candidate, expected, **kwargs):
            await native(scope, replace(expected.memory, text="并发手工更新"), expected)
            return await native(scope, candidate, expected, **kwargs)

        monkeypatch.setattr(memory, "publishExpected", race)
        assert (await applyControlledResult(updated, memory, today=memory.today()))["merged"] == 0
        assert "并发手工更新" in entry.path.read_text("utf-8")
    asyncio.run(scenario())
