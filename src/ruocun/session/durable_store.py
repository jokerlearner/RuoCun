"""StoragePort v1 产品实现（MM-593 / MM-601 / REC-01..03 / REC-09）。

冻结行为来源（只读解包副本）：``src/session/durable_store.ts`` 与
``durable_store.test.ts``、``src/session/sqlite.ts``、``src/session/recovery.ts``、
``src/session/process_identity.ts``。契约来源：``09-storage-extension-route.md``
``# StoragePort v1`` / ``# SQLite及文件路线``、``08-python-runtime-route.md``、
ADR-0005、任务 07 票。

本票实现「本票路径真正需要的最小子集」：全部九个端口方法均有可运行实现，
但下列细节明确留后续票（见交接与证据）：
- 完整 RunRecord 的 runner/进程身份/launch 关联、agent checkpoint 与 fork 材料；
- OutboxEvent 的完整快照/附件 hash、分模型费用桶、pending interaction 全字段；
- 双原子域 runner 收据导入、control_epoch / stream_generation（本票只实现
  owner_epoch）；完整恢复决定 UI 与后台调度。
关键保证不缩减：owner fencing（每个写事务内）、原子提交、未知结果保护、
失败保留原错、品牌/数据身份与版本拒绝、运行库门禁不静默回退。

任务15在既有RunRecord快照内增加Shell启动关联与control_epoch校验。
runner收据的实际身份及日志核验由manager完成，再经本端口提交。
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, replace
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
    verify_private_file,
)
from .contract import (
    FORMAT,
    LEGACY_SESSION_USER_VERSION,
    PRODUCT,
    STORAGE_VERSION,
    USER_VERSION,
    AcceptedInput,
    ArchiveImport,
    ArchiveOperation,
    ArchiveRewrite,
    Checkpoint,
    CheckpointOperation,
    CorruptDatabaseError,
    DbOwner,
    IdentityProvider,
    Intent,
    MissingCheckpointError,
    OutboxEvent,
    OwnerConflictError,
    OwnerFencedError,
    ProcessIdentity,
    RecoveryDecision,
    RecoveryReceipt,
    RecoveryView,
    RunRecord,
    RunRef,
    RuntimeGateError,
    RuntimeRecord,
    StoreError,
    ToolRecord,
    ToolRef,
    ToolResult,
    UnknownOutcomeBlockedError,
    VersionRejectError,
    archive_request_digest,
    checkpoint_operation_id,
    checkpoint_request_digest,
    task_inbox_messages,
)
from .messages import isValidToolResult
from .process_identity import RealIdentityProvider
from .sqlite_port import configure_connection, connect_database, transaction

if TYPE_CHECKING:
    import sqlite3

_T = TypeVar("_T")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE NOT NULL,
    json TEXT NOT NULL,
    delivered INTEGER
);
CREATE TABLE IF NOT EXISTS tools (
    scope TEXT NOT NULL,
    id TEXT NOT NULL,
    json TEXT NOT NULL,
    PRIMARY KEY(scope, id)
);
CREATE TABLE IF NOT EXISTS decisions (id TEXT PRIMARY KEY, json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoint_operations (
    id TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    revision INTEGER NOT NULL
);
"""

_TABLE_COLUMNS = {
    "meta": (("key", "TEXT", 0, 1), ("json", "TEXT", 1, 0)),
    "runs": (("id", "TEXT", 0, 1), ("json", "TEXT", 1, 0)),
    "events": (("seq", "INTEGER", 0, 1), ("id", "TEXT", 1, 0), ("json", "TEXT", 1, 0), ("delivered", "INTEGER", 0, 0)),
    "tools": (("scope", "TEXT", 1, 1), ("id", "TEXT", 1, 2), ("json", "TEXT", 1, 0)),
    "decisions": (("id", "TEXT", 0, 1), ("json", "TEXT", 1, 0)),
    "checkpoint_operations": (("id", "TEXT", 0, 1), ("request_digest", "TEXT", 1, 0), ("revision", "INTEGER", 1, 0)),
}


def _validate_schema(con: "sqlite3.Connection") -> None:
    tables = {str(row[0]) for row in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    if tables != set(_TABLE_COLUMNS):
        raise CorruptDatabaseError("会话数据库表结构不完整或未经版本迁移。")
    for name, expected in _TABLE_COLUMNS.items():
        actual = tuple((row[1], row[2], row[3], row[5]) for row in con.execute(f"PRAGMA table_info({name})"))
        if actual != expected:
            raise CorruptDatabaseError("会话数据库列结构不符。")
    if con.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise CorruptDatabaseError("会话数据库完整性校验失败。")


def _validated_checkpoint(con: "sqlite3.Connection") -> dict[str, Any]:
    if _read_meta(con, "pruned") is not None:
        raise VersionRejectError("会话已封存清理，拒绝恢复或重新取得执行权。")
    identity = _read_meta(con, "identity")
    if isinstance(identity, dict) and identity.get("storage_version") == 1:
        raise VersionRejectError("旧会话需要显式离线备份升级；请停止旧进程后使用 --upgrade-session。")
    if not isinstance(identity, dict) or (
        identity.get("product") != PRODUCT
        or identity.get("format") != FORMAT
        or identity.get("storage_version") != STORAGE_VERSION
    ):
        raise VersionRejectError("会话产品/数据身份不符，拒绝接管。")
    raw = _read_meta(con, "checkpoint")
    if not isinstance(raw, dict):
        raise MissingCheckpointError("会话缺少可信检查点，不能恢复为空会话。")
    checkpoint = _decode_checkpoint(raw)
    revision = _read_meta(con, "revision")
    if (
        checkpoint.session_id != identity.get("session_id")
        or not isinstance(revision, int) or isinstance(revision, bool)
        or checkpoint.revision != revision or revision < 1
    ):
        raise CorruptDatabaseError("检查点身份或 revision 与权威记录不一致。")
    _all_tools(con)
    _all_runs(con)
    _pending_events(con)
    from .archive import validate_projection
    validate_projection(con, checkpoint.session_id, "main", list(checkpoint.messages))
    return raw


# ---------------------------------------------------------------------------
# JSON 编解码（冻结来源以 json 列保存逻辑状态；不把 JSON 旁路当等价真相）
# ---------------------------------------------------------------------------
def _dumps(value: Any) -> str:
    # SQLite TEXT与HTTP均要求有效UTF-8；仅把孤立代理项转成合法JSON转义。
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8", errors="backslashreplace",
    ).decode("utf-8")


def _loads(text: str) -> Any:
    return json.loads(text)


def _read_meta(con: "sqlite3.Connection", key: str) -> Any | None:
    row = con.execute("SELECT json FROM meta WHERE key=?", (key,)).fetchone()
    return _loads(row[0]) if row else None


def _put_meta(con: "sqlite3.Connection", key: str, value: Any) -> None:
    con.execute(
        "INSERT INTO meta VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET json=excluded.json",
        (key, _dumps(value)),
    )


def _decode_process_identity(data: dict[str, Any]) -> ProcessIdentity:
    return ProcessIdentity(
        host=str(data["host"]), boot=str(data["boot"]),
        pid=int(data["pid"]), start=str(data["start"]),
    )


def _decode_owner(data: dict[str, Any]) -> DbOwner:
    return DbOwner(
        session_id=str(data["session_id"]),
        canonical_cwd=str(data["canonical_cwd"]),
        instance_id=str(data["instance_id"]),
        owner_epoch=int(data["owner_epoch"]),
        identity=_decode_process_identity(dict(data["identity"])),
    )


def _decode_run_ref(data: dict[str, Any]) -> RunRef:
    return RunRef(task_id=str(data["task_id"]), run_id=str(data["run_id"]))


def _decode_tool_ref(data: dict[str, Any]) -> ToolRef:
    return ToolRef(scope=str(data["scope"]), tool_call_id=str(data["tool_call_id"]))


def _decode_intent(data: dict[str, Any] | None) -> Intent | None:
    if data is None:
        return None
    return Intent(
        tool_ref=_decode_tool_ref(dict(data["tool_ref"])),
        run_ref=_decode_run_ref(dict(data["run_ref"])),
        name=str(data["name"]),
        args=str(data["args"]),
        args_digest=str(data["args_digest"]),
        side_effect=bool(data["side_effect"]),
        approval_ref=str(data["approval_ref"]),
        policy_version=str(data["policy_version"]),
        owner_epoch=int(data["owner_epoch"]),
        created_at=str(data["created_at"]),
        parent_tool_ref=_decode_tool_ref(data["parent_tool_ref"]) if data.get("parent_tool_ref") is not None else None,
    )


def _decode_tool_record(data: dict[str, Any]) -> ToolRecord:
    ref = _decode_tool_ref(dict(data["tool_ref"]))
    result = data.get("result")
    if result is not None and not isValidToolResult(result, ref.tool_call_id):
        raise CorruptDatabaseError("工具结果不是可配对的完整ToolMessage或文字。")
    return ToolRecord(
        tool_ref=ref,
        name=str(data["name"]),
        args=str(data["args"]),
        state=str(data["state"]),  # type: ignore[arg-type]
        result=result,
        intent=_decode_intent(data.get("intent")),
        decision_ref=data.get("decision_ref"),
    )


def _decode_run_record(data: dict[str, Any]) -> RunRecord:
    return RunRecord(
        run_ref=_decode_run_ref(dict(data["run_ref"])),
        kind=str(data["kind"]),  # type: ignore[arg-type]
        status=str(data["status"]),
        cancel_requested=bool(data["cancel_requested"]),
        snapshot=dict(data["snapshot"]),
    )


def _decode_event(data: dict[str, Any], seq: int, delivered: int | None) -> OutboxEvent:
    return OutboxEvent(
        event_id=str(data["event_id"]),
        session_id=str(data["session_id"]),
        run_ref=_decode_run_ref(dict(data["run_ref"])),
        event_type=str(data["event_type"]),
        snapshot=dict(data["snapshot"]),
        owner_epoch=int(data["owner_epoch"]),
        seq=seq,
        delivered_revision=delivered,
    )


