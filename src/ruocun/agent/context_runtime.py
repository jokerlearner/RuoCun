"""冻结 index.ts 上下文/预算/文字命令控制器（MIT；失败策略见 ADR-0012）。

复用 Session 与已审 Conversation 接缝，不导入主循环，不另建存储。
"""

from __future__ import annotations

import asyncio
import copy
import json
import math
import re
import time
import uuid
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from importlib.resources import files
from typing import Protocol, cast

from ..client.client import buildRequestBody
from ..client.resilient import ResilientContext, ResilientResult, streamChatResilient
from ..client.responses import buildResponsesRequest, usesResponses
from ..client.types import ChatMessage, StreamChatOptions, Usage
from ..config.compat import resolve_env
from ..config.model_selection import getAgentModel
from ..config.profiles import Provider, contextWindowFor
from ..session.cache_audit import CacheAuditSink
from ..session.context_window import parseContextWindow
from ..session.contract import ArchiveDerivation, ArchiveRewrite
from ..session.cost import formatCNY
from ..session.session import Session
from ..tools.todo_store import formatTodos
from ..tools.types import ToolContext
from .compact import buildCompaction, estimateTokens
from .compaction_policy import (
    CompactionBudget,
    estimateRequestTokens,
    resolveCompactionBudget,
)

COMPACT_INSTRUCTION = files("ruocun.agent").joinpath("resources/compact.zh.txt").read_text("utf-8")

Request = Callable[[StreamChatOptions, ResilientContext], ResilientResult]


class ContextJournal(Protocol):
    async def save(self, session: Session) -> None: ...
    async def replace_context(self, session: Session, messages: list[ChatMessage]) -> None: ...
    def redact(self, text: str) -> str: ...


class CompactionFailed(RuntimeError):
    """压缩未成功确认；调用方须保留原上下文并停止本轮。"""


@dataclass(frozen=True)
class PreparedModelContext:
    previous_model: str
    model: str
    messages: list[ChatMessage]
    rewrite: ArchiveRewrite


def _number(value: str | None) -> float:
    """来源 Number(env) 的有限提取，不把 MAX_TURNS 改成新的正整数规则。"""
    if value is None:
        return math.nan
    text = value.strip()
    if not text:
        return 0
    if re.fullmatch(r"0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+", text):
        try:
            return float(int(text, 0))
        except OverflowError:
            return math.inf
    if re.fullmatch(r"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|Infinity)", text):
        return float(text)
    return math.nan


def _numberOr(value: str | None, default: float) -> float:
    number = _number(value)
    return number if number != 0 and not math.isnan(number) else default


def _numberText(number: float) -> str:
    if math.isfinite(number) and number == int(number) and abs(number) < 1e21:
        return str(int(number))
    return str(number).replace("inf", "Infinity").replace("nan", "NaN")


def _formatTokens(number: float) -> str:
    return f"{number:,.3f}".rstrip("0").rstrip(".")


