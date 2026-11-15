"""管理单个语言服务器的进程和 JSON-RPC 会话。

启动时完成 LSP 初始化，按请求编号匹配返回结果，发送位置查询前同步对应文档。释放会话时回收服务器进程树和管道。
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath
from typing import Any
from urllib.parse import unquote, urlsplit

MAX_HEADER_BYTES = 16 * 1024
MAX_MESSAGE_BYTES = 16 * 1024 * 1024
REQUEST_TIMEOUT = 30.0
SHUTDOWN_TIMEOUT = 3.0
_LANGUAGES = {".ts": "typescript", ".tsx": "typescriptreact", ".js": "javascript", ".jsx": "javascriptreact",
              ".mjs": "javascript", ".cjs": "javascript", ".py": "python", ".go": "go", ".rs": "rust",
              ".java": "java", ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp", ".rb": "ruby", ".php": "php"}


def fileUriToPath(uri: str) -> str:
    parsed = urlsplit(uri)
    if parsed.scheme != "file" or parsed.query or parsed.fragment:
        raise ValueError("LSP location 不是普通 file URI。")
    path = unquote(parsed.path, errors="strict")
    if parsed.netloc and parsed.netloc != "localhost":
        return str(PureWindowsPath("//" + parsed.netloc + path)) if os.name == "nt" else "//" + parsed.netloc + path
    if os.name == "nt":
        return str(PureWindowsPath(path[1:] if re.match(r"^/[A-Za-z]:", path) else path))
    return path


def pathToFileUri(path: str | Path) -> str:
    return Path(path).resolve().as_uri()


def toLspPosition(line: int, character: int) -> dict[str, int]:
    if type(line) is not int or type(character) is not int or min(line, character) < 1:
        raise ValueError("LSP 行列必须为1-based整数（列为UTF16单位）。")
    return {"line": line - 1, "character": character - 1}


def fmtLocation(location: dict[str, Any]) -> str:
    start = location["range"]["start"]
    return f"{fileUriToPath(location['uri'])}:{start['line'] + 1}:{start['character'] + 1}"


class LspClient:
    def __init__(self, command: str, args: list[str], rootUri: str, *,
                 environ: Mapping[str, str] | None = None, request_timeout: float = REQUEST_TIMEOUT) -> None:
        self.command, self.args, self.rootUri = command, list(args), rootUri
        self.root = Path(fileUriToPath(rootUri)).resolve()
        self.environ = dict(os.environ if environ is None else environ)
        self.request_timeout = request_timeout
        self._process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.Task[None] | None = None
        self._stderr: asyncio.Task[None] | None = None
        self._initializing: asyncio.Task[None] | None = None
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._next_id = 0
        self._write_lock = asyncio.Lock()
        self._sync_lock = asyncio.Lock()
        self._documents: dict[str, tuple[int, int]] = {}
        self._closing = False
        self._closed = False
        self._failure: BaseException | None = None
        self._job: Any = None
        self._disposing: asyncio.Task[None] | None = None

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    @property
    def returncode(self) -> int | None:
        return self._process.returncode if self._process is not None else None

    async def _write(self, message: dict[str, Any]) -> None:
        process = self._process
        if self._failure is not None:
            raise ConnectionError("LSP 协议连接不可用。") from self._failure
        if process is None or process.stdin is None or process.returncode is not None:
            raise ConnectionError("LSP server 已退出或尚未启动。")
        payload = json.dumps(message, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if len(payload) > MAX_MESSAGE_BYTES:
            raise ValueError("LSP 消息超过16MiB边界，未发送。")
        async with self._write_lock:
            process.stdin.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii") + payload)
            await asyncio.wait_for(process.stdin.drain(), self.request_timeout)

    async def _notify(self, method: str, params: Any = None) -> None:
        await self._write({"jsonrpc": "2.0", "method": method, "params": params})

    async def request(self, method: str, params: Any, *, signal: threading.Event | None = None,
                       timeout: float | None = None) -> Any:
        if signal is not None and signal.is_set():
            raise InterruptedError("LSP 请求已取消，未发送。")
        self._next_id += 1
        if len(self._pending) >= 128:
            raise RuntimeError("LSP 并发请求达到上限。")
        request_id = self._next_id
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        try:
            deadline = asyncio.get_running_loop().time() + (self.request_timeout if timeout is None else timeout)
            await asyncio.wait_for(self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}),
                                   max(.001, deadline - asyncio.get_running_loop().time()))
            while not future.done():
                if signal is not None and signal.is_set():
                    raise InterruptedError("LSP 请求已取消。")
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TimeoutError("LSP 请求超过等待期限。")
                await asyncio.wait({future}, timeout=min(.05, remaining))
            return future.result()
        except (InterruptedError, TimeoutError, asyncio.CancelledError):
            with contextlib.suppress(OSError, ValueError, ConnectionError, TimeoutError):
                await asyncio.wait_for(self._notify("$/cancelRequest", {"id": request_id}), 1)
            raise
        finally:
            self._pending.pop(request_id, None)
            if not future.done():
                future.cancel()
            elif not future.cancelled():
                future.exception()  # 发送被取消时，读取任务也可能同时失败，取出结果以完成清理。

    async def _read(self) -> None:
        assert self._process is not None and self._process.stdout is not None
        stream = self._process.stdout
        try:
            while True:
                headers: dict[bytes, bytes] = {}
                header_bytes = 0
                while True:
                    line = await stream.readline()
                    if not line:
                        raise ConnectionError("LSP server 关闭了输出。")
                    header_bytes += len(line)
                    if header_bytes > MAX_HEADER_BYTES or not line.endswith(b"\r\n"):
                        raise ValueError("LSP header 超长或分帧无效。")
                    if line == b"\r\n":
                        break
                    key, separator, value = line[:-2].partition(b":")
                    key = key.strip().lower()
                    if not separator or key in headers:
                        raise ValueError("LSP header 重复或无效。")
                    headers[key] = value.strip()
                raw_length = headers.get(b"content-length", b"")
                if not re.fullmatch(rb"[0-9]{1,9}", raw_length):
                    raise ValueError("LSP Content-Length 无效。")
                length = int(raw_length)
                if not 0 < length <= MAX_MESSAGE_BYTES:
                    raise ValueError("LSP 消息长度超限。")
                message = json.loads((await stream.readexactly(length)).decode("utf-8"))
                if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                    raise ValueError("LSP JSON-RPC 消息无效。")
                identity = message.get("id")
                if "method" in message:
                    if "id" in message:
                        await self._write({"jsonrpc": "2.0", "id": identity,
                                           "error": {"code": -32601, "message": "Method not found"}})
                    continue  # 客户端没有注册服务端主动调用的扩展处理器。
                if type(identity) is not int:
                    continue
                future = self._pending.get(identity)
                if future is None or future.done():
                    continue  # 迟到的响应按原请求编号匹配，已取消的编号没有等待方。
                if "error" in message:
                    error = message["error"]
                    future.set_exception(RuntimeError("LSP server error: " + str(error)))
                elif "result" in message:
                    future.set_result(message["result"])
                else:
                    raise ValueError("LSP response 缺少result/error。")
        except (OSError, ValueError, ConnectionError, asyncio.IncompleteReadError) as error:
            self._failure = error
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(ConnectionError(f"LSP 协议连接已关闭（{type(error).__name__}）。"))

    async def _drain_stderr(self) -> None:
        assert self._process is not None and self._process.stderr is not None
        while await self._process.stderr.read(65536):
            pass  # 持续排空服务端标准错误，避免管道写满或保留用户侧诊断内容。

    async def _initialize(self) -> None:
        command = self.command
        if not Path(command).is_absolute():
            command = shutil.which(command, path=self.environ.get("PATH", "")) or str(self.root / command)
        argv = [command, *self.args]
        if os.name == "nt" and Path(command).suffix.lower() in {".cmd", ".bat"}:
            argv = [self.environ.get("COMSPEC", "C:/Windows/System32/cmd.exe"), "/d", "/s", "/c",
                    '"' + subprocess.list2cmdline(argv) + '"']
        self._process = await asyncio.create_subprocess_exec(
            *argv, cwd=self.root, env=self.environ, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, limit=MAX_HEADER_BYTES,
            **({"creationflags": subprocess.CREATE_NO_WINDOW | 4} if os.name == "nt" else {"start_new_session": True}),
        )
        if os.name == "nt":
            from .windows_job import WindowsJob

            try:
                self._job = WindowsJob(self._process)
            except BaseException:
                self._process.kill()
                await self._process.wait()
                raise
        self._reader = asyncio.create_task(self._read(), name="lsp-reader")
        self._stderr = asyncio.create_task(self._drain_stderr(), name="lsp-stderr")
        result = await self.request("initialize", {"processId": os.getpid(), "rootUri": self.rootUri,
            "capabilities": {"textDocument": {name: {} for name in (
                "definition", "references", "hover", "documentSymbol", "implementation", "callHierarchy")},
                "workspace": {"symbol": {}}, "general": {"positionEncodings": ["utf-16"]}}})
        encoding = result.get("capabilities", {}).get("positionEncoding", "utf-16") if isinstance(result, dict) else "utf-16"
        if encoding != "utf-16":
            raise ValueError("LSP server 未采用UTF16位置编码。")
        await self._notify("initialized", {})

    async def _ready(self, signal: threading.Event | None = None) -> None:
        if self._closing or self._closed:
            raise ConnectionError("LSP client 已关闭。")
        if self._initializing is None:
            self._initializing = asyncio.create_task(self._initialize(), name="lsp-initialize")
        while not self._initializing.done():
            if signal is not None and signal.is_set():
                raise InterruptedError("LSP 初始化等待已取消。")
            await asyncio.wait({self._initializing}, timeout=.05)
        await self._initializing

    async def _sync(self, filePath: str) -> str:
        path = Path(filePath)
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        uri = pathToFileUri(path)
        async with self._sync_lock:
            stat = await asyncio.to_thread(path.stat)
            existing = self._documents.get(uri)
            if existing is None or existing[1] != stat.st_mtime_ns:
                text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
                version = 1 if existing is None else existing[0] + 1
                if existing is None:
                    await self._notify("textDocument/didOpen", {"textDocument": {
                        "uri": uri, "languageId": _LANGUAGES.get(path.suffix.lower(), "plaintext"), "version": version, "text": text}})
                else:
                    await self._notify("textDocument/didChange", {"textDocument": {"uri": uri, "version": version},
                                                                 "contentChanges": [{"text": text}]})
                self._documents[uri] = version, stat.st_mtime_ns
        return uri

    async def _prep(self, path: str, line: int, character: int, signal: threading.Event | None) -> dict[str, Any]:
        await self._ready(signal)
        return {"textDocument": {"uri": await self._sync(path)}, "position": toLspPosition(line, character)}

    @staticmethod
    def formatLocations(result: Any, emptyMsg: str) -> str:
        locations = result if isinstance(result, list) else [result] if result else []
        return "\n".join(fmtLocation(item if "uri" in item else {
            "uri": item["targetUri"], "range": item["targetRange"]}) for item in locations) if locations else emptyMsg

    async def _locations(self, operation: str, empty: str, path: str, line: int, character: int,
                         signal: threading.Event | None) -> str:
        params = await self._prep(path, line, character, signal)
        if operation == "references":
            params["context"] = {"includeDeclaration": True}
        return self.formatLocations(await self.request("textDocument/" + operation, params, signal=signal), empty)

    async def definition(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        return await self._locations("definition", "未找到定义", path, line, character, signal)

    async def references(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        return await self._locations("references", "未找到引用", path, line, character, signal)

    async def implementation(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        return await self._locations("implementation", "未找到实现", path, line, character, signal)

    async def hover(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        result = await self.request("textDocument/hover", await self._prep(path, line, character, signal), signal=signal)
        content = result.get("contents") if result else None
        if not content:
            return "(无 hover 信息)"
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(item if isinstance(item, str) else item.get("value", "") for item in content)
        value = content.get("value")
        return value if isinstance(value, str) else "(无 hover 信息)"

    async def documentSymbol(self, path: str, *, signal: threading.Event | None = None) -> str:
        await self._ready(signal)
        result = await self.request("textDocument/documentSymbol", {"textDocument": {"uri": await self._sync(path)}}, signal=signal)
        lines: list[str] = []

        def walk(symbols: list[dict[str, Any]], depth: int) -> None:
            for symbol in symbols:
                start = symbol.get("range", symbol.get("location", {}).get("range", {})).get("start")
                if start:
                    lines.append("  " * depth + f"{symbol['name']}  (行 {start['line'] + 1})")
                walk(symbol.get("children", []), depth + 1)
        walk(result or [], 0)
        return "\n".join(lines) if result else "(无符号)"

    async def workspaceSymbol(self, query: str, *, signal: threading.Event | None = None) -> str:
        await self._ready(signal)
        result = await self.request("workspace/symbol", {"query": query}, signal=signal)
        return "\n".join(item["name"] + "  " + fmtLocation(item["location"]) for item in result) if result else f"未找到匹配「{query}」的符号"

    async def _hierarchy(self, path: str, line: int, character: int, signal: threading.Event | None) -> Any:
        result = await self.request("textDocument/prepareCallHierarchy", await self._prep(path, line, character, signal), signal=signal)
        return result[0] if result else None

    async def prepareCallHierarchy(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        item = await self._hierarchy(path, line, character, signal)
        return json.dumps(item, ensure_ascii=False, separators=(",", ":")) if item else "(该位置无法建立调用层级——需是函数/方法)"

    async def _calls(self, incoming: bool, path: str, line: int, character: int, signal: threading.Event | None) -> str:
        item = await self._hierarchy(path, line, character, signal)
        if not item:
            return "(该位置无法建立调用层级——需是函数/方法)"
        result = await self.request("callHierarchy/" + ("incomingCalls" if incoming else "outgoingCalls"), {"item": item}, signal=signal)
        key = "from" if incoming else "to"
        return ("\n".join(call[key]["name"] + "  " + fmtLocation(call[key]) for call in result)
                if result else "(没有调用方)" if incoming else "(没有被调用方)")

    async def incomingCalls(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        return await self._calls(True, path, line, character, signal)

    async def outgoingCalls(self, path: str, line: int, character: int, *, signal: threading.Event | None = None) -> str:
        return await self._calls(False, path, line, character, signal)

    async def dispose(self) -> None:
        if self._disposing is None:
            self._disposing = asyncio.create_task(self._dispose(), name="lsp-dispose")
        await asyncio.shield(self._disposing)

    async def _dispose(self) -> None:
        if self._closed:
            return
        self._closing = True
        if self._initializing is not None:
            if not self._initializing.done():
                self._initializing.cancel()
            await asyncio.gather(self._initializing, return_exceptions=True)
        process = self._process
        if process is not None:
            try:
                if process.returncode is None:
                    with contextlib.suppress(Exception):
                        await self.request("shutdown", None, timeout=SHUTDOWN_TIMEOUT)
                    with contextlib.suppress(Exception):
                        await self._notify("exit")
                    if process.stdin is not None:
                        process.stdin.close()
                    try:
                        await asyncio.wait_for(process.wait(), 1)
                    except TimeoutError:
                        pass  # 下方回收服务端进程树，以关闭仍被后代进程持有的管道。
            finally:
                if self._job is not None:
                    await asyncio.to_thread(self._job.close)
                    self._job = None
                if os.name != "nt":
                    import signal as signals

                    with contextlib.suppress(ProcessLookupError):
                        getattr(os, "killpg")(process.pid, getattr(signals, "SIGKILL"))
                if process.returncode is None:
                    process.kill()
                await asyncio.wait_for(process.wait(), 3)
                for task in (self._reader, self._stderr):
                    if task is not None and not task.done():
                        task.cancel()
                await asyncio.gather(*(task for task in (self._reader, self._stderr) if task is not None), return_exceptions=True)
        self._closed = True