def _event_payload(event: OutboxEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "session_id": event.session_id,
        "run_ref": asdict(event.run_ref),
        "event_type": event.event_type,
        "snapshot": event.snapshot,
        "owner_epoch": event.owner_epoch,
    }


def _decode_accepted_input(data: dict[str, Any]) -> AcceptedInput:
    return AcceptedInput(
        input_id=str(data["input_id"]),
        seq=int(data["seq"]),
        payload=str(data["payload"]),
        attachment_refs=tuple(str(x) for x in data["attachment_refs"]),
        state=str(data["state"]),  # type: ignore[arg-type]
    )


def copy_background(value: Any) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, dict) else None


def _decode_checkpoint(data: dict[str, Any]) -> Checkpoint:
    return Checkpoint(
        session_id=str(data["session_id"]),
        messages=tuple(dict(m) for m in data["messages"]),
        model=str(data["model"]),
        mode=str(data["mode"]),
        title=str(data["title"]),
        revision=int(data["revision"]),
        accepted_inputs=tuple(
            _decode_accepted_input(dict(a)) for a in data["accepted_inputs"]
        ),
        pending_event_ids=tuple(str(x) for x in data["pending_event_ids"]),
        usage={str(k): int(v) for k, v in dict(data["usage"]).items()},
        background_state=str(data["background_state"]),
        delivered_revision=int(data["delivered_revision"]),
        background=copy_background(data.get("background")),
        task_title=data.get("task_title"),
        reflection_state=copy_background(data.get("reflection_state")),
    )


# ---------------------------------------------------------------------------
# 表级读写助手（都接受 con，不自行开启事务，避免线程内/跨 await 伪嵌套）
# ---------------------------------------------------------------------------
def _read_tool(con: "sqlite3.Connection", ref: ToolRef) -> ToolRecord | None:
    row = con.execute(
        "SELECT json FROM tools WHERE scope=? AND id=?",
        (ref.scope, ref.tool_call_id),
    ).fetchone()
    return _decode_tool_record(_loads(row[0])) if row else None


def _put_tool(con: "sqlite3.Connection", record: ToolRecord) -> None:
    con.execute(
        "INSERT INTO tools VALUES (?,?,?) "
        "ON CONFLICT(scope,id) DO UPDATE SET json=excluded.json",
        (record.tool_ref.scope, record.tool_ref.tool_call_id, _dumps(asdict(record))),
    )


def _put_run(con: "sqlite3.Connection", run: RunRecord) -> None:
    con.execute(
        "INSERT INTO runs VALUES (?,?) "
        "ON CONFLICT(id) DO UPDATE SET json=excluded.json",
        (run.run_ref.run_id, _dumps(asdict(run))),
    )


def _read_run(con: "sqlite3.Connection", run_ref: RunRef) -> RunRecord | None:
    row = con.execute("SELECT json FROM runs WHERE id=?", (run_ref.run_id,)).fetchone()
    return _decode_run_record(_loads(row[0])) if row else None


def _put_event(con: "sqlite3.Connection", event: OutboxEvent) -> OutboxEvent:
    payload = _event_payload(event)
    con.execute(
        "INSERT INTO events(id,json) VALUES (?,?) ON CONFLICT(id) DO NOTHING",
        (event.event_id, _dumps(payload)),
    )
    row = con.execute(
        "SELECT seq,json,delivered FROM events WHERE id=?", (event.event_id,)
    ).fetchone()
    if row is None:
        raise StoreError("事件写入后无法读回，停止发布成功。")
    stored = _loads(row[1])
    if stored != payload:
        raise StoreError("重试同 event ID 且内容不符，拒绝把旧快照覆盖新 run。")
    delivered = row[2]
    return _decode_event(
        stored, int(row[0]), int(delivered) if delivered is not None else None
    )


def _all_tools(con: "sqlite3.Connection") -> list[ToolRecord]:
    return [
        _decode_tool_record(_loads(row[0]))
        for row in con.execute("SELECT json FROM tools").fetchall()
    ]


def _all_runs(con: "sqlite3.Connection") -> list[RunRecord]:
    return [
        _decode_run_record(_loads(row[0]))
        for row in con.execute("SELECT json FROM runs ORDER BY rowid").fetchall()
    ]


def _verify_task_inbox(con: "sqlite3.Connection", owner: DbOwner, before: RunRecord | None, after: RunRecord) -> None:
    pending = before.snapshot.get("task_inbox", []) if before is not None else []
    incoming = after.snapshot.get("task_inbox", [])
    if pending == incoming:
        return
    if (before is None or before.run_ref != after.run_ref or before.kind != after.kind
            or after.kind not in {"agent", "fork"} or before.status != "running" or after.status != "running"
            or not isinstance(pending, list) or not isinstance(incoming, list)):
        raise StoreError("代理收件箱与当前运行身份或状态不匹配。")
    if not incoming and pending:
        from .recovery import repairToolPairs

        prior_messages = before.snapshot.get("messages")
        if (not isinstance(prior_messages, list)
                or repairToolPairs(prior_messages) != prior_messages
                or after.snapshot.get("messages") != [*prior_messages, *task_inbox_messages(pending)]):
            raise StoreError("未在已配对边界保存追加指令，不能清除收件箱。")
        return
    if len(incoming) != len(pending) + 1 or incoming[:-1] != pending or not isinstance(incoming[-1], dict):
        raise StoreError("代理收件箱只能按发送顺序追加。")
    entry = incoming[-1]
    sender = entry.get("sender")
    if (not isinstance(sender, dict) or set(sender) != {"scope", "tool_call_id"} or sender.get("scope") != "main"
            or not isinstance(sender.get("tool_call_id"), str) or any(item.get("sender") == sender for item in pending)):
        raise StoreError("追加指令缺少唯一父工具身份。")
    tool = _read_tool(con, _decode_tool_ref(sender))
    args = _loads(tool.intent.args) if tool is not None and tool.intent is not None else None
    if (tool is None or tool.intent is None or tool.name != "TaskSend" or tool.state != "started"
            or not tool.intent.side_effect or tool.intent.owner_epoch != owner.owner_epoch
            or not isinstance(args, dict) or args.get("id") != after.run_ref.task_id
            or not isinstance(entry.get("message"), str) or entry["message"] != args.get("message")
            or replace(before, snapshot={**before.snapshot, "task_inbox": incoming}) != after):
        raise StoreError("追加指令不匹配当前持久 TaskSend 授权。")


def _verify_task_send_resume(con: "sqlite3.Connection", owner: DbOwner, run: RunRecord, *, registering: bool) -> None:
    data = run.snapshot
    sender, old = data.get("task_send_ref"), data.get("resumed_from")
    if (run.kind != "agent" or not isinstance(sender, dict) or sender.get("scope") != "main"
            or not isinstance(sender.get("tool_call_id"), str) or not isinstance(old, dict)
            or old.get("task_id") != run.run_ref.task_id or not isinstance(old.get("run_id"), str)
            or old["run_id"] == run.run_ref.run_id):
        raise StoreError("TaskSend 恢复缺少当前工具与原运行身份。")
    tool_ref = _decode_tool_ref(sender)
    tool = _read_tool(con, tool_ref)
    source = _read_run(con, RunRef(old["task_id"], old["run_id"]))
    args = _loads(tool.intent.args) if tool is not None and tool.intent is not None else None
    tool_states = {"started", "result_committed"}
    if not registering and run.status == "unknown":
        tool_states.add("outcome_unknown")
    if (tool is None or tool.name != "TaskSend" or tool.intent is None or not tool.intent.side_effect
            or tool.intent.owner_epoch != owner.owner_epoch or tool.state not in tool_states
            or registering and tool.state != "started" or not isinstance(args, dict) or args.get("id") != run.run_ref.task_id
            or not isinstance(args.get("message"), str) or not args["message"] or source is None
            or asdict(source.run_ref) != old or source.kind != "agent" or source.status not in {"completed", "failed", "canceled"}
            or source.snapshot.get("handoff_to") is not None or source.snapshot.get("parent_tool_ref") != data.get("parent_tool_ref")):
        raise StoreError("TaskSend 当前授权与已结束的原代理不匹配。")
    if not registering:
        return
    from .recovery import repairToolPairs

    all_runs = _all_runs(con)
    latest = next((entry for entry in reversed(all_runs) if entry.run_ref.task_id == run.run_ref.task_id), None)
    if (latest != source or any(entry.status == "unknown" for entry in all_runs)
            or any(record.state != "result_committed" for record in _all_tools(con) if record.tool_ref != tool_ref)):
        raise StoreError("TaskSend 原运行已变化或仍有未决操作，禁止恢复。")
    before, after = source.snapshot.get("recovery_material"), data.get("recovery_material")
    if not isinstance(before, dict) or not isinstance(after, dict) or before.get("agentType") in {"explore", "plan"}:
        raise StoreError("TaskSend 原代理缺少可继续的材料。")
    messages = before.get("messages")
    stable = ("model", "agentType", "definitionVersion", "worktree", "worktreeIdentity", "workspaceRoot",
              "workspaceIdentity", "provider", "baseUrl", "permissions", "externalPolicy", "requestedMode",
              "budget", "turnLimit", "turnsRemaining", "reasoningEffort")
    if (not isinstance(messages, list) or not messages or repairToolPairs(messages) != messages
            or any(before.get(key) != after.get(key) for key in stable) or after.get("toolPolicy") != "background"
            or type(before.get("turnsRemaining")) is not int or before["turnsRemaining"] <= 0):
        raise StoreError("TaskSend 原消息、模型、路径、权限或轮次材料不匹配。")
    expected = [*messages, *task_inbox_messages(source.snapshot.get("task_inbox", [])), {"role": "user", "content": args["message"]}]
    if data.get("messages") != expected or after.get("messages") != expected:
        raise StoreError("TaskSend 只允许从已配对原转录追加本次指令。")


