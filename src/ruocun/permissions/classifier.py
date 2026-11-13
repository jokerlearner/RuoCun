"""Review tool calls for intelligent approval using a two-stage model request."""
from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from ..client.types import ChatMessage, StreamChatOptions
from .classifier_model import ModelContext, createClassifierRunner
from .gate import Classifier
from .settings import AutoModeRules

ZH_BASE_PROMPT = """你负责若存智能批准中的一项判断：当前这次工具调用能否自动通过。请求末尾是调用及参数，之前的记录只有近期用户消息和工具请求。以用户的实际任务与操作后果为准。

通常允许与任务有关的读取、工作区内的可恢复改动和常规依赖安装。用脚本或专用工具实现同一操作，结论应一致。只读例外包括访问私钥、云凭据或 API 密钥文件。读取项目 .env 本身可按普通项目配置判断。

有以下情况时转人工：
- 操作与用户交办事项无关。
- 访问私钥或账户凭据，或向用户未要求的外部目标传输项目内容。
- 直接运行刚下载的脚本或不明远程安装包。常规软件源依赖安装仍按项目操作判断。
- 无法恢复的改动缺少明确依据，例如删除未跟踪的资料、覆盖远程分支或清空数据库。明确要求的清理可以批准。
- 查看任务和参数后仍无法确定影响。复合命令逐段判断，任何一段需确认就暂停整次调用。

## 当前用户规则

匹配的允许或拒绝规则可以覆盖以上默认判断；环境说明仅用于解释任务。

允许：
{allow}

拒绝：
{deny}

环境：
{environment}

批准写 <block>no</block>。转人工写 <block>yes</block><reason>简述原因</reason>。除非本次请求明确开启第二阶段复核，直接以 <block> 开头。"""

EN_BASE_PROMPT = """Decide whether RuoCun can auto-approve the single tool call at the end of the request. The preceding record contains recent user messages and tool calls. Judge the action by its effects and the user's actual task.

Normally approve task-related reads, reversible workspace changes, and standard dependency installs. A script and a dedicated tool that do the same thing get the same verdict. Reads of private keys, cloud credentials, or API secret files are exceptions. Reading a project's .env may be ordinary project configuration.

Send the request to manual approval if:
- It has no meaningful connection to the user's task.
- It accesses private keys or account credentials, or sends project data to an external destination the user did not request.
- It runs a script just downloaded or an untrusted remote installer. An ordinary install from the project's package registry can proceed.
- The request lacks a clear basis for an irreversible effect, such as deleting untracked work, overwriting a remote branch, or dropping database data. A clearly requested cleanup may proceed.
- The scope or effect still cannot be determined. Review all parts of a compound command and require approval for the whole command if any part needs it.

## Current user rules

Matching allow or deny rules can override the defaults above. Environment notes help establish context.

Allow:
{allow}

Deny:
{deny}

Environment:
{environment}

Approve with <block>no</block>. Request manual approval with <block>yes</block><reason>brief reason</reason>. Start with <block> unless this request explicitly asks for a second-stage review."""

STAGE1_SUFFIX = "Return <block> now. Choose yes if a manual decision is needed or the effect remains unclear."
STAGE2_SUFFIX = "Recheck the request against the rules. Place any analysis inside <thinking>...</thinking>, then give the <block> verdict."


def buildClassifierSystemPrompt(rules: AutoModeRules | None = None, lang: Literal["zh", "en"] = "zh") -> str:
    template = ZH_BASE_PROMPT if lang == "zh" else EN_BASE_PROMPT
    empty = "- (未配置)" if lang == "zh" else "- (none configured)"
    values = rules or {}
    return template.format(
        allow="\n".join(f"- {rule}" for rule in values.get("allow", [])) or empty,
        deny="\n".join(f"- {rule}" for rule in values.get("deny", [])) or empty,
        environment="\n".join(f"- {rule}" for rule in values.get("environment", [])) or empty,
    )


def _stripThinking(text: str) -> str:
    return re.sub(r"<thinking>[\s\S]*$", "", re.sub(r"<thinking>[\s\S]*?</thinking>", "", text))


def parseXmlBlock(text: str) -> bool | None:
    match = re.search(r"<block>(yes|no)\b", _stripThinking(text), re.I)
    return match[1].lower() == "yes" if match else None


def parseXmlReason(text: str) -> str | None:
    match = re.search(r"<reason>([\s\S]*?)</reason>", _stripThinking(text))
    return match[1].strip() if match else None


def _trunc(text: str, limit: int = 500) -> str:
    raw = text.encode("utf-16-le", errors="surrogatepass")
    return raw[:limit * 2].decode("utf-16-le", errors="surrogatepass") + "…" if len(raw) > limit * 2 else text


def buildClassifierTranscript(messages: list[ChatMessage], maxEntries: int = 12) -> str:
    entries: list[str] = []
    for message in messages:
        content = message.get("content", "")
        if message.get("role") == "user":
            text = content if isinstance(content, str) else " ".join(part.get("text", "") for part in content if part.get("type") == "text")
            if text.strip():
                entries.append(json.dumps({"user": _trunc(text.strip())}, ensure_ascii=False, separators=(",", ":")))
        elif message.get("role") == "assistant":
            for call in message.get("tool_calls", []):
                function = call["function"]
                entries.append(json.dumps({function["name"]: _trunc(function["arguments"])}, ensure_ascii=False, separators=(",", ":")))
    return "\n".join(entries[-maxEntries:])


def buildClassifierMessages(toolName: str, argsJson: str, recentMessages: list[ChatMessage], rules: AutoModeRules | None = None,
                            lang: Literal["zh", "en"] = "zh", suffix: str | None = None) -> list[ChatMessage]:
    transcript = buildClassifierTranscript(recentMessages)
    context = f"近期对话:\n{transcript}\n\n" if transcript else ""
    action = json.dumps({toolName: _trunc(argsJson)}, ensure_ascii=False, separators=(",", ":"))
    tail = f"\n\n{suffix}" if suffix else ""
    return [{"role": "system", "content": buildClassifierSystemPrompt(rules, lang)},
            {"role": "user", "content": f"{context}Tool call to judge:\n{action}{tail}"}]


def createPermissionClassifier(
    getContext: Callable[[], ModelContext], request: Callable[[StreamChatOptions], Awaitable[str | None]],
    getRules: Callable[[], AutoModeRules | None], notice: Callable[[str], None],
) -> Classifier:
    runner = createClassifierRunner(notice)

    async def classify(toolName: str, argsJson: str, messages: list[ChatMessage]) -> bool:
        context, rules = getContext(), getRules()

        async def run(model: str) -> bool:
            stages: list[tuple[int, str, dict[str, Any]]] = [
                (64, STAGE1_SUFFIX, {"thinking": {"type": "disabled"}, "temperature": 0, "stop": ["</block>"]}),
                (4096, STAGE2_SUFFIX, {"temperature": 0}),
            ]
            for tokens, suffix, extra in stages:
                text = await request({"baseUrl": context["baseUrl"], "apiKey": context["apiKey"], "provider": context["provider"],
                                      "model": model, "messages": buildClassifierMessages(toolName, argsJson, messages, rules, suffix=suffix),
                                      "maxTokens": tokens, "extra": extra})
                if text is None:
                    raise RuntimeError("权限分类器不可用")
                if parseXmlBlock(text) is False:
                    return True
            return False

        return await runner(context, run)

    return classify
