"""用一个专属线程串行执行会话 SQLite 工作。

上层提交操作后可取消等待，已接纳的数据库工作仍继续执行。检查点等操作通过原请求身份和持久回执核对，从而区分完成、失败和结果未知。
"""

from __future__ import annotations

import asyncio
import copy
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Generic, Literal, TypeVar, cast

from .contract import (
    ArchiveImport,
    ArchiveOperation,
    ArchiveRewrite,
    Checkpoint,
    CheckpointOperation,
    DbOwner,
    IdentityProvider,
    Intent,
    OutboxEvent,
    RecoveryDecision,
    RecoveryReceipt,
    RecoveryView,
    RunRecord,
    RunRef,
    RuntimeRecord,
    StoragePort,
    StoreError,
    ToolRef,
    ToolResult,
    archive_request_digest,
    checkpoint_operation_id,
    checkpoint_request_digest,
)
from .sqlite_port import CommitUnconfirmedError, RollbackError

_T = TypeVar("_T")


async def _wait_without_cancelling(future: Future[_T]) -> _T:
    wrapped = asyncio.wrap_future(future)
    try:
        return await asyncio.shield(wrapped)
    except asyncio.CancelledError:
        # 调用方取消等待后，数据库线程仍处理已接纳的工作。
        # 收取迟到的异常，避免无人等待的 Future 触发未处理异常日志。
        def consume(done: asyncio.Future[_T]) -> None:
            if not done.cancelled():
                done.exception()

        wrapped.add_done_callback(consume)
        raise


@dataclass(frozen=True)
class CheckpointStatus:
    state: Literal["pending", "committed", "failed", "outcome_unknown"]
    revision: int | None = None
    error: BaseException | None = None


@dataclass(frozen=True)
class CheckpointHandle:
    operation_id: str
    request_digest: str
    _future: Future[int]

    async def wait(self) -> int:
        """取消只停止本次等待，数据库线程继续处理已经接纳的请求。"""
        return await _wait_without_cancelling(self._future)

    def status(self) -> CheckpointStatus:
        if not self._future.done():
            return CheckpointStatus("pending")
        try:
            revision = self._future.result()
        except (CommitUnconfirmedError, RollbackError) as exc:
            return CheckpointStatus("outcome_unknown", error=exc)
        except StoreError as exc:
            return CheckpointStatus("failed", error=exc)
        except BaseException as exc:
            # 未分类的异常也可能发生在提交之后。
            # 缺少确认时保留结果未知状态，等待原请求的证据。
            return CheckpointStatus("outcome_unknown", error=exc)
        return CheckpointStatus("committed", revision=revision)


@dataclass(frozen=True)
class OperationStatus:
    state: Literal["pending", "committed", "failed", "outcome_unknown"]
    error: BaseException | None = None


@dataclass(frozen=True)
class OperationHandle(Generic[_T]):
    """跟踪已接纳的工作。归档运行和结果写入另外保存持久回执。"""

    operation_id: str
    _future: Future[_T]
    request_digest: str | None = None

    async def wait(self) -> _T:
        return await _wait_without_cancelling(self._future)

    def status(self) -> OperationStatus:
        if not self._future.done():
            return OperationStatus("pending")
        try:
            self._future.result()
        except (CommitUnconfirmedError, RollbackError) as exc:
            return OperationStatus("outcome_unknown", error=exc)
        except StoreError as exc:
            return OperationStatus("failed", error=exc)
        except BaseException as exc:
            return OperationStatus("outcome_unknown", error=exc)
        return OperationStatus("committed")