def _verify_foreground_handoff(con: "sqlite3.Connection", run: RunRecord, parent_ref: dict[str, Any], *,
                               registering: bool) -> RunRecord | None:
    data = run.snapshot
    source_ref = data.get("foreground_handoff")
    if (run.kind not in {"agent", "fork"} or not isinstance(source_ref, dict) or set(source_ref) != {"task_id", "run_id"}
            or not all(isinstance(value, str) and value for value in source_ref.values())):
        raise StoreError("转后台缺少可信前台代理身份。")
    expected = RunRef(source_ref["task_id"], source_ref["run_id"])
    source = _read_run(con, expected)
    if (source is None or source.run_ref != expected or source.kind != run.kind
            or source.run_ref.run_id == run.run_ref.run_id or source.run_ref.task_id == run.run_ref.task_id
            or source.snapshot.get("foreground") is not True or source.snapshot.get("handoff_allowed") is not True
            or source.snapshot.get("parent_tool_ref") != parent_ref):
        raise StoreError("转后台来源与同一父Agent的前台记录不匹配。")
    before = source.snapshot
    material = data.get("recovery_material")
    isolation, tree = before.get("isolation"), before.get("isolation_tree")
    if (isolation not in (None, "remote") or isolation != data.get("isolation") or tree != data.get("isolation_tree")
            or isolation == "remote" and (not isinstance(tree, dict) or tree.get("root") != before.get("cwd")
                    or not isinstance(tree.get("branch"), str) or not tree["branch"].startswith("ruocun-wt-"))
            or isolation is None and tree is not None):
        raise StoreError("转后台不得改变原代理的隔离工作树。")
    if run.kind == "fork" and (isolation is not None or not isinstance(material, dict)
            or not isinstance(before.get("forkToolDigest"), str) or material.get("toolRosterDigest") != before["forkToolDigest"]):
        raise StoreError("转后台必须使用 fork 的原精确工具目录。")
    if not registering:
        if source.status != "completed" or before.get("handoff_to") != asdict(run.run_ref):
            raise StoreError("后台代理缺少原前台交接收据。")
        return None
    from .recovery import repairToolPairs

    messages = before.get("messages")
    remaining = before.get("turnsRemaining")
    if (source.status != "running" or source.cancel_requested or "handoff_to" in before
            or not isinstance(messages, list) or not messages or not all(isinstance(message, dict) for message in messages)
            or messages != data.get("messages") or repairToolPairs(messages) != messages
            or not isinstance(material, dict) or material.get("messages") != messages
            or type(remaining) is not int or not 0 < remaining <= before.get("turnLimit", 0)
            or any(material.get(key) != before.get(key) for key in ("model", "agentType", "definitionVersion", "turnLimit", "turnsRemaining"))
            or material.get("toolPolicy") != "background" or material.get("worktree") != before.get("cwd")
            or material.get("workspaceRoot") != before.get("workspaceRoot") or data.get("output_start") != before.get("output_start")
            or not isinstance(material.get("permissions"), dict) or material["permissions"].get("mode") != before.get("permissionMode")):
        raise StoreError("原前台代理尚无匹配的完整已保存边界。")
    if any(record.state != "result_committed" for record in _all_tools(con)
           if record.tool_ref.scope == source.run_ref.run_id):
        raise StoreError("原前台代理有未确认工具结果，禁止转后台。")
    prior_material = before.get("recovery_material")
    if isinstance(prior_material, dict) and any(material.get(key) != prior_material.get(key) for key in (
            "worktreeIdentity", "workspaceIdentity", "provider", "baseUrl", "permissions", "externalPolicy",
            "requestedMode", "budget", "reasoningEffort")):
        raise StoreError("原前台代理的工作区、端点或权限已变化，禁止转后台。")
    return source


def _pending_events(con: "sqlite3.Connection") -> list[OutboxEvent]:
    return [
        _decode_event(
            _loads(row[1]), int(row[0]),
            int(row[2]) if row[2] is not None else None,
        )
        for row in con.execute(
            "SELECT seq,json,delivered FROM events "
            "WHERE delivered IS NULL ORDER BY seq"
        ).fetchall()
    ]


def assert_runtime_gate(runtime: RuntimeRecord) -> None:
    """声明的受控清单必须与进程实际 sqlite3 运行库一致；不符即拒绝（不静默回退）。"""
    from .runtime import verify_controlled_runtime

    if runtime.gate != "met":
        raise RuntimeGateError(
            "运行库门禁未达（未核验受控 SQLite 3.54.1 候选），明确拒绝启用耐久恢复。"
        )
    actual = verify_controlled_runtime(Path(runtime.dll_path))
    if actual != runtime:
        raise RuntimeGateError(
            "实际运行库与声明的受控清单不符，拒绝启用耐久恢复。"
        )


def _verify_private_database_files(directory: Path) -> None:
    for name in ("session.db", "session.db-wal", "session.db-shm", "session.db-journal"):
        path = directory / name
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        verify_private_file(path)


