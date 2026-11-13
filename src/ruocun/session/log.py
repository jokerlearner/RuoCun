"""Frozen session/log.ts (MIT), reading the native durable SQLite authority."""

from __future__ import annotations

import json
import os
import re
import stat
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict

from ..platform.windows.durable_file import atomic_publish, ensure_private_dir
from .contract import RuntimeRecord, StoreError
from .durable_store import inspect_durable_session


class SessionMeta(TypedDict, total=False):
    id: str
    cwd: str
    title: str
    updatedAt: float
    done: bool
    messageCount: int
    userMessageCount: int
    summary: str
    ownerAlive: bool
    protected: bool


def firstUserExcerpt(messages: Sequence[Mapping[str, Any]]) -> str | None:
    for message in messages:
        content = message.get("content")
        if message.get("role") == "user" and isinstance(content, str) and content.strip():
            flattened = re.sub(r"\s+", " ", content).strip()
            return flattened[:60] + "…" if len(flattened) > 60 else flattened
    return None


def _session_path(baseDir: Path, id: str) -> Path | None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", id) or id.endswith("."):
        return None
    path = Path(baseDir) / id
    try:
        attrs = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISDIR(attrs.st_mode) or getattr(attrs, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return None
    return path


def loadState(baseDir: Path, id: str, *, runtime: RuntimeRecord) -> dict[str, Any] | None:
    directory = _session_path(baseDir, id)
    if directory is None or not (directory / "session.db").is_file():
        return None
    view = inspect_durable_session(directory, runtime)
    saved = view["checkpoint"]
    if saved["session_id"] != id:
        raise StoreError("会话目录与持久身份不匹配，保留现场。")
    messages = saved["messages"]
    identity = view.get("identity")
    if not isinstance(identity, dict) or not isinstance(identity.get("canonical_cwd"), str):
        raise StoreError("会话缺少已保存的工作区身份。")
    return {
        "id": id, "cwd": identity["canonical_cwd"], "model": saved["model"], "mode": saved["mode"],
        "title": saved["title"], "taskTitle": saved.get("task_title", firstUserExcerpt(messages)), "messages": messages, "usage": saved["usage"],
        "updatedAt": view["updated_at"], "done": view["done"], "ownerAlive": view["owner_alive"],
        "protected": view["owner_alive"] or not view["done"], "backgroundWait": bool(view["pending_events"]),
    }


def loadMeta(baseDir: Path, id: str, *, runtime: RuntimeRecord) -> SessionMeta | None:
    state = loadState(baseDir, id, runtime=runtime)
    if state is None:
        return None
    messages = state["messages"]
    result: SessionMeta = {
        "id": state["id"], "cwd": state["cwd"], "title": state["title"], "updatedAt": state["updatedAt"],
        "done": state["done"], "messageCount": len(messages), "ownerAlive": state["ownerAlive"],
        "userMessageCount": sum(message.get("role") == "user" for message in messages), "protected": state["protected"],
    }
    if summary := state.get("taskTitle"):
        result["summary"] = summary
    return result


def _canonical(cwd: str) -> str:
    return os.path.normcase(str(Path(cwd).resolve()))


def listSessions(baseDir: Path, cwd: str | None = None, *, runtime: RuntimeRecord) -> list[SessionMeta]:
    try:
        children = list(Path(baseDir).iterdir())
    except FileNotFoundError:
        return []
    want = _canonical(cwd) if cwd is not None else None
    found = []
    for child in children:
        try:
            meta = loadMeta(baseDir, child.name, runtime=runtime)
        except (StoreError, OSError):
            continue  # An invalid candidate stays untouched and cannot be selected implicitly.
        if meta is not None and (want is None or _canonical(meta["cwd"]) == want):
            found.append(meta)
    return sorted(found, key=lambda meta: meta["updatedAt"], reverse=True)


def findResumable(baseDir: Path, cwd: str, *, runtime: RuntimeRecord) -> dict[str, Any] | None:
    for meta in listSessions(baseDir, cwd, runtime=runtime):
        if not meta["done"] and not meta["ownerAlive"] and meta["userMessageCount"]:
            return loadState(baseDir, meta["id"], runtime=runtime)
    return None


def exportSessionMarkdown(state: Mapping[str, Any]) -> str:
    def block(message: Mapping[str, Any]) -> str:
        content = message.get("content")
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2)
        metadata = {key: value for key, value in message.items() if key not in {"role", "content"}}
        detail = "\n\n```json\n" + json.dumps(metadata, ensure_ascii=False, indent=2) + "\n```" if metadata else ""
        return f"## {message.get('role', '')}\n\n{text}{detail}"
    blocks = [block(message) for message in state["messages"]]
    if state.get("legacy_gap"):
        blocks.insert(0, "> 旧摘要缺少已遗失原文：本导出仅包含当时实际保存的材料。")
    if state.get("boundaries"):
        blocks.append("## 历史投影边界（不重新执行）\n\n```json\n" +
                      json.dumps(state["boundaries"], ensure_ascii=False, indent=2) + "\n```")
    return "\n\n---\n\n".join(blocks)