class StorageWorker:
    """在自己的线程上创建、操作和关闭同一个 StoragePort。"""

    def __init__(self, factory: Callable[[], tuple[StoragePort, DbOwner]]) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ruocun-db")
        self._opening = self._executor.submit(factory)
        self._lock = threading.Lock()
        self._jobs: dict[str, CheckpointHandle] = {}
        self._closed = False
        self._close_future: Future[None] | None = None
        # 该字段只由专属数据库线程读写。
        self._write_fault: BaseException | None = None

    @classmethod
    def open(
        cls, session_dir: Path, session_id: str, cwd: Path, runtime: RuntimeRecord,
        identities: IdentityProvider | None = None,
    ) -> StorageWorker:
        """在数据库线程上建立端口并取得会话所有权，此后的操作都运行在同一个线程。"""
        from .durable_store import DurableStore
        from .process_identity import RealIdentityProvider

        def factory() -> tuple[StoragePort, DbOwner]:
            provider = identities or RealIdentityProvider()
            port = DurableStore(session_dir, session_id, cwd, runtime, provider)
            owner, _ = port.open_or_claim(provider.current())
            return port, owner

        return cls(factory)

    def _run_write(self, operation: Callable[[StoragePort, DbOwner], _T]) -> _T:
        if self._write_fault is not None:
            raise StoreError("存储结果未确认或发生数据库错误；拒绝后续写入。") from self._write_fault
        try:
            port, owner = self._opening.result()
            return operation(port, owner)
        except (CommitUnconfirmedError, RollbackError) as exc:
            self._write_fault = exc
            raise
        except StoreError:
            # 这是明确的契约拒绝，数据库没有提交事务。
            raise
        except BaseException as exc:
            self._write_fault = exc
            raise

    def _enqueue_write(
        self, operation: Callable[[StoragePort, DbOwner], _T], *,
        operation_id: str | None = None, request_digest: str | None = None,
    ) -> OperationHandle[_T]:
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")

            def run() -> _T:
                return self._run_write(operation)

            return OperationHandle(operation_id or str(uuid.uuid4()), self._executor.submit(run), request_digest)

    def enqueue_intent(self, intent: Intent) -> OperationHandle[ToolResult | None]:
        accepted = copy.deepcopy(intent)
        return self._enqueue_write(lambda port, owner: copy.deepcopy(port.commit_intent(owner, accepted)))

    def enqueue_result_and_event(
        self, tool_ref: ToolRef, result: ToolResult,
        run_update: RunRecord | None, event: OutboxEvent | None,
        *, operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> OperationHandle[None]:
        ref, saved_result, run, saved_event = copy.deepcopy((tool_ref, result, run_update, event))
        rewrite, imported = copy.deepcopy((archive_rewrite, archive_import))
        digest = archive_request_digest(run, saved_event, tool_ref=ref, result=saved_result,
                                        archive_rewrite=rewrite, archive_import=imported)
        op_id = operation_id or "run-v1:" + uuid.uuid4().hex
        options: dict[str, Any] = {"operation_id": op_id, "archive_rewrite": rewrite, "archive_import": imported}
        return self._enqueue_write(
            lambda port, owner: port.commit_result_and_event(owner, ref, saved_result, run, saved_event,
                **(options if hasattr(port, "lookup_archive_operation") else {})),
            operation_id=op_id, request_digest=digest,
        )

    def enqueue_run_event(
        self, run_update: RunRecord, event: OutboxEvent | None, *, operation_id: str | None = None,
        archive_rewrite: ArchiveRewrite | None = None, archive_import: ArchiveImport | None = None,
    ) -> OperationHandle[OutboxEvent | None]:
        run, saved_event = copy.deepcopy((run_update, event))
        rewrite, imported = copy.deepcopy((archive_rewrite, archive_import))
        digest = archive_request_digest(run, saved_event, archive_rewrite=rewrite, archive_import=imported)
        op_id = operation_id or "run-v1:" + uuid.uuid4().hex
        options: dict[str, Any] = {"operation_id": op_id, "archive_rewrite": rewrite, "archive_import": imported}
        return self._enqueue_write(
            lambda port, owner: port.commit_run_event(owner, run, saved_event,
                **(options if hasattr(port, "lookup_archive_operation") else {})),
            operation_id=op_id, request_digest=digest,
        )

    def enqueue_attachment(self, file: str, digest: str) -> OperationHandle[None]:
        return self._enqueue_write(lambda port, owner: port.add_attachment(owner, file, digest))

    def enqueue_prepare_shell(
        self, tool_ref: ToolRef, run_ref: RunRef, snapshot: dict[str, Any]
    ) -> OperationHandle[RunRecord]:
        ref, execution, payload = copy.deepcopy((tool_ref, run_ref, snapshot))
        return self._enqueue_write(lambda port, owner: port.prepare_shell(owner, ref, execution, payload))

    def enqueue_shell_run(self, run: RunRecord) -> OperationHandle[None]:
        saved = copy.deepcopy(run)
        return self._enqueue_write(lambda port, owner: port.commit_shell_run(owner, saved))

    def enqueue_recovery_decision(
        self, decision_id: str, target: str, decision: str, explanation: str,
    ) -> OperationHandle[None]:
        return self._enqueue_write(
            lambda port, owner: port.record_recovery_decision(
                owner, decision_id, target, decision, explanation
            )
        )

    def enqueue_prepare_recovery(self, material_errors: dict[str, str] | None = None) -> OperationHandle[None]:
        return self._enqueue_write(lambda port, owner: port.prepare_recovery(owner, copy.deepcopy(material_errors)))

    def enqueue_recovery(
        self, decision: RecoveryDecision, expected_revision: int, checkpoint: Checkpoint,
    ) -> OperationHandle[RecoveryReceipt]:
        saved, candidate = copy.deepcopy((decision, checkpoint))
        return self._enqueue_write(
            lambda port, owner: port.commit_recovery(owner, saved, expected_revision, candidate)
        )

    async def load_recovery_view(self) -> RecoveryView:
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")

            def read() -> RecoveryView:
                port, _ = self._opening.result()
                return port.load_recovery_view()

            future = self._executor.submit(read)
        return await _wait_without_cancelling(future)

    async def read_pending_events(self) -> tuple[OutboxEvent, ...]:
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")

            def read() -> tuple[OutboxEvent, ...]:
                port, _ = self._opening.result()
                return port.read_pending_events()

            future = self._executor.submit(read)
        return await _wait_without_cancelling(future)

    def enqueue_checkpoint(
        self,
        expected_revision: int,
        checkpoint: Checkpoint,
        consumed_event_ids: tuple[str, ...],
        *,
        operation_id: str | None = None,
        archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> CheckpointHandle:
        # 冻结的数据类内部可能仍引用可变的消息或用量字典。
        # 先复制参数，再计算摘要和入队，确保提交的请求与摘要对应。
        checkpoint = copy.deepcopy(checkpoint)
        archive_rewrite, archive_import = copy.deepcopy((archive_rewrite, archive_import))
        consumed_event_ids = tuple(consumed_event_ids)
        digest = checkpoint_request_digest(expected_revision, checkpoint, consumed_event_ids,
                                           archive_rewrite=archive_rewrite, archive_import=archive_import)
        op_id = operation_id if operation_id is not None else checkpoint_operation_id(
            expected_revision, checkpoint, consumed_event_ids,
            archive_rewrite=archive_rewrite, archive_import=archive_import,
        )
        if not op_id or len(op_id) > 256:
            raise StoreError("检查点操作身份不能为空或超过 256 字符。")
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")
            existing = self._jobs.get(op_id)
            if existing is not None:
                if existing.request_digest != digest:
                    raise StoreError("检查点操作 ID 内容冲突。")
                if existing.status().state != "failed":
                    return existing
                # 已明确拒绝或回滚的请求没有提交回执。
                # 修复原因后，可再次提交同一批暂存事件。
                self._jobs.pop(op_id)

            def commit() -> int:
                return self._run_write(
                    lambda port, owner: port.commit_checkpoint_ack(
                        owner, expected_revision, checkpoint, consumed_event_ids,
                        operation_id=op_id,
                        **cast(dict[str, Any], {"archive_rewrite": archive_rewrite} if archive_rewrite is not None else {}),
                        **cast(dict[str, Any], {"archive_import": archive_import} if archive_import is not None else {}),
                    )
                )

            handle = CheckpointHandle(op_id, digest, self._executor.submit(commit))
            self._jobs[op_id] = handle
            return handle

    async def _archive_read(self, method: str, *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")
            def read() -> Any:
                port, _ = self._opening.result()
                return copy.deepcopy(getattr(port, method)(*args, **kwargs))
            future = self._executor.submit(read)
        return await _wait_without_cancelling(future)

    async def archive_projection(self, scope: str = "main") -> dict[str, Any]:
        return cast(dict[str, Any], await self._archive_read("archive_projection", scope))

    async def archive_scopes(self) -> list[str]:
        return cast(list[str], await self._archive_read("archive_scopes"))

    async def archive_list(self, scope: str = "main", *, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        return cast(dict[str, Any], await self._archive_read("archive_list", scope, offset=offset, limit=limit))

    async def archive_read(self, identity: str, scope: str = "main", *, offset: int = 0,
                           limit: int = 4096) -> dict[str, Any]:
        return cast(dict[str, Any], await self._archive_read("archive_read", identity, scope, offset=offset, limit=limit))

    async def archive_export(self, scope: str = "main", *, offset: int = 0, limit: int = 100,
                             versions: bool = False) -> dict[str, Any]:
        return cast(dict[str, Any], await self._archive_read("archive_export", scope, offset=offset, limit=limit, versions=versions))

    async def archive_branch(self, scope: str = "main", *, indices: tuple[int, ...] | None = None) -> ArchiveImport:
        return cast(ArchiveImport, await self._archive_read("archive_branch", scope, indices=indices))

    async def lookup_archive_operation(self, operation_id: str, *, request_digest: str | None = None) -> ArchiveOperation | None:
        return cast(ArchiveOperation | None, await self._archive_read("lookup_archive_operation", operation_id, request_digest=request_digest))

    async def lookup_checkpoint_operation(
        self, operation_id: str, *, request_digest: str | None = None
    ) -> CheckpointOperation | None:
        with self._lock:
            if self._closed:
                raise StoreError("会话存储线程已关闭。")

            def lookup() -> CheckpointOperation | None:
                port, owner = self._opening.result()
                return port.lookup_checkpoint_operation(owner, operation_id, request_digest=request_digest)

            future = self._executor.submit(lookup)
        return await _wait_without_cancelling(future)

    async def close(self) -> None:
        """处理完已接纳的工作后，在数据库线程释放会话所有权并关闭连接。"""
        with self._lock:
            if self._close_future is None:
                self._closed = True

                def close_port() -> None:
                    port, owner = self._opening.result()
                    port.close(owner)

                self._close_future = self._executor.submit(close_port)
            future = self._close_future
        try:
            await _wait_without_cancelling(future)
        finally:
            # 等待取消后，已排队的关闭操作仍会继续。
            # 让数据库线程自行收尾，避免事件循环阻塞在待完成的工作上。
            self._executor.shutdown(wait=False)
