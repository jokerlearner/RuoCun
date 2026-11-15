"""离线将 v1 会话升级到带归档的 v3 格式。

显式调用前先停止仍在使用会话的进程。确认备份可独立验证后，才写入升级后的数据库。
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Any

from ..platform.windows.durable_file import (
    PrivateDirectory,
    atomic_publish,
    sync_directory,
    verify_private_file,
)
from .archive import canonical, save_projection, validate_projection
from .contract import (
    FORMAT,
    PRODUCT,
    STORAGE_VERSION,
    USER_VERSION,
    RuntimeRecord,
    StoreError,
    VersionRejectError,
)
from .durable_store import (
    _all_runs,
    _all_tools,
    _decode_checkpoint,
    _decode_owner,
    _decode_process_identity,
    _put_meta,
    _read_meta,
    _validate_schema,
    _verify_private_database_files,
    assert_runtime_gate,
)
from .process_identity import RealIdentityProvider
from .sqlite_port import connect_database, transaction


def upgrade_session(session_dir: Path, runtime: RuntimeRecord, *, expected_session_id: str | None = None,
                    cwd: Path | None = None) -> dict[str, Any]:
    """显式升级入口。先关闭仍在使用源数据库的旧进程。"""
    assert_runtime_gate(runtime)
    directory = Path(session_dir).absolute()
    if not (directory / "session.db").is_file():
        raise StoreError("升级目标会话数据库不存在。")
    with PrivateDirectory(directory, readonly=True, anchor_file="session.db"):
        _verify_private_database_files(directory)
        con = connect_database(directory / "session.db")
        try:
            if con.execute("PRAGMA user_version").fetchone()[0] != USER_VERSION:
                raise VersionRejectError("不支持此 SQL 结构版本的离线升级。")
            _validate_schema(con)
            identity = _read_meta(con, "identity")
            if (not isinstance(identity, dict) or identity.get("product") != PRODUCT
                    or identity.get("format") != FORMAT or identity.get("storage_version") != 1):
                raise VersionRejectError("仅支持显式升级若存 v1 会话；未来或已升级版本不会重写。")
            session_id = identity.get("session_id")
            if (not isinstance(session_id, str) or not session_id
                    or expected_session_id is not None and session_id != expected_session_id
                    or cwd is not None and identity.get("canonical_cwd") != str(Path(cwd).resolve())):
                raise StoreError("升级会话身份或工作区不匹配。")
            if _read_meta(con, "pruned") is not None:
                raise StoreError("已封存会话不能升级。")
            owner = _read_meta(con, "owner")
            if isinstance(owner, dict) and RealIdentityProvider().alive(_decode_owner(owner).identity):
                raise StoreError("会话仍有活动 owner；请先停止全部旧进程。")
            runs, tools = _all_runs(con), _all_tools(con)
            if any(tool.state != "result_committed" for tool in tools) or any(
                    run.status not in {"completed", "failed", "canceled", "interrupted"} for run in runs):
                raise StoreError("会话仍有活动执行或未确认结果，未升级。")
            for run in runs:
                runner = run.snapshot.get("runner_identity")
                if isinstance(runner, dict) and RealIdentityProvider().alive(_decode_process_identity(runner)):
                    raise StoreError("旧 runner 仍在运行，未升级。")
            checkpoint_data = _read_meta(con, "checkpoint")
            if not isinstance(checkpoint_data, dict):
                raise StoreError("旧会话缺少可信检查点。")
            checkpoint = _decode_checkpoint(checkpoint_data)
            revision = _read_meta(con, "revision")
            if (checkpoint.session_id != session_id or type(revision) is not int or revision < 1
                    or checkpoint.revision != revision):
                raise StoreError("旧会话检查点与身份或 revision 不一致。")
            attachments = _read_meta(con, "attachments") or {}
            for name, expected in attachments.items():
                file = Path(name)
                if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                    raise StoreError("旧会话附件缺失或哈希不符，未升级。")
            before = canonical([identity, owner, revision, checkpoint_data, attachments])
            backup_dir = directory.parent / f"{directory.name}-upgrade-backup-{uuid.uuid4().hex[:12]}"
            with PrivateDirectory(backup_dir):
                backup_file = backup_dir / "session.db"
                backup = connect_database(backup_file)
                try:
                    con.backup(backup)
                    _validate_schema(backup)
                    if canonical([_read_meta(backup, "identity"), _read_meta(backup, "owner"),
                                  _read_meta(backup, "revision"), _read_meta(backup, "checkpoint"),
                                  _read_meta(backup, "attachments") or {}]) != before:
                        raise StoreError("升级备份与源会话不一致，原数据保留。")
                finally:
                    backup.close()
                verify_private_file(backup_file)
                with backup_file.open("r+b") as stream:
                    os.fsync(stream.fileno())
                backup_hash = hashlib.sha256(backup_file.read_bytes()).hexdigest()
                attachment_file = backup_dir / "attachments.json"
                atomic_publish(attachment_file, canonical({"format": 1, "session_id": session_id,
                    "backup_sha256": backup_hash, "attachments": attachments,
                    "external_files_copied": False}).encode("utf-8"))
                sync_directory(backup_dir)

            def upgrade() -> None:
                if canonical([_read_meta(con, "identity"), _read_meta(con, "owner"),
                              _read_meta(con, "revision"), _read_meta(con, "checkpoint"),
                              _read_meta(con, "attachments") or {}]) != before:
                    raise StoreError("备份后会话发生变化，停止升级并要求重新备份。")
                save_projection(con, session_id, "main", list(checkpoint.messages), legacy_gap=True)
                for run in runs:
                    if run.kind not in {"agent", "fork"}:
                        continue
                    messages = run.snapshot.get("messages")
                    material = run.snapshot.get("recovery_material")
                    if not isinstance(messages, list) and isinstance(material, dict):
                        messages = material.get("messages")
                    if isinstance(messages, list):
                        save_projection(con, session_id, run.run_ref.run_id, messages, legacy_gap=True)
                _put_meta(con, "identity", {**identity, "storage_version": STORAGE_VERSION})
                _put_meta(con, "archive:upgrade", {"from_version": 1, "backup_path": str(backup_file),
                                                  "backup_sha256": backup_hash})
                validate_projection(con, session_id, "main", list(checkpoint.messages))
            transaction(con, upgrade)
            _verify_private_database_files(directory)
            return {"session_id": session_id, "backup_path": str(backup_file), "backup_sha256": backup_hash,
                    "attachment_manifest": str(attachment_file), "storage_version": STORAGE_VERSION}
        finally:
            con.close()
