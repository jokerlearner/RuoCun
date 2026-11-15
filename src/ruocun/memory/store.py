"""读取多个作用域的 Markdown 记忆并保留来源身份。写入只发往若存原生存储，兼容来源保持只读。"""

from __future__ import annotations

import asyncio
import hashlib
import re
import stat
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PureWindowsPath
from threading import Event, Lock
from typing import Literal
from uuid import uuid4

from ..config.compat import Compatibility, CompatibilitySource
from ..platform.file_contract import AtomicFileError
from ..platform.windows.durable_file import (
    AtomicPublishPreReplaceError,
    PrivateDirectory,
    atomic_publish,
    sync_directory,
)
from ..tools.types import ToolRejected
from .frontmatter import parseMemoryFile, serializeMemory
from .types import Memory, MemoryType, Scope

_SCOPE_ORDER: tuple[Scope, ...] = ("project", "user", "knowledge")
_COMMAND_ORDER: tuple[Scope, ...] = ("user", "knowledge", "project")
_MUTATION_LOCK = Lock()


@dataclass(frozen=True)
class MemoryEntry:
    memory: Memory
    scope: Scope
    path: Path
    source: CompatibilitySource | None
    contentDigest: str = ""


@dataclass(frozen=True)
class UpsertResult:
    action: Literal["added", "updated"]
    name: str


@dataclass(frozen=True)
class DeleteResult:
    removed: tuple[str, ...]
    readOnly: bool
    locked: bool


@dataclass(frozen=True)
class _Directory:
    path: Path
    source: CompatibilitySource | None = None


def routeScope(kind: MemoryType) -> Scope:
    if kind == "procedural":
        return "knowledge"
    if kind in ("user", "feedback"):
        return "user"
    return "project"


def slug(text: str) -> str:
    chars = (char if unicodedata.category(char)[0] in "LN" else " " for char in text.lower())
    name = "-".join("".join(chars).split())
    return name.encode("utf-16-le")[:80].decode("utf-16-le", errors="ignore") or "mem"


def projectIdOf(workspaceRoot: Path) -> str:
    return slug(workspaceRoot.name)


def keepKnowledgeForProject(memory: Memory, projectId: str) -> bool:
    return memory.locked or bool(memory.origin and memory.origin == projectId)


def dedupKey(memory: Memory) -> str:
    return slug(memory.title) if memory.title and memory.title.strip() else memory.name


def isMemoryName(name: str) -> bool:
    return bool(name and not name.endswith((" ", ".")) and not PureWindowsPath(name).is_reserved()
                and all(char not in '<>:"/\\|?*' and ord(char) >= 32 for char in name))


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _regular(file: Path, *, mutable: bool = False) -> bool:
    info = file.lstat()
    return (stat.S_ISREG(info.st_mode)
            and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and (not mutable or info.st_nlink == 1))


def _readSnapshot(file: Path, *, mutable: bool = False) -> tuple[Memory, bytes] | None:
    if not _regular(file, mutable=mutable):
        return None
    raw = file.read_bytes()
    memory = parseMemoryFile(file.stem, raw.decode("utf-8"))
    if memory is None:
        return None
    return memory, raw


def _checkCancellation(signal: Event | None) -> None:
    if signal is not None and signal.is_set():
        raise ToolRejected("记忆操作已取消。")