class ContextManager:
    def __init__(
        self, session: Session, journal: ContextJournal, ctx: ToolContext,
        options: StreamChatOptions, env: MutableMapping[str, str], notify: Callable[[str], None], *,
        request: Request | None = None, cache_sink: CacheAuditSink | None = None,
        permission_mode: Callable[[], str] | None = None,
        usage_session: Session | None = None,
    ) -> None:
        self.session, self.journal, self.ctx = session, journal, ctx
        self.options, self.env, self.notify = options, env, notify
        self.cache_sink = cache_sink
        self.permission_mode = permission_mode
        self.usage_session = usage_session if usage_session is not None else session
        self.request = request if request is not None else self._request
        initial = resolve_env("CONTEXT_WINDOW", env)
        self._manually_set = math.isfinite(_number(initial))
        self._window = _numberOr(initial, self._modelWindow())
        self._window_connection = (session.model, options.get("provider"), options.get("baseUrl"))
        budget = _number(resolve_env("MAX_BUDGET", env))
        if math.isfinite(budget) and budget > 0:
            session.budgetCNY = budget
        self.max_turns = _numberOr(resolve_env("MAX_TURNS", env), math.inf)
        self.empty_max_retries = _numberOr(resolve_env("EMPTY_MAX_RETRIES", env), 2)
        self.empty_retry_max_tokens = _numberOr(resolve_env("EMPTY_RETRY_MAX_TOKENS", env), 256000)
        self.budget_hard = resolve_env("MAX_BUDGET_HARD", env) == "1"
        self._cooldown_ms = _numberOr(resolve_env("COMPACT_COOLDOWN_MS", env), 5 * 60_000)
        self._failures = 0
        self._breaker_opened_at = 0.0
        self._last_request: StreamChatOptions | None = None
        self._summary_limit: int | None = None

    def _request(self, options: StreamChatOptions, context: ResilientContext) -> ResilientResult:
        return streamChatResilient(options, env=self.env, context=context)

    def _modelWindow(self) -> float:
        return contextWindowFor(self.session.model, cast(Provider | None, self.options.get("provider")),
                                self.options.get("baseUrl"))

    @property
    def context_window(self) -> float:
        connection = (self.session.model, self.options.get("provider"), self.options.get("baseUrl"))
        if connection != self._window_connection:
            if not self._manually_set:
                self._window = self._modelWindow()
                self.env["RUOCUN_CONTEXT_WINDOW"] = _numberText(self._window)
            self._window_connection = connection
        return self._window

    def should_compact(self) -> bool:
        opts = cast(StreamChatOptions, {**(self._last_request or self.options), "model": self.session.model,
                                      "messages": self.session.messages})
        return self.needs_compaction(opts)

    def prepare_request(self, options: StreamChatOptions, *, remember: bool = True) -> StreamChatOptions:
        """Apply a window-sized default cap to the actual outgoing request."""
        extra = options.get("extra", {})
        explicit = (options.get("maxTokens") is not None or bool(resolve_env("MAX_OUTPUT_TOKENS", self.env))
                    or any(key in extra for key in ("max_tokens", "max_completion_tokens", "max_output_tokens")))
        body = self.request_body(options)
        output = body.get("max_output_tokens", body.get("max_completion_tokens", body.get("max_tokens")))
        if type(output) is not int:
            raise ValueError("output limit must be a positive integer")
        budget = resolveCompactionBudget(int(self.context_window), output,
                                         output_explicit=explicit, env=self.env)
        prepared = cast(StreamChatOptions, dict(options))
        prepared["maxTokens"] = budget.output_limit
        if remember:
            self._last_request = prepared
        return prepared

    def request_body(self, options: StreamChatOptions) -> dict[str, object]:
        """Measure the same Chat/Responses projection that the client sends."""
        routed = usesResponses(options.get("baseUrl", ""), options.get("model", self.session.model))
        body = buildRequestBody(options, env=self.env, use_responses=routed)
        return cast(dict[str, object], buildResponsesRequest(body) if routed else body)

    def needs_compaction(self, options: StreamChatOptions) -> bool:
        prepared = self.prepare_request(options)
        body = self.request_body(prepared)
        budget = self.request_budget(prepared)
        return estimateRequestTokens(body) >= budget.threshold_tokens

    def request_budget(self, options: StreamChatOptions) -> CompactionBudget:
        body = self.request_body(options)
        output = body.get("max_output_tokens", body.get("max_completion_tokens", body.get("max_tokens")))
        return resolveCompactionBudget(int(self.context_window), cast(int, output), env=self.env)

    async def before_request(self, options: StreamChatOptions) -> StreamChatOptions:
        """Qualify the current complete request and require confirmed progress."""
        for _attempt in range(2):
            current = cast(StreamChatOptions, {**options, "messages": copy.deepcopy(self.session.messages)})
            prepared = self.prepare_request(current)
            if not self.needs_compaction(prepared):
                return prepared
            before = estimateRequestTokens(self.request_body(prepared))
            await self.compact(request_options=prepared)
            following = cast(StreamChatOptions, {**prepared, "messages": copy.deepcopy(self.session.messages)})
            if estimateRequestTokens(self.request_body(following)) >= before:
                raise CompactionFailed("上下文超出预算且没有可安全缩小的历史，原文保留；本轮停止。")
        final = self.prepare_request(cast(StreamChatOptions, {**options, "messages": copy.deepcopy(self.session.messages)}))
        if self.needs_compaction(final):
            raise CompactionFailed("有界压缩后上下文仍超出预算，已保存进展；本轮停止。")
        return final

    def _recordUsage(self, usage: Usage | None, model: str, options: StreamChatOptions | None = None) -> None:
        if usage is None:
            return
        self.usage_session.addUsage(usage, model)
        if self.cache_sink is not None:
            redact = self.journal.redact
            body = self.request_body(options) if options is not None else {}
            messages = body.get("messages", body.get("input", []))
            first = messages[0] if isinstance(messages, list) and messages else {}
            system = body.get("instructions", first.get("content", "") if isinstance(first, dict) else "")
            self.cache_sink.record({"agent": "summary", "depth": 0, "turn": 0, "model": model,
                "usage": usage, "sys": redact(system if isinstance(system, str) else str(system)),
                "tools": redact(json.dumps(body.get("tools", []), ensure_ascii=False,
                                           separators=(",", ":"))) if options is not None else "",
                "tail": redact(COMPACT_INSTRUCTION) if options is not None else "",
                "msgs": redact(json.dumps(messages, ensure_ascii=False))})

    def _pinnedTodos(self) -> str | None:
        """A reopened projection may retain only its pin, not the old TodoWrite calls.

        Walk confirmed visible updates in order so an explicit empty list clears
        an older pin. Reading the pin never grants authority or replays a tool.
        """
        if self.ctx.todos:
            return formatTodos(self.ctx.todos)
        pinned = None
        calls: dict[str, str] = {}
        for message in self.session.messages:
            content = message.get("content")
            if (message.get("role") == "system" and isinstance(content, str)
                    and content.startswith("[当前任务清单]\n")):
                pinned = content.partition("\n")[2]
            for call in message.get("tool_calls", []):
                function = call.get("function", {})
                if function.get("name") == "TodoWrite":
                    calls[call["id"]] = function.get("arguments", "")
            if (message.get("role") == "tool" and message.get("tool_call_id") in calls
                    and isinstance(content, str) and not content.startswith("Error:")):
                try:
                    todos = json.loads(calls[message["tool_call_id"]])["todos"]
                    if isinstance(todos, list) and all(isinstance(todo, dict)
                            and todo.get("status") in {"pending", "in_progress", "completed"}
                            and isinstance(todo.get("content"), str) for todo in todos):
                        pinned = formatTodos(todos)
                except (ValueError, TypeError, KeyError):
                    pass
        return pinned

    async def _summarize(self, messages: list[ChatMessage], *,
                         request_options: StreamChatOptions | None = None) -> str:
        # guard 位于摘要回调内；只有system/旧摘要时 compactMessages 仍可直接无操作返回。
        if self._failures >= 3 and time.monotonic() * 1000 - self._breaker_opened_at < self._cooldown_ms:
            raise CompactionFailed("压缩熔断冷却中：连续摘要失败，原上下文已保留；本轮已停止。")
        try:
            summary = await self._requestSummary(messages, request_options=request_options)
        except InterruptedError:
            raise
        except Exception:
            self._failures += 1
            if self._failures >= 3:
                self._breaker_opened_at = time.monotonic() * 1000
            raise
        self._failures = 0
        self._breaker_opened_at = 0
        return summary

    async def _requestSummary(self, messages: list[ChatMessage], *,
                              request_options: StreamChatOptions | None = None) -> str:
        source = request_options if request_options is not None else self.options
        source_model = source.get("model", self.session.model)
        model = getAgentModel(resolve_env("SUMMARY_MODEL", self.env), source_model)
        received_usage: Usage | None = None

        def on_usage(usage: Usage) -> None:
            nonlocal received_usage
            received_usage = usage

        raw_options = copy.deepcopy(dict(source))
        for key in ("onFinishReason", "onEmptyTruncation"):
            raw_options.pop(key, None)
        extra = copy.deepcopy(source.get("extra", {}))
        for key in ("tool_choice", "max_tokens", "max_completion_tokens", "max_output_tokens"):
            extra.pop(key, None)
        if model != source_model:
            # Explicit alternate-model summaries cannot reuse the original model's KV.
            raw_options.pop("tools", None)
            raw_options.pop("parallelToolCalls", None)
            extra = {"thinking": {"type": "disabled"}, "temperature": 0}
        options = cast(StreamChatOptions, {**raw_options, "model": model,
            "messages": [*copy.deepcopy(messages), {"role": "user", "content": COMPACT_INSTRUCTION}],
            "extra": extra, "onUsage": on_usage})
        if self._summary_limit is not None:
            options["maxTokens"] = self._summary_limit
        body = self.request_body(options)
        output_limit = body.get("max_output_tokens", body.get("max_completion_tokens", body.get("max_tokens")))
        window = self.context_window if model == self.session.model else contextWindowFor(
            model, cast(Provider | None, options.get("provider")), options.get("baseUrl"))
        if (type(output_limit) is not int or output_limit <= 0
                or estimateRequestTokens(body) + output_limit >= window):
            raise CompactionFailed("摘要原始前缀超过目标窗口，原上下文已保留；请调整摘要模型或预算。")
        work = asyncio.create_task(asyncio.to_thread(
            self.request, options, ResilientContext(cancel=self.ctx.signal.is_set),
        ))
        try:
            response = await asyncio.shield(work)
        except asyncio.CancelledError as exc:
            # 取消等待不会停止线程；发出取消并等请求归并，保留末尾已收到的用量。
            self.ctx.signal.set()
            try:
                response = await asyncio.shield(work)
            except Exception:
                self._recordUsage(received_usage, model, options)
            else:
                self._recordUsage(received_usage if received_usage is not None else cast(Usage | None, response.usage), model, options)
            raise InterruptedError("上下文压缩已取消，原上下文已保留。") from exc
        except Exception as exc:
            self._recordUsage(received_usage, model, options)
            if self.ctx.signal.is_set():
                raise InterruptedError("上下文压缩已取消，原上下文已保留。") from exc
            raise
        self._recordUsage(received_usage if received_usage is not None else cast(Usage | None, response.usage), model, options)
        if response.cancelled or self.ctx.signal.is_set():
            raise InterruptedError("上下文压缩已取消，原上下文已保留。")
        if (response.status != "complete" or response.error
                or response.finish_reason in {"length", "max_tokens", "max_output_tokens"}):
            raise CompactionFailed("上下文摘要未完成，原上下文已保留；本轮已停止。")
        if (response.message.get("tool_calls") or response.finish_reason == "tool_calls"
                or any(delta.get("kind") == "tool_call" for delta in response.deltas)):
            raise CompactionFailed("上下文摘要返回工具调用，未执行工具；原上下文已保留，本轮停止。")
        output = "".join(str(delta.get("text", "")) for delta in response.deltas if delta.get("kind") == "content").strip()
        if not output:
            content = response.message.get("content")
            output = content if isinstance(content, str) else ""
        match = re.search(r"<摘要>([\s\S]*?)</摘要>", output)
        summary = (match[1] if match else re.sub(r"<分析>[\s\S]*?</分析>", "", output)).strip()
        if not summary:
            # 实现差异：不把来源“(摘要为空)”占位视为可替换原上下文的成功摘要。
            raise CompactionFailed("上下文摘要为空，原上下文已保留；本轮已停止。")
        return summary

    async def recover_overflow(self) -> str:
        return await self.compact(request_options=self._last_request, force=True)

    async def compact(self, *, request_options: StreamChatOptions | None = None, force: bool = False) -> str:
        if self.ctx.signal.is_set():
            raise InterruptedError("上下文压缩已取消，原上下文已保留。")
        before = estimateTokens(self.session.messages)
        original = copy.deepcopy(self.session.messages)
        original_model = self.session.model
        try:
            opts = cast(StreamChatOptions, {**(request_options if request_options is not None else self._last_request or self.options),
                                           "model": self.session.model, "messages": original})
            opts = copy.deepcopy(self.prepare_request(opts))
            budget = self.request_budget(opts)
            self._summary_limit = budget.summary_max_tokens
            namespace = uuid.uuid4().hex
            async def summarize(messages: list[ChatMessage]) -> str:
                return await self._summarize(messages, request_options=opts)
            candidate = await buildCompaction(original, {
                "summarize": summarize, "retainTokens": 0 if force else budget.retain_tokens,
                "thresholdTokens": budget.threshold_tokens, "tools": opts.get("tools", []),
                "measureMessages": lambda items: estimateRequestTokens(self.request_body(
                    cast(StreamChatOptions, {**opts, "messages": items}))),
                "protectedIndices": {index for index, message in enumerate(original)
                    if message.get("role") == "system" and any(marker in str(message.get("content", ""))
                        for marker in ("[[ruocun:background", "[恢复：", "[后台任务数据", "[后台事件", "[任务等待"))},
                "archiveIdForRange": lambda indices, kind: f"{kind}-{namespace}-" + "-".join(map(str, indices[:2])),
            }, self._pinnedTodos())
        except InterruptedError:
            await self._saveOriginal()
            raise
        except Exception as exc:
            await self._saveOriginal()
            if isinstance(exc, CompactionFailed):
                raise
            raise CompactionFailed("上下文压缩失败，原上下文已保留；本轮已停止。") from exc
        if candidate.status != "unchanged":
            if self.session.model != original_model:
                raise CompactionFailed("摘要生成期间模型已变化，旧候选未提交；本轮停止。")
            if self.ctx.signal.is_set():
                await self._saveOriginal()
                raise InterruptedError("上下文压缩已取消，原上下文已保留。")
            try:
                archived = getattr(self.journal, "compact_context", None)
                if archived is None:
                    await self.journal.replace_context(self.session, candidate.messages)
                else:
                    rewrite = ArchiveRewrite("compact", tuple(original), candidate.origins, tuple(
                        ArchiveDerivation(item.archive_id, item.kind, item.new_index, item.old_indices, "context pressure")
                        for item in candidate.replacements))
                    await archived(self.session, candidate.messages, rewrite=rewrite)
            except asyncio.CancelledError as exc:
                raise InterruptedError("压缩保存未确认，原模型上下文保持；本轮已停止。") from exc
            except Exception as exc:
                raise CompactionFailed("压缩保存未确认，原模型上下文保持；本轮已停止。") from exc
        after = estimateTokens(self.session.messages)
        message = (f"[已压缩对话:~{before:,} → ~{after:,} tok]" if after < before else "[对话较短,无需压缩]")
        self.notify(message)
        return message

    async def prepare_model_change(self, options: StreamChatOptions, system_prompt: str) -> PreparedModelContext:
        """Qualify a target connection before publishing its config or changing live context."""
        original = copy.deepcopy(self.session.messages)
        target = Session(system_prompt, options["model"], env=self.env)
        target.messages = [{"role": "system", "content": system_prompt}, *copy.deepcopy(original[1:])]
        target_env = dict(self.env)
        window = (self.context_window if self._manually_set else contextWindowFor(target.model,
                  cast(Provider | None, options.get("provider")), options.get("baseUrl")))
        target_env["RUOCUN_CONTEXT_WINDOW"] = _numberText(window)
        preview = ContextManager(target, self.journal, self.ctx, options, target_env, self.notify,
                                 request=self.request, cache_sink=self.cache_sink, usage_session=self.usage_session)
        opts = preview.prepare_request(cast(StreamChatOptions, {**options, "messages": target.messages}))
        budget = preview.request_budget(opts)
        messages = target.messages
        origins: tuple[int | None, ...] = tuple(range(len(messages)))
        derived: tuple[ArchiveDerivation, ...] = ()
        if preview.needs_compaction(opts):
            preview._summary_limit = budget.summary_max_tokens
            namespace = uuid.uuid4().hex
            async def summarize(messages: list[ChatMessage]) -> str:
                # The target system head is not committed yet. Summarize the
                # actual old transcript so source index 0 still names what was
                # read; publish the new system head only with the final rewrite.
                source_messages = [copy.deepcopy(original[0]), *messages[1:]] if messages else messages
                return await preview._summarize(source_messages, request_options=opts)
            candidate = await buildCompaction(messages, {
                "summarize": summarize, "retainTokens": budget.retain_tokens,
                "thresholdTokens": budget.threshold_tokens,
                "measureMessages": lambda items: estimateRequestTokens(preview.request_body(
                    cast(StreamChatOptions, {**opts, "messages": items}))),
                "protectedIndices": {i for i, message in enumerate(messages) if message.get("role") == "system"
                    and str(message.get("content", "")).startswith(("[后台任务数据", "[恢复：", "[任务等待"))},
                "archiveIdForRange": lambda indices, kind: f"{kind}-{namespace}-" + "-".join(map(str, indices[:2])),
            }, self._pinnedTodos())
            messages, origins = candidate.messages, candidate.origins
            derived = tuple(ArchiveDerivation(item.archive_id, item.kind, item.new_index, item.old_indices,
                                             "target model pressure") for item in candidate.replacements)
            if estimateRequestTokens(preview.request_body(cast(StreamChatOptions, {**opts, "messages": messages}))) >= budget.threshold_tokens:
                raise CompactionFailed("目标模型容量不足或没有可安全压缩区间；当前模型及原文保持。")
        if self.ctx.signal.is_set():
            raise InterruptedError("目标模型检查已取消。")
        mapping = tuple(None if source == 0 and messages[index] != original[0] else source
                        for index, source in enumerate(origins))
        return PreparedModelContext(self.session.model, target.model, messages,
                                    ArchiveRewrite("prefix", tuple(original), mapping, derived, "model change"))

    async def _saveOriginal(self) -> None:
        try:
            await self.journal.save(self.session)
        except (Exception, asyncio.CancelledError) as exc:
            raise CompactionFailed("原上下文保存未确认；本轮已停止，禁止自动重放。") from exc

    def _usageReport(self) -> str:
        usage = self.session.usage
        budget = (f"提醒阈值 {formatCNY(self.session.budgetCNY)}" if self.session.budgetCNY is not None
                  else "未设提醒阈值")
        turns = "不限" if self.max_turns == math.inf else _numberText(self.max_turns)
        policy = "达到预算硬停" if self.budget_hard else "默认提醒不停"
        return (f"累计token（可能含历史）:输入 {usage['promptTokens']} tok(cache 命中 {usage['cacheHitTokens']},"
                f"命中率 {self.session.cacheHitRatio() * 100:.1f}%)· 输出 {usage['completionTokens']} tok\n"
                f"本次进程费用:约 {formatCNY(self.session.costCNY())}（历史费用不完整）\n"
                f"本次进程预算:{budget} · {policy} · 主轮数上限 {turns}")

    def _contextReport(self) -> str:
        used = self.session.lastPromptTokens or 0
        window = self.context_window
        pct = math.floor(used / window * 100 + .5)
        tool_tokens = sum(math.ceil(len(json.dumps(tool, ensure_ascii=False, separators=(",", ":"))
                                        .encode("utf-16-le", errors="surrogatepass")) / 6)
                          for tool in self.options.get("tools", []))
        skill_tokens = sum(max(1, math.floor(len((skill.get("name", "") + skill.get("description", ""))
                                               .encode("utf-16-le", errors="surrogatepass")) / 4 + .5))
                           for skill in self.ctx.skills)
        options = self.prepare_request(cast(StreamChatOptions, {**self.options, "model": self.session.model,
                                                               "messages": self.session.messages}), remember=False)
        budget = self.request_budget(options)
        estimated = estimateRequestTokens(self.request_body(options))
        return (f"上下文用量  {used:,} / {_formatTokens(window)} tok ({pct}%)\n模型: {self.session.model}\n"
                "用量采用上次主模型 API prompt_tokens（尚无统计时为 0）；以下分类为粗估。\n"
                f"  系统提示      ~{estimateTokens(self.session.messages[:1]):,} tok\n"
                f"  工具定义      ~{tool_tokens:,} tok\n"
                f"  技能描述      ~{skill_tokens:,} tok  {len(self.ctx.skills)} 个启用（计入系统提示）\n"
                f"  对话历史      ~{estimateTokens(self.session.messages[1:]):,} tok（含既有摘要）\n"
                f"  当前请求粗估  ~{estimated:,} tok（含最终工具与协议投影）\n"
                f"  实际输出上限  {budget.output_limit:,} tok · 安全余量 {budget.headroom_tokens:,} tok\n"
                f"  剩余空间      {_formatTokens(max(0, window - used))} tok\n"
                f"自动压缩阈值 {budget.threshold_tokens:,} tok；按当前最终请求粗估触发，非精确 tokenizer。")

    async def command(self, line: str) -> str | None:
        parts = line.strip().split()
        if not parts or not parts[0].startswith("/"):
            return None
        name = parts[0][1:]
        arg = parts[1] if len(parts) > 1 else ""
        if name == "compact":
            await self.compact()
            return ""
        if name in {"cost", "usage"}:
            return self.journal.redact(self._usageReport())
        if name == "context":
            return self.journal.redact(self._contextReport())
        if name == "status":
            pct = math.floor((self.session.lastPromptTokens or 0) / self.context_window * 100 + .5)
            effort = resolve_env("REASONING_EFFORT", self.env) or "max"
            mode = self.permission_mode() if self.permission_mode is not None else self.session.mode
            flags = "免审批" if mode == "bypassPermissions" else "—"
            return self.journal.redact(
                f"状态:模型 {self.session.model} · 模式 {mode} · 开关 {flags} · 上下文 {pct}% · 思考 {effort}\n"
                + self._usageReport(),
            )
        if name == "context-window":
            if not arg:
                return (f"当前上下文窗口为 {_formatTokens(self.context_window)} tok。\n"
                        "用 /context-window 设定大小，例如 200K（20 万）或 1M（100 万）。"
                        "纯数字按千 token 解释，例如 500 表示 50 万。")
            previous_window = self._window
            try:
                self._window = parseContextWindow(arg)
                budget = self.request_budget(self.prepare_request(cast(StreamChatOptions,
                    {**self.options, "model": self.session.model, "messages": self.session.messages}), remember=False))
            except ValueError as exc:
                self._window = previous_window
                return self.journal.redact(str(exc))
            self._manually_set = True
            self.env["RUOCUN_CONTEXT_WINDOW"] = _numberText(self._window)
            return (f"上下文窗口已设为 {_formatTokens(self._window)} tok({self._window / 1000:.0f}K),"
                    f"自动压缩阈值 {budget.threshold_tokens:,} tok。立即生效。")
        if name == "effort":
            valid = ("low", "medium", "high", "max")
            current = resolve_env("REASONING_EFFORT", self.env) or "max"
            if not arg:
                return self.journal.redact(f"当前思考强度:{current}。用法:/effort <{'|'.join(valid)}>")
            if arg not in valid:
                return self.journal.redact(f"无效:{arg}(可选 {'/'.join(valid)})")
            self.env["RUOCUN_REASONING_EFFORT"] = arg
            return f"思考强度已设为 {arg}(下一回合生效)"
        return None
