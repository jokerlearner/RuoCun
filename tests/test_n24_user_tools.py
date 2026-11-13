"""冻结ask_user.test.ts语义及SendUserMessage最小产品确认。"""

import asyncio
import json

import pytest

from ruocun.tools.ask_user import DISCUSS_ZH, askUserTool
from ruocun.tools.registry import ToolRegistry
from ruocun.tools.send_message import sendMessageTool
from ruocun.tools.types import ToolContext


def context(tmp_path, *, answer="blue", choice=None):
    async def ask(question):
        return answer

    ctx = ToolContext(str(tmp_path), askChoice=choice)
    ctx.ask = ask
    ctx.notifyUser = None
    return ctx


@pytest.mark.parametrize(("answer", "expected"), [("blue", "blue"), ("   ", "(用户未回答)")])
def test_free_text_answer_and_blank_answer(tmp_path, answer, expected):
    assert asyncio.run(askUserTool.handler({"question": "favorite color?"}, context(tmp_path, answer=answer))) == expected


def test_missing_callback_rejected(tmp_path):
    ctx = context(tmp_path)
    ctx.ask = None
    with pytest.raises(ValueError, match="ask 未配置"):
        asyncio.run(askUserTool.handler({"question": "x?"}, ctx))


def test_shorthand_options_and_multiselect_reach_same_choice_callback(tmp_path):
    seen = []

    async def choice(question, options, multi=False):
        seen.append((question, options, multi))
        return "方案 B"

    args = {"question": "选哪个?", "options": ["方案 A", "方案 B"], "multiSelect": True}
    assert asyncio.run(askUserTool.handler(args, context(tmp_path, choice=choice))) == "方案 B"
    assert seen == [("选哪个?", ["方案 A", "方案 B"], True)]
    assert askUserTool.name == "AskUserQuestion" and askUserTool.approval == "auto"


def test_options_fall_back_to_free_text_without_choice_callback(tmp_path):
    assert asyncio.run(askUserTool.handler(
        {"question": "选哪个?", "options": ["A", "B"]}, context(tmp_path, answer="我自己写一个"),
    )) == "我自己写一个"


def test_structured_questions_are_sequential_and_description_is_preserved(tmp_path):
    seen = []

    async def choice(question, options, multi=False):
        seen.append((question, options))
        return "React" if "框架" in question else "TypeScript"

    result = asyncio.run(askUserTool.handler({"questions": [
        {"question": "用什么框架?", "options": [{"label": "React", "description": "用户界面"}, {"label": "Vue"}]},
        {"question": "用什么语言?", "options": [{"label": "TypeScript"}, {"label": "JavaScript"}]},
    ]}, context(tmp_path, choice=choice)))
    assert result == "[1. 用什么框架?] React\n[2. 用什么语言?] TypeScript"
    assert seen == [("用什么框架?", ["React - 用户界面", "Vue"]), ("用什么语言?", ["TypeScript", "JavaScript"])]


def test_discuss_stops_later_questions_and_labels_missing_answers(tmp_path):
    seen = []

    async def choice(question, options, multi=False):
        seen.append(question)
        return DISCUSS_ZH if "语言" in question else "React"

    result = asyncio.run(askUserTool.handler({"questions": [
        {"question": question, "options": [{"label": "A"}, {"label": "B"}]}
        for question in ["用什么框架?", "用什么语言?", "用什么数据库?"]
    ]}, context(tmp_path, choice=choice)))
    assert seen == ["用什么框架?", "用什么语言?"]
    assert result == ("[1. 用什么框架?] React\n[2. 用什么语言?] ⚠ 用户想先讨论一下,先别急着定方向。\n"
                      "[3. 用什么数据库?] (未问——用户要求先讨论)")


@pytest.mark.parametrize(("args", "message"), [
    ({"question": "a?", "questions": [{"question": "b?"}]}, "二选一"),
    ({}, "必须传"),
])
def test_question_styles_are_exclusive(tmp_path, args, message):
    with pytest.raises(ValueError, match=message):
        asyncio.run(askUserTool.handler(args, context(tmp_path)))


def test_question_array_limits_match_source_schema(tmp_path):
    registry = ToolRegistry()
    registry.register(askUserTool)
    for args in [{"questions": []}, {"questions": [{"question": "?"}] * 5}, {"question": "?", "options": ["A"]}]:
        with pytest.raises(ValueError):
            registry.validate("AskUserQuestion", json.dumps(args))


def test_send_message_attachments_cwd_failures_and_proactive_notification(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "note.txt").write_text("🙂" * 2001, encoding="utf-8")
    ctx = context(tmp_path)
    ctx.cwd = str(workspace)
    notices = []
    ctx.notifyUser = notices.append
    result = asyncio.run(sendMessageTool.handler({
        "message": "**合成通知**", "attachments": ["note.txt", "missing.txt"], "status": "normal",
    }, ctx))
    assert result == ("**合成通知**\n\n---\n附件:note.txt\n```\n" + "🙂" * 2000
                      + "\n…(已截断)\n```\n\n(附件 missing.txt 读取失败)")
    assert notices == []
    assert asyncio.run(sendMessageTool.handler({"message": "🙂" * 51, "status": "proactive"}, ctx)) == "🙂" * 51
    assert notices == ["🙂" * 50]
