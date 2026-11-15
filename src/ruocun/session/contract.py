"""定义会话持久化共用的数据类型、失败状态和存储接口。

前台会话和后台运行用这些记录交换已接受输入、工具结果、检查点及恢复决策。存储层按统一契约控制写入权和提交边界，调用方可区分明确失败与结果未知。
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
# 产品标记与会话格式版本。打开数据库时用这些值辨认数据归属和兼容性。
# ---------------------------------------------------------------------------
PRODUCT = "ruocun"
FORMAT = "ruocun-session"
STORAGE_VERSION = 3
USER_VERSION = 1
LEGACY_SESSION_USER_VERSION = 2

# ---------------------------------------------------------------------------
# 数据库写入权、模型流与 runner 各有独立的代次。
# ---------------------------------------------------------------------------
# owner_epoch 随数据库所有者接管递增，写事务据此识别旧写入者。
# stream_generation 由模型流维护，用于区分当前与已过期的流。
# control_epoch 是单次 runner 控制租约的代次。
# 这里的 DbOwner 只描述数据库写入权。
# runner 的 control_epoch 随 RunRecord.snapshot 保存，供控制协议和存储层核验。

# ---------------------------------------------------------------------------
# 存储失败类型，用于把明确的拒绝与尚待确认的结果传给调用方。
# ---------------------------------------------------------------------------
class StoreError(RuntimeError):
    """可以向上报告的会话存储错误。"""


class OwnerConflictError(StoreError):
    """现有所有者仍存活，或会话身份不匹配，无法接管。"""


class OwnerFencedError(StoreError):
    """写入者身份或代次已过期，写事务被拒绝。"""


class VersionRejectError(StoreError):
    """数据库版本与当前支持的若存会话格式不兼容。"""


class CorruptDatabaseError(StoreError):
    """数据库损坏，恢复流程保留已有数据并明确失败。"""


class MissingCheckpointError(StoreError):
    """找不到可信的会话检查点，无法恢复。"""


class RuntimeGateError(StoreError):
    """实际 SQLite 运行库未通过核验，拒绝开启持久化或恢复。"""


class IdentityQueryError(StoreError):
    """进程是否存活无法确认。上层保留已有所有权。"""


class CrossHostError(OwnerConflictError):
    """会话来自另一台机器，不能自动接管。"""


class UnknownOutcomeBlockedError(StoreError):
    """尚有结果未确认的操作，需要先核实才能引入新副作用。"""


# ---------------------------------------------------------------------------
# 跨前台会话、后台运行和存储接口交换的数据记录。
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ProcessIdentity:
    """用主机、开机标记、PID 和创建时间共同标识一个进程。"""

    host: str
    boot: str
    pid: int
    start: str


@dataclass(frozen=True)
class DbOwner:
    """记录数据库的当前所有者和持有代次，供写事务校验。"""

    session_id: str
    canonical_cwd: str
    instance_id: str
    owner_epoch: int
    identity: ProcessIdentity


@dataclass(frozen=True)
class RunRef:
    """任务引用区分长期任务与一次执行。继续同一任务使用新的 run_id。"""

    task_id: str
    run_id: str


@dataclass(frozen=True)
class ToolRef:
    """工具引用由执行范围和工具调用 ID 组成，归属指定会话。"""

    scope: str
    tool_call_id: str


@dataclass(frozen=True)
class Intent:
    """在调用副作用工具前保存已批准的执行意图。

    记录脱敏的最终参数并附摘要，后续可确认恢复的仍是同一次操作。
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
    """保留工具调用的执行状态。结果未知时继续留作待核实。"""

    tool_ref: ToolRef
    name: str
    args: str
    state: Literal["started", "result_committed", "outcome_unknown"]
    result: ToolResult | None
    intent: Intent | None
    decision_ref: str | None


@dataclass(frozen=True)
class RunRecord:
    """保留单次 Shell、代理或其它后台执行的状态和快照。"""

    run_ref: RunRef
    kind: Literal["shell", "agent", "fork", "monitor", "manual"]
    status: str
    cancel_requested: bool
    snapshot: dict[str, Any]


def task_inbox_messages(inbox: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"role": "user", "content": "[追加指令] " + entry["message"]} for entry in inbox]


@dataclass(frozen=True)
class OutboxEvent:
    """为待投递事件保存稳定身份、数据库分配的序号和投递确认版本。"""

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
    """记录输入排队、消费或丢弃的状态。持久化确认后才向用户显示已保存。"""

    input_id: str
    seq: int
    payload: str
    attachment_refs: tuple[str, ...]
    state: Literal["queued", "consumed", "discarded"]


