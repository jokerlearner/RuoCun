"""冻结参考 agent/loop.ts 的会话循环（MIT）。

复用已迁移的传输、权限和保存接口，压缩失败遵循 ADR-0012。
"""

from __future__ import annotations

import asyncio
import copy
import json
import math
import re
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, nullcontext
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Protocol, cast

from ..client.resilient import (
    ResilientContext,
    ResilientResult,
    isContextLengthError,
    isRateLimitError,
    isRetryable,
    streamChatResilient,
)
from ..client.types import StreamChatOptions, StreamDelta, Usage
from ..config.compat import resolve_env
from ..obs.backend import getObsMeta
from ..session.cache_audit import cachePrefixFingerprint
from ..session.messages import flushReadImages
from ..session.session import Session
from ..tools.execute import Approval, Registry, looksFailed
from ..tools.registry import ToolRegistry
from ..tools.tool_batch import (
    Authorize,
    BatchAuthorize,
    CallScope,
    ToolJournal,
    UnknownToolOutcome,
    executeToolBatch,
)
from ..tools.types import ToolContext
from .background_runtime import WaitControl, currentWaitControl
from .background_types import WaitHandle
from .progress_advice import createProgressAdvice
from .reflect_prompts import SELF_CHALLENGE_NUDGE
from .turn_health import (
    TurnOutcome,
    assessTurn,
    defaultHealthConfig,
    errSignature,
    initHealth,
)


class Journal(ToolJournal, Protocol):
    async def save(self, session: Session) -> None: ...
    async def replace_context(self, session: Session, messages: list[dict[str, Any]], *, reset_prompt: bool = True) -> None: ...


@dataclass(frozen=True)
class TurnResult:
    status: str
    error: str = ""
    wait: WaitHandle | None = None


Request = Callable[[StreamChatOptions, ResilientContext], ResilientResult]
EMPTY_TRUNCATION_NOTE = files("ruocun.agent").joinpath("resources/empty-truncation.zh.txt").read_text("utf-8")
_FORCED_TOOLS = {"Write", "Edit", "NotebookEdit", "Bash"}
_TRANSIENT_MODEL_FAILURE = re.compile(r"\b5[0-9]{2}\b|overload|timeout|timed out|超时|连接.*失败|网络|非流式", re.I)
_WAIT_ON_RATE_LIMIT = "等待后用当前模型重试"
_STOP_ON_RATE_LIMIT = "中止本轮(稍后可用 /account 切换账号)"
_RATE_LIMIT_STOPPED = "已中止:当前账号触发限流(请求频率/配额超限)。可运行 /account 切换账号后重新发送消息。"


def _retry_setting(name: str, default: float, env: Mapping[str, str]) -> float:
    try:
        value = float(resolve_env(name, env) or 0)
    except ValueError:
        return default
    return value if value and math.isfinite(value) else default


def _request(opts: StreamChatOptions, context: ResilientContext) -> ResilientResult:
    return streamChatResilient(opts, context=context)


def _reject_json_constant(value: str) -> None:
    raise ValueError("JSON不允许NaN或Infinity常量")


