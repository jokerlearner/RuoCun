"""逐项向用户收集选择或自由回答，再汇总交还模型。请求通过当前回合的交互入口展示。"""

from __future__ import annotations

from typing import Any

from .schema import objectSchema
from .types import Tool, ToolContext

DISCUSS_ZH = "我想先讨论一下,先别急着定方向。"
DISCUSS_EN = "I'd like to discuss first; let's not lock in a direction yet."

_OPTION = objectSchema({
    "label": {"type": "string", "description": "选项显示文本(1-5 个词)"},
    "description": {"type": "string", "description": "选项说明(选了会发生什么)"},
}, ["label"])
_QUESTION = objectSchema({
    "question": {"type": "string", "description": "要问用户的问题"},
    "header": {"type": "string", "description": "简短标签(最多 12 字符,如 'Auth method')"},
    "options": {"type": "array", "items": _OPTION, "minItems": 2,
                "description": "结构化选项(无需写'其他'/'先讨论',会自动加)"},
    "multiSelect": {"type": "boolean", "description": "是否允许多选(checkbox);默认单选"},
}, ["question"])


async def _ask_one(ctx: ToolContext, question: str, options: list[str] | None, multi: bool = False) -> str:
    if ctx.signal.is_set():
        return "[用户中断]"
    if options and ctx.askChoice is not None:
        answer = await ctx.askChoice(question, options, multi)
    else:
        if ctx.ask is None:
            raise ValueError("当前环境不支持向用户提问(ask 未配置)")
        answer = await ctx.ask(question)
    return "[用户中断]" if ctx.signal.is_set() else answer.strip() or "(用户未回答)"


async def _handle(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.ask is None:
        raise ValueError("当前环境不支持向用户提问(ask 未配置)")
    if args.get("question") and args.get("questions"):
        raise ValueError("question 和 questions 不能同时传(二选一)")
    if args.get("questions"):
        results = []
        discussing = False
        discuss_value = DISCUSS_EN if ctx.lang == "en" else DISCUSS_ZH
        for index, item in enumerate(args["questions"], 1):
            prefix = f"[{index}. {item['question']}] "
            if discussing:
                results.append(prefix + "(未问——用户要求先讨论)")
                continue
            options = [option["label"] + (" - " + option["description"] if option.get("description") else "")
                       for option in item.get("options", [])]
            answer = await _ask_one(ctx, item["question"], options, item.get("multiSelect", False))
            if answer == discuss_value:
                results.append(prefix + "⚠ 用户想先讨论一下,先别急着定方向。")
                discussing = True
            else:
                results.append(prefix + answer)
        return "\n".join(results)
    if args.get("question"):
        return await _ask_one(ctx, args["question"], args.get("options"), args.get("multiSelect", False))
    raise ValueError("必须传 question(简写)或 questions(完整)之一")
DESCRIPTION = (
    "需要用户提供关键事实或作决定时，在这里提问。单题用 question，选填 options 和 multiSelect；多题用 questions（1 到 4 "
    "题），每题可带 header 和有说明的选项。没有选项就收集自由文本。需要用户同时选择多项时设置 multiSelect；选项由界面补上其他答案入口。"
)
DESCRIPTION_EN = (
    "Ask for facts you cannot verify locally or for a decision the user needs to make. "
    "Use question with optional options and multiSelect for one question. Use questions "
    "for up to four, with a header and labelled choices when useful. Omit options for "
    "free text. Enable multiSelect when several answers may apply. The interface "
    "supplies a way to give a different answer."
)


askUserTool = Tool(
    name="AskUserQuestion", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
    capability="read", approval="auto", handler=_handle,
    schema=objectSchema({
        "question": {"type": "string", "description": "要问用户的问题(简写模式,与 questions 二选一)"},
        "options": {"type": "array", "items": {"type": "string"}, "minItems": 2,
                    "description": "正常可选项(简写模式,纯字符串;无需写'其他'/'先讨论',会自动加)"},
        "multiSelect": {"type": "boolean", "description": "是否允许多选(checkbox);默认单选"},
        "questions": {"type": "array", "items": _QUESTION, "minItems": 1, "maxItems": 4,
                      "description": "多问题数组(完整模式,与 question 二选一)"},
    }, []),
)