class MemoryStore:
    def __init__(
        self, cwd: Path, userRoot: Path, compatibility: Compatibility, *,
        today: Callable[[], str] | None = None,
    ) -> None:
        self.cwd = cwd
        self.today = today if today is not None else _today
        self._native: dict[Scope, Path] = {
            "project": cwd / ".ruocun" / "memory",
            "user": userRoot / "memory",
            "knowledge": userRoot / "knowledge",
        }
        self._compatible: dict[Scope, list[_Directory]] = {scope: [] for scope in _SCOPE_ORDER}
        for source in compatibility.sources:
            if source.resource == "knowledge" and source.scope == "user":
                self._compatible["knowledge"].append(_Directory(Path(source.path), source))
            elif source.resource == "memory" and source.scope in ("project", "user"):
                self._compatible[source.scope].append(_Directory(Path(source.path), source))

    def _scan(self, directory: _Directory, scope: Scope, *, strictNative: bool) -> list[MemoryEntry]:
        try:
            root = directory.path.resolve(strict=True)
            if directory.source is None and root != directory.path.absolute():
                raise OSError("原生记忆目录包含重解析路径")
            files = list(root.iterdir())
        except FileNotFoundError:
            return []
        except (OSError, RuntimeError) as exc:
            if strictNative and directory.source is None:
                raise ToolRejected("原生记忆目录不可读，已保留现场。") from exc
            return []
        result = []
        for file in files:
            if file.suffix != ".md":
                continue
            try:
                snapshot = _readSnapshot(file)
            except (OSError, UnicodeError):
                continue
            if snapshot is not None:
                memory, raw = snapshot
                result.append(MemoryEntry(memory, scope, file, directory.source, hashlib.sha256(raw).hexdigest()))
        return result

    def _load(
        self, scopes: Sequence[Scope], includeSuperseded: bool, *, strictNative: bool = False,
    ) -> list[MemoryEntry]:
        result = []
        for scope in scopes:
            for directory in (_Directory(self._native[scope]), *self._compatible[scope]):
                result.extend(self._scan(directory, scope, strictNative=strictNative))
        return result if includeSuperseded else [entry for entry in result if entry.memory.status == "active"]

    async def load(
        self, scopes: Sequence[Scope] = _SCOPE_ORDER, *, includeSuperseded: bool = False,
    ) -> list[MemoryEntry]:
        return await asyncio.to_thread(self._load, tuple(scopes), includeSuperseded)

    def _loadNative(self, scope: Scope, includeSuperseded: bool) -> list[MemoryEntry]:
        entries = self._scan(_Directory(self._native[scope]), scope, strictNative=True)
        return entries if includeSuperseded else [entry for entry in entries if entry.memory.status == "active"]

    async def loadNative(self, scope: Scope, *, includeSuperseded: bool = False) -> list[MemoryEntry]:
        return await asyncio.to_thread(self._loadNative, scope, includeSuperseded)

    def _writable(self, scope: Scope) -> Path:
        directory = self._native[scope].absolute()
        try:
            if directory.resolve() != directory:
                raise ToolRejected("原生记忆目录包含重解析路径，未修改。")
            for compatible in self._compatible.values():
                for entry in compatible:
                    root = entry.path.resolve()
                    if directory.is_relative_to(root) or root.is_relative_to(directory):
                        raise ToolRejected("原生记忆目录与只读兼容来源重叠，未修改。")
        except (OSError, RuntimeError) as exc:
            raise ToolRejected("无法核对原生记忆目录，未修改。") from exc
        return directory

    @staticmethod
    def _occupantSnapshot(target: Path) -> tuple[Memory, bytes] | None:
        try:
            snapshot = _readSnapshot(target, mutable=True)
        except FileNotFoundError:
            return None
        except (OSError, UnicodeError) as exc:
            raise ToolRejected("目标记忆不可读，保留原文件。") from exc
        if (snapshot is None or snapshot[0].status not in ("active", "superseded")
                or snapshot[0].type not in ("user", "feedback", "semantic", "procedural", "episodic")):
            raise ToolRejected("目标记忆格式无效，保留原文件。")
        return snapshot

    @staticmethod
    def _occupant(target: Path) -> Memory | None:
        snapshot = MemoryStore._occupantSnapshot(target)
        return snapshot[0] if snapshot is not None else None

    @staticmethod
    def _serialize(memory: Memory) -> bytes:
        metadata = (memory.name, memory.title, memory.type, memory.created, memory.lastUsed,
                    memory.source, memory.sourceHash, memory.status, memory.supersededBy,
                    memory.validUntil, memory.origin)
        if any(value is not None and ("\r" in value or "\n" in value) for value in metadata):
            raise ToolRejected("记忆元数据须为单行，保留原文件。")
        serialized = serializeMemory(memory)
        expected = replace(memory, text=memory.text.replace("\r\n", "\n").strip())
        if parseMemoryFile(memory.name, serialized) != expected:
            raise ToolRejected("记忆元数据无法完整保存，保留原文件。")
        try:
            return serialized.encode("utf-8")
        except UnicodeError as exc:
            raise ToolRejected("记忆写入前检查失败，保留原文件。") from exc

    @staticmethod
    def _publish(target: Path, memory: Memory) -> None:
        MemoryStore._publishBytes(target, MemoryStore._serialize(memory))

    @staticmethod
    def _publishBytes(target: Path, data: bytes) -> None:
        try:
            target.parent.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ToolRejected("记忆写入前检查失败，保留原文件。") from exc
        try:
            atomic_publish(target, data)
        except AtomicPublishPreReplaceError as exc:
            if exc.replacement_uncertain:
                raise
            raise ToolRejected("记忆发布未发生，保留原文件。") from exc

    @staticmethod
    def _ownsEntry(directory: Path, entry: MemoryEntry) -> bool:
        return (entry.source is None and not entry.memory.locked and bool(entry.contentDigest)
                and entry.path.parent == directory and entry.path.suffix == ".md"
                and isMemoryName(entry.path.stem))

    @staticmethod
    def _matchesSnapshot(entry: MemoryEntry, current: tuple[Memory, bytes]) -> bool:
        return current[0] == entry.memory and hashlib.sha256(current[1]).hexdigest() == entry.contentDigest

    def _unlink(self, entry: MemoryEntry, *, strict: bool = True, signal: Event | None = None) -> bool:
        directory = self._writable(entry.scope)
        if not self._ownsEntry(directory, entry):
            if strict:
                raise ToolRejected("记忆目标已变化，未删除。")
            return False
        if not directory.exists():
            return False
        with PrivateDirectory(directory):
            try:
                current = self._occupantSnapshot(entry.path)
            except ToolRejected:
                if strict:
                    raise
                return False
            if current is None:
                return False
            if not self._matchesSnapshot(entry, current):
                if strict:
                    raise ToolRejected("记忆已变化或锁定，保留原文件。")
                return False
            _checkCancellation(signal)
            try:
                entry.path.unlink()
            except FileNotFoundError:
                return False
            sync_directory(directory)
        return True

    def _publishPreserving(
        self, target: Path, data: bytes, original: tuple[Memory, bytes], signal: Event | None,
    ) -> bool:
        while True:
            # 保留能识别正式文件名的前缀，并给发布器追加的临时后缀
            # 预留足够的 Windows 路径长度。
            backup = target.with_name(f".{target.stem}.{uuid4().hex[:12]}.bak")
            try:
                backup.lstat()
            except FileNotFoundError:
                break
        _checkCancellation(signal)
        self._publishBytes(backup, original[1])
        if not _regular(backup, mutable=True) or backup.read_bytes() != original[1]:
            raise RuntimeError("记忆恢复副本未确认，已停止替换。")
        try:
            current = self._occupantSnapshot(target)
        except ToolRejected:
            return False
        if current != original:
            return False
        _checkCancellation(signal)
        self._publishBytes(target, data)
        # 正式替换已经确认，恢复材料只作为可选辅助。
        try:
            with PrivateDirectory(target.parent):
                if _regular(backup, mutable=True) and backup.read_bytes() == original[1]:
                    backup.unlink()
                    sync_directory(target.parent)
        except (OSError, AtomicFileError):
            pass
        return True

    def _publishExpected(
        self, scope: Scope, memory: Memory, expected: MemoryEntry | None,
        preserveOriginal: bool, signal: Event | None,
    ) -> bool:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            directory = self._writable(scope)
            if expected is None:
                if not isMemoryName(memory.name):
                    raise ToolRejected("记忆名不能用作安全文件名，未写入。")
                target = directory / f"{memory.name}.md"
                try:
                    target.lstat()
                except FileNotFoundError:
                    pass
                else:
                    return False
            else:
                if (expected.scope != scope or memory.name != expected.memory.name
                        or not self._ownsEntry(directory, expected)):
                    return False
                target = expected.path
                try:
                    current = self._occupantSnapshot(target)
                except ToolRejected:
                    return False
                if current is None or not self._matchesSnapshot(expected, current):
                    return False
                if preserveOriginal:
                    return self._publishPreserving(target, self._serialize(memory), current, signal)
            _checkCancellation(signal)
            self._publish(target, memory)
            return True

    async def publishExpected(
        self, scope: Scope, memory: Memory, expected: MemoryEntry | None, *,
        preserveOriginal: bool = False, signal: Event | None = None,
    ) -> bool:
        return await asyncio.to_thread(self._publishExpected, scope, memory, expected, preserveOriginal, signal)

    def _touchConfirmed(self, entry: MemoryEntry, today: str, signal: Event | None) -> bool:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            directory = self._writable(entry.scope)
            # 已确认的锁定事实只允许刷新日期，正文和其他元数据须保留。
            # 兼容来源只读，不能刷新日期。
            unlocked = replace(entry, memory=replace(entry.memory, locked=False))
            if not self._ownsEntry(directory, unlocked):
                return False
            try:
                current = self._occupantSnapshot(entry.path)
            except ToolRejected:
                return False
            if current is None or not self._matchesSnapshot(entry, current):
                return False
            memory = replace(entry.memory, lastUsed=today)
            return self._publishPreserving(entry.path, self._serialize(memory), current, signal)

    async def touchConfirmed(self, entry: MemoryEntry, today: str, *, signal: Event | None = None) -> bool:
        return await asyncio.to_thread(self._touchConfirmed, entry, today, signal)

    def _deleteExpected(self, entry: MemoryEntry, signal: Event | None) -> bool:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            if entry.source is not None or entry.memory.locked:
                return False
            return self._unlink(entry, strict=False, signal=signal)

    async def deleteExpected(self, entry: MemoryEntry, *, signal: Event | None = None) -> bool:
        return await asyncio.to_thread(self._deleteExpected, entry, signal)

    @staticmethod
    def _readMarker(target: Path) -> int:
        try:
            if not _regular(target, mutable=True):
                raise ToolRejected("整理标记不是可安全使用的原生文件，保留原件。")
            text = target.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return 0
        except (OSError, UnicodeError) as exc:
            raise ToolRejected("整理标记无法读取，保留原件。") from exc
        if not re.fullmatch(r"-?[0-9]+", text):
            raise ToolRejected("整理标记格式无效，保留原件。")
        try:
            return int(text)
        except ValueError as exc:
            raise ToolRejected("整理标记格式无效，保留原件。") from exc

    def _readConsolidationMarker(self, scope: Scope) -> int:
        return self._readMarker(self._writable(scope) / ".last-consolidation")

    async def readConsolidationMarker(self, scope: Scope) -> int:
        return await asyncio.to_thread(self._readConsolidationMarker, scope)

    def _writeConsolidationMarker(self, scope: Scope, now: int, signal: Event | None) -> None:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            target = self._writable(scope) / ".last-consolidation"
            self._readMarker(target)
            _checkCancellation(signal)
            self._publishBytes(target, str(now).encode("ascii"))

    async def writeConsolidationMarker(self, scope: Scope, now: int, *, signal: Event | None = None) -> None:
        await asyncio.to_thread(self._writeConsolidationMarker, scope, now, signal)

    def _upsert(self, scope: Scope, candidate: Memory, signal: Event | None) -> UpsertResult:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            directory = self._writable(scope)
            entries = self._load(_SCOPE_ORDER, True, strictNative=True)
            key = dedupKey(candidate)
            match = next((entry for entry in entries if entry.memory.status == "active"
                          and not entry.memory.locked and (entry.memory.name == candidate.name
                                                           or dedupKey(entry.memory) == key)), None)
            if match is not None and match.source is not None:
                raise ToolRejected("匹配记忆来自只读兼容来源，请明确导入原生数据后再修改。")
            memory = candidate if match is None else replace(
                match.memory, title=candidate.title or match.memory.title, text=candidate.text,
                lastUsed=candidate.lastUsed, importance=max(match.memory.importance, candidate.importance),
                uses=match.memory.uses + 1,
            )
            if not isMemoryName(memory.name):
                raise ToolRejected("记忆名不能用作安全文件名，未写入。")
            target = directory / f"{memory.name}.md"
            occupant = self._occupant(target)
            if occupant is not None and occupant.locked:
                index = 2
                while occupant is not None:
                    target = directory / f"{memory.name}-{index}.md"
                    index += 1
                    occupant = self._occupant(target)
                memory = replace(memory, name=target.stem)
            elif occupant is not None and (match is None or occupant != match.memory):
                raise ToolRejected("写入目标已有另一条记忆，保留原文件。")
            _checkCancellation(signal)
            self._publish(target, memory)
            if match is not None:
                for entry in entries:
                    if (entry.source is None and entry.path.parent == directory and entry.path != target
                            and not entry.memory.locked and dedupKey(entry.memory) == dedupKey(memory)):
                        try:
                            self._unlink(entry)
                        except ToolRejected as exc:
                            # 新数据已经对外发布，不能返回普通的未执行结果。
                            raise RuntimeError("已写入记忆，重复项清理未确认。") from exc
            return UpsertResult("added" if match is None else "updated", memory.name)

    async def upsert(self, scope: Scope, candidate: Memory, *, signal: Event | None = None) -> UpsertResult:
        return await asyncio.to_thread(self._upsert, scope, candidate, signal)

    def _delete(self, key: str, exactName: bool, signal: Event | None) -> DeleteResult:
        with _MUTATION_LOCK:
            _checkCancellation(signal)
            scopes = _COMMAND_ORDER if exactName else _SCOPE_ORDER
            entries = self._load(scopes, True, strictNative=True)
            normalized = slug(key)
            matches = [entry for entry in entries if
                       (entry.path.stem == key if exactName else
                        entry.path.stem in (key, normalized) or bool(entry.memory.title
                                                                     and slug(entry.memory.title) == normalized))]
            writable = [entry for entry in matches if entry.source is None and not entry.memory.locked]
            removed: list[str] = []
            _checkCancellation(signal)
            for entry in writable:
                try:
                    deleted = self._unlink(entry)
                except ToolRejected as exc:
                    if not removed:
                        raise
                    raise RuntimeError("部分记忆已删除，后续删除未确认。") from exc
                if deleted:
                    removed.append(entry.path.stem)
                    if exactName:
                        break
            return DeleteResult(tuple(removed), any(entry.source is not None for entry in matches),
                                any(entry.memory.locked for entry in matches))

    async def delete(self, key: str, *, exactName: bool = False, signal: Event | None = None) -> DeleteResult:
        return await asyncio.to_thread(self._delete, key, exactName, signal)
