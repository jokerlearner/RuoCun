"""冻结参考 deck_bridge.ts（MIT）：独立的本地 HTTP 会话协议桥。"""

from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
import secrets
import socket
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from concurrent.futures import CancelledError
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from ..approval.types import ApprovalDecision, ApprovalRequest
from ..config.compat import resolve_env
from ..platform.file_contract import AtomicFileError
from ..platform.windows.durable_file import atomic_publish
from ..session.contract import AcceptedInput
from ..session.session import Session
from ..tui.render import TurnEvents
from .background_runtime import BackgroundRuntime
from .deck_messages import (
    contentText,
    json_bytes,
    messagePage,
    utf16_length,
    utf16_slice,
    utf16_tail,
)
from .session_scheduler import SchedulerStatus, SessionScheduler

_PERMISSION_COMMAND = re.compile(r"^/(mode|bypass|yolo|permissions|plan)(?:\s|$)", re.IGNORECASE)
_DECIMAL_POSITION = re.compile(r"[+\-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+\-]?[0-9]+)?")
_PERMISSION_MODES = ("default", "auto", "plan", "bypassPermissions")
_INTERRUPTED = "[用户中断]"
_REQUEST_LIMIT = 65536
_Response = tuple[int, dict[str, Any]]


def _now() -> int:
    return time.time_ns() // 1_000_000


def _clip(text: str, limit: int) -> str:
    return text if utf16_length(text) <= limit else utf16_slice(text, limit) + "\n…（已截断）"


def _error(status: int, text: str) -> _Response:
    return status, {"error": text}


def deck_managed(env: Mapping[str, str]) -> bool:
    managed = resolve_env("DECK_MANAGED", env) == "1"
    if managed and resolve_env("DECK", env) == "0":
        raise ValueError("Deck 托管模式不能同时禁用 Deck")
    return managed


@dataclass(frozen=True)
class DeckOptions:
    scheduler: SessionScheduler
    session: Session
    runtime: BackgroundRuntime
    cwd: Path
    version: str
    writable: bool
    tasks: Callable[[], list[Any]]
    todos: Callable[[], list[Any]]
    getPermissionMode: Callable[[], str] | None = None
    setPermissionMode: Callable[[str], None] | None = None
    title: Callable[[], str] | None = None
    redact: Callable[[str], str] | None = None
    submitMessage: Callable[[str], Awaitable[AcceptedInput | None]] | None = None


@dataclass
class _Receipt:
    id: str
    text: str
    status: str
    at: int
    input_id: str | None = None


class _BodyTooLarge(ValueError):
    pass


class _DeckHttpServer(ThreadingHTTPServer):
    def __init__(self, bridge: DeckBridge) -> None:
        self.bridge = bridge
        self._sockets: set[socket.socket] = set()
        self._socket_lock = threading.Lock()
        super().__init__(("127.0.0.1", 0), _DeckRequest)

    def process_request(self, request: socket.socket | tuple[bytes, socket.socket], client_address: Any) -> None:
        if isinstance(request, socket.socket):
            with self._socket_lock:
                self._sockets.add(request)
        super().process_request(request, client_address)

    def close_request(self, request: socket.socket | tuple[bytes, socket.socket]) -> None:
        if isinstance(request, socket.socket):
            with self._socket_lock:
                self._sockets.discard(request)
        super().close_request(request)

    def close_connections(self) -> None:
        with self._socket_lock:
            active = tuple(self._sockets)
        for request in active:
            try:
                request.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            request.close()

    def handle_error(self, request: Any, client_address: Any) -> None:
        # Errors from disconnected clients never print untrusted requests to stderr.
        return