def sanitizeHistoryForResume(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """冻结loop.ts的续写清洗：只改坏arguments，保留推理/其它历史字段。"""
    cleaned = []
    for message in messages:
        if message.get("role") != "assistant" or not message.get("tool_calls"):
            cleaned.append(message)
            continue
        updated = copy.deepcopy(message)
        for call in updated["tool_calls"]:
            function = call.get("function", {})
            try:
                json.loads(function.get("arguments") or "{}", parse_constant=_reject_json_constant)
            except (ValueError, TypeError):
                function["arguments"] = "{}"
        cleaned.append(updated)
    return cleaned


def _safe_calls(raw: Any) -> tuple[list[dict[str, Any]], list[tuple[str, str, str]]]:
    """历史中的坏JSON归一为{}，实际校验仍使用原参数（回合循环测试）。"""
    saved: list[dict[str, Any]] = []
    calls: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    if not isinstance(raw, list):
        raise ValueError("模型tool_calls必须为列表")
    for call in raw:
        if not isinstance(call, dict) or not isinstance(call.get("function"), dict):
            raise ValueError("模型工具调用格式无效")
        fn = call["function"]
        call_id, name, args = call.get("id"), fn.get("name"), fn.get("arguments", "")
        if (not isinstance(call_id, str) or not call_id or not isinstance(name, str)
                or not name or not isinstance(args, str)):
            raise ValueError("模型工具调用缺少id、名称或JSON字符串参数")
        if call_id in seen:
            raise ValueError("同一模型回答出现重复工具调用id")
        seen.add(call_id)
        normalized = args
        try:
            json.loads(args, parse_constant=_reject_json_constant)
        except ValueError:
            normalized = "{}"
        saved.append({"id": call_id, "type": "function", "function": {
            "name": name, "arguments": normalized,
        }})
        calls.append((call_id, name, args))
    return saved, calls


async def run_turn(
    session: Session, options: StreamChatOptions, registry: Registry, ctx: ToolContext, *,
    approve: Approval, request: Request = _request, journal: Journal | None = None,
    on_delta: Callable[[StreamDelta], None] | None = None,
    on_boundary: Callable[[], Awaitable[None]] | None = None,
    on_tool_boundary: Callable[[], Awaitable[None]] | None = None,
    on_tool_result: Callable[[str, str], None] | None = None,
    on_assistant_saved: Callable[[dict[str, Any]], None] | None = None,
    on_tool_message: Callable[[dict[str, Any], dict[str, Any]], None] | None = None,
    accepts_delta: Callable[[], bool] | None = None,
    authorize: Authorize | None = None, authorize_batch: BatchAuthorize | None = None,
    call_scope: CallScope | None = None,
    permission_mode: Callable[[], str] | None = None,
    api_tools: Callable[[], list[dict[str, Any]]] | None = None,
    compact: Callable[[], Awaitable[Any]] | None = None,
    should_compact: Callable[[], bool] | None = None,
    request_preflight: Callable[[StreamChatOptions], Awaitable[StreamChatOptions]] | None = None,
    wait_control: WaitControl | None = None,
    tool_batch_scope: AbstractAsyncContextManager[None] | None = None,
    max_turns: float = float("inf"), budget_hard: bool = False,
    notice: Callable[[str], None] | None = None,
    reasoning_effort: str = "max", empty_max_retries: float = 2,
    empty_retry_max_tokens: float = 256000,
    model_recovery_env: Mapping[str, str] | None = None,
    list_other_accounts: Callable[[], Sequence[str]] | None = None,
    switch_account_and_wait: Callable[[str], Awaitable[bool]] | None = None,
    on_model_unavailable: Callable[[], Awaitable[None]] | None = None,
    reflect: Callable[[str], Awaitable[str | None]] | None = None,
    self_challenge: bool = False, long_task: bool = False,
    progress_advice: bool = False, interactive: bool = True,
    has_running_background: Callable[[], bool] | None = None,
) -> TurnResult:
    """用户消息先由组合入口保存；所有副作用在已提交intent之后开始。"""
    wait_control = (wait_control or currentWaitControl()) if ctx.subagentDepth == 0 else None
    empty = 0
    turns = 0
    context_retries = 0
    boundary = True
    budget_warned = False
    retry_reasoning = False
    forcing_unsupported = False
    generic_retried = False
    rate_retries = 0
    recovery_env = model_recovery_env if model_recovery_env is not None else {}
    health, health_cfg = initHealth(), defaultHealthConfig(recovery_env)
    progress = createProgressAdvice(recovery_env)
    foreground = ctx.subagentDepth == 0 and not options.get("background")
    ctx.sessionModel = session.model
    ctx.forkToolSnapshot = None
    event_loop = asyncio.get_running_loop()
    active_request: object | None = None

    async def save() -> None:
        if journal is not None:
            try:
                await journal.save(session)
            except BaseException:
                if wait_control is not None and not wait_control.runtime.checkpointUnknown:
                    if wait_control.pending and session.messages and session.messages[-1].get("role") == "tool":
                        session.messages[-1]["content"] = "Error: 等待状态保存失败,未激活等待;后台结果仍待投递。"
                    wait_control.rollback()
                raise

    async def compress() -> TurnResult | None:
        assert compact is not None
        original = copy.deepcopy(session.messages)
        try:
            await compact()
        except InterruptedError:
            return TurnResult("cancelled", "压缩已取消，原上下文保留。")
        except Exception:
            # ADR-0012：异常不硬截断、不进入下一次请求或工具派发。
            return TurnResult("compaction_failed", "摘要未确认，原上下文保留；本轮已停止，可修复后重试。")
        if ctx.signal.is_set():
            return TurnResult("cancelled", "本轮已取消。")
        if session.messages == original:
            return TurnResult("compaction_failed", "没有可安全缩小的历史，原文保留；本轮停止。")
        return None

    async def retry_delay(ms: float) -> TurnResult | None:
        deadline = event_loop.time() + max(0, ms) / 1000
        while not ctx.signal.is_set():
            remaining = deadline - event_loop.time()
            if remaining <= 0:
                return None
            await asyncio.sleep(min(remaining, .05))
        return TurnResult("cancelled", "本轮已取消。")

    async def recover_rate_limit() -> TurnResult | None:
        nonlocal rate_retries
        await save()
        if ctx.signal.is_set():
            return TurnResult("cancelled", "本轮已取消。")
        if ctx.askChoice is not None:
            accounts = ({f"切到账号「{name}」重试": name for name in list_other_accounts()}
                        if list_other_accounts is not None and switch_account_and_wait is not None else {})
            choice = await ctx.askChoice("当前账号触发限流(请求频率/配额超限)。接下来怎么办?",
                                         [_WAIT_ON_RATE_LIMIT, *accounts, _STOP_ON_RATE_LIMIT])
            if ctx.signal.is_set():
                return TurnResult("cancelled", "本轮已取消。")
            if choice in accounts and switch_account_and_wait is not None:
                target = accounts[choice]
                try:
                    switched = await switch_account_and_wait(target)
                except Exception:
                    # The confirmed configuration may already have changed. Do not resend.
                    return TurnResult("failed", "限流时切换账号的结果未确认，原现场已保留；本轮已停止。")
                if ctx.signal.is_set():
                    return TurnResult("cancelled", "本轮已取消。")
                if switched:
                    if notice is not None:
                        notice(f"[已切换到账号「{target}」,继续重试…]")
                    return None
                if notice is not None:
                    notice(f"[切换到账号「{target}」失败,仍在原账号]")
                return TurnResult("failed", _RATE_LIMIT_STOPPED)
            if choice != _WAIT_ON_RATE_LIMIT:
                return TurnResult("failed", _RATE_LIMIT_STOPPED)
        elif rate_retries >= _retry_setting("RATE_LIMIT_MAX_RETRIES", 5, recovery_env):
            return TurnResult("failed", _RATE_LIMIT_STOPPED)
        rate_retries += 1
        ms = min(_retry_setting("RATE_LIMIT_WAIT_MS", 5000, recovery_env) * rate_retries, 30000)
        if notice is not None:
            notice(f"[限流,等待 {max(0, ms) / 1000:g}s 后用当前模型重试…]")
        return await retry_delay(ms)

    async def recover_unavailable() -> TurnResult | None:
        nonlocal generic_retried
        if not generic_retried:
            generic_retried = True
            await save()
            if notice is not None:
                notice("[请求失败(疑似过载/超时/网络问题),用当前模型重试一次…]")
            return await retry_delay(_retry_setting("HARD_RETRY_DELAY_MS", 1000, recovery_env))
        end = ("已停止本轮，已有进展、对话上下文和任务清单均已保留；可稍后重新发送消息继续，或用 /account 切换账号。"
               if ctx.askChoice is not None else "本次运行到此结束，已保留的上下文和任务清单不受影响。")
        note = "模型请求持续失败(疑似过载/超时/网络问题),重试一次仍未恢复。" + end
        assistant = {"role": "assistant", "content": note}
        session.messages.append(assistant)
        await save()
        if on_assistant_saved is not None:
            on_assistant_saved(assistant)
        if on_model_unavailable is not None and not ctx.signal.is_set():
            try:
                await on_model_unavailable()
            except Exception:
                return TurnResult("model_unavailable", note + "后台停止结果未确认，请查看任务状态。")
        return TurnResult("model_unavailable", note)

    while not ctx.signal.is_set():
        if boundary:
            if turns >= max_turns:
                await save()
                return TurnResult("turn_limit", "已达最大轮数，记录已保存。")
            if session.overBudget():
                if not budget_warned and notice:
                    notice(f"[成本提醒] 本次进程费用约 ¥{session.costCNY():.2f}，已达阈值 ¥{session.budgetCNY}。")
                budget_warned = True
                if budget_hard:
                    await save()
                    return TurnResult("budget_limit", "已达显式硬预算上限，本轮停止。")
            if turns > 0 and compact and should_compact and should_compact():
                if notice:
                    notice("[轮内接近上下文上限，自动压缩…]")
                stopped = await compress()
                if stopped:
                    return stopped
            if on_boundary is not None:
                await on_boundary()
                if ctx.signal.is_set():
                    break
            boundary = False
        opts = cast(StreamChatOptions, dict(options))
        opts["model"] = session.model
        opts["messages"] = copy.deepcopy(session.messages)
        opts["tools"] = api_tools() if api_tools is not None else registry.toApiTools()
        if opts["tools"]:
            opts["parallelToolCalls"] = True
        opts["extra"] = {**options.get("extra", {}), "reasoning_effort": reasoning_effort}
        forced = retry_reasoning and not forcing_unsupported
        if retry_reasoning:
            opts["extra"]["reasoning_effort"] = "low"
            opts["maxTokens"] = cast(int, empty_retry_max_tokens)
            if forced:
                productive = [tool for tool in opts["tools"] if tool["function"]["name"] in _FORCED_TOOLS]
                opts["tools"] = productive or opts["tools"]
                opts["extra"]["tool_choice"] = "required"
        if request_preflight is not None:
            try:
                opts = await request_preflight(opts)
            except InterruptedError:
                return TurnResult("cancelled", "上下文检查已取消，原文保留。")
            except Exception as preflight_error:
                return TurnResult("compaction_failed", f"上下文检查未完成，原文保留；本轮停止。{preflight_error}")
            if ctx.signal.is_set():
                return TurnResult("cancelled", "本轮已取消。")
        if (ctx.subagentDepth == 0 and isinstance(registry, ToolRegistry)
                and (ctx.runAgent is not None or ctx.launchAgent is not None)):
            ctx.forkToolSnapshot = registry.forkSnapshot(opts["tools"])
        empty_truncation = False

        def on_empty_truncation() -> None:
            nonlocal empty_truncation
            empty_truncation = True

        opts["onEmptyTruncation"] = on_empty_truncation
        session.lastSentLength = len(session.messages)
        system = opts["messages"][0].get("content") if opts["messages"] else ""
        tools_raw = json.dumps(opts["tools"], ensure_ascii=False, separators=(",", ":"))
        session.notePrefix(cachePrefixFingerprint(opts["model"], system if isinstance(system, str) else "", tools_raw))
        token = object()
        active_request = token

        exposed = False
        streamed_text: list[str] = []

        def receive_delta(value: StreamDelta, request_token: object = token) -> None:
            nonlocal exposed
            if value.get("kind") in {"content", "reasoning", "tool_call"}:
                exposed = True
            if value.get("kind") == "content" and isinstance(value.get("text"), str):
                streamed_text.append(value["text"])
            if on_delta is None:
                return

            def deliver() -> None:
                if (active_request is request_token and not ctx.signal.is_set()
                        and (accepts_delta is None or accepts_delta())):
                    on_delta(value)
            try:
                event_loop.call_soon_threadsafe(deliver)
            except RuntimeError:
                # 已关闭的业务loop不再消费迟到展示事件；可信结果由完成口处理。
                pass

        request_error: Exception | None = None
        try:
            if wait_control is not None:
                wait_control.runtime.modelRequested()
            response = await asyncio.to_thread(
                request, opts, ResilientContext(cancel=ctx.signal.is_set, on_delta=receive_delta),
            )
        except Exception as exc:
            request_error, response = exc, None
        finally:
            active_request = None
        if response is not None and response.usage:
            session.addUsage(cast(Usage, response.usage), opts["model"])
            if ctx.cacheAudit is not None:
                redact = ctx.auditRedact or str
                identity = getObsMeta()
                record = {"agent": "sub" if ctx.subagentDepth else "main", "depth": ctx.subagentDepth,
                    "turn": turns, "model": opts["model"], "usage": cast(Usage, response.usage),
                    "sys": redact(system if isinstance(system, str) else ""), "tools": redact(tools_raw), "tail": ""}
                if ctx.subagentDepth:
                    record["subId"] = identity.get("runId", "")
                else:
                    record["msgs"] = redact(json.dumps(opts["messages"], ensure_ascii=False))
                try:
                    ctx.cacheAudit.record(cast(Any, record))
                except Exception:
                    pass  # Observation cannot alter the model result or tool dispatch.
        message = copy.deepcopy(response.message) if response is not None else {}
        content = message.get("content") or "".join(streamed_text)
        if ctx.signal.is_set() or response is not None and response.cancelled:
            if content:
                # 部分文字保留，但取消时绝不执行已收集的工具。
                session.messages.append({"role": "assistant", "content": content})
            await save()
            return TurnResult("cancelled", "本轮已取消。")
        if response is None or response.status != "complete":
            failure = (response.error or "模型回答未完成，工具未执行。" if response is not None
                       else f"模型请求失败：{type(request_error).__name__}")
            if (exposed or content or message.get("tool_calls") or
                    response is not None and (response.status == "partial" or response.deltas)):
                if content:
                    session.messages.append({"role": "assistant", "content": content})
                await save()
                return TurnResult("failed", failure)
            error = request_error or (response.error_exception if response is not None else None) or RuntimeError(failure)
            status = response.error_status if response is not None else getattr(error, "status", None)
            if isContextLengthError(error) or isContextLengthError(RuntimeError(failure)):
                await save()
                if compact and context_retries < 2:
                    context_retries += 1
                    stopped = await compress()
                    if stopped:
                        return stopped
                    continue
                return TurnResult("context_limit", "上下文仍达模型上限，记录已保留；请调整窗口或启动新会话。")
            if foreground and (status == 429 or isRateLimitError(error)):
                stopped = await recover_rate_limit()
                if stopped is not None:
                    return stopped
                continue
            if foreground and (isRetryable(error) or _TRANSIENT_MODEL_FAILURE.search(f"{type(error).__name__} {error}")
                               or isinstance(status, int) and 500 <= status <= 599):
                stopped = await recover_unavailable()
                if stopped is not None:
                    return stopped
                continue
            if forced:
                forcing_unsupported = True
                if notice:
                    notice("[服务端不接受强制工具调用，回退成普通重试…]")
                continue
            await save()
            return TurnResult("failed", failure)
        generic_retried, rate_retries = False, 0
        try:
            saved_calls, calls = _safe_calls(message.get("tool_calls", []))
        except ValueError as exc:
            await save()
            return TurnResult("failed", str(exc))
        if not (isinstance(content, str) and content.strip()) and not calls:
            empty += 1
            if empty > empty_max_retries:
                await save()
                return TurnResult("failed", "模型连续返回空回答，已停止本轮。")
            retry_reasoning = empty_truncation
            forcing_unsupported = False
            if retry_reasoning:
                session.messages.append({"role": "system", "content": EMPTY_TRUNCATION_NOTE})
                await save()
                if notice:
                    notice("[思考耗尽输出预算，提示收敛后重试…]")
            continue
        empty = 0
        retry_reasoning = False
        forcing_unsupported = False
        context_retries = 0
        # 来源sanitizeForHistory保留完整assistant，包括Chat reasoningContent和
        # Responses encrypted reasoning现场；重建role/content会破坏后续工具回合。
        assistant: dict[str, Any] = message
        assistant["role"] = "assistant"
        assistant["content"] = content
        if saved_calls:
            assistant["tool_calls"] = saved_calls
        session.messages.append(assistant)
        await save()
        if on_assistant_saved is not None:
            on_assistant_saved(assistant)
        if not calls:
            return TurnResult("complete")

        try:
            async with tool_batch_scope if tool_batch_scope is not None else nullcontext():
                batch = await executeToolBatch(
                    calls, registry, ctx, approve=approve, journal=journal, authorize=authorize,
                    authorize_batch=authorize_batch, call_scope=call_scope, permission_mode=permission_mode,
                )
        except UnknownToolOutcome as exc:
            return TurnResult("outcome_unknown", str(exc))
        session.messages.extend(batch.messages)
        if wait_control is not None and wait_control.pending and journal is None:
            wait_control.rollback()
            return TurnResult("failed", "TaskWait 需要会话保存接口。")
        await save()
        if on_tool_message is not None:
            saved_by_id = {call["id"]: call for call in saved_calls}
            for tool_message in batch.messages:
                on_tool_message(saved_by_id[tool_message["tool_call_id"]], tool_message)
        if on_tool_result is not None:
            names = {call_id: name for call_id, name, raw in calls}
            for tool_message in batch.messages:
                on_tool_result(names[tool_message["tool_call_id"]], tool_message["content"])
        if batch.approval_incomplete:
            return TurnResult("failed", "权限确认未完成，现场已保存，本轮已停止。")
        if wait_control is not None and wait_control.pending:
            if ctx.signal.is_set():
                wait_control.rollback()
                return TurnResult("cancelled", "本轮已取消。")
            handle = wait_control.commit()
            if handle is not None:
                return TurnResult("waiting", wait=handle)
        projected = flushReadImages(session.messages)
        if projected is not session.messages:
            if journal is None:
                session.messages = projected
            else:
                await journal.replace_context(session, projected, reset_prompt=False)
        if on_tool_boundary is not None and not ctx.signal.is_set():
            # 在已配对、图片投影也已提交后发布工具批产生的会话状态。
            await on_tool_boundary()
        batch_names = [name for _, name, _ in calls]
        running_background = has_running_background() if has_running_background is not None else False
        advice = progress.step(batch_names, runningBackground=running_background, interactive=interactive, enabled=progress_advice)
        if advice and not ctx.signal.is_set():
            messages = [*session.messages, {"role": "system", "content": advice}]
            if journal is None:
                session.messages = messages
            else:
                await journal.replace_context(session, messages, reset_prompt=False)
            if progress.notice and notice:
                notice(progress.notice)
        if (reflect is not None or self_challenge) and not ctx.signal.is_set():
            failures = [m["content"] for m in batch.messages if looksFailed(m["content"])]
            progressed = any(name in _FORCED_TOOLS for name in batch_names) or bool(batch_names and running_background and all(
                name in {"BashOutput", "TaskOutput", "TaskGet", "TaskList"} for name in batch_names))
            outcome: TurnOutcome = {"progressed": progressed,
                                    "toolFailures": len(failures)}
            if failures:
                outcome["errSig"] = errSignature(failures[-1])
            decision = assessTurn(health, outcome, health_cfg, {"longTask": long_task})
            health = decision["next"]
            advice = ""
            if reflect is not None and (decision["challenger"] or decision["refocuser"]):
                label = "审视者" if decision["challenger"] else "纠偏者"
                if notice:
                    notice(f"[反思：{label}…]")
                verdict = await reflect("challenger" if decision["challenger"] else "refocuser")
                if verdict and not ctx.signal.is_set():
                    advice = f"[{label}]\n{verdict}"
            elif self_challenge and decision["challenger"]:
                advice = SELF_CHALLENGE_NUDGE
            if advice:
                messages = [*session.messages, {"role": "system", "content": advice}]
                if journal is None:
                    session.messages = messages
                else:
                    await journal.replace_context(session, messages, reset_prompt=False)
        if turns == max_turns - 5 and notice:
            notice(f"[轮数提醒：接近最大轮数 {turns + 1}/{max_turns:g}]")
        turns += 1
        boundary = True
    return TurnResult("cancelled", "本轮已取消。")
