"""Immutable transcript segments inside the existing SQLite transaction.

The projection/raw distinction is informed by DeepSeek Harness (MIT), fixed at
e8f7b93a344964de3dca1ace9e72b6e4d6de87cb. No second connection or file authority.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import stat
from pathlib import Path
from time import time_ns
from typing import TYPE_CHECKING, Any

from .contract import ArchiveImport, ArchiveRewrite, StoreError

if TYPE_CHECKING:
    import sqlite3

_METADATA = {"imageDelivered", "responseItems", "reasoning_content", "reasoning_details"}
_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_SPILL = re.compile(r"\[完整输出 [^\r\n]*?已落盘:(.*?) —— 需要完整内容时用 Read")


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
        "utf-8", errors="backslashreplace").decode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def archiveIdForRange(messages: list[dict[str, Any]], start: int, end: int, kind: str,
                      namespace: str = "") -> str:
    """Program-generated short reference; callers supply their candidate identity."""
    return "d-" + digest([namespace, kind, start, end, messages])[:40]


def _read(con: "sqlite3.Connection", key: str) -> Any:
    row = con.execute("SELECT json FROM meta WHERE key=?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def _put(con: "sqlite3.Connection", key: str, value: Any) -> None:
    con.execute("INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET json=excluded.json",
                (key, canonical(value)))


def _scope(scope: str) -> str:
    if not isinstance(scope, str) or not scope or len(scope) > 256:
        raise StoreError("归档执行范围无效。")
    return hashlib.sha256(scope.encode("utf-8")).hexdigest()[:24]


def _record_key(scope: str, identity: str) -> str:
    if not isinstance(identity, str) or not _ID.fullmatch(identity):
        raise StoreError("归档 ID 无效；只接受当前范围内的记录身份。")
    return f"archive:record:{_scope(scope)}:{identity}"


def _projection_key(scope: str) -> str:
    return "archive:projection:" + _scope(scope)


def _display(child: Any) -> Any:
    if isinstance(child, dict):
        return {key: ("[图片负载保留在归档JSON中]" if key in {"base64", "imageData"} else _display(item))
                for key, item in child.items()}
    if isinstance(child, list):
        return [_display(item) for item in child]
    if isinstance(child, str) and child.startswith("data:image/"):
        return "[内联图片负载保留在归档JSON中]"
    return child


def manifest(con: "sqlite3.Connection", session_id: str) -> dict[str, Any]:
    value = _read(con, "archive:manifest")
    if value is None:
        return {"format": 1, "session_id": session_id, "scopes": {}, "scope_order": []}
    if not isinstance(value, dict) or value.get("format") != 1 or value.get("session_id") != session_id:
        raise StoreError("归档格式或会话身份不兼容。")
    if not isinstance(value.get("scopes"), dict):
        raise StoreError("归档范围清单损坏。")
    return value


def record(con: "sqlite3.Connection", scope: str, identity: str, trail: frozenset[str] = frozenset(), *,
           sources: bool = True) -> dict[str, Any]:
    if identity in trail:
        raise StoreError("归档来源循环，停止读取。")
    value = _read(con, _record_key(scope, identity))
    if not isinstance(value, dict) or value.get("id") != identity or value.get("scope") != scope:
        raise StoreError("当前执行范围未找到归档或记录已损坏。")
    payload = {key: child for key, child in value.items() if key != "digest"}
    if value.get("digest") != digest(payload):
        raise StoreError("归档内容哈希不符，停止读取。")
    if sources and value.get("kind") in {"summary", "prune"}:
        children = value.get("sources")
        if not isinstance(children, list) or not children:
            raise StoreError("派生归档缺少原文来源。")
        for source in children:
            record(con, scope, source, trail | {identity})
    return value


def _insert(con: "sqlite3.Connection", scope: str, value: dict[str, Any], index: list[dict[str, Any]]) -> None:
    value = {**value, "scope": scope}
    value["digest"] = digest(value)
    key = _record_key(scope, value["id"])
    old = _read(con, key)
    if old is not None:
        if old != value:
            raise StoreError("不可变归档 ID 对应不同内容。")
        return
    _put(con, key, value)
    index.append({key: value[key] for key in ("id", "kind", "created_at", "raw_seq", "version", "digest",
                                              "sources", "previous", "before_seq", "boundary", "origin_session",
                                              "origin_scope", "attachments") if key in value}
                 | ({"display_length": len(canonical(_display(value["message"])))} if "message" in value else {}))


def projection(con: "sqlite3.Connection", scope: str = "main") -> dict[str, Any]:
    _scope(scope)
    value = _read(con, _projection_key(scope))
    if value is None:
        return {"scope": scope, "revision": 0, "lineage": [], "messages_digest": digest([])}
    if not isinstance(value, dict) or value.get("scope") != scope or not isinstance(value.get("lineage"), list):
        raise StoreError("归档投影清单损坏。")
    messages = [record(con, scope, identity, sources=False)["message"] for identity in value["lineage"]]
    if value.get("messages_digest") != digest(messages):
        raise StoreError("归档投影哈希不符。")
    return value


def _append(con: "sqlite3.Connection", session: str, scope: str, state: dict[str, Any],
            old_refs: list[str], messages: list[dict[str, Any]]) -> list[str]:
    if len(messages) < len(old_refs):
        raise StoreError("历史投影缩短必须提供明确归档改写映射。")
    refs = list(old_refs)
    namespace = digest([session, scope])[:16]
    for position, message in enumerate(messages):
        previous = record(con, scope, refs[position], sources=False) if position < len(refs) else None
        if previous is not None:
            if previous["message"] == message:
                continue
            left = {k: v for k, v in previous["message"].items() if k not in _METADATA}
            right = {k: v for k, v in message.items() if k not in _METADATA}
            if left != right:
                raise StoreError("历史正文变更缺少明确来源映射，原归档保留。")
            if previous["kind"] != "raw":
                raise StoreError("派生消息元数据更新需要明确改写。")
            sequence, version = previous["raw_seq"], previous["version"] + 1
        else:
            sequence, version = state["next_raw_seq"], 1
            state["next_raw_seq"] += 1
        identity = f"{namespace}-r{sequence}v{version}"
        value = {"id": identity, "kind": "raw", "raw_seq": sequence, "version": version,
                 "message": copy.deepcopy(message), "created_at": time_ns() // 1_000_000,
                 "origin_session": previous.get("origin_session", session) if previous else session,
                 "origin_scope": previous.get("origin_scope", scope) if previous else scope}
        attachments = {**(previous.get("attachments", {}) if previous else {}), **_message_attachments(con, message)}
        if attachments:
            value["attachments"] = attachments
            registered = _read(con, "attachments") or {}
            aliases = _read(con, "archive:attachment_aliases") or {}
            for path, fingerprint in attachments.items():
                physical = aliases.get(path, path)
                if physical in registered and registered[physical] != fingerprint:
                    raise StoreError("归档附件内容已变化，保留原引用并停止保存。")
                registered[physical] = fingerprint
            _put(con, "attachments", registered)
        if previous is not None:
            value["previous"] = previous["id"]
        _insert(con, scope, value, state["index"])
        if position < len(refs):
            refs[position] = identity
        else:
            refs.append(identity)
    return refs


def _message_attachments(con: "sqlite3.Connection", message: dict[str, Any]) -> dict[str, str]:
    """Only the existing tool spill format and exact private workspace roots."""
    aliases = _read(con, "archive:attachment_aliases") or {}
    registered = _read(con, "attachments") or {}
    serialized = canonical(message)
    result = {}
    for physical, fingerprint in registered.items():
        logical = next((name for name, actual in aliases.items() if actual == physical), physical)
        if canonical(logical)[1:-1] in serialized:
            result[logical] = fingerprint
    if message.get("role") != "tool" or not isinstance(message.get("content"), str):
        return result
    identity = _read(con, "identity") or {}
    workspace = Path(identity.get("canonical_cwd", ""))
    allowed = {(workspace / ".ruocun" / name).absolute() for name in ("spill", "subagents")}
    for matched in _SPILL.finditer(message["content"]):
        file = Path(matched[1]).absolute()
        if file.parent not in allowed or file.resolve() != file or not file.name.endswith(".txt"):
            continue
        try:
            physical = Path(aliases.get(str(file), str(file)))
            info = physical.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
                raise StoreError("归档引用不是普通工具输出文件。")
            result[str(file)] = hashlib.sha256(physical.read_bytes()).hexdigest()
        except OSError as error:
            raise StoreError("归档工具输出引用缺失，未确认保存。") from error
    return result


def save_projection(con: "sqlite3.Connection", session: str, scope: str,
                    messages: list[dict[str, Any]], rewrite: ArchiveRewrite | None = None,
                    imported: ArchiveImport | None = None, *, legacy_gap: bool = False) -> None:
    """Called only inside the checkpoint/run transaction after owner fencing."""
    current = manifest(con, session)
    if scope not in current["scopes"]:
        current.setdefault("scope_order", list(current["scopes"])).append(scope)
    state = current["scopes"].setdefault(scope, {"revision": 0, "next_raw_seq": 1, "index": [],
                                                "legacy_gap": legacy_gap})
    prior = projection(con, scope)
    refs = prior["lineage"]
    if imported is not None:
        if refs or state["index"] or rewrite is not None:
            raise StoreError("只能将归档闭包导入新的空执行范围。")
        for saved in imported.records:
            if saved.get("digest") != digest({k: v for k, v in saved.items() if k != "digest"}):
                raise StoreError("导入归档内容哈希不符。")
            payload = {k: v for k, v in saved.items() if k not in {"digest", "scope"}}
            _insert(con, scope, payload, state["index"])
        refs = list(imported.lineage)
        restored = [record(con, scope, identity)["message"] for identity in refs]
        if messages[:len(restored)] != restored:
            raise StoreError("分支归档闭包与目标投影不一致。")
        state["legacy_gap"] = imported.legacy_gap
        state["branch_source"] = imported.source_session
        state["next_raw_seq"] = 1 + max((item.get("raw_seq", 0) for item in state["index"]), default=0)
        refs = _append(con, session, scope, state, refs, messages)
    elif rewrite is not None:
        expected = list(rewrite.expected_messages)
        refs = _append(con, session, scope, state, refs, expected)
        if len(rewrite.mapping) != len(messages) or rewrite.kind not in {"compact", "clear", "rewind", "prefix"}:
            raise StoreError("归档改写形状无效。")
        derived = {item.target_index: item for item in rewrite.derived}
        if len(derived) != len(rewrite.derived):
            raise StoreError("归档派生目标重复。")
        updated: list[str] = []
        for position, source in enumerate(rewrite.mapping):
            if source is not None:
                if type(source) is not int or not 0 <= source < len(refs) or expected[source] != messages[position]:
                    raise StoreError("归档保留来源与候选消息不一致。")
                updated.append(refs[source])
            elif position in derived:
                item = derived[position]
                if item.kind not in {"summary", "prune"} or not item.source_indices or any(
                        type(i) is not int or not 0 <= i < len(refs) for i in item.source_indices):
                    raise StoreError("派生来源范围无效。")
                value = {"id": item.id, "kind": item.kind, "sources": [refs[i] for i in item.source_indices],
                         "message": copy.deepcopy(messages[position]), "reason": item.reason,
                         "created_at": time_ns() // 1_000_000, "policy_version": 1}
                _insert(con, scope, value, state["index"])
                updated.append(item.id)
            elif messages[position].get("role") == "system" and (rewrite.kind == "prefix" or
                    rewrite.kind == "compact" and str(messages[position].get("content", "")).startswith("[当前任务清单]")):
                updated.extend(_append(con, session, scope, state, [], [messages[position]]))
            else:
                raise StoreError("新投影消息缺少原文或派生来源。")
        if rewrite.kind in {"clear", "rewind", "prefix"}:
            boundary = {"id": "b-" + digest([session, scope, state["revision"], rewrite.kind, messages])[:40],
                        "kind": "boundary", "boundary": rewrite.kind, "reason": rewrite.reason,
                        "sources": refs, "before_seq": state["next_raw_seq"], "created_at": time_ns() // 1_000_000}
            _insert(con, scope, boundary, state["index"])
        refs = updated
    else:
        refs = _append(con, session, scope, state, refs, messages)
    state["revision"] += 1
    _put(con, "archive:manifest", current)
    _put(con, _projection_key(scope), {"scope": scope, "revision": state["revision"],
                                      "lineage": refs, "messages_digest": digest(messages)})


def validate_projection(con: "sqlite3.Connection", session: str, scope: str,
                        messages: list[dict[str, Any]]) -> None:
    """Validate the active view and short reference graph without loading old bodies."""
    current = manifest(con, session)
    if scope not in current["scopes"]:
        raise StoreError("会话缺少归档范围清单。")
    state = current["scopes"][scope]
    index = {item["id"]: item for item in state["index"]}
    if len(index) != len(state["index"]):
        raise StoreError("归档索引身份重复。")
    done: set[str] = set()
    def visit(identity: str, trail: frozenset[str]) -> None:
        if identity in trail or identity not in index:
            raise StoreError("归档来源缺失或循环。")
        if identity in done:
            return
        for source in index[identity].get("sources", []):
            visit(source, trail | {identity})
        if index[identity].get("previous"):
            visit(index[identity]["previous"], trail | {identity})
        done.add(identity)
    active = projection(con, scope)
    for identity in active["lineage"]:
        visit(identity, frozenset())
    if active["messages_digest"] != digest(messages) or active["revision"] != state["revision"]:
        raise StoreError("归档投影与会话检查点不一致。")


def list_archive(con: "sqlite3.Connection", session: str, scope: str = "main", *,
                 offset: int = 0, limit: int = 20) -> dict[str, Any]:
    _page(offset, limit, 100)
    state = manifest(con, session)["scopes"].get(scope)
    if state is None:
        raise StoreError("当前会话未登记此归档范围。")
    selected = state["index"][offset:offset + limit]
    for item in selected:
        record(con, scope, item["id"], sources=False)
    values = [{key: value for key, value in item.items() if key not in {"sources", "previous", "digest"}}
              | {"source_count": len(item.get("sources", []))} for item in selected]
    end = offset + len(selected)
    return {"scope": scope, "revision": state["revision"], "items": values,
            "next_offset": end if end < len(state["index"]) else None, "legacy_gap": state["legacy_gap"]}


def list_scopes(con: "sqlite3.Connection", session: str) -> list[str]:
    current = manifest(con, session)
    scopes = current.get("scope_order", list(current["scopes"]))
    if set(scopes) != set(current["scopes"]) or len(scopes) != len(set(scopes)):
        raise StoreError("归档范围索引不一致。")
    return list(scopes)


def _page(offset: int, limit: int, maximum: int) -> None:
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= maximum:
        raise StoreError("归档分页参数无效。")


def read_archive(con: "sqlite3.Connection", scope: str, identity: str, *,
                 offset: int = 0, limit: int = 4096) -> dict[str, Any]:
    _page(offset, limit, 16000)
    value = record(con, scope, identity, sources=False)
    current = _read(con, "archive:manifest")
    index = {item["id"]: item for item in current["scopes"][scope]["index"]}
    originals: dict[tuple[Any, ...], dict[str, Any]] = {}
    def expand(source: str, trail: frozenset[str] = frozenset()) -> None:
        if source in trail or source not in index:
            raise StoreError("归档来源循环，停止读取。")
        saved = index[source]
        if saved["kind"] == "raw":
            key = (saved.get("origin_session"), saved.get("origin_scope", scope), saved["raw_seq"])
            if key not in originals or saved["version"] > originals[key]["version"]:
                originals[key] = saved
        else:
            for child in saved.get("sources", []):
                expand(child, trail | {source})
    if value["kind"] in {"summary", "prune"}:
        expand(identity)
        # A retained Hook can precede an older summary in the current projection.
        # Read raw chronology, not traversal order; branches preserve raw_seq and
        # allocate their new messages after the imported maximum.
        parts = sorted(originals.values(), key=lambda item: item["raw_seq"])
        total = 2 + max(0, len(parts) - 1) + sum(item["display_length"] for item in parts)
        text_parts = []
        cursor = 0
        def take(text: str) -> None:
            nonlocal cursor
            end = cursor + len(text)
            if end > offset and cursor < offset + limit:
                text_parts.append(text[max(0, offset-cursor):max(0, offset+limit-cursor)])
            cursor = end
        take("[")
        for position, saved in enumerate(parts):
            if position:
                take(",")
            length = saved["display_length"]
            if cursor + length > offset and cursor < offset + limit:
                original = record(con, scope, saved["id"], sources=False)
                fragment = canonical(_display(original["message"]))
                if len(fragment) != length:
                    raise StoreError("归档分页索引与原文不一致。")
                take(fragment)
            else:
                cursor += length
        take("]")
        text = "".join(text_parts)
    else:
        full_text = canonical(_display(value.get("message", value)))
        total = len(full_text)
        text = full_text[offset:offset + limit]
    end = min(total, offset + limit)
    return {"id": identity, "scope": scope, "kind": value["kind"], "text": text,
            "total": total, "next_offset": end if end < total else None,
            "digest": value["digest"], "source_count": len(value.get("sources", [])),
            "derived_message": canonical(_display(value["message"]))[:512] if value["kind"] in {"summary", "prune"} else None,
            "attachments": attachment_refs(con, [item["id"] for item in originals.values()] if originals else [identity], scope)}


def attachment_refs(con: "sqlite3.Connection", identities: list[str], scope: str, *,
                    limit: int | None = 20) -> list[dict[str, Any]]:
    aliases = _read(con, "archive:attachment_aliases") or {}
    found: dict[str, str] = {}
    current = _read(con, "archive:manifest")
    index = {item["id"]: item for item in current["scopes"][scope]["index"]}
    for identity in identities:
        found.update(index[identity].get("attachments", {}))
    result = []
    entries = list(found.items())
    for logical, fingerprint in entries if limit is None else entries[:limit]:
        physical = aliases.get(logical, logical)
        try:
            if hashlib.sha256(Path(physical).read_bytes()).hexdigest() != fingerprint:
                raise StoreError("归档附件哈希不符，停止读取。")
        except OSError as error:
            raise StoreError("归档附件已缺失，停止读取。") from error
        result.append({"logical_path": logical, "path": physical, "sha256": fingerprint})
    return result


def export_archive(con: "sqlite3.Connection", session: str, scope: str = "main", *,
                   offset: int = 0, limit: int = 100, versions: bool = False) -> dict[str, Any]:
    _page(offset, limit, 1000)
    state = manifest(con, session)["scopes"].get(scope)
    if state is None:
        raise StoreError("当前会话未登记此归档范围。")
    latest: dict[int, dict[str, Any]] = {}
    raws = []
    boundaries = []
    for item in state["index"]:
        if item["kind"] == "raw":
            raws.append(item)
            if item["raw_seq"] not in latest or item["version"] > latest[item["raw_seq"]]["version"]:
                latest[item["raw_seq"]] = item
        elif item["kind"] == "boundary":
            boundaries.append(record(con, scope, item["id"]))
    selected = sorted(latest.values(), key=lambda item: item["raw_seq"])[offset:offset + limit]
    sequences = {item["raw_seq"] for item in selected}
    records = [record(con, scope, item["id"]) for item in raws if item["raw_seq"] in sequences]
    messages = [record(con, scope, item["id"])["message"] for item in selected]
    end = offset + len(selected)
    index = {item["id"]: item for item in state["index"]}
    anchors: dict[str, int] = {}
    def anchor(identity: str, trail: frozenset[str] = frozenset()) -> int:
        if identity in trail or identity not in index:
            raise StoreError("导出归档来源缺失或循环。")
        if identity not in anchors:
            item = index[identity]
            anchors[identity] = item["raw_seq"] if item["kind"] == "raw" else min(
                anchor(source, trail | {identity}) for source in item.get("sources", []))
        return anchors[identity]
    derived = [record(con, scope, item["id"], sources=False) for item in state["index"]
               if versions and item["kind"] in {"summary", "prune"} and anchor(item["id"]) in sequences]
    return {"scope": scope, "revision": state["revision"], "messages": messages, "records": records,
            "boundaries": boundaries, "legacy_gap": state["legacy_gap"],
            "derived": derived, "projection": projection(con, scope) if offset == 0 else None,
            "attachments": attachment_refs(con, [item["id"] for item in selected], scope, limit=None),
            "next_offset": end if end < len(latest) else None}


def branch_archive(con: "sqlite3.Connection", session: str, scope: str = "main", *,
                   indices: tuple[int, ...] | None = None) -> ArchiveImport:
    current = manifest(con, session)
    refs = projection(con, scope)["lineage"]
    if indices is not None:
        if any(type(i) is not int or not 0 <= i < len(refs) for i in indices) or tuple(sorted(set(indices))) != indices:
            raise StoreError("继承投影位置无效或未按原顺序排列。")
        refs = [refs[i] for i in indices]
    kept: dict[str, dict[str, Any]] = {}
    def visit(identity: str) -> None:
        value = record(con, scope, identity)
        if identity in kept:
            return
        for source in value.get("sources", []):
            visit(source)
        if value.get("previous"):
            visit(value["previous"])
        kept[identity] = value
    for identity in refs:
        visit(identity)
    attachments: dict[str, str] = {}
    for saved in kept.values():
        attachments.update(saved.get("attachments", {}))
    # Existing registered background/image files can also be named by a raw message.
    registered = _read(con, "attachments") or {}
    raw_text = canonical([saved.get("message") for saved in kept.values()])
    aliases = _read(con, "archive:attachment_aliases") or {}
    for path, fingerprint in registered.items():
        logical = next((name for name, actual in aliases.items() if actual == path), path)
        if canonical(logical)[1:-1] in raw_text:
            attachments[logical] = fingerprint
    return ArchiveImport(session, tuple(kept.values()), tuple(refs),
                         current["scopes"].get(scope, {}).get("legacy_gap", False), attachments,
                         {path: aliases.get(path, path) for path in attachments})