class _DeckRequest(BaseHTTPRequestHandler):
    server: _DeckHttpServer

    def setup(self) -> None:
        self.request.settimeout(5)
        super().setup()

    def log_message(self, format: str, *args: Any) -> None:
        # Discovery credentials and user payload never go to HTTP logs.
        return

    def _read_body(self) -> bytes:
        transfer = self.headers.get("Transfer-Encoding")
        lengths = self.headers.get_all("Content-Length", [])
        if transfer:
            if transfer.strip().lower() != "chunked" or lengths:
                raise ValueError("ambiguous body framing")
            chunks = bytearray()
            while True:
                line = self.rfile.readline(256)
                if not line.endswith(b"\r\n"):
                    raise ValueError("invalid chunk length")
                value = line.partition(b";")[0].strip()
                if not re.fullmatch(rb"[0-9a-fA-F]+", value):
                    raise ValueError("invalid chunk length")
                size = int(value, 16)
                if len(chunks) + size > _REQUEST_LIMIT:
                    raise _BodyTooLarge
                if not size:
                    # The server handles one request per connection and does not consume trailers.
                    return bytes(chunks)
                chunk = self.rfile.read(size + 2)
                if len(chunk) != size + 2 or not chunk.endswith(b"\r\n"):
                    raise ValueError("incomplete chunk")
                chunks.extend(chunk[:-2])
        if len(lengths) != 1 or not re.fullmatch(r"[0-9]+", lengths[0]):
            raise ValueError("missing or invalid content length")
        size = int(lengths[0])
        if size > _REQUEST_LIMIT:
            raise _BodyTooLarge
        body = self.rfile.read(size)
        if len(body) != size:
            raise ValueError("incomplete body")
        return body

    def _handle(self) -> None:
        bridge = self.server.bridge
        auth = self.headers.get_all("Authorization", [])
        if (len(auth) != 1 or "Origin" in self.headers
                or not hmac.compare_digest(auth[0].encode("latin-1"), bridge._authorization)):
            response = _error(403, "Forbidden")
        else:
            try:
                body = self._read_body() if self.command == "POST" and self.path == "/command" else b""
                operation = bridge._request(self.command, self.path, body)
                try:
                    result = asyncio.run_coroutine_threadsafe(operation, bridge._loop)
                except RuntimeError:
                    operation.close()
                    response = _error(409, "会话已关闭")
                else:
                    response = result.result()
            except _BodyTooLarge:
                response = _error(413, "消息太长")
            except (CancelledError, OSError, ValueError):
                response = _error(400, "无法处理指令")
        status, data = response
        payload = json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(payload)
            except OSError:
                pass

    do_GET = do_POST = do_HEAD = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _handle