# ---------------------------------------------------------------------------
# DurableStore
# ---------------------------------------------------------------------------
class DurableStore:
    """StoragePort v1 最小子集；连接由调用方在专属线程内创建/使用/关闭。"""

    def __init__(
        self,
        session_dir: Path,
        session_id: str,
        cwd: Path,
        runtime: RuntimeRecord,
        identities: IdentityProvider | None = None,
    ) -> None:
        self._dir = Path(session_dir)
        self._session_id = session_id
        self._cwd = Path(cwd)
        self._runtime = runtime
        self._identities: IdentityProvider = identities or RealIdentityProvider()
        self._instance_id = str(uuid.uuid4())
        self._con: "sqlite3.Connection | None" = None
        self._owner: DbOwner | None = None
        self._closed = False
        self._config: dict[str, Any] = {}
        self._namespace: PrivateDirectory | None = None

    @property
    def config(self) -> dict[str, Any]:
        """已读回的 WAL/FULL/busy_timeout/foreign_keys 配置证据。"""
        return dict(self._config)

    @property
    def runtime(self) -> RuntimeRecord:
        return self._runtime

    def _require_con(self) -> "sqlite3.Connection":
        if self._con is None:
            raise StoreError("会话存储尚未打开。")
        return self._con

    # ---- 版本/身份协商（REC-02） ----
    def _open_and_initialize(self) -> None:
        import sqlite3

        assert_runtime_gate(self._runtime)
        db_file = self._dir / "session.db"
        self._verify_database_files()
        con = connect_database(db_file)
        try:
            original = int(con.execute("PRAGMA user_version").fetchone()[0])
            tables = [
                str(row[0])
                for row in con.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
        except sqlite3.DatabaseError as exc:
            con.close()
            raise CorruptDatabaseError("会话数据库损坏或不可读，拒绝恢复。") from exc

        try:
            if original == LEGACY_SESSION_USER_VERSION:
                raise VersionRejectError(
                    "检测到不兼容的旧版会话；若存已保留原数据。"
                )
            if original not in (0, USER_VERSION):
                raise VersionRejectError(
                    f"不支持的会话存储版本 {original}，未修改原数据。"
                )
            if original == 0 and tables:
                raise VersionRejectError(
                    "非空版本 0 数据库；只初始化真正空数据库，拒绝覆写或转换。"
                )
            if original == USER_VERSION:
                _validate_schema(con)
                _validated_checkpoint(con)
            self._config = configure_connection(con)
            if original == 0:
                def initialize() -> None:
                    for statement in _SCHEMA_SQL.split(";"):
                        if statement.strip():
                            con.execute(statement)
                    con.execute(f"PRAGMA user_version={USER_VERSION}")
                    _put_meta(con, "identity", {
                        "product": PRODUCT,
                        "format": FORMAT,
                        "storage_version": STORAGE_VERSION,
                        "user_version": USER_VERSION,
                        "session_id": self._session_id,
                        "canonical_cwd": str(self._cwd.resolve()),
                    })
                transaction(con, initialize)
            self._verify_database_files()
        except BaseException as exc:
            con.close()
            if isinstance(exc, StoreError) or not isinstance(
                exc, (sqlite3.DatabaseError, ValueError, KeyError, TypeError)
            ):
                raise
            raise CorruptDatabaseError("会话数据库初始化/校验失败，拒绝恢复。") from exc
        self._con = con

    def _verify_database_files(self) -> None:
        _verify_private_database_files(self._dir)

    # ---- owner fencing ----
    def _assert_owner(self, owner: DbOwner) -> None:
        """每个写事务内校验当前 owner；旧 writer / 错误 epoch 一律 fence。"""
        if self._closed:
            raise StoreError("会话存储已关闭。")
        con = self._require_con()
        current = _read_meta(con, "owner")
        if not isinstance(current, dict):
            raise OwnerFencedError("会话所有权已失效，停止执行。")
        if (
            current.get("instance_id") != owner.instance_id
            or current.get("owner_epoch") != owner.owner_epoch
        ):
            raise OwnerFencedError("会话所有权已失效，停止执行。")

    def _atomic(
        self, owner: DbOwner, body: Callable[["sqlite3.Connection"], _T]
    ) -> _T:
        con = self._require_con()

        def wrapped() -> _T:
            self._assert_owner(owner)
            return body(con)

        return transaction(con, wrapped)

    # ---- StoragePort v1 ----
    def open_or_claim(
        self, identity: ProcessIdentity
    ) -> tuple[DbOwner, RecoveryView]:
        """拒活 owner；死 owner 接管递增 epoch；身份查询错误不冒充死亡。"""
        if self._con is not None or self._closed:
            raise StoreError("会话存储已经打开或关闭，不能重复建立所有权。")
        self._namespace = PrivateDirectory(self._dir)
        try:
            self._namespace.__enter__()
            self._open_and_initialize()
        except BaseException:
            self._namespace.close()
            self._namespace = None
            raise
        con = self._require_con()

        def claim() -> DbOwner:
            if _read_meta(con, "pruned") is not None:
                raise OwnerConflictError("会话已封存清理，拒绝重新取得执行权。")
            meta_identity = _read_meta(con, "identity")
            canonical = str(self._cwd.resolve())
            if isinstance(meta_identity, dict) and (
                meta_identity.get("session_id") != self._session_id
                or meta_identity.get("canonical_cwd") != canonical
            ):
                raise OwnerConflictError("会话身份或工作目录不匹配。")
            prior = _read_meta(con, "owner")
            if isinstance(prior, dict):
                prior_owner = _decode_owner(prior)
                if self._identities.alive(prior_owner.identity):
                    raise OwnerConflictError(
                        f"会话已由进程 {prior_owner.identity.pid} 使用，不能并发恢复。"
                    )
            epoch = int(_read_meta(con, "epoch") or 0) + 1
            owner = DbOwner(
                session_id=self._session_id,
                canonical_cwd=canonical,
                instance_id=self._instance_id,
                owner_epoch=epoch,
                identity=identity,
            )
            _put_meta(con, "owner", asdict(owner))
            _put_meta(con, "epoch", epoch)
            for record in _all_tools(con):
                if record.state == "started":
                    _put_tool(con, replace(record, state="outcome_unknown"))
            return owner

        try:
            self._owner = transaction(con, claim)
        except BaseException:
            self._con = None
            con.close()
            self._namespace.close()
            self._namespace = None
            raise
        return self._owner, self.load_recovery_view()

    def commit_intent(self, owner: DbOwner, intent: Intent) -> ToolResult | None:
        """副作用许可前提交；同 ToolRef 已知结果返回复用结果。"""

        def body(con: "sqlite3.Connection") -> ToolResult | None:
            existing = _read_tool(con, intent.tool_ref)
            if existing is not None:
                saved = existing.intent
                if saved is None or replace(
                    intent, owner_epoch=saved.owner_epoch, created_at=saved.created_at
                ) != saved:
                    raise StoreError("同一工具操作身份对应的最终参数或授权内容冲突。")
            if existing is not None and existing.state == "result_committed":
                return existing.result
            if intent.owner_epoch != owner.owner_epoch:
                raise OwnerFencedError("工具意图属于旧 owner epoch。")
            parent_ref = intent.parent_tool_ref
            background_child = False
            canceling_stop = False
            if parent_ref is not None:
                parent = _read_tool(con, parent_ref)
                run = _read_run(con, intent.run_ref)
                if run is not None and run.status == "canceling" and run.cancel_requested and intent.name == "SubagentStop":
                    from ..hooks.journal import hookIntentId
                    canceling_stop = intent.side_effect and intent.tool_ref.tool_call_id == hookIntentId(intent.name, run.run_ref.run_id)
                if (parent is None or parent.name != "Agent" or parent.intent is None
                        or not parent.intent.side_effect or parent.intent.parent_tool_ref is not None
                        or parent_ref.scope != "main" or run is None or run.run_ref != intent.run_ref
                        or run.kind not in {"agent", "fork"} or run.status != "running" and not canceling_stop
                        or intent.tool_ref.scope != run.run_ref.run_id
                        or run.snapshot.get("parent_tool_ref") != asdict(parent_ref)):
                    raise StoreError("子代理工具缺少匹配的当前父Agent执行授权。")
                background_child = "background_agent_epoch" in run.snapshot
                if background_child:
                    self._verify_background_agent(con, owner, run)
                else:
                    arguments = _loads(parent.intent.args)
                    if (parent.state != "started" or parent.intent.owner_epoch != owner.owner_epoch
                            or not isinstance(arguments, dict)
                            or (arguments.get("fork") is True) != (run.kind == "fork")):
                        raise StoreError("前台子代理缺少匹配的当前父Agent执行授权。")

            def unresolved(record: ToolRecord) -> bool:
                if record.state == "result_committed" or record.tool_ref == parent_ref:
                    return False
                active = record.intent
                if record.state != "started" or active is None or active.owner_epoch != owner.owner_epoch:
                    return True
                if canceling_stop and record.name == "TaskStop" and record.tool_ref.scope == "main":
                    target = _loads(active.args)
                    if isinstance(target, dict) and target.get("id") == intent.run_ref.task_id:
                        return False  # The matching cancellation is already durable; its text receipt may still be writing.
                task_control = intent.name in {"TaskStop", "TaskSend"} and intent.tool_ref.scope == "main"
                if (background_child or task_control and intent.name == "TaskSend") and not active.side_effect:
                    return False
                if task_control:
                    target = _loads(intent.args)
                    active_run = next((run for run in _all_runs(con) if run.run_ref.run_id == record.tool_ref.scope), None)
                    if (isinstance(target, dict) and active_run is not None and target.get("id") == active_run.run_ref.task_id
                            and active_run.kind in {"agent", "fork"} and active_run.status == "running"
                            and "background_agent_epoch" in active_run.snapshot and active.parent_tool_ref is not None):
                        self._verify_background_agent(con, owner, active_run)
                        return False
                return True

            blocked = any(unresolved(record) for record in _all_tools(con)) or any(run.status == "unknown" for run in _all_runs(con))
            if existing is not None or (intent.side_effect and blocked):
                raise UnknownOutcomeBlockedError(
                    "存在结果未知的操作。请先通过恢复视图只读核实；"
                    "未决工具由用户显式 resolve，unknown 后台任务由 decide 处理后再执行。"
                )
            _put_tool(con, ToolRecord(
                tool_ref=intent.tool_ref,
                name=intent.name,
                args=intent.args,
                state="started",
                result=None,
                intent=intent,
                decision_ref=None,
            ))
            return None

        return self._atomic(owner, body)

    @staticmethod
    def _verify_background_agent(con: "sqlite3.Connection", owner: DbOwner, run: RunRecord, *, registering: bool = False) -> RunRecord | None:
        data = run.snapshot
        epoch = data.get("background_agent_epoch")
        if type(epoch) is not int or epoch != owner.owner_epoch:
            raise StoreError("后台代理运行许可属于不同会话 owner。")
        execution = data.get("background_execution")
        if (not isinstance(execution, dict) or execution.get("background") is not True or execution.get("kind") != run.kind
                or execution.get("taskId") != run.run_ref.task_id or execution.get("runId") != run.run_ref.run_id
                or execution.get("status") != run.status):
            raise StoreError("后台代理运行快照与持久许可不匹配。")
        parent_ref = data.get("parent_tool_ref")
        if not isinstance(parent_ref, dict) or parent_ref.get("scope") != "main" or not isinstance(parent_ref.get("tool_call_id"), str):
            raise StoreError("后台代理缺少原父Agent身份。")
        parent = _read_tool(con, ToolRef("main", parent_ref["tool_call_id"]))
        if parent is None or parent.name != "Agent" or parent.intent is None or not parent.intent.side_effect:
            raise StoreError("后台代理缺少真实父Agent工具意图。")
        decision_id = data.get("decision_ref")
        if "task_send_ref" in data:
            if decision_id is not None or "foreground_handoff" in data:
                raise StoreError("后台代理的 TaskSend 许可来源冲突。")
            _verify_task_send_resume(con, owner, run, registering=registering)
            return None
        if decision_id is None:
            arguments = _loads(parent.intent.args)
            if "foreground_handoff" in data:
                if (parent.intent.owner_epoch != owner.owner_epoch or parent.state not in {"started", "result_committed"}
                        or registering and parent.state != "started" or not isinstance(arguments, dict)
                        or (arguments.get("fork") is True) != (run.kind == "fork") or arguments.get("background") is True
                        or arguments.get("isolation") not in (None, "remote")
                        or arguments.get("isolation") == "remote" and data.get("isolation") != "remote"
                        or arguments.get("isolation") is None and arguments.get("isolate") is True):
                    raise StoreError("转后台缺少匹配的当前前台Agent授权。")
                return _verify_foreground_handoff(con, run, parent_ref, registering=registering)
            material = data.get("recovery_material")
            selected_type = arguments.get("agent_type") or "general-purpose" if isinstance(arguments, dict) else None
            definition_background = (data.get("background_by_definition") is True and isinstance(material, dict)
                                     and material.get("agentType") == selected_type == data.get("agentType")
                                     and isinstance(material.get("definitionVersion"), str)
                                     and bool(re.fullmatch(r"[0-9a-f]{64}", material["definitionVersion"])))
            if (parent.intent.owner_epoch != owner.owner_epoch or parent.state not in {"started", "result_committed"}
                    or registering and parent.state != "started"
                    or not isinstance(arguments, dict) or (arguments.get("fork") is True) != (run.kind == "fork")
                    or not (arguments.get("background") is True or (run.kind == "agent" and definition_background))):
                raise StoreError("后台代理启动与当前父Agent工具许可不符。")
            return None
        row = con.execute("SELECT json FROM decisions WHERE id=?", (decision_id,)).fetchone()
        request = _loads(row[0]).get("request") if row else None
        if (not isinstance(request, dict) or request.get("action") != "continue"
                or request.get("new_run") != asdict(run.run_ref) or request.get("target") != run.run_ref.task_id):
            raise StoreError("后台代理缺少匹配的本次持久继续许可。")
        return None

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
        """结果 + 关联 run 状态 + outbox 事件同一 DB 事务；COMMIT 前不发布成功。"""

        digest = archive_request_digest(run_update, event, tool_ref=tool_ref, result=result,
                                        archive_rewrite=archive_rewrite, archive_import=archive_import)
        op_id = operation_id or "run-v1:" + uuid.uuid4().hex

        def body(con: "sqlite3.Connection") -> None:
            if self._archive_operation(con, op_id, digest) is not None:
                return
            if not isValidToolResult(result, tool_ref.tool_call_id):
                raise StoreError("工具结果不是身份匹配的完整ToolMessage或文字。")
            record = _read_tool(con, tool_ref)
            if record is None:
                raise StoreError("缺少工具执行意图，拒绝无意图的结果提交。")
            if record.intent is None:
                raise StoreError("工具记录缺少可信执行关联。")
            expected_run = record.intent.run_ref
            if run_update is not None and run_update.run_ref != expected_run:
                raise StoreError("工具结果与后台运行关联冲突。")
            if event is not None and (
                event.session_id != self._session_id or event.run_ref != expected_run
            ):
                raise StoreError("工具结果与会话/事件运行关联冲突。")
            if record.state == "result_committed":
                if record.result == result:
                    if archive_rewrite is not None or archive_import is not None:
                        raise StoreError("工具结果已保存但缺少本次归档操作回执，拒绝重新改写。")
                    return
                raise StoreError("同一操作已有不同结果，拒绝覆盖。")
            _put_tool(con, replace(record, state="result_committed", result=result))
            updated_run = run_update or _read_run(con, expected_run)
            if updated_run is not None and updated_run.kind == "shell" and updated_run.snapshot.get("tool_ref") == asdict(tool_ref):
                updated_run = replace(updated_run, snapshot={**updated_run.snapshot, "tool_result": result})
            if updated_run is not None:
                self._archive_run(con, updated_run, archive_rewrite, archive_import)
                if updated_run.kind == "shell":
                    self._save_shell_run(con, updated_run)
                else:
                    _put_run(con, updated_run)
            if event is not None:
                _put_event(con, event)
            self._save_archive_operation(con, op_id, digest, expected_run.run_id, None)

        self._atomic(owner, body)

    def prepare_shell(
        self, owner: DbOwner, tool_ref: ToolRef, run_ref: RunRef, snapshot: dict[str, Any]
    ) -> RunRecord:
        def body(con: "sqlite3.Connection") -> RunRecord:
            tool = _read_tool(con, tool_ref)
            if (tool is None or tool.intent is None or tool.name != "Bash"
                    or tool.state != "started" or tool.intent.owner_epoch != owner.owner_epoch):
                raise StoreError("缺少当前owner已提交的Bash启动意图。")
            associated = [run for run in _all_runs(con) if run.snapshot.get("tool_ref") == asdict(tool_ref)]
            if associated:
                existing = associated[0]
                if existing.run_ref == run_ref and all(existing.snapshot.get(key) == snapshot.get(key)
                        for key in ("launch_id", "plan_digest", "run_dir")):
                    return existing
                raise StoreError("同一Bash意图已经关联其它执行，拒绝重新启动。")
            if _read_run(con, run_ref) is not None:
                raise StoreError("执行身份已经被使用。")
            epoch = snapshot.get("control_epoch")
            if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 0:
                raise StoreError("runner缺少有效control_epoch。")
            run = RunRecord(run_ref, "shell", "launching", False,
                            {**snapshot, "tool_ref": asdict(tool_ref), "storage_link_version": 1})
            _put_tool(con, replace(tool, intent=replace(tool.intent, run_ref=run_ref)))
            _put_run(con, run)
            return run

        return self._atomic(owner, body)

    def _save_shell_run(self, con: "sqlite3.Connection", run: RunRecord, *, background_update: bool = False) -> None:
        existing = _read_run(con, run.run_ref)
        if existing is None or existing.run_ref != run.run_ref or run.kind != "shell":
            raise StoreError("runner缺少已登记执行身份。")
        immutable = ("tool_ref", "storage_link_version", "launch_id", "plan_digest", "run_dir")
        if any(existing.snapshot.get(key) != run.snapshot.get(key) for key in immutable):
            raise StoreError("runner执行关联与原启动记录不符。")
        epoch, previous = run.snapshot.get("control_epoch"), existing.snapshot.get("control_epoch")
        if (not isinstance(epoch, int) or isinstance(epoch, bool)
                or not isinstance(previous, int) or epoch < previous):
            raise StoreError("runner控制租约已经过期。")
        old_endpoint = existing.snapshot.get("endpoint")
        if epoch == previous and old_endpoint is not None and old_endpoint != run.snapshot.get("endpoint"):
            raise StoreError("更换控制端点必须递增control_epoch。")
        if existing.status in {"completed", "failed", "canceled", "failed-before-grant"} and run.status != existing.status:
            raise StoreError("已确认终态不能回到其它状态。")
        runner_identity = existing.snapshot.get("runner_identity")
        if runner_identity and runner_identity != run.snapshot.get("runner_identity"):
            raise StoreError("已确认runner身份不能被新进程替换。")
        if run.status in {"completed", "failed", "canceled"}:
            receipt_digest = run.snapshot.get("receipt_digest")
            if not isinstance(receipt_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", receipt_digest):
                raise StoreError("终态缺少已核验收据摘要。")
        raw_ref = run.snapshot.get("tool_ref")
        if not isinstance(raw_ref, dict):
            raise StoreError("runner缺少工具关联。")
        tool_ref = ToolRef(str(raw_ref["scope"]), str(raw_ref["tool_call_id"]))
        tool = _read_tool(con, tool_ref)
        if tool is None or tool.intent is None or tool.intent.run_ref != run.run_ref:
            raise StoreError("runner与工具意图不匹配。")
        result = run.snapshot.get("tool_result")
        if tool.state == "result_committed":
            result = tool.result
        elif isinstance(result, str) and run.status != "unknown":
            _put_tool(con, replace(tool, state="result_committed", result=result))
        snapshot = dict(run.snapshot)
        if not background_update and "background_execution" in existing.snapshot:
            snapshot["background_execution"] = existing.snapshot["background_execution"]
        if result is not None:
            snapshot["tool_result"] = result
        _put_run(con, replace(run, snapshot=snapshot))

    def commit_shell_run(self, owner: DbOwner, run: RunRecord) -> None:
        self._atomic(owner, lambda con: self._save_shell_run(con, run))

    @staticmethod
    def _is_task_description_update(prior: RunRecord, updated: RunRecord) -> bool:
        previous = prior.snapshot.get("background_execution")
        description = updated.snapshot.get("description")
        if prior.kind not in {"agent", "fork"} or not isinstance(previous, dict) or not isinstance(description, str):
            return False
        snapshot = {**prior.snapshot, "description": description, "background_execution": {**previous, "description": description}}
        return replace(prior, snapshot=snapshot) == updated

    def commit_run_event(
        self, owner: DbOwner, run_update: RunRecord, event: OutboxEvent | None, *,
        operation_id: str | None = None, archive_rewrite: ArchiveRewrite | None = None,
        archive_import: ArchiveImport | None = None,
    ) -> OutboxEvent | None:
        """无工具结果的后台进展；有 event 时 run+event 原子。"""

        digest = archive_request_digest(run_update, event, archive_rewrite=archive_rewrite, archive_import=archive_import)
        op_id = operation_id or "run-v1:" + uuid.uuid4().hex

        def body(con: "sqlite3.Connection") -> OutboxEvent | None:
            prior_receipt = self._archive_operation(con, op_id, digest)
            if prior_receipt is not None:
                saved = prior_receipt.get("result")
                return _decode_event(saved, saved["seq"], saved.get("delivered_revision")) if saved is not None else None
            if event is not None and (
                event.session_id != self._session_id or event.run_ref != run_update.run_ref
            ):
                raise StoreError("后台运行与会话/事件关联冲突。")
            if event is not None:
                execution = event.snapshot.get("execution")
                if (not isinstance(execution, dict) or execution.get("runId") != run_update.run_ref.run_id
                        or execution.get("taskId") != run_update.run_ref.task_id
                        or execution.get("kind") != run_update.kind or execution.get("status") != run_update.status
                        or execution.get("background") is not True
                        or event.event_type in {"completed", "failed", "canceled"} and execution.get("status") != event.event_type):
                    raise StoreError("后台事件快照执行身份或状态不匹配。")
                prefix = run_update.run_ref.run_id + ":message-parent:"
                if event.event_type == "message" and event.event_id.startswith(prefix):
                    ref = ToolRef(run_update.run_ref.run_id, event.event_id.removeprefix(prefix))
                    tool = _read_tool(con, ref)
                    if (tool is None or tool.name != "MessageParent" or tool.state != "started" or tool.intent is None
                            or not tool.intent.side_effect or tool.intent.owner_epoch != owner.owner_epoch
                            or tool.intent.run_ref != run_update.run_ref or event.snapshot.get("requiresAttention") is not True):
                        raise StoreError("父代理消息缺少当前子任务已保存的 MessageParent 意图。")
            prior = _read_run(con, run_update.run_ref)
            if run_update.kind == "monitor":
                self._verify_monitor(con, owner, prior, run_update)
            _verify_task_inbox(con, owner, prior, run_update)
            if prior is None and "task_send_ref" in run_update.snapshot and self._missing_attachments(con):
                raise StoreError("原会话附件未确认，禁止 TaskSend 恢复。")
            if run_update.kind == "manual" and (event is not None or "background_execution" in run_update.snapshot
                    or run_update.status not in {"running", "completed", "failed", "canceled"}
                    or prior is None and run_update.status != "running"
                    or prior is not None and prior.cancel_requested and not run_update.cancel_requested):
                raise StoreError("手工任务只能保存记录，不能发布执行事件或重启终态。")
            if event is None and prior is not None and self._is_task_description_update(prior, run_update):
                # This write touches only the visible description of an existing task,
                # including tasks created by a previous owner. Execution grants stay unchanged.
                _put_run(con, run_update)
                self._save_archive_operation(con, op_id, digest, run_update.run_ref.run_id, None)
                return None
            if run_update.kind == "shell" and (run_update.snapshot.get("storage_link_version") == 1
                    or prior is not None and prior.snapshot.get("storage_link_version") == 1):
                self._save_shell_run(con, run_update, background_update=True)
            else:
                if run_update.kind in {"agent", "fork"} and ("background_agent_epoch" in run_update.snapshot
                        or prior is not None and "background_agent_epoch" in prior.snapshot):
                    handoff_source = self._verify_background_agent(con, owner, run_update, registering=prior is None)
                    if prior is None and run_update.status != "running":
                        raise StoreError("后台代理首次登记必须为 running。")
                    if prior is not None and (prior.snapshot.get("parent_tool_ref") != run_update.snapshot.get("parent_tool_ref")
                            or prior.snapshot.get("decision_ref") != run_update.snapshot.get("decision_ref")
                            or prior.snapshot.get("foreground_handoff") != run_update.snapshot.get("foreground_handoff")
                            or prior.snapshot.get("task_send_ref") != run_update.snapshot.get("task_send_ref")
                            or prior.snapshot.get("resumed_from") != run_update.snapshot.get("resumed_from")
                            or prior.status != "unknown" and prior.snapshot.get("background_by_definition") != run_update.snapshot.get("background_by_definition")
                            or prior.cancel_requested and not run_update.cancel_requested
                            or prior.status == "canceling" and run_update.status == "running"
                            or prior.status in {"unknown", "interrupted"} and run_update.status != prior.status
                            and not (prior.status == "unknown" and prior.snapshot.get("phase") == "continuation-authorized"
                                     and run_update.snapshot.get("phase") == "continuation-running")):
                        raise StoreError("后台代理运行许可或状态转移与原登记不符。")
                    if handoff_source is not None:
                        _put_run(con, replace(handoff_source, status="completed", snapshot={
                            **handoff_source.snapshot, "handoff_to": asdict(run_update.run_ref),
                            "endedAt": run_update.snapshot.get("startedAt"),
                        }))
                if run_update.kind == "shell" and event is not None:
                    raise StoreError("旧Shell材料不能作为已认证后台事件发布。")
                if prior is not None and (prior.run_ref != run_update.run_ref or prior.kind != run_update.kind
                        or prior.status in {"completed", "failed", "canceled"} and run_update.status != prior.status):
                    raise StoreError("后台运行身份或已确认终态发生冲突。")
                _put_run(con, run_update)
            self._archive_run(con, run_update, archive_rewrite, archive_import)
            result = _put_event(con, event) if event is not None else None
            self._save_archive_operation(con, op_id, digest, run_update.run_ref.run_id,
                                         asdict(result) if result is not None else None)
            return result

        return self._atomic(owner, body)

    @staticmethod
    def _archive_operation(con: "sqlite3.Connection", operation_id: str, request_digest: str | None = None) -> dict[str, Any] | None:
        from .archive import digest
        if not operation_id or len(operation_id) > 256:
            raise StoreError("归档操作身份无效。")
        saved = _read_meta(con, "archive:operation:" + digest(operation_id))
        if saved is not None and (saved.get("operation_id") != operation_id
                                  or request_digest is not None and saved.get("request_digest") != request_digest):
            raise StoreError("归档操作 ID 内容冲突。")
        return saved

    def _save_archive_operation(self, con: "sqlite3.Connection", operation_id: str, request_digest: str,
                               scope: str, result: Any) -> None:
        from .archive import digest, projection
        _put_meta(con, "archive:operation:" + digest(operation_id), {
            "operation_id": operation_id, "request_digest": request_digest, "scope": scope,
            "revision": projection(con, scope)["revision"], "result": result})

    def _archive_run(self, con: "sqlite3.Connection", run: RunRecord,
                     rewrite: ArchiveRewrite | None = None, imported: ArchiveImport | None = None) -> None:
        from .archive import save_projection
        messages = run.snapshot.get("messages")
        material = run.snapshot.get("recovery_material")
        if not isinstance(messages, list) and isinstance(material, dict):
            messages = material.get("messages")
        if isinstance(messages, list) and run.kind in {"agent", "fork"}:
            if imported is not None:
                self._import_archive_materials(con, imported)
            save_projection(con, self._session_id, run.run_ref.run_id, messages, rewrite, imported)
        elif rewrite is not None or imported is not None:
            raise StoreError("归档改写缺少代理执行消息。")

    def lookup_archive_operation(self, operation_id: str, *, request_digest: str | None = None) -> ArchiveOperation | None:
        def read() -> ArchiveOperation | None:
            value = self._archive_operation(self._require_con(), operation_id, request_digest)
            return ArchiveOperation(value["operation_id"], value["request_digest"], value["scope"], value["revision"]) if value is not None else None
        return transaction(self._require_con(), read, readonly=True)

    @staticmethod
    def _verify_monitor(con: "sqlite3.Connection", owner: DbOwner,
                        prior: RunRecord | None, run: RunRecord) -> None:
        data = run.snapshot
        parent_ref = data.get("parent_tool_ref")
        if not isinstance(parent_ref, dict) or parent_ref.get("scope") != "main":
            raise StoreError("监控缺少原始工具授权。")
        parent = _read_tool(con, ToolRef(**parent_ref))
        if (parent is None or parent.name != "Monitor" or parent.intent is None
                or not parent.intent.side_effect or parent.intent.owner_epoch != owner.owner_epoch
                or parent.state not in {"started", "result_committed"}
                or data.get("monitor_epoch") != owner.owner_epoch):
            raise StoreError("监控授权或所有权已失效。")
        args = _loads(parent.intent.args)
        if not isinstance(args, dict):
            raise StoreError("监控参数无效。")
        persistent = args.get("persistent", False)
        expected_timeout = None if persistent else args.get("timeout_ms", 300000)
        if (args.get("command") != data.get("command") or prior is None and args.get("description") != data.get("description")
                or data.get("persistent") != persistent or data.get("timeout_ms") != expected_timeout
                or not isinstance(data.get("cwd"), str)):
            raise StoreError("监控执行与已批准参数不符。")
        if prior is None:
            if run.status != "running" or parent.state != "started" or run.cancel_requested:
                raise StoreError("监控首次登记状态无效。")
        else:
            fixed = ("monitor_epoch", "parent_tool_ref", "command", "cwd", "persistent", "timeout_ms", "startedAt")
            if (any(prior.snapshot.get(key) != data.get(key) for key in fixed)
                    or prior.cancel_requested and not run.cancel_requested
                    or prior.status in {"canceling", "unknown", "interrupted"} and run.status == "running"):
                raise StoreError("监控执行身份或取消状态发生冲突。")

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
        """Save checkpoint and idempotency receipt in the same transaction."""
        if checkpoint.session_id != self._session_id:
            raise StoreError("检查点会话身份不匹配。")
        digest = checkpoint_request_digest(expected_revision, checkpoint, consumed_event_ids,
                                           archive_rewrite=archive_rewrite, archive_import=archive_import)
        op_id = operation_id if operation_id is not None else checkpoint_operation_id(
            expected_revision, checkpoint, consumed_event_ids,
            archive_rewrite=archive_rewrite, archive_import=archive_import,
        )
        if not op_id or len(op_id) > 256:
            raise StoreError("检查点操作身份不能为空或超过 256 字符。")

        def body(con: "sqlite3.Connection") -> int:
            row = con.execute(
                "SELECT request_digest, revision FROM checkpoint_operations WHERE id=?",
                (op_id,),
            ).fetchone()
            if row is not None:
                if row[0] != digest:
                    raise StoreError("检查点操作 ID 内容冲突。")
                return int(row[1])
            current = int(_read_meta(con, "revision") or 0)
            if current != expected_revision:
                raise StoreError("revision 冲突，拒绝覆盖比自己更新的状态。")
            revision = current + 1
            from .archive import save_projection
            if archive_import is not None:
                self._import_archive_materials(con, archive_import)
            save_projection(con, self._session_id, "main", list(checkpoint.messages), archive_rewrite, archive_import)
            for event_id in consumed_event_ids:
                con.execute(
                    "UPDATE events SET delivered=? "
                    "WHERE id=? AND delivered IS NULL",
                    (revision, event_id),
                )
            _put_meta(con, "checkpoint", asdict(replace(
                checkpoint,
                revision=revision,
                delivered_revision=revision,
            )))
            _put_meta(con, "revision", revision)
            _put_meta(con, "updated_at", time_ns() // 1_000_000)
            con.execute(
                "INSERT INTO checkpoint_operations (id, request_digest, revision) VALUES (?, ?, ?)",
                (op_id, digest, revision),
            )
            return revision

        return self._atomic(owner, body)

    def archive_projection(self, scope: str = "main") -> dict[str, Any]:
        from .archive import projection
        return transaction(self._require_con(), lambda: projection(self._require_con(), scope), readonly=True)

    def archive_scopes(self) -> list[str]:
        from .archive import list_scopes
        return transaction(self._require_con(), lambda: list_scopes(self._require_con(), self._session_id), readonly=True)

    def archive_list(self, scope: str = "main", *, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        from .archive import list_archive
        return transaction(self._require_con(), lambda: list_archive(
            self._require_con(), self._session_id, scope, offset=offset, limit=limit), readonly=True)

    def archive_read(self, identity: str, scope: str = "main", *, offset: int = 0, limit: int = 4096) -> dict[str, Any]:
        from .archive import read_archive
        return transaction(self._require_con(), lambda: read_archive(
            self._require_con(), scope, identity, offset=offset, limit=limit), readonly=True)

    def archive_export(self, scope: str = "main", *, offset: int = 0, limit: int = 100,
                       versions: bool = False) -> dict[str, Any]:
        from .archive import export_archive
        return transaction(self._require_con(), lambda: export_archive(
            self._require_con(), self._session_id, scope, offset=offset, limit=limit, versions=versions), readonly=True)

    def archive_branch(self, scope: str = "main", *, indices: tuple[int, ...] | None = None) -> ArchiveImport:
        from .archive import branch_archive
        def read() -> ArchiveImport:
            return branch_archive(self._require_con(), self._session_id, scope, indices=indices)
        return transaction(self._require_con(), read, readonly=True)

    def _import_archive_materials(self, con: "sqlite3.Connection", imported: ArchiveImport) -> None:
        """Confirm private copies before publishing DB aliases; originals remain immutable."""
        import hashlib
        import stat

        registered = _read_meta(con, "attachments") or {}
        aliases = _read_meta(con, "archive:attachment_aliases") or {}
        for logical, fingerprint in imported.attachments.items():
            source = Path(imported.attachment_sources.get(logical, logical))
            if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
                raise StoreError("导入附件哈希无效。")
            try:
                info = source.lstat()
                if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or source.resolve() != source.absolute()
                        or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                    raise StoreError("导入附件不是普通文件。")
                data = source.read_bytes()
            except OSError as error:
                raise StoreError("导入附件不存在，分支未确认。") from error
            if hashlib.sha256(data).hexdigest() != fingerprint:
                raise StoreError("导入附件哈希不符，分支未确认。")
            suffix = source.suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,8}", source.suffix) else ".bin"
            target = self._dir / "archive-materials" / (fingerprint + suffix)
            with PrivateDirectory(target.parent):
                if target.exists():
                    verify_private_file(target)
                    if hashlib.sha256(target.read_bytes()).hexdigest() != fingerprint:
                        raise StoreError("分支私有附件已有不同内容，保留现场。")
                else:
                    atomic_publish(target, data)
                if hashlib.sha256(target.read_bytes()).hexdigest() != fingerprint:
                    raise StoreError("分支私有附件发布未确认。")
            registered[str(target)] = fingerprint
            aliases[logical] = str(target)
        _put_meta(con, "attachments", registered)
        _put_meta(con, "archive:attachment_aliases", aliases)

    def lookup_checkpoint_operation(
        self, owner: DbOwner, operation_id: str, *, request_digest: str | None = None
    ) -> CheckpointOperation | None:
        """Read committed receipt; None says nothing about an in-flight request."""
        def body(con: "sqlite3.Connection") -> CheckpointOperation | None:
            row = con.execute(
                "SELECT request_digest, revision FROM checkpoint_operations WHERE id=?",
                (operation_id,),
            ).fetchone()
            if row is None:
                return None
            if request_digest is not None and request_digest != row[0]:
                raise StoreError("检查点操作 ID 内容冲突。")
            return CheckpointOperation(operation_id, str(row[0]), int(row[1]))

        return self._atomic(owner, body)

    def record_recovery_decision(
        self,
        owner: DbOwner,
        decision_id: str,
        target: str,
        decision: str,
        explanation: str,
    ) -> None:
        """decision ID 幂等且内容冲突拒绝；resolve 不自动执行旧工具。"""

        def body(con: "sqlite3.Connection") -> None:
            if not explanation.strip():
                raise StoreError("请明确填写核实结果或处理决定。")
            payload = {
                "decision_id": decision_id,
                "target": target,
                "decision": decision,
                "explanation": explanation,
            }
            row = con.execute(
                "SELECT json FROM decisions WHERE id=?", (decision_id,)
            ).fetchone()
            if row is not None:
                if _loads(row[0]) != payload:
                    raise StoreError("恢复决定 ID 幂等冲突：同 ID 内容不符，拒绝。")
                return
            con.execute(
                "INSERT INTO decisions VALUES (?,?)",
                (decision_id, _dumps(payload)),
            )
            if decision == "resolve":
                scope, separator, call_id = target.partition(":")
                if not separator:
                    raise StoreError("resolve 目标应为 scope:tool_call_id。")
                record = _read_tool(con, ToolRef(scope=scope, tool_call_id=call_id))
                if record is None or record.state != "outcome_unknown":
                    raise StoreError("只允许处理尚未核实的操作。")
                _put_tool(con, replace(
                    record,
                    state="result_committed",
                    result=f"[用户处理未决操作] {explanation}",
                    decision_ref=decision_id,
                ))

        self._atomic(owner, body)

    def prepare_recovery(self, owner: DbOwner, material_errors: dict[str, str] | None = None) -> None:
        """Frozen recovery.ts: missing results stay unresolved; lost agents never restart."""
        from .recovery import attachmentToolRef

        def body(con: "sqlite3.Connection") -> None:
            unresolved_children: dict[str, ToolRef] = {}
            for record in _all_tools(con):
                intent = record.intent
                if (record.state != "result_committed" and intent is not None and intent.side_effect
                        and intent.parent_tool_ref is not None):
                    unresolved_children[record.tool_ref.scope] = intent.parent_tool_ref
                if record.state == "started":
                    _put_tool(con, replace(record, state="outcome_unknown"))
            for run in _all_runs(con):
                if run.kind in {"agent", "fork", "monitor"} and run.status in {"running", "canceling"}:
                    parent = unresolved_children.get(run.run_ref.run_id)
                    unknown = (run.kind in {"agent", "fork"} and parent is not None
                               and run.snapshot.get("parent_tool_ref") == asdict(parent))
                    status = "unknown" if unknown else "interrupted"
                    message = ("子代理存在结果未确认的原操作，未自动继续。" if unknown else
                               "原代理执行器已丢失，未自动继续。")
                    snapshot = {**run.snapshot, "recovery_previous_status": run.status, "recovery": status}
                    raw = snapshot.get("background_execution")
                    if isinstance(raw, dict):
                        execution = {**raw, "status": status, "recovery": status}
                        snapshot["background_execution"] = execution
                        _put_event(con, OutboxEvent(run.run_ref.run_id + ":recovery-" + status, self._session_id,
                                   run.run_ref, status, {"execution": execution,
                                   "message": message, "requiresAttention": True}, owner.owner_epoch))
                    _put_run(con, replace(run, status=status, snapshot=snapshot))
            for run_id, error in (material_errors or {}).items():
                ref = ToolRef("recovery", "shell-material:" + run_id)
                if _read_tool(con, ref) is None:
                    _put_tool(con, ToolRecord(ref, "RecoveryMaterial", _dumps({"runId": run_id, "error": error}),
                                              "outcome_unknown", None, None, None))
            for file in self._missing_attachments(con):
                ref = attachmentToolRef(file)
                previous = _read_tool(con, ref)
                if previous is not None and previous.state == "result_committed":
                    digest = str((_read_meta(con, "attachments") or {}).get(file, "unknown"))
                    ref = ToolRef(ref.scope, ref.tool_call_id + ":" + digest)
                if _read_tool(con, ref) is None:
                    _put_tool(con, ToolRecord(ref, "MissingResultAttachment", _dumps({"path": file}),
                                              "outcome_unknown", None, None, None))

        self._atomic(owner, body)

    def commit_recovery(
        self, owner: DbOwner, decision: RecoveryDecision, expected_revision: int,
        checkpoint: Checkpoint,
    ) -> RecoveryReceipt:
        """Human attestation is never converted into an authenticated runner receipt."""
        from .recovery import repairToolPairs

        def body(con: "sqlite3.Connection") -> RecoveryReceipt:
            if (not decision.decision_id or len(decision.decision_id) > 256
                    or not decision.explanation.strip() or checkpoint.session_id != self._session_id):
                raise StoreError("恢复决定身份、说明或会话不合法。")
            payload = asdict(decision)
            row = con.execute("SELECT json FROM decisions WHERE id=?", (decision.decision_id,)).fetchone()
            if row is not None:
                prior = _loads(row[0])
                if prior.get("request") != payload:
                    raise StoreError("恢复决定 ID 幂等冲突：同 ID 内容不符，拒绝。")
                return RecoveryReceipt(int(prior["revision"]), True, decision.new_run)
            current = int(_read_meta(con, "revision") or 0)
            if current != expected_revision:
                raise StoreError("revision 冲突，恢复决定未提交。")
            if decision.action == "resolve":
                scope, separator, call_id = decision.target.partition(":")
                record = _read_tool(con, ToolRef(scope, call_id)) if separator else None
                if record is None or record.state != "outcome_unknown":
                    raise StoreError("只允许处理尚未核实的操作。")
                _put_tool(con, replace(record, state="result_committed",
                                      result="[用户处理未决操作] " + decision.explanation,
                                      decision_ref=decision.decision_id))
                if record.name == "RecoveryMaterial":
                    run_id = _loads(record.args).get("runId")
                    for run in _all_runs(con):
                        if run.run_ref.run_id == run_id and run.status in {"completed", "failed", "canceled"}:
                            _put_run(con, replace(run, snapshot={**run.snapshot,
                                      "recovery_material_accepted": decision.decision_id}))
                if record.name == "MissingResultAttachment":
                    path = _loads(record.args).get("path")
                    accepted = _read_meta(con, "recovery_accepted_missing") or {}
                    accepted[str(path)] = {"decision_ref": decision.decision_id,
                                           "digest": (_read_meta(con, "attachments") or {}).get(str(path)),
                                           "explanation": decision.explanation}
                    _put_meta(con, "recovery_accepted_missing", accepted)
            elif decision.action == "decide":
                runs = [run for run in _all_runs(con) if run.run_ref.task_id == decision.target]
                unknown = [run for run in runs if run.status == "unknown"]
                if (len(unknown) != 1 or runs[-1].run_ref != unknown[0].run_ref
                        or decision.status not in {"completed", "failed", "canceled"}):
                    raise StoreError("只能对唯一结果未知的运行作 completed/failed/canceled 人工核实。")
                run = unknown[0]
                snapshot = {**run.snapshot, "resolved_by_user": True, "decision_ref": decision.decision_id,
                            "recovery_previous_status": run.status, "user_evidence": decision.explanation,
                            "user_declared_status": decision.status}
                raw = snapshot.get("background_execution")
                if isinstance(raw, dict):
                    execution = {**raw, "status": decision.status, "result": "[用户核实] " + decision.explanation,
                                 "recovery": "resolved-by-user"}
                    snapshot["background_execution"] = execution
                    _put_event(con, OutboxEvent(run.run_ref.run_id + ":user-decision", self._session_id,
                               run.run_ref, decision.status, {"execution": execution,
                               "message": "[用户核实] " + decision.explanation, "requiresAttention": True},
                               owner.owner_epoch))
                _put_run(con, replace(run, status=decision.status, snapshot=snapshot))
                for record in _all_tools(con):
                    if (record.name == "Bash" and record.intent is not None
                            and record.intent.run_ref == run.run_ref and record.state == "outcome_unknown"):
                        _put_tool(con, replace(record, state="result_committed",
                                  result="[用户核实执行结果，非runner收据] " + decision.explanation,
                                  decision_ref=decision.decision_id))
            elif decision.action == "continue":
                if (decision.new_run is None or any(record.state != "result_committed" for record in _all_tools(con))
                        or any(run.status == "unknown" for run in _all_runs(con)) or self._missing_attachments(con)):
                    raise StoreError("继续执行缺少新身份或仍有未决工具/运行/附件。")
                prior_runs = [run for run in _all_runs(con) if run.run_ref.task_id == decision.target]
                if not prior_runs or prior_runs[-1].status != "interrupted" or prior_runs[-1].kind not in {"agent", "fork"}:
                    raise StoreError("只允许显式继续已中断的代理。")
                prior_run = prior_runs[-1]
                if (decision.new_run.task_id != prior_run.run_ref.task_id
                        or _read_run(con, decision.new_run) is not None):
                    raise StoreError("继续执行的新run身份冲突。")
                # A durable one-shot authorization precedes dispatch. If owner dies next,
                # its outcome stays unknown; no recovery path re-invokes this operation.
                snapshot = {**prior_run.snapshot, "continuation_of": asdict(prior_run.run_ref),
                            "decision_ref": decision.decision_id, "phase": "continuation-authorized"}
                snapshot.pop("background_execution", None)
                _put_run(con, RunRecord(decision.new_run, prior_run.kind, "unknown", False, snapshot))
            else:
                raise StoreError("未知恢复决定。")
            revision = current + 1
            messages = repairToolPairs(list(checkpoint.messages), tuple(_all_tools(con)))
            messages.append({"role": "user", "content": "[用户恢复决定] " + decision.command})
            from .archive import save_projection
            save_projection(con, self._session_id, "main", messages)
            _put_meta(con, "checkpoint", asdict(replace(checkpoint, messages=tuple(messages),
                      revision=revision, delivered_revision=revision)))
            _put_meta(con, "revision", revision)
            con.execute("INSERT INTO decisions VALUES (?,?)", (decision.decision_id,
                        _dumps({"request": payload, "revision": revision})))
            return RecoveryReceipt(revision, False, decision.new_run)

        return self._atomic(owner, body)

    def load_recovery_view(self) -> RecoveryView:
        """同一一致视图；检查附件 hash；不触发副作用。"""
        con = self._require_con()
        owner = self._owner
        if owner is None:
            raise StoreError("会话所有权尚未建立。")

        def read() -> RecoveryView:
            checkpoint_raw = _read_meta(con, "checkpoint")
            checkpoint = (
                _decode_checkpoint(checkpoint_raw)
                if isinstance(checkpoint_raw, dict) else None
            )
            return RecoveryView(
                owner=owner,
                checkpoint=checkpoint,
                tool_records=tuple(_all_tools(con)),
                runs=tuple(_all_runs(con)),
                pending_events=tuple(_pending_events(con)),
                missing_attachments=tuple(self._missing_attachments(con)),
                decisions=tuple(_loads(row[0]) for row in con.execute("SELECT json FROM decisions ORDER BY rowid")),
            )

        return transaction(con, read, readonly=True)

    def read_pending_events(self) -> tuple[OutboxEvent, ...]:
        return tuple(_pending_events(self._require_con()))

    def mark_interrupted_tools(self, owner: DbOwner) -> None:
        """恢复时 started 无可信结果 → outcome_unknown（不重执行）。"""

        def body(con: "sqlite3.Connection") -> None:
            for record in _all_tools(con):
                if record.state == "started":
                    _put_tool(con, replace(record, state="outcome_unknown"))

        self._atomic(owner, body)

    def add_attachment(self, owner: DbOwner, file: str, digest: str) -> None:
        """登记结果附件 hash；恢复时检验，缺失/变更成为明确未决。"""

        def body(con: "sqlite3.Connection") -> None:
            files = _read_meta(con, "attachments") or {}
            files[file] = digest
            _put_meta(con, "attachments", files)

        self._atomic(owner, body)

    def _missing_attachments(self, con: "sqlite3.Connection") -> list[str]:
        files = _read_meta(con, "attachments") or {}
        missing: list[str] = []
        accepted = _read_meta(con, "recovery_accepted_missing") or {}
        for name, digest in dict(files).items():
            if isinstance(accepted.get(str(name)), dict) and accepted[str(name)].get("digest") == digest:
                continue
            try:
                import hashlib

                actual = hashlib.sha256(Path(str(name)).read_bytes()).hexdigest()
            except OSError:
                missing.append(str(name))
                continue
            if actual != digest:
                missing.append(str(name))
        return missing

    def close(self, owner: DbOwner) -> None:
        """停止接受新写；只有仍为本 owner 才释放 owner，旧 writer 不能清掉新 owner。"""
        if self._closed:
            return
        con = self._require_con()
        try:

            def body() -> None:
                self._assert_owner(owner)
                _put_meta(con, "owner", None)

            transaction(con, body)
        finally:
            self._closed = True
            self._con = None
            try:
                con.close()
            finally:
                if self._namespace is not None:
                    self._namespace.close()
                    self._namespace = None


def read_durable_state(session_dir: Path, runtime: RuntimeRecord) -> dict[str, Any]:
    """只读恢复：忽略 JSON/events.jsonl 旁路，只认 SQLite 权威状态。

    未来版本 / 旧版 / 产品身份不符 / 缺可信 checkpoint / 损坏一律拒绝，
    不静默创建空会话、不自动转换、不退成 JSON 恢复。
    """
    assert_runtime_gate(runtime)
    if not (Path(session_dir) / "session.db").is_file():
        raise MissingCheckpointError("会话数据库不存在，拒绝恢复为空会话。")
    with PrivateDirectory(Path(session_dir), readonly=True, anchor_file="session.db"):
        return _read_durable_state_pinned(session_dir)


def inspect_durable_session(session_dir: Path, runtime: RuntimeRecord) -> dict[str, Any]:
    """Read checkpoint, ownership and outstanding work from one pinned transaction."""
    assert_runtime_gate(runtime)
    if not (Path(session_dir) / "session.db").is_file():
        raise MissingCheckpointError("会话数据库不存在。")
    with PrivateDirectory(Path(session_dir), readonly=True, anchor_file="session.db"):
        return _read_durable_state_pinned(session_dir, inspect=True)


def seal_durable_session(session_dir: Path, runtime: RuntimeRecord, *, cutoff_ms: int,
                         protected_paths: tuple[str, ...] | None = None) -> str | None:
    """Fence an old, inactive and fully settled session before filesystem cleanup."""
    assert_runtime_gate(runtime)
    directory = Path(session_dir)
    with PrivateDirectory(directory, readonly=True, anchor_file="session.db"):
        _verify_private_database_files(directory)
        con = connect_database(directory / "session.db")
        try:
            con.execute("BEGIN IMMEDIATE")
            if int(con.execute("PRAGMA user_version").fetchone()[0]) != USER_VERSION:
                raise VersionRejectError("清理目标的会话版本不兼容。")
            _validate_schema(con)
            state = _validated_checkpoint(con)
            owner = _read_meta(con, "owner")
            if isinstance(owner, dict) and RealIdentityProvider().alive(_decode_owner(owner).identity):
                return None
            stamp = _read_meta(con, "updated_at")
            if not isinstance(stamp, (int, float)):
                stamp = max(file.stat().st_mtime_ns for file in directory.glob("session.db*") if file.is_file()) / 1_000_000
            if (stamp >= cutoff_ms or state.get("background_state") != "closed"
                    or any(item.get("state") == "queued" for item in state.get("accepted_inputs", []))
                    or any(tool.state != "result_committed" for tool in _all_tools(con))
                    or any(run.status not in {"completed", "failed", "canceled"} for run in _all_runs(con))
                    or _pending_events(con) or protected_paths is None and (_read_meta(con, "attachments") or {})
                    or protected_paths is not None and any(Path(path).resolve().is_relative_to(directory.resolve())
                                                           for path in protected_paths)):
                return None
            nonce = uuid.uuid4().hex
            _put_meta(con, "pruned", nonce)
            _verify_private_database_files(directory)
            con.execute("COMMIT")
            return nonce
        finally:
            con.close()


def read_prune_seal(session_dir: Path, runtime: RuntimeRecord) -> str | None:
    assert_runtime_gate(runtime)
    directory = Path(session_dir)
    with PrivateDirectory(directory, readonly=True, anchor_file="session.db"):
        _verify_private_database_files(directory)
        con = connect_database(directory / "session.db", readonly=True)
        try:
            con.execute("BEGIN")
            _validate_schema(con)
            identity = _read_meta(con, "identity")
            if (not isinstance(identity, dict) or identity.get("product") != PRODUCT or identity.get("format") != FORMAT
                    or identity.get("storage_version") != STORAGE_VERSION):
                raise VersionRejectError("清理目标的产品身份不匹配。")
            nonce = _read_meta(con, "pruned")
            return nonce if isinstance(nonce, str) and re.fullmatch(r"[0-9a-f]{32}", nonce) else None
        finally:
            con.close()


def _read_durable_state_pinned(session_dir: Path, *, inspect: bool = False) -> dict[str, Any]:
    import sqlite3

    db_file = Path(session_dir) / "session.db"
    _verify_private_database_files(Path(session_dir))
    con = connect_database(db_file, readonly=True)
    try:
        con.execute("BEGIN")
        version = int(con.execute("PRAGMA user_version").fetchone()[0])
        if version != USER_VERSION:
            raise VersionRejectError(f"会话版本不兼容（{version}），未修改原数据。")
        _validate_schema(con)
        checkpoint = dict(_validated_checkpoint(con))
        if inspect:
            owner = _read_meta(con, "owner")
            decoded = _decode_owner(owner) if isinstance(owner, dict) else None
            checkpoint = {"checkpoint": checkpoint, "owner": owner, "identity": _read_meta(con, "identity"),
                          "owner_alive": decoded is not None and RealIdentityProvider().alive(decoded.identity),
                          "runs": [asdict(run) for run in _all_runs(con)],
                          "tools": [asdict(record) for record in _all_tools(con)],
                          "pending_events": [asdict(event) for event in _pending_events(con)]}
            stamp = _read_meta(con, "updated_at")
            fallback = max(file.stat().st_mtime_ns for file in (
                db_file, db_file.with_name("session.db-wal")) if file.exists()) // 1_000_000
            checkpoint["updated_at"] = stamp if isinstance(stamp, (int, float)) else fallback
            checkpoint["updated_at_source"] = "metadata" if stamp is not None else "database-mtime"
            checkpoint["attachments"] = _read_meta(con, "attachments")
            saved = checkpoint["checkpoint"]
            checkpoint["done"] = (saved.get("background_state") == "closed"
                                  and not any(item.get("state") == "queued" for item in saved.get("accepted_inputs", []))
                                  and all(item["state"] == "result_committed" for item in checkpoint["tools"])
                                  and all(item["status"] in {"completed", "failed", "canceled"} for item in checkpoint["runs"])
                                  and not checkpoint["pending_events"])
        _verify_private_database_files(Path(session_dir))
        return checkpoint
    except (sqlite3.DatabaseError, ValueError, KeyError, TypeError) as exc:
        raise CorruptDatabaseError("会话数据库损坏或不可读，拒绝恢复。") from exc
    finally:
        con.close()


__all__ = ["DurableStore", "read_durable_state", "assert_runtime_gate"]
