"""冻结 src/tools/todo_write.test.ts 的首版语义断言。"""

import asyncio

import pytest

from ruocun.tools.todo_write import todoWriteTool
from ruocun.tools.types import ToolContext


def test_renders_todos_and_stores_them(tmp_path):
    ctx = ToolContext(str(tmp_path))
    todos = [{"content": "design", "status": "completed"},
             {"content": "build", "status": "in_progress"},
             {"content": "test", "status": "pending"}]
    out = asyncio.run(todoWriteTool.handler({"todos": todos}, ctx))
    assert "☑ design" in out
    assert "▶ build" in out
    assert "☐ test" in out
    assert len(ctx.todos) == 3


def call(tmp_path, todos):
    ctx = ToolContext(str(tmp_path))
    return asyncio.run(todoWriteTool.handler({"todos": todos}, ctx)), ctx.todos


def test_rejects_more_than_one_in_progress(tmp_path):
    with pytest.raises(ValueError, match="in_progress"):
        call(tmp_path, [{"content": "a", "status": "in_progress"}, {"content": "b", "status": "in_progress"}])


def test_clears_list(tmp_path):
    out, stored = call(tmp_path, [])
    assert out == "(任务清单已清空)"
    assert stored == []


def test_declares_plan_auto():
    assert (todoWriteTool.name, todoWriteTool.capability, todoWriteTool.approval) == ("TodoWrite", "plan", "auto")


def test_all_three_completed_nudge(tmp_path):
    out, _ = call(tmp_path, [{"content": name, "status": "completed"} for name in "abc"])
    assert "verify 子代理" in out  # 恢复冻结 todo_write.test.ts 的原断言；MVP提示改写已撤销。


def test_completion_checks_original_task(tmp_path):
    out, _ = call(tmp_path, [{"content": name, "status": "completed"} for name in "abc"])
    assert "用户的原始要求" in out
    assert "逐条检查实际证据" in out


def test_less_than_three_no_nudge(tmp_path):
    out, _ = call(tmp_path, [{"content": name, "status": "completed"} for name in "ab"])
    assert "verify 子代理" not in out


def test_incomplete_no_nudge(tmp_path):
    out, _ = call(tmp_path, [{"content": "a", "status": "completed"},
                             {"content": "b", "status": "completed"},
                             {"content": "c", "status": "pending"}])
    assert "verify 子代理" not in out


def test_active_form_overrides_content(tmp_path):
    out, stored = call(tmp_path, [{"content": "Run tests", "status": "in_progress", "activeForm": "Running tests"},
                                {"content": "Build project", "status": "pending", "activeForm": "Building project"}])
    assert "▶ Running tests" in out and "▶ Run tests" not in out
    assert "☐ Building project" in out and "☐ Build project" not in out
    assert stored[0]["activeForm"] == "Running tests"
    assert stored[0]["content"] == "Run tests"


def test_omitted_active_form_uses_content(tmp_path):
    out, _ = call(tmp_path, [{"content": "Write code", "status": "in_progress"}])
    assert "▶ Write code" in out