class DeckBridge:
    """HTTP workers parse requests; all session/command state stays on the Agent loop."""

    def __init__(self, options: DeckOptions, env: Mapping[str, str], managed: bool) -> None:
        self._options = options
        self._loop = asyncio.get_running_loop()
        self._managed = managed
        self._instance = str(uuid.uuid4())
        self._token = secrets.token_hex(32)
        self._authorization = f"Bearer {self._token}".encode("ascii")
        self._started = self._last_activity = _now()
        self._session_id = options.runtime.sessionId
        self._live = self._activity = ""
        self._attention: dict[str, Any] | None = None
        self._prompts: dict[str, tuple[dict[str, Any], asyncio.Future[str]]] = {}
        self._receipts: dict[str, _Receipt] = {}
        self._commands: dict[str, tuple[bytes, _Response]] = {}
        self._unknown_commands: dict[str, tuple[bytes, _Response]] = {}
        self._events: list[dict[str, Any]] = []
        self._command_lock = asyncio.Lock()
        self._closed = False
        self._close_task: asyncio.Task[None] | None = None
        home = Path(env.get("AGENT_DECK_HOME") or Path.home() / ".agent-deck")
        self._record_file = home / "agents" / f"{os.getpid()}-{self._instance}.json"
        self._server = _DeckHttpServer(self)
        self._thread = threading.Thread(
            target=self._server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True, name="ruocun-deck",
        )
        self._thread.start()
        self._heartbeat = self._loop.create_task(self._refresh())
        self._unsubscribe = self._options.scheduler.subscribe(self._status_changed)

    @classmethod
    async def start(cls, options: DeckOptions, *, env: Mapping[str, str]) -> DeckBridge | None:
        managed = deck_managed(env)
        if resolve_env("DECK", env) == "0":
            return None
        try:
            bridge = cls(options, env, managed)
        except OSError:
            if managed:
                raise RuntimeError("Deck 托管模式无法启动本地协议。") from None
            return None
        if not bridge._publish() and managed:
            await bridge.close()
            raise RuntimeError("Deck 托管模式无法发布私有连接记录。")
        return bridge

    def _redact(self, value: str) -> str:
        return self._options.redact(value) if self._options.redact is not None else value

    def _redact_payload(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact(value)
        if isinstance(value, dict):
            return {key: self._redact_payload(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._redact_payload(item) for item in value]
        return value

    def _publish(self) -> bool:
        if self._closed:
            return False
        self._sync_session()
        data = json_bytes({
            "protocol": 1, "instanceId": self._instance, "sessionId": self._session_id, "pid": os.getpid(),
            "cwd": str(self._options.cwd), "version": self._options.version, "port": self._server.server_port,
            "token": self._token, "startedAt": self._started, "updatedAt": _now(),
        })
        parent = self._record_file.parent
        try:
            parent.parent.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                atomic_publish(self._record_file, data, require_durability=False)
            else:
                parent.mkdir(mode=0o700, exist_ok=True)
                if parent.is_symlink() or parent.stat().st_mode & 0o077:
                    return False
                fd, name = tempfile.mkstemp(prefix=f".{self._record_file.name}.", dir=parent)
                temporary = Path(name)
                try:
                    with os.fdopen(fd, "wb") as file:
                        file.write(data)
                    os.replace(temporary, self._record_file)
                finally:
                    temporary.unlink(missing_ok=True)
        except (OSError, AtomicFileError):
            return False
        return True

    async def _refresh(self) -> None:
        while not self._closed:
            await asyncio.sleep(5)
            self._publish()

    def _status_changed(self, status: SchedulerStatus) -> None:
        if status.state == "paused":
            self.cancel_prompts()
            for receipt in self._receipts.values():
                if receipt.status == "queued":
                    receipt.status = "canceled"
        elif status.state == "closed":
            self._begin_close()

    def _begin_close(self) -> asyncio.Task[None]:
        if self._close_task is None:
            self._closed = True
            self.cancel_prompts()
            self._close_task = self._loop.create_task(self._close())
        return self._close_task

    async def close(self) -> None:
        await asyncio.shield(self._begin_close())

    async def _close(self) -> None:
        self._unsubscribe()
        self._heartbeat.cancel()
        await asyncio.gather(self._heartbeat, return_exceptions=True)
        try:
            self._record_file.unlink(missing_ok=True)
        except OSError:
            pass
        await asyncio.to_thread(self._server.shutdown)
        self._server.close_connections()
        self._server.server_close()
        await asyncio.to_thread(self._thread.join)

    def _sync_session(self) -> None:
        session_id = self._options.runtime.sessionId
        if self._session_id != session_id:
            self._session_id = session_id
            self._live = self._activity = ""
            self.cancel_prompts()
            self._events.clear()
            self._receipts.clear()
            self._commands.clear()
            self._unknown_commands.clear()

    def cancel_prompts(self) -> None:
        for _, future in self._prompts.values():
            if not future.done():
                future.set_result(_INTERRUPTED)
        self._prompts.clear()
        self._attention = None

    def _next_prompt(self) -> None:
        entry = next(iter(self._prompts.values()), None)
        self._attention = entry[0] if entry is not None else None

    async def _prompt(self, kind: str, text: str, requests: list[dict[str, str]] | None = None,
                      *, cancelled: Callable[[], bool] | None = None) -> str:
        self._sync_session()
        if (self._closed or self._options.scheduler.status().state in ("paused", "closed")
                or cancelled is not None and cancelled()):
            return _INTERRUPTED
        prompt_id = str(uuid.uuid4())
        prompt: dict[str, Any] = {"id": prompt_id, "kind": kind, "text": self._redact(text), "at": _now(), "replyable": True}
        if requests is not None:
            prompt["requests"] = requests
        future: asyncio.Future[str] = self._loop.create_future()
        self._prompts[prompt_id] = prompt, future
        self._next_prompt()
        try:
            if cancelled is None:
                return await future
            while not future.done() and not cancelled():
                await asyncio.wait((future,), timeout=0.05)
            return _INTERRUPTED if cancelled() else future.result()
        finally:
            if self._prompts.pop(prompt_id, None) is not None:
                self._next_prompt()
            if not future.done():
                future.cancel()

    async def approve(self, requests: list[ApprovalRequest], *,
                      cancelled: Callable[[], bool] | None = None) -> dict[str, ApprovalDecision]:
        display = [
            {"id": row["id"], "summary": self._redact(row["summary"]), "toolName": row["toolName"]}
            for row in requests
        ]
        answer = await self._prompt("approval", "\n".join(row["summary"] for row in requests), display,
                                    cancelled=cancelled)
        return {row["id"]: "once" if answer == "allow" else "deny" for row in requests}

    async def question(self, text: str, *, cancelled: Callable[[], bool] | None = None) -> str:
        return await self._prompt("question", text, cancelled=cancelled)

    def input(self, input_id: str, accepted: bool) -> bool:
        self._sync_session()
        receipt = next((row for row in self._receipts.values() if row.input_id == input_id and row.status == "queued"), None)
        if receipt is None:
            return False
        receipt.status = "consumed" if accepted else "rejected"
        return True

    def attention(self, kind: str, text: str) -> Callable[[], None]:
        self._sync_session()
        current = {"kind": kind, "text": self._redact(text), "at": _now()}
        self._attention = current

        def clear() -> None:
            if self._attention is current:
                self._next_prompt()

        return clear

    def _event(self, kind: str, text: str) -> None:
        self._last_activity = _now()
        self._events.append({"id": str(uuid.uuid4()), "kind": kind, "text": _clip(self._redact(text), 6000), "at": self._last_activity})
        if len(self._events) > 120:
            self._events.pop(0)

    def events(self, inner: TurnEvents | None = None) -> TurnEvents:
        return _DeckEvents(self, inner)

    def _history(self, before: int | None = None) -> dict[str, Any]:
        return messagePage(self._options.session.messages, before, redact=self._redact)

    def _snapshot(self) -> dict[str, Any]:
        options = self._options
        state = asdict(options.scheduler.status())
        if state.get("waiting") is None:
            state.pop("waiting", None)
        title = options.title() if options.title is not None else ""
        if not title:
            first = next((message for message in options.session.messages if message.get("role") == "user"), {})
            title = utf16_slice(self._redact(contentText(first.get("content"))), 120)
        snapshot: dict[str, Any] = {
            "protocol": 1, "instanceId": self._instance, "sessionId": self._session_id, "pid": os.getpid(),
            "cwd": str(options.cwd), "version": options.version, "title": self._redact(title),
            "startedAt": self._started, "updatedAt": _now(), "lastActivityAt": self._last_activity, **state,
            "model": options.session.model, "mode": options.session.mode,
            "usage": dict(options.session.usage), "costCNY": options.session.costCNY(),
            "activity": self._activity, "live": utf16_tail(self._redact(self._live), 24000),
            "capabilities": {"message": options.writable, "pause": True, "answer": self._managed,
                             "history": True, "permissions": options.writable and options.getPermissionMode is not None
                             and options.setPermissionMode is not None},
            **self._history(), "tasks": self._redact_payload(options.tasks()[-60:]),
            "todos": self._redact_payload(options.todos()[:100]),
            "events": self._events.copy(),
            "receipts": [{"id": row.id, "text": _clip(self._redact(row.text), 300),
                          "status": row.status, "at": row.at} for row in self._receipts.values()],
        }
        if self._attention is not None:
            snapshot["attention"] = self._attention
        if options.scheduler.lastError is not None:
            snapshot["error"] = self._redact(str(options.scheduler.lastError))
        if options.getPermissionMode is not None:
            snapshot["permissionMode"] = options.getPermissionMode()
        return snapshot

    async def _request(self, method: str, path: str, body: bytes) -> _Response:
        if self._closed:
            return _error(409, "会话已关闭")
        self._sync_session()
        try:
            url = urlsplit(path)
            if method == "GET" and url.path == "/messages":
                position = parse_qs(url.query, keep_blank_values=True).get("before")
                before = None
                if position:
                    raw = position[0].strip() or "0"
                    try:
                        if raw.lower().startswith(("0x", "0o", "0b")):
                            value = Decimal(int(raw, 0))
                        else:
                            value = Decimal(raw) if _DECIMAL_POSITION.fullmatch(raw) else Decimal("NaN")
                        if not value.is_finite() or not 0 <= value <= 9007199254740991 or value != value.to_integral_value():
                            return _error(400, "无效的历史位置")
                        before = int(value)
                    except (InvalidOperation, ValueError):
                        return _error(400, "无效的历史位置")
                return 200, {"sessionId": self._session_id, "instanceId": self._instance,
                             "cwd": str(self._options.cwd), **self._history(before)}
            if method == "GET" and path == "/snapshot":
                return 200, self._snapshot()
            if method != "POST" or path != "/command":
                return _error(404, "Not found")
            command = json.loads(body)
            if not isinstance(command, dict):
                return _error(400, "无法处理指令")
            async with self._command_lock:
                return await self._command(command)
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            return _error(400, "无法处理指令")

    async def _command(self, command: dict[str, Any]) -> _Response:
        self._sync_session()
        if command.get("sessionId") != self._session_id:
            return _error(409, "会话已切换，请刷新后重试")
        key = command.get("id")
        if not isinstance(key, str) or not key or utf16_length(key) > 100:
            return _error(400, "缺少指令 ID")
        signature = json_bytes([command.get(field) for field in ("type", "text", "promptId", "decision", "mode")])
        if (previous := self._unknown_commands.get(key) or self._commands.get(key)) is not None:
            return previous[1] if previous[0] == signature else _error(409, "指令 ID 已使用")
        if self._closed or self._options.scheduler.status().state == "closed":
            return _error(409, "会话已关闭")
        try:
            response = await self._dispatch(key, command)
        except Exception:
            # Once dispatch is attempted, a failed save/control acknowledgment can be ambiguous.
            # Preserve this command ID instead of retrying it into another write or execution.
            response = _error(400, "无法处理指令")
            self._unknown_commands[key] = signature, response
        if response[0] == 200:
            self._commands[key] = signature, response
        if len(self._commands) > 200:
            del self._commands[next(iter(self._commands))]
        if len(self._receipts) > 100:
            del self._receipts[next(iter(self._receipts))]
        return response

    async def _dispatch(self, key: str, command: dict[str, Any]) -> _Response:
        kind, text = command.get("type"), command.get("text")
        options = self._options
        if kind == "permission":
            return self._permission(key, command.get("mode"))
        if kind == "message":
            if not options.writable:
                return _error(409, "一次性任务仅支持查看和暂停，请在交互会话中发消息")
            if not isinstance(text, str) or not text.strip() or utf16_length(text) > 16000:
                return _error(400, "消息应为 1–16000 个字符")
            if _PERMISSION_COMMAND.match(text.strip()):
                return _error(400, "这是终端控制命令，请使用 Deck 的权限设置；当前消息未发送给模型")
            self._receipts[key] = receipt = _Receipt(key, text, "queued", _now())
            submit = options.submitMessage or options.scheduler.submit
            try:
                accepted = await submit(text)
            except Exception:
                receipt.status = "unknown"
                raise
            if accepted is None:
                receipt.status = "rejected"
                return _error(409, "会话已关闭")
            receipt.input_id = accepted.input_id
            return 200, {"id": key, "status": "queued"}
        if kind == "pause":
            self.cancel_prompts()
            await options.scheduler.pause()
            for receipt in self._receipts.values():
                if receipt.status == "queued":
                    receipt.status = "canceled"
            return 200, {"id": key, "status": "paused"}
        if kind == "answer":
            return self._answer(key, command)
        return _error(400, "未知指令")

    def _permission(self, key: str, mode: Any) -> _Response:
        options = self._options
        if not options.writable:
            return _error(409, "一次性任务不支持切换权限")
        if options.getPermissionMode is None or options.setPermissionMode is None:
            return _error(409, "当前版本未接入权限切换，请更新入口并恢复会话")
        if mode not in _PERMISSION_MODES:
            return _error(400, "未知权限模式")
        if options.scheduler.status().state not in ("idle", "paused") or self._attention or self._prompts:
            return _error(409, "请先暂停执行并结束当前审批，再切换权限")
        options.setPermissionMode(mode)
        updated = options.getPermissionMode()
        self._event("permission", f"权限模式已切换为 {updated}")
        return 200, {"id": key, "status": "applied", "permissionMode": updated}

    def _answer(self, key: str, command: dict[str, Any]) -> _Response:
        prompt_id = command.get("promptId")
        if not self._managed or not isinstance(prompt_id, str) or prompt_id not in self._prompts:
            return _error(409, "问题已失效或需要在原终端处理")
        prompt, future = self._prompts[prompt_id]
        if prompt["kind"] == "approval":
            answer = command.get("decision")
            if answer not in ("allow", "deny"):
                return _error(400, "请选择允许本次或拒绝")
        else:
            answer = command.get("text")
            if not isinstance(answer, str) or not answer.strip() or utf16_length(answer) > 16000:
                return _error(400, "请输入回答")
        if future.done():
            return _error(409, "问题已失效或需要在原终端处理")
        del self._prompts[prompt_id]
        self._next_prompt()
        future.set_result(answer)
        return 200, {"id": key, "status": "answered"}


class _DeckEvents:
    def __init__(self, deck: DeckBridge, inner: TurnEvents | None) -> None:
        self._deck, self._inner = deck, inner

    def reasoning(self, chunk: str) -> None:
        self._deck._last_activity = _now()
        self._deck._activity = "正在思考"
        if self._inner is not None:
            self._inner.reasoning(chunk)

    def content(self, chunk: str) -> None:
        self._deck._last_activity = _now()
        # Keep a bounded tail in memory; apply redaction to the combined text before serving.
        self._deck._live = (self._deck._live + chunk)[-48000:]
        self._deck._activity = "正在回复"
        if self._inner is not None:
            self._inner.content(chunk)

    def assistantDone(self, message: dict[str, Any]) -> None:
        self._deck._live = ""
        if self._inner is not None:
            self._inner.assistantDone(message)

    def toolStart(self, call: dict[str, Any]) -> None:
        name = self._deck._redact(str(call["name"]))
        self._deck._activity = f"执行 {name}"
        self._deck._event("tool_start", name)
        if self._inner is not None:
            self._inner.toolStart(call)

    def toolResult(self, call: dict[str, Any], message: dict[str, Any]) -> None:
        name = call["function"]["name"]
        self._deck._event("tool_result", f"{name}\n{contentText(message.get('content'))}")
        if self._inner is not None:
            self._inner.toolResult(call, message)

    def notice(self, text: str) -> None:
        self._deck._event("notice", text)
        if self._inner is not None:
            self._inner.notice(text)

    def userMessage(self, text: str) -> None:
        if self._inner is not None:
            self._inner.userMessage(text)
