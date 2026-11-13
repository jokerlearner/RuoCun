"""StoragePort v1 唯一声明模块（任务 07）。

唯一契约来源：``.scratch/ruocun-discovery/research/09-storage-extension-route.md``
的 ``# StoragePort v1``、``# 三类epoch``、``# SQLite及文件路线``、
``# 原生路径、兼容source map与写回``，以及 ``08-python-runtime-route.md``
与 ADR-0005。冻结行为参照为只读解包副本
``src/session/{durable_store,sqlite,recovery,process_identity,log}.ts``
及 ``durable_store.test.ts`` / ``process_identity.test.ts``。

本模块只声明共享类型、常量与端口签名；实际编码从这一处导入，不维护第二套类型，
不从 Python 当前实现倒推契约。三类 epoch 的职责严格分离，见下方注释。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Protocol

from ..platform.file_contract import (
    AtomicFileError,
    DurabilityUnconfirmedError,
    PublishReceipt,
)

# ---------------------------------------------------------------------------
# 品牌 / 数据身份（09 报告「SQLite及文件路线」+ 任务 07 票）
# ---------------------------------------------------------------------------
PRODUCT = "ruocun"
FORMAT = "ruocun-session"
STORAGE_VERSION = 3
USER_VERSION = 1
LEGACY_SESSION_USER_VERSION = 2

# ---------------------------------------------------------------------------
# 三类 epoch（09 报告 ``# 三类epoch``），职责不得混用
# ---------------------------------------------------------------------------
# owner_epoch       : SQLite 会话所有权；死 owner 接管时递增，每个写事务内 fencing。
# stream_generation : D08 每个模型流/当前轮的内存代次；本票不实现（后续票）。
# control_epoch     : D08 runner 控制租约；本票不实现（后续票）。
# 本票只实现 owner_epoch，且只用于 DB 所有权，绝不用于模型流或 runner 控制。
# 任务15的control_epoch位于RunRecord.snapshot，由独立runner控制协议与存储校验。

# ---------------------------------------------------------------------------
# 异常：失败保留真实错误，不以 placeholders 伪造成功
# ---------------------------------------------------------------------------
class StoreError(RuntimeError):
    """存储层明确失败基类。"""


class OwnerConflictError(StoreError):
    """活 owner / 会话身份不符 / 跨 host 自动接管被拒。"""


class OwnerFencedError(StoreError):
    """旧 writer 或错误 epoch 的写事务被 fence。"""


class VersionRejectError(StoreError):
    """旧版、未来版本、非空版本 0 等不接受为 RuoCun 自有会话。"""


class CorruptDatabaseError(StoreError):
    """损坏数据库，拒绝恢复为空会话。"""


class MissingCheckpointError(StoreError):
    """缺少可信 checkpoint，不静默创建空会话。"""


class RuntimeGateError(StoreError):
    """受控 SQLite 运行库门禁未达，明确拒绝启用耐久恢复。"""


class IdentityQueryError(StoreError):
    """进程身份查询错误；不得冒充进程已死亡。"""


class CrossHostError(OwnerConflictError):
    """会话来自另一台机器，不自动接管。"""


class UnknownOutcomeBlockedError(StoreError):
    """存在结果未知的操作，阻挡新副作用。"""


# ---------------------------------------------------------------------------
# 数据记录（09 报告 ``# StoragePort v1`` 最小必须信息及不变量）
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProcessIdentity:
    """进程身份：host / boot / pid / start（冻结 process_identity.ts）。"""

    host: str
    boot: str
    pid: int
    start: str


@dataclass(frozen=True)
class DbOwner:
    """DB 所有权记录；每个写事务内校验当前 owner。"""

    session_id: str
    canonical_cwd: str
    instance_id: str
    owner_epoch: int
    identity: ProcessIdentity


@dataclass(frozen=True)
class RunRef:
    """task_id / run_id 分层；续跑同 task 产生新 run。"""

    task_id: str
    run_id: str


@dataclass(frozen=True)
class ToolRef:
    """scope / tool_call_id；与 session 关联。"""

    scope: str
    tool_call_id: str


@dataclass(frozen=True)
class Intent:
    """副作用许可前的执行意图；不持久化明文凭据。

    ``args`` 是最终参数（或脱敏引用），``args_digest`` 固定同一操作身份。
    """

    tool_ref: ToolRef
    run_ref: RunRef
    name: str
    args: str
    args_digest: str
    side_effect: bool
    approval_ref: str
    policy_version: str
    owner_epoch: int
    created_at: str
    parent_tool_ref: ToolRef | None = None


ToolResult = str | dict[str, Any]


@dataclass(frozen=True)
class ToolRecord:
    """started / result_committed / outcome_unknown；未知结果不是已知终态。"""

    tool_ref: ToolRef
    name: str
    args: str
    state: Literal["started", "result_committed", "outcome_unknown"]
    result: ToolResult | None
    intent: Intent | None
    decision_ref: str | None


@dataclass(frozen=True)
class RunRecord:
    """执行类别/状态；kind 区分 shell/agent/fork/monitor/manual。"""

    run_ref: RunRef
    kind: Literal["shell", "agent", "fork", "monitor", "manual"]
    status: str
    cancel_requested: bool
    snapshot: dict[str, Any]


def task_inbox_messages(inbox: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": "user", "content": "[追加指令] " + entry["message"]} for entry in inbox]


@dataclass(frozen=True)
class OutboxEvent:
    """唯一 event_id、DB 分配单调 seq、delivered_revision。"""

    event_id: str
    session_id: str
    run_ref: RunRef
    event_type: str
    snapshot: dict[str, Any]
    owner_epoch: int
    seq: int = 0
    delivered_revision: int | None = None


@dataclass(frozen=True)
class AcceptedInput:
    """已接受输入：queued / consumed / discarded；显示「已保存」须在提交后。"""

    input_id: str
    seq: int
    payload: str
    attachment_refs: tuple[str, ...]
    state: Literal["queued", "consumed", "discarded"]


@dataclass(frozen=True)
class Checkpoint:
    """消息/工具配对、模型/模式、revision、accepted 输入、pending、用量。

    最小可恢复信息按 09 报告；完整 agent checkpoint / 分模型费用桶 / fork 材料
    属后续票，本票不缩减「已接受且已确认保存的输入不能丢失」这一不变量。
    """

    session_id: str
    messages: tuple[dict[str, Any], ...]
    model: str
    mode: str
    title: str
    revision: int
    accepted_inputs: tuple[AcceptedInput, ...]
    pending_event_ids: tuple[str, ...]
    usage: dict[str, int]
    background_state: str
    delivered_revision: int
    background: dict[str, Any] | None = None
    task_title: str | None = None
    reflection_state: dict[str, Any] | None = None


@dataclass(frozen=True)
class ArchiveDerivation:
    """A program-owned replacement; indices address ArchiveRewrite.expected_messages."""

    id: str
    kind: Literal["summary", "prune"]
    target_index: int
    source_indices: tuple[int, ...]
    reason: str = ""


@dataclass(frozen=True)
class ArchiveRewrite:
    kind: Literal["compact", "clear", "rewind", "prefix"]
    expected_messages: tuple[dict[str, Any], ...]
    mapping: tuple[int | None, ...]
    derived: tuple[ArchiveDerivation, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ArchiveImport:
    source_session: str
    records: tuple[dict[str, Any], ...]
    lineage: tuple[str, ...]
    legacy_gap: bool = False
    attachments: dict[str, str] = field(default_factory=dict)
    attachment_sources: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ArchiveOperation:
    operation_id: str
    request_digest: str
    scope: str
    revision: int


def archive_request_digest(run: RunRecord | None, event: OutboxEvent | None, *,
                           tool_ref: ToolRef | None = None, result: ToolResult | None = None,
                           archive_rewrite: ArchiveRewrite | None = None,
                           archive_import: ArchiveImport | None = None) -> str:
    value = {"format": 1, "run": asdict(run) if run is not None else None,
             "event": asdict(event) if event is not None else None,
             "tool_ref": asdict(tool_ref) if tool_ref is not None else None, "result": result,
             "rewrite": asdict(archive_rewrite) if archive_rewrite is not None else None,
             "import": asdict(archive_import) if archive_import is not None else None}
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8", errors="backslashreplace")).hexdigest()


def checkpoint_request_digest(
    expected_revision: int, checkpoint: Checkpoint, consumed_event_ids: tuple[str, ...], *,
    archive_rewrite: ArchiveRewrite | None = None, archive_import: ArchiveImport | None = None,
) -> str:
    """Versioned canonical digest; session identity is part of the checkpoint."""
    request = {
        "version": 1,
        "expected_revision": expected_revision,
        "checkpoint": asdict(checkpoint),
        "consumed_event_ids": list(consumed_event_ids),
    }
    if archive_rewrite is not None:
        request["archive_rewrite"] = asdict(archive_rewrite)
    if archive_import is not None:
        request["archive_import"] = asdict(archive_import)
    if checkpoint.background is None:
        request["checkpoint"].pop("background", None)  # type: ignore[attr-defined]
    if checkpoint.task_title is None:
        request["checkpoint"].pop("task_title", None)  # type: ignore[attr-defined]
    if checkpoint.reflection_state is None:
        request["checkpoint"].pop("reflection_state", None)  # type: ignore[attr-defined]
    encoded = json.dumps(
        request, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8", errors="backslashreplace")
    return hashlib.sha256(encoded).hexdigest()


def checkpoint_operation_id(
    expected_revision: int, checkpoint: Checkpoint, consumed_event_ids: tuple[str, ...], *,
    archive_rewrite: ArchiveRewrite | None = None, archive_import: ArchiveImport | None = None,
) -> str:
    return "checkpoint-v1:" + checkpoint_request_digest(
        expected_revision, checkpoint, consumed_event_ids,
        archive_rewrite=archive_rewrite, archive_import=archive_import,
    )


@dataclass(frozen=True)
class CheckpointOperation:
    operation_id: str
    request_digest: str
    revision: int


@dataclass(frozen=True)
class RecoveryDecision:
    decision_id: str
    action: Literal["resolve", "decide", "continue"]
    target: str
    explanation: str
    command: str
    status: str | None = None
    new_run: RunRef | None = None


@dataclass(frozen=True)
class RecoveryReceipt:
    revision: int
    replayed: bool
    new_run: RunRef | None = None


@dataclass(frozen=True)
class RecoveryView:
    """从同一一致视图读出的恢复快照；不触发副作用。"""

    owner: DbOwner
    checkpoint: Checkpoint | None
    tool_records: tuple[ToolRecord, ...]
    runs: tuple[RunRecord, ...]
    pending_events: tuple[OutboxEvent, ...]
    missing_attachments: tuple[str, ...]
    decisions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RuntimeRecord:
    """产品实际使用的 SQLite 运行库清单（REC-15）。"""

    version: str
    source_id: str
    compile_options: tuple[str, ...]
    dll_path: str
    dll_sha256: str
    driver: str
    driver_extension: str
    driver_extension_sha256: str
    vfs: str
    python_version: str
    connection: dict[str, Any]
    gate: Literal["met", "not-met"]
    reason: str
    wal_fix_basis: str


# ---------------------------------------------------------------------------
# 身份提供方 seam（冻结 durable_store.test.ts 注入 identities 的做法）
# ---------------------------------------------------------------------------
class IdentityProvider(Protocol):
    def current(self) -> ProcessIdentity:
        """当前进程身份。"""
        ...

    def alive(self, identity: ProcessIdentity) -> bool:
        """owner 是否仍存活；查询错误必须抛错，不返回 False 冒充死亡。"""
        ...


# ---------------------------------------------------------------------------
# StoragePort v1（09 报告方法/事务契约；本票实现最小子集，见交付交接）
# ---------------------------------------------------------------------------
class StoragePort(Protocol):
    """业务持久端口；连接由专属单线程创建/使用/关闭，事务内 owner fencing。"""

    def open_or_claim(self, identity: ProcessIdentity) -> tuple[DbOwner, RecoveryView]:
        """拒活 owner / 身份不符；死 owner 接管递增 epoch；返回可信恢复视图。"""
        ...

    def commit_intent(self, owner: DbOwner, intent: Intent) -> ToolResult | None:
        """副作用获许可前提交；同 ToolRef 已知结果返回复用结果。"""
        ...

    def commit_result_and_event(
        self,
        owner: DbOwner,
        tool_ref: ToolRef,
        result: ToolResult,
        run_update: RunRecord | None,
        event: OutboxEvent | None,
        *, operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> None:
        """结果、关联 run 状态与 outbox 事件同一 DB 事务。"""
        ...

    def commit_run_event(
        self, owner: DbOwner, run_update: RunRecord, event: OutboxEvent | None, *,
        operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> OutboxEvent | None:
        """无工具结果的后台进展；有 event 时 run+event 原子。"""
        ...

    def prepare_shell(
        self, owner: DbOwner, tool_ref: ToolRef, run_ref: RunRef, snapshot: dict[str, Any]
    ) -> RunRecord:
        """同事务关联已批准的Bash意图与唯一runner启动身份。"""
        ...

    def commit_shell_run(self, owner: DbOwner, run: RunRecord) -> None:
        """经owner fencing保存同一执行及控制租约，复用已确认工具结果。"""
        ...

    def commit_checkpoint_ack(
        self,
        owner: DbOwner,
        expected_revision: int,
        checkpoint: Checkpoint,
        consumed_event_ids: tuple[str, ...],
        *,
        operation_id: str | None = None,
        archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> int:
        """消息/background/revision/delivered 同事务；返回新 revision 后才内存 ack。"""
        ...

    def lookup_checkpoint_operation(
        self, owner: DbOwner, operation_id: str, *, request_digest: str | None = None
    ) -> CheckpointOperation | None:
        """Read committed receipt; absence does not prove an accepted operation failed."""
        ...

    def record_recovery_decision(
        self, owner: DbOwner, decision_id: str, target: str, decision: str, explanation: str
    ) -> None:
        """decision ID 幂等且内容冲突拒绝；resolve 不自动执行旧工具。"""
        ...

    def prepare_recovery(self, owner: DbOwner, material_errors: dict[str, str] | None = None) -> None:
        """归类丢失执行器及缺失附件；不启动或重放执行。"""
        ...

    def commit_recovery(
        self, owner: DbOwner, decision: RecoveryDecision, expected_revision: int,
        checkpoint: Checkpoint,
    ) -> RecoveryReceipt:
        """决定、受影响journal/run及用户消息同事务；同ID内容冲突拒绝。"""
        ...

    def load_recovery_view(self) -> RecoveryView:
        """同一一致视图；检查损坏、附件 hash/执行身份；不触发副作用。"""
        ...

    def read_pending_events(self) -> tuple[OutboxEvent, ...]:
        """按 seq 读未投递事件。"""
        ...

    def add_attachment(self, owner: DbOwner, file: str, digest: str) -> None: ...

    def archive_projection(self, scope: str = "main") -> dict[str, Any]: ...
    def archive_scopes(self) -> list[str]: ...
    def archive_list(self, scope: str = "main", *, offset: int = 0, limit: int = 20) -> dict[str, Any]: ...
    def archive_read(self, identity: str, scope: str = "main", *, offset: int = 0, limit: int = 4096) -> dict[str, Any]: ...
    def archive_export(self, scope: str = "main", *, offset: int = 0, limit: int = 100, versions: bool = False) -> dict[str, Any]: ...
    def archive_branch(self, scope: str = "main", *, indices: tuple[int, ...] | None = None) -> ArchiveImport: ...
    def lookup_archive_operation(self, operation_id: str, *, request_digest: str | None = None) -> ArchiveOperation | None: ...

    def close(self, owner: DbOwner) -> None:
        """停止接受新写；只有仍为本 owner 才释放 owner。"""
        ...


__all__ = [
    "PRODUCT",
    "FORMAT",
    "STORAGE_VERSION",
    "USER_VERSION",
    "LEGACY_SESSION_USER_VERSION",
    "StoreError",
    "OwnerConflictError",
    "OwnerFencedError",
    "VersionRejectError",
    "CorruptDatabaseError",
    "MissingCheckpointError",
    "RuntimeGateError",
    "IdentityQueryError",
    "CrossHostError",
    "UnknownOutcomeBlockedError",
    "AtomicFileError",
    "DurabilityUnconfirmedError",
    "ProcessIdentity",
    "DbOwner",
    "RunRef",
    "ToolRef",
    "Intent",
    "ToolRecord",
    "ToolResult",
    "RunRecord",
    "OutboxEvent",
    "AcceptedInput",
    "Checkpoint",
    "CheckpointOperation",
    "ArchiveDerivation",
    "ArchiveRewrite",
    "ArchiveImport",
    "ArchiveOperation",
    "archive_request_digest",
    "checkpoint_operation_id",
    "checkpoint_request_digest",
    "RecoveryView",
    "RecoveryDecision",
    "RecoveryReceipt",
    "RuntimeRecord",
    "PublishReceipt",
    "IdentityProvider",
    "StoragePort",
]