def writeSessionExport(workspaceRoot: Path, state: Mapping[str, Any], *, json_format: bool = False) -> Path:
    import uuid
    from datetime import datetime, timezone

    directory = Path(workspaceRoot) / ".ruocun" / "exports"
    if not directory.parent.exists():
        ensure_private_dir(directory.parent)
    ensure_private_dir(directory)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(":", "-").replace(".", "-")
    file = directory / f"session-{timestamp}-{uuid.uuid4().hex[:8]}.{'json' if json_format else 'md'}"
    content = json.dumps(state, ensure_ascii=False, indent=2) if json_format else exportSessionMarkdown(state)
    atomic_publish(file, content.encode("utf-8"))
    return file


def writeArchiveExport(workspaceRoot: Path, session_id: str, scopes: list[str],
                       page: Callable[[str, int], dict[str, Any]], *, json_format: bool = False) -> Path:
    """Consume bounded archive pages into the same private, atomic file publisher."""
    import uuid
    from datetime import datetime, timezone

    directory = Path(workspaceRoot) / ".ruocun" / "exports"
    if not directory.parent.exists():
        ensure_private_dir(directory.parent)
    ensure_private_dir(directory)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(":", "-").replace(".", "-")
    file = directory / f"session-{timestamp}-{uuid.uuid4().hex[:8]}.{'json' if json_format else 'md'}"
    def encoded(value: Any) -> bytes:
        return json.dumps(value, ensure_ascii=False).encode("utf-8", errors="backslashreplace")
    revisions: dict[str, int] = {}
    def checked_page(scope: str, offset: int) -> dict[str, Any]:
        result = page(scope, offset)
        revision = result["revision"]
        if scope in revisions and revisions[scope] != revision:
            raise StoreError("导出期间执行范围发生变化，停止发布；请待后台稳定后重试。")
        revisions[scope] = revision
        return result
    def chunks() -> Iterator[bytes]:
        if json_format:
            yield b'{"view":"full","session_id":' + encoded(session_id) + b',"scopes":['
        for scope_index, scope in enumerate(scopes):
            first = checked_page(scope, 0)
            if json_format:
                yield (b"," if scope_index else b"") + b'{"scope":' + encoded(scope)
                yield b',"legacy_gap":' + encoded(first["legacy_gap"])
                yield b',"boundaries":' + encoded(first["boundaries"])
                yield b',"projection":' + encoded(first.get("projection"))
                for field in ("messages", "records", "derived", "attachments"):
                    yield b',"' + field.encode() + b'":['
                    offset = 0
                    started = False
                    current = first
                    while True:
                        for item in current.get(field, []):
                            yield (b"," if started else b"") + encoded(item)
                            started = True
                        if current["next_offset"] is None:
                            break
                        offset = current["next_offset"]
                        current = checked_page(scope, offset)
                    yield b"]"
                if "attachment_aliases" in first:
                    yield b',"attachment_aliases":' + encoded(first["attachment_aliases"])
                yield b"}"
            else:
                yield (f"# 执行范围 {scope}\n\n").encode("utf-8")
                current = first
                while True:
                    yield exportSessionMarkdown({"messages": current["messages"],
                        "legacy_gap": first["legacy_gap"] if current is first else False}).encode("utf-8", errors="backslashreplace")
                    yield b"\n\n---\n\n"
                    if current["next_offset"] is None:
                        break
                    current = checked_page(scope, current["next_offset"])
                yield exportSessionMarkdown({"messages": [], "boundaries": first["boundaries"]}).encode("utf-8")
        for scope in revisions:
            checked_page(scope, 0)
        if json_format:
            yield b"]}"
    atomic_publish(file, chunks())
    return file
