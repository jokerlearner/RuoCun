"""把前台会话接到存储线程，协调用户输入、模型上下文和后台事件的提交。

新的内存状态在数据库提交确认后生效。恢复时复用已保存的结果补齐消息，不自动重放工具调用。
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import re
import uuid
from collections.abc import Sequence
from contextvars import ContextVar
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

from ..client.types import ImageData
from .contract import (
    AcceptedInput,
    ArchiveImport,
    ArchiveRewrite,
    Checkpoint,
    Intent,
    OutboxEvent,
    RecoveryDecision,
    RecoveryReceipt,
    RecoveryView,
    RunRecord,
    RunRef,
    RuntimeRecord,
    ToolRef,
    ToolResult,
)
from .inputs import modelInput, originalInput, packQueuedInput
from .messages import flushReadImages
from .session import Session
from .storage_worker import StorageWorker

if TYPE_CHECKING:
    from ..agent.background_runtime import BackgroundRuntime


class Conversation:
    def __init__(self, worker: StorageWorker, session_id: str, secret: str) -> None:
        self.worker = worker
        self.session_id = session_id
        self.secret = secret
        self._known_secrets = {secret} if secret else set()
        self.revision = 0
        self.owner_epoch = 0
        self.blocked = False
        self.historical_usage = False
        self._accepted_inputs: tuple[AcceptedInput, ...] = ()
        self._title = "RuoCun"
        self._task_title: str | None = None
        self.reflection_state: dict[str, Any] | None = None
        self.foreground_state = "idle"
        self._checkpoint_lock = asyncio.Lock()
        self.agent_tool_batches = asyncio.Lock()
        self.policy_version = "mvp-adr11"
        self.approval_ref: str | None = None
        self._current_tool: ContextVar[ToolRef | None] = ContextVar("current_shell_tool", default=None)
        self._shell_refs: dict[ToolRef, RunRef] = {}
        self._background: BackgroundRuntime | None = None
        self._saved_background: dict[str, Any] | None = None
        self.directory = Path(".")

    def remember_secret(self, secret: str) -> None:
        """只在本进程内保留显式提供的密钥，用于后续脱敏。密钥本身不序列化。"""
        if secret:
            self._known_secrets.add(secret)

    def redact(self, text: str) -> str:
        known = self._known_secrets | ({self.secret} if self.secret else set())
        if not known:
            return text
        pattern = "|".join(re.escape(key) for key in sorted(known, key=lambda key: (-len(key), key)))
        return re.sub(pattern, "[REDACTED]", text)

    def _safe(self, value: Any) -> Any:
        if isinstance(value, str):
            return self.redact(value)
        if isinstance(value, list):
            return [self._safe(v) for v in value]
        if isinstance(value, dict):
            image = value.get("imageData")
            opaque_image = (
                value.get("role") == "tool" and isinstance(value.get("tool_call_id"), str)
                and isinstance(value.get("content"), str) and isinstance(image, dict)
                and set(image) == {"base64", "mediaType"}
                and isinstance(image["base64"], str) and isinstance(image["mediaType"], str)
                and re.fullmatch(r"image/[A-Za-z0-9][A-Za-z0-9.+-]*", image["mediaType"]) is not None
            )
            image_url = value.get("image_url")
            inline_image = (
                value.get("type") == "image_url" and isinstance(image_url, dict)
                and isinstance(image_url.get("url"), str)
                and re.fullmatch(r"data:image/[A-Za-z0-9][A-Za-z0-9.+-]*;base64,[A-Za-z0-9+/]*={0,2}",
                                 image_url["url"]) is not None
            )
            saved: dict[str, Any] = {}
            for key, child in value.items():
                if key == "imageData" and opaque_image:
                    # 即使图像字节碰巧包含待脱敏的子串，仍应保持原始内容。
                    saved[key] = copy.deepcopy(child)
                elif key == "image_url" and inline_image:
                    saved[key] = {name: copy.deepcopy(item) if name == "url" else self._safe(item)
                                  for name, item in child.items()}
                else:
                    saved[key] = self._safe(child)
            return saved
        return value

    def redacted_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._safe(message) for message in messages]

    @classmethod
    async def open(
        cls, directory: Path, session_id: str, cwd: Path, runtime: RuntimeRecord,
        session: Session, secret: str, *, resume: bool, archive_import: ArchiveImport | None = None,
    ) -> Conversation:
        if resume and not (directory / "session.db").is_file():
            raise ValueError("指定会话不存在，不能恢复为空会话。")
        worker = StorageWorker.open(directory, session_id, cwd, runtime)
        obj = cls(worker, session_id, secret)
        obj.directory = directory.resolve()
        try:
            view = await worker.load_recovery_view()
            obj.owner_epoch = view.owner.owner_epoch
            if view.checkpoint is not None:
                checkpoint = view.checkpoint
                obj.revision = checkpoint.revision
                obj._saved_background = copy.deepcopy(checkpoint.background)
                obj._accepted_inputs = checkpoint.accepted_inputs
                obj._title = checkpoint.title
                from .log import firstUserExcerpt
                obj._task_title = checkpoint.task_title or firstUserExcerpt(checkpoint.messages)
                obj.reflection_state = copy.deepcopy(checkpoint.reflection_state)
                session.messages = copy.deepcopy(list(checkpoint.messages))
                session.model = checkpoint.model
                session.mode = "plan" if checkpoint.mode == "plan" else "normal"
                obj.foreground_state = {"foreground-only": "idle", "running": "paused",
                                        "closed": "idle"}.get(checkpoint.background_state,
                                                              checkpoint.background_state)
                # 恢复历史总用量。分模型费用只能从当前进程重新累计。
                for key in session.usage:
                    session.usage[key] = checkpoint.usage.get(key, 0)  # type: ignore[literal-required]
                obj.historical_usage = any(session.usage.values())
            elif resume:
                raise ValueError("会话没有可信保存点，拒绝恢复。")
            await obj._restore_tool_pairs(session, view, archive_import=archive_import)
            return obj
        except BaseException:
            await worker.close()
            raise

    async def _restore_tool_pairs(self, session: Session, view: RecoveryView, *,
                                  archive_import: ArchiveImport | None = None) -> None:
        self._shell_refs = {record.tool_ref: record.intent.run_ref for record in view.tool_records
                            if record.name == "Bash" and record.intent is not None}
        self.blocked = bool(view.missing_attachments or (view.pending_events and not (self._background and self._background.materialsVerified))
                           or any(run.status == "unknown" for run in view.runs)
                           or any(rec.state != "result_committed" for rec in view.tool_records))
        if not self.blocked:
            # 工具结果已经提交而检查点缺少结果消息时，补齐消息配对即可复用结果。
            from .recovery import repairToolPairs
            messages = repairToolPairs(session.messages, view.tool_records)
            # 工具消息已配对时仍需检查图像投递标记，范围限于当前模型上下文。
            candidate = flushReadImages(messages)
            await self._commit(session, candidate, self._accepted_inputs, archive_import=archive_import)
            session.messages = candidate

    async def commit_recovery(self, session: Session, decision: RecoveryDecision) -> RecoveryReceipt:
        """会话被未决结果阻挡时，只有恢复入口允许写入。决定和对话历史一起提交。"""
        async with self._checkpoint_lock:
            if self._safe(asdict(decision)) != asdict(decision):
                raise ValueError("恢复说明含账户凭据，请移除后重试。")
            view = await self.worker.load_recovery_view()
            if view.checkpoint is None:
                raise ValueError("没有可信保存点，拒绝恢复决定。")
            checkpoint = replace(view.checkpoint, messages=tuple(self._safe(session.messages)))
            handle = self.worker.enqueue_recovery(decision, self.revision, checkpoint)
            try:
                receipt = await handle.wait()
            except BaseException:
                if handle.status().state != "failed":
                    self.blocked = True
                raise
            saved = await self.worker.load_recovery_view()
            if saved.checkpoint is None:
                self.blocked = True
                raise RuntimeError("恢复决定已提交但保存点无法读取，保留现场。")
            self.revision = saved.checkpoint.revision
            session.messages = copy.deepcopy(list(saved.checkpoint.messages))
            return receipt

    async def refresh_recovery(self, session: Session) -> None:
        await self._restore_tool_pairs(session, await self.worker.load_recovery_view())

    async def save(self, session: Session) -> None:
        async with self._checkpoint_lock:
            await self._commit(session, session.messages, self._accepted_inputs)

    async def set_reflection_state(self, session: Session, state: dict[str, Any] | None, *,
                                   advisories: Sequence[str] = ()) -> None:
        async with self._checkpoint_lock:
            self._require_paired(session)
            messages = [*session.messages, *({"role": "system", "content": text} for text in advisories)]
            await self._commit(session, messages, self._accepted_inputs,
                               reflection=state, update_reflection=True)
            session.messages = messages

    def queued_inputs(self) -> tuple[AcceptedInput, ...]:
        return tuple(item for item in self._accepted_inputs if item.state == "queued")

    def _input(self, content: str | list[dict[str, Any]], *, queued: bool,
               model_content: str | list[dict[str, Any]] | None = None) -> AcceptedInput:
        seq = max((item.seq for item in self._accepted_inputs), default=0) + 1
        return AcceptedInput(str(uuid.uuid4()), seq,
                             packQueuedInput(self._safe(content), model_content) if queued else
                             json.dumps(self._safe(content), ensure_ascii=False), (),
                             "queued" if queued else "consumed")

    async def queue_user(self, session: Session, content: str | list[dict[str, Any]], *,
                         model_content: str | list[dict[str, Any]] | None = None) -> AcceptedInput:
        """把排队输入的身份和当前检查点一起提交，确认后才返回接纳回执。"""
        async with self._checkpoint_lock:
            if self._safe(content) != content or self._safe(model_content) != model_content:
                raise ValueError("此输入含当前账户凭据，无法完整保存；未接纳排队，请保留原输入并移除凭据后重试。")
            item = self._input(content, queued=True, model_content=model_content)
            await self._commit(session, session.messages, (*self._accepted_inputs, item))
            return item

    async def consume_user(
        self, session: Session, input_id: str, *,
        model_content: str | list[dict[str, Any]] | None = None, rejected: bool = False,
        hook_context: str = "",
    ) -> bool:
        """在调度器安全边界消费排队输入，待在途请求结束后再更新模型上下文。"""
        async with self._checkpoint_lock:
            item = next((entry for entry in self._accepted_inputs if entry.input_id == input_id), None)
            if item is None:
                raise ValueError("没有已确认的排队输入身份。")
            if item.state != "queued":
                return False
            if self.queued_inputs()[0].input_id != input_id:
                raise ValueError("必须按已确认输入序号消费。")
            messages = session.messages
            if not rejected:
                self._require_paired(session)
                projected = modelInput(item.payload) if model_content is None else model_content
                if self._safe(projected) != projected:
                    raise ValueError("模型输入无法完整保存，保留排队原文，停止本次消费。")
                messages = [*messages, {"role": "user", "content": copy.deepcopy(projected)}]
                if hook_context:
                    messages.append({"role": "system", "content": self.redact(hook_context)})
            replacement = replace(item, state="discarded" if rejected else "consumed",
                                  payload=item.payload if rejected else packQueuedInput(originalInput(item.payload)))
            updated = tuple(replacement if entry.input_id == input_id else entry for entry in self._accepted_inputs)
            await self._commit(session, messages, updated)
            session.messages = messages
            return not rejected

    async def discard_queued(self, session: Session, *, state: str = "paused") -> None:
        async with self._checkpoint_lock:
            updated = tuple(replace(item, state="discarded") if item.state == "queued" else item
                            for item in self._accepted_inputs)
            await self._commit(session, session.messages, updated, state=state)

    async def set_foreground_state(self, session: Session, state: str) -> None:
        async with self._checkpoint_lock:
            await self._commit(session, session.messages, self._accepted_inputs, state=state)

    async def accept_user(
        self, session: Session, content: str | list[dict[str, Any]], *,
        model_content: str | list[dict[str, Any]] | None = None,
    ) -> None:
        """提交确认后接受用户输入。输入账本保留的身份独立于可以压缩的模型上下文。"""
        async with self._checkpoint_lock:
            item = self._input(content, queued=False)
            # 手动调用 Skill 时同时保留用户输入的原命令与发给模型的 Skill 正文。
            projected = content if model_content is None else model_content
            messages = [*session.messages, {"role": "user", "content": copy.deepcopy(projected)}]
            await self._commit(session, messages, (*self._accepted_inputs, item))
            session.messages = messages

    async def replace_context(
        self, session: Session, messages: list[dict[str, Any]], *, reset_prompt: bool = True,
    ) -> None:
        """持久提交成功后更新模型上下文。批末注入图片时可沿用当前主请求的用量。"""
        async with self._checkpoint_lock:
            if (not messages or not session.messages or messages[0].get("role") != "system"
                    or reset_prompt and messages[0] != session.messages[0]):
                raise ValueError("压缩须保留当前系统前缀。")
            self._require_paired(session)
            original = session.messages
            candidate = copy.deepcopy(messages)
            rewrite = self._context_rewrite(session.messages, messages)
            await self._commit(session, candidate, self._accepted_inputs, archive_rewrite=rewrite)
            # 追加事实消息后仍保留已存在的用户消息对象，
            # 进程内代码回退检查点仍凭这些对象定位。
            session.messages = ([*original, *candidate[len(original):]]
                                if len(candidate) >= len(original) and candidate[:len(original)] == original else candidate)
            if reset_prompt:
                session.lastPromptTokens = None
                session.lastSentLength = 0

    @staticmethod
    def _context_rewrite(original: list[dict[str, Any]], messages: list[dict[str, Any]]) -> ArchiveRewrite | None:
        """为已核验的上下文修改保留消息位置和对象身份，文字相同的消息各自记录。"""
        if len(messages) >= len(original) and messages[:len(original)] == original:
            return None
        expected = copy.deepcopy(original)
        positions = {id(message): index for index, message in enumerate(original)}
        mapping: list[int | None] = []
        metadata = {"imageDelivered", "responseItems", "reasoning_content", "reasoning_details"}
        for index, message in enumerate(messages):
            source = positions.get(id(message))
            if source is None and index < len(original):
                left = {k: v for k, v in original[index].items() if k not in metadata}
                right = {k: v for k, v in message.items() if k not in metadata}
                if left == right:
                    source = index
                    expected[index] = copy.deepcopy(message)
            if source is not None:
                mapping.append(source)
            elif message.get("role") == "system":
                mapping.append(None)
            else:
                mapping.append(len(expected))
                expected.append(copy.deepcopy(message))
        kind: Literal["rewind", "prefix"] = "rewind" if messages == original[:len(messages)] else "prefix"
        return ArchiveRewrite(kind, tuple(expected), tuple(mapping), reason="trusted context projection edit")

    async def compact_context(self, session: Session, messages: list[dict[str, Any]], *,
                              rewrite: ArchiveRewrite) -> None:
        async with self._checkpoint_lock:
            self._require_paired(session)
            if tuple(session.messages) != rewrite.expected_messages or not messages or messages[0] != session.messages[0]:
                raise ValueError("压缩准备后的模型投影已变化，拒绝提交旧候选。")
            candidate = copy.deepcopy(messages)
            await self._commit(session, candidate, self._accepted_inputs, archive_rewrite=rewrite)
            session.messages = candidate
            session.lastPromptTokens = None
            session.lastSentLength = 0

    async def change_model(self, session: Session, model: str, messages: list[dict[str, Any]], *,
                           previous_model: str, rewrite: ArchiveRewrite) -> None:
        async with self._checkpoint_lock:
            self._require_paired(session)
            if session.model != previous_model or tuple(session.messages) != rewrite.expected_messages:
                raise ValueError("目标模型检查后的会话已变化，拒绝过期候选。")
            session.model = model
            try:
                await self._commit(session, messages, self._accepted_inputs, archive_rewrite=rewrite)
            except BaseException:
                session.model = previous_model
                raise
            session.messages = copy.deepcopy(messages)
            session.lastPromptTokens = None
            session.lastSentLength = 0

    @staticmethod
    def _require_paired(session: Session) -> None:
        called = {call["id"] for m in session.messages for call in m.get("tool_calls", [])}
        paired = {m.get("tool_call_id") for m in session.messages if m.get("role") == "tool"}
        if called - paired:
            raise ValueError("工具回合尚未配对，不能替换上下文或消费排队输入。")

    async def rename(self, session: Session, title: str) -> None:
        async with self._checkpoint_lock:
            await self._commit(session, session.messages, self._accepted_inputs, title=title)

    async def clear(self, session: Session) -> None:
        async with self._checkpoint_lock:
            self._require_paired(session)
            candidate = copy.deepcopy(session.messages[:1])
            await self._commit(session, candidate, self._accepted_inputs, clear_task=True,
                archive_rewrite=ArchiveRewrite("clear", tuple(copy.deepcopy(session.messages)), (0,), reason="/clear"))
            session.messages = candidate
            session.lastPromptTokens = None
            session.lastSentLength = 0

    async def branch(self, session: Session, directory: Path, runtime: RuntimeRecord, cwd: Path,
                     *, title: str | None = None) -> str:
        """为分支创建自己的工具账本，导入配对的对话快照，父会话执行仍归父会话。"""
        self._require_paired(session)
        import uuid

        branch_id = str(uuid.uuid4())
        target = Session(str(session.messages[0]["content"]), session.model)
        target.mode = session.mode
        target.usage.update(session.usage)
        target.messages = copy.deepcopy(session.messages)
        await self.save(session)
        imported = await self.worker.archive_branch()
        child = await Conversation.open(directory / branch_id, branch_id, cwd, runtime, target, self.secret,
                                        resume=False, archive_import=imported)
        child._known_secrets.update(self._known_secrets)
        try:
            # 以持久引用保留原附件身份。
            # 清理时按附件归属保护这些路径，其中也可能包含父会话目录。
            for file, digest in imported.attachments.items():
                await child.register_background_attachment(file, digest)
            child._task_title = self._task_title
            await child._commit(target, target.messages, (), state="paused", title=title or self._title)
        finally:
            await child.close()
        return branch_id

    async def write_export(self, session: Session, workspace: Path, *, context: bool = False,
                           json_format: bool = False) -> Path:
        from .log import writeArchiveExport, writeSessionExport

        async with self._checkpoint_lock:
            await self._commit(session, session.messages, self._accepted_inputs)
            if context:
                return await asyncio.to_thread(writeSessionExport, workspace,
                    {"session_id": self.session_id, "view": "context", "messages": self._safe(session.messages)},
                    json_format=json_format)
            loop = asyncio.get_running_loop()
            async def read(scope: str, offset: int) -> dict[str, Any]:
                return cast(dict[str, Any], self._safe(await self.worker.archive_export(
                    scope, offset=offset, limit=16, versions=json_format)))
            def page(scope: str, offset: int) -> dict[str, Any]:
                return asyncio.run_coroutine_threadsafe(read(scope, offset), loop).result()
            # 这是用户主动导出。可读范围由存储线程返回的已登记范围确定。
            scopes = await self.worker.archive_scopes()
            task = asyncio.create_task(asyncio.to_thread(writeArchiveExport, workspace, self.session_id,
                                                       scopes, page, json_format=json_format))
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                await task  # 导出已进入发布阶段时继续持锁，等到发布结果明确才释放。
                raise

    async def _commit(
        self, session: Session, messages: list[dict[str, Any]], inputs: tuple[AcceptedInput, ...],
        *, state: str | None = None, title: str | None = None, clear_task: bool = False,
        reflection: dict[str, Any] | None = None, update_reflection: bool = False,
        archive_rewrite: ArchiveRewrite | None = None, archive_import: ArchiveImport | None = None,
    ) -> None:
        if self.blocked:
            raise RuntimeError("会话存在未确认结果，拒绝提交新上下文。")
        background = self._background
        if background is not None:
            if background.fault is not None:
                raise RuntimeError("后台事件持久化或附件未确认，保留现场。") from background.fault
            await background.flushAttachments()
        consumed = background.consumedForMessages(messages) if background is not None else ()
        background_checkpoint = background.checkpoint() if background is not None else copy.deepcopy(self._saved_background)
        saved = self._safe(copy.deepcopy(messages))
        from .log import firstUserExcerpt
        task_title = None if clear_task else self._task_title or firstUserExcerpt(messages)
        title = title if title is not None else (str(originalInput(inputs[0].payload))[:80]
                 if inputs and not self._accepted_inputs else self._title)
        foreground_state = self.foreground_state if state is None else state
        reflection_state = self._safe(copy.deepcopy(reflection if update_reflection else self.reflection_state))
        # 摘要失败后应保留既有等待状态，重新打开时的保存也遵循这一点。
        if (state is None and foreground_state != "paused" and background_checkpoint
                and background_checkpoint["state"] == "waiting"):
            foreground_state = "waiting"
        if foreground_state not in {"idle", "running", "paused", "closed", "waiting", "recovering"}:
            raise ValueError("无效的会话执行状态。")
        checkpoint = Checkpoint(
            self.session_id, tuple(saved), session.model, session.mode, self.redact(title),
            self.revision, inputs, tuple(event.eventId for event in background.events() if event.eventId not in consumed) if background else (), {
                "promptTokens": session.usage["promptTokens"],
                "completionTokens": session.usage["completionTokens"],
                "cacheHitTokens": session.usage["cacheHitTokens"],
                "cacheMissTokens": session.usage["cacheMissTokens"],
            },
            foreground_state, self.revision, background_checkpoint, self.redact(task_title) if task_title else None,
            reflection_state,
        )
        archive_args: dict[str, Any] = {}
        if archive_rewrite is not None:
            archive_args["archive_rewrite"] = replace(archive_rewrite,
                expected_messages=tuple(self._safe(list(archive_rewrite.expected_messages))))
        if archive_import is not None:
            archive_args["archive_import"] = archive_import
        handle = self.worker.enqueue_checkpoint(self.revision, checkpoint, consumed, **archive_args)
        try:
            revision = await handle.wait()
        except BaseException:
            outcome = handle.status()
            if background is not None and outcome.state == "failed":
                background.unstageConsumed(list(consumed))
            else:
                self.blocked = True
                if background is not None:
                    background.checkpointUnknown = True
            raise
        if background is not None:
            background.acknowledge(list(consumed))
        self.revision = revision
        self._accepted_inputs = inputs
        self._title = title
        self._task_title = task_title
        self.reflection_state = reflection_state
        self.foreground_state = foreground_state
        self._saved_background = copy.deepcopy(background_checkpoint)

    def bind_background(self, runtime: BackgroundRuntime) -> None:
        if runtime.sessionId != self.session_id:
            raise ValueError("后台会话身份不匹配。")
        self._background = runtime

    async def background_view(self) -> RecoveryView:
        return await self.worker.load_recovery_view()

    def stage_background(self, run: RunRecord, event: OutboxEvent | None, *,
                         operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
                         archive_import: ArchiveImport | None = None) -> Any:
        saved_run = replace(run, snapshot=self._safe(run.snapshot))
        saved_event = replace(event, snapshot=self._safe(event.snapshot)) if event is not None else None
        safe_rewrite = (replace(archive_rewrite, expected_messages=tuple(self._safe(list(archive_rewrite.expected_messages))))
                        if archive_rewrite is not None else None)
        return self.worker.enqueue_run_event(saved_run, saved_event, operation_id=operation_id,
            archive_rewrite=safe_rewrite, archive_import=archive_import)

    async def publish_background(self, run: RunRecord, event: OutboxEvent | None, *,
                                 operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
                                 archive_import: ArchiveImport | None = None) -> OutboxEvent | None:
        handle = self.stage_background(run, event, operation_id=operation_id,
            archive_rewrite=archive_rewrite, archive_import=archive_import)
        try:
            result = await handle.wait()
        except BaseException:
            if handle.status().state != "failed":
                self.blocked = True
            raise
        if run.status == "unknown":
            self.blocked = True
        return result  # type: ignore[no-any-return]

    async def register_background_attachment(self, file: str, digest: str) -> None:
        await self.worker.enqueue_attachment(file, digest).wait()

    async def deliver_background(self, session: Session, messages: list[dict[str, Any]]) -> None:
        async with self._checkpoint_lock:
            self._require_paired(session)
            await self._commit(session, messages, self._accepted_inputs)
            session.messages = messages

    def current_agent_parent(self) -> ToolRef:
        parent = self.current_tool_ref()
        if parent.scope != "main":
            raise RuntimeError("子代理缺少当前父Agent工具意图。")
        return parent

    def current_tool_ref(self) -> ToolRef:
        ref = self._current_tool.get()
        if ref is None:
            raise RuntimeError("当前工具缺少已保存的执行意图。")
        return ref

    async def intent(self, call_id: str, name: str, args: str, effect: bool) -> ToolResult | None:
        return await self.scoped_intent(ToolRef("main", call_id), name, args, effect)

    async def scoped_intent(
        self, tool_ref: ToolRef, name: str, args: str, effect: bool, *,
        agent_run: RunRef | None = None, parent_tool_ref: ToolRef | None = None,
        approval_ref: str | None = None,
    ) -> ToolResult | None:
        if self.blocked:
            raise RuntimeError("会话存在未确认的工具结果，拒绝继续。")
        digest = hashlib.sha256(args.encode("utf-8")).hexdigest()
        run_ref = self._shell_refs.get(tool_ref, agent_run or RunRef("main", "foreground"))
        intent = Intent(
            tool_ref, run_ref, name,
            self.redact(args), digest, effect,
            approval_ref or self.approval_ref or ("text-confirmed" if effect else "read-only"),
            self.policy_version, self.owner_epoch, datetime.now(timezone.utc).isoformat(),
            parent_tool_ref=parent_tool_ref,
        )
        cached = await self.worker.enqueue_intent(intent).wait()
        self._current_tool.set(tool_ref if cached is None else None)
        return cached

    async def prepare(self, run_ref: RunRef, snapshot: dict[str, Any]) -> RunRecord:
        tool_ref = self._current_tool.get()
        if tool_ref is None:
            raise RuntimeError("runner缺少当前工具意图。")
        safe = self._safe(snapshot)
        if safe != snapshot:
            raise ValueError("runner启动元数据含当前凭据，无法完整保存。")
        run = await self.worker.enqueue_prepare_shell(tool_ref, run_ref, safe).wait()
        self._shell_refs[tool_ref] = run_ref
        return run

    async def commit(self, record: RunRecord) -> None:
        safe = replace(record, snapshot=self._safe(record.snapshot))
        await self.worker.enqueue_shell_run(safe).wait()

    async def recover(self) -> tuple[RunRecord, ...]:
        view = await self.worker.load_recovery_view()
        tools = {record.tool_ref: record for record in view.tool_records}
        runs = []
        for run in view.runs:
            if run.kind != "shell" or "storage_link_version" not in run.snapshot:
                continue
            if run.snapshot["storage_link_version"] != 1:
                raise ValueError("runner存储关联版本无法识别，保留原记录。")
            raw_ref = run.snapshot.get("tool_ref")
            if (not isinstance(raw_ref, dict) or not isinstance(raw_ref.get("scope"), str)
                    or not isinstance(raw_ref.get("tool_call_id"), str)):
                raise ValueError("runner缺少可信工具身份，保留原记录。")
            ref = ToolRef(raw_ref["scope"], raw_ref["tool_call_id"])
            self._shell_refs[ref] = run.run_ref
            tool = tools.get(ref)
            if tool is not None and tool.state == "result_committed":
                run = replace(run, snapshot={**run.snapshot, "tool_result": tool.result})
            runs.append(run)
        return tuple(runs)

    async def result(self, call_id: str, text: str, image_data: ImageData | None = None) -> None:
        await self.scoped_result(ToolRef("main", call_id), text, image_data)

    async def scoped_result(self, tool_ref: ToolRef, text: str, image_data: ImageData | None = None) -> None:
        result: ToolResult = self.redact(text)
        if image_data is not None:
            result = self._safe({"role": "tool", "tool_call_id": tool_ref.tool_call_id, "content": text,
                                 "imageData": copy.deepcopy(image_data)})
        await self.worker.enqueue_result_and_event(
            tool_ref, result, None, None,
        ).wait()

    async def close(self) -> None:
        await self.worker.close()