@dataclass(frozen=True)
class Checkpoint:
    """保存恢复会话所需的消息、运行设置、已接纳输入、未投递事件和用量。

    有些消息会从模型上下文移除，独立的输入记录仍让已确认的用户消息可以找回。
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
    """记录程序生成的归档替换，索引指向 ArchiveRewrite.expected_messages。"""

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
    """按固定版本和序列化口径为检查点请求计算摘要，会话身份也是摘要输入。"""
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
    """从同一一致视图读取可恢复的检查点、执行和待处理信息。"""

    owner: DbOwner
    checkpoint: Checkpoint | None
    tool_records: tuple[ToolRecord, ...]
    runs: tuple[RunRecord, ...]
    pending_events: tuple[OutboxEvent, ...]
    missing_attachments: tuple[str, ...]
    decisions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class RuntimeRecord:
    """描述当前进程实际加载的 SQLite 运行库。"""

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
# 抽象进程身份查询，允许持久化流程使用真实或合成提供方。
# ---------------------------------------------------------------------------
class IdentityProvider(Protocol):
    def current(self) -> ProcessIdentity:
        """读取当前进程身份。"""
        ...

    def alive(self, identity: ProcessIdentity) -> bool:
        """确认所有者是否仍存活。查询失败必须抛出，避免把错误当作死亡。"""
        ...


# ---------------------------------------------------------------------------
# 由 SQLite 存储实现、供会话存储线程调用的事务接口。
# ---------------------------------------------------------------------------
class StoragePort(Protocol):
    """保存会话状态的接口，数据库连接在同一个专属线程创建、使用和关闭。

    实现应在每个写事务校验所有权，避免旧所有者覆盖接管后的数据。
    """

    def open_or_claim(self, identity: ProcessIdentity) -> tuple[DbOwner, RecoveryView]:
        """所有者仍活跃时拒绝接管。确认原所有者退出后递增代次，并返回恢复视图。"""
        ...

    def commit_intent(self, owner: DbOwner, intent: Intent) -> ToolResult | None:
        """执行副作用前先提交意图。相同 ToolRef 已有可信结果时返回该结果。"""
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
        """在同一事务内提交工具结果、关联运行状态和待投递事件。"""
        ...

    def commit_run_event(
        self, owner: DbOwner, run_update: RunRecord, event: OutboxEvent | None, *,
        operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> OutboxEvent | None:
        """无需提交工具结果时，可单独保存后台进展和关联事件。"""
        ...

    def prepare_shell(
        self, owner: DbOwner, tool_ref: ToolRef, run_ref: RunRef, snapshot: dict[str, Any]
    ) -> RunRecord:
        """在同一事务内关联已批准的 Bash 意图与唯一 runner 启动身份。"""
        ...

    def commit_shell_run(self, owner: DbOwner, run: RunRecord) -> None:
        """核对当前写入权后保存原执行及控制租约，工具结果已确认时直接复用。"""
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
        """同事务提交消息、后台状态和投递确认，返回新版本后才更新内存。"""
        ...

    def lookup_checkpoint_operation(
        self, owner: DbOwner, operation_id: str, *, request_digest: str | None = None
    ) -> CheckpointOperation | None:
        """读取已提交的检查点回执。未找到时仍可能有请求在执行。"""
        ...

    def record_recovery_decision(
        self, owner: DbOwner, decision_id: str, target: str, decision: str, explanation: str
    ) -> None:
        """同一决定可用原 ID 读取此前结果，内容冲突会被拒绝。核实结果不会重放工具。"""
        ...

    def prepare_recovery(self, owner: DbOwner, material_errors: dict[str, str] | None = None) -> None:
        """标记已失联的执行器和缺失附件，供恢复流程核对。"""
        ...

    def commit_recovery(
        self, owner: DbOwner, decision: RecoveryDecision, expected_revision: int,
        checkpoint: Checkpoint,
    ) -> RecoveryReceipt:
        """同事务保存恢复决定、受影响的工具或执行记录，以及用户消息。"""
        ...

    def load_recovery_view(self) -> RecoveryView:
        """从同一只读视图核对会话、附件摘要和执行身份。"""
        ...

    def read_pending_events(self) -> tuple[OutboxEvent, ...]:
        """按数据库序号读取尚未投递的事件。"""
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
        """停止接收写入，只释放仍由当前存储端持有的所有权。"""
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
