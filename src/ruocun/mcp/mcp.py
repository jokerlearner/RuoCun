"""维护 MCP 服务连接，并将发现的工具、资源和提示接入若存。

连接和能力列表可以刷新。一次调用如果已进入发送流程但没有可信结果，将未确认状态交还给调用方，避免重连时把可能已执行的操作再发一遍。
"""

from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import logging
import os
import re
import shutil
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AsyncExitStack
from datetime import timedelta
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qsl, urlsplit

import httpx
from anyio import BrokenResourceError, ClosedResourceError, EndOfStream
from anyio.streams.memory import MemoryObjectReceiveStream
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError
from mcp.shared.message import SessionMessage
from pydantic import model_serializer

from ..permissions.secrets import redactSecrets
from ..tools.registry import ToolRegistry
from ..tools.tool_batch import UnknownToolOutcome
from ..tools.types import Tool, ToolContext, ToolRejected
from ..version import __version__

_REQUEST_TIMEOUT = timedelta(seconds=60)
ElicitHandler = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def _invalid_constant(value: str) -> None:
    raise ValueError(f"Invalid JSON constant: {value}")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


async def loadMcpConfig(files: Sequence[Path]) -> dict[str, Any]:
    servers: dict[str, Any] = {}
    for file in files:
        try:
            text = await asyncio.to_thread(Path(file).read_text, encoding="utf-8")
            raw = json.loads(text, parse_constant=_invalid_constant)
        except (OSError, ValueError, UnicodeError):
            continue
        declared = raw.get("mcpServers") if isinstance(raw, dict) else None
        if isinstance(declared, dict):
            servers.update(declared)
    return {"mcpServers": servers}


def unpack(result: Mapping[str, Any]) -> str:
    parts = [str(part.get("text") or "") if part.get("type") == "text" else _json(part)
             for part in result.get("content") or []]
    return "\n".join(parts).strip() or "(无输出)"


def unpackResource(result: Mapping[str, Any]) -> str:
    parts = [str(part["text"]) if part.get("text") is not None else (
        f"[二进制内容 {part.get('mimeType') or '?'}{(' @ ' + part['uri']) if part.get('uri') else ''}]"
        if part.get("blob") is not None else "") for part in result.get("contents") or []]
    return "\n".join(parts).strip() or "(无内容)"


def unpackPrompt(result: Mapping[str, Any]) -> str:
    return "\n".join(f"{message.get('role', '?')}: " + (
        str(message["content"].get("text") or "") if message.get("content", {}).get("type") == "text"
        else _json(message.get("content"))) for message in result.get("messages") or []).strip() or "(空模板)"


class _FetchClient(httpx.AsyncClient):
    """跟随重定向，请求头如何随跳转转交由 HTTPX 处理。"""

    async def send(self, request: httpx.Request, **kwargs: Any) -> httpx.Response:
        return await super().send(request, **{**kwargs, "follow_redirects": True})


class _RedactLog(logging.Filter):
    """在纳入过滤的 SDK 日志送往处理器前清理敏感内容。"""

    def __init__(self, redact: Callable[[str], str]) -> None:
        super().__init__()
        self.redact = redact

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if record.exc_info:
            message += "\n" + logging.Formatter().formatException(record.exc_info)
        elif record.exc_text:
            message += "\n" + record.exc_text
        record.msg, record.args = self.redact(message), ()
        record.exc_info, record.exc_text = None, None
        if record.stack_info:
            record.stack_info = self.redact(record.stack_info)
        return True


_SDK_LOGGERS = ("mcp.client.sse", "mcp.client.streamable_http", "mcp.client.stdio",
                "mcp.client.session", "mcp.shared.session", "httpx")


class _NotSent(RuntimeError):
    """服务不可用，调用在进入发送接口前被拒绝。"""


class _ProtocolRejected(RuntimeError):
    """服务器已返回有效的 JSON-RPC 错误，应以该响应结算本次调用。"""


class _ReadResourceParams(types.ReadResourceRequestParams):
    # 资源 URI 是服务端识别原资源的字符串，仅校验类型，保留原有写法。
    uri: Any


class _ReadResourceRequest(types.ClientRequest):
    @model_serializer
    def wire(self) -> dict[str, Any]:
        # 直接序列化原字符串，避免 SDK 转换 URI 后妨碍服务端匹配。
        root = cast(types.ReadResourceRequest, self.root)
        return {"method": "resources/read", "params": {"uri": root.params.uri}}


class _ReadTap:
    """在 SDK 校验公开返回值之前观测收到的协议响应。"""

    def __init__(self, stream: Any, owner: _Connection) -> None:
        self.stream, self.owner = stream, owner

    async def __aenter__(self) -> _ReadTap:
        await self.stream.__aenter__()
        return self

    async def __aexit__(self, kind: Any, error: Any, trace: Any) -> None:
        await self.stream.__aexit__(kind, error, trace)

    def __aiter__(self) -> _ReadTap:
        return self

    async def __anext__(self) -> Any:
        try:
            return await self.receive()
        except EndOfStream:
            raise StopAsyncIteration from None

    async def aclose(self) -> None:
        await self.stream.aclose()

    async def receive(self) -> Any:
        try:
            message = await self.stream.receive()
        except (EndOfStream, BrokenResourceError, ClosedResourceError) as error:
            self.owner.unavailable(error)
            raise
        if not isinstance(message, Exception):
            raw = message.message.root
            if isinstance(raw, types.JSONRPCError):
                self.owner.wire_error = raw.error.model_dump(mode="json", exclude_none=True)
            elif isinstance(raw, types.JSONRPCResponse):
                self.owner.wire_result = copy.deepcopy(raw.result)
        return message


class _Connection:
    def __init__(self, owner: McpManager, name: str, config: Mapping[str, Any]) -> None:
        self.owner, self.name, self.config = owner, name, copy.deepcopy(dict(config))
        self.session: ClientSession | None = None
        self.capabilities: dict[str, Any] = {}
        self.wire_error: dict[str, Any] | None = None
        self.wire_result: dict[str, Any] | None = None
        self._lock = asyncio.Lock()
        self._stop = asyncio.Event()
        self._ready: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._task: asyncio.Task[None] | None = None
        self.error: BaseException | None = None
        self._changed = asyncio.Event()
        self._changes: set[str] = set()
        self._observer: asyncio.Task[None] | None = None
        self._closing = False
        self._unavailable = asyncio.Event()
        self.transport_error: BaseException | None = None

    def unavailable(self, error: BaseException) -> None:
        self.transport_error = error
        self._unavailable.set()

    def _parameters(self) -> StdioServerParameters:
        if self.config.get("url"):
            raise ValueError("HTTP/SSE transport is not connected in this stdio stage.")
        command = self.config.get("command", "")
        args = self.config.get("args", [])
        declared = self.config.get("env", {})
        if (not isinstance(command, str) or not command or not isinstance(args, list)
                or not all(isinstance(arg, str) for arg in args) or not isinstance(declared, dict)
                or not all(isinstance(key, str) and isinstance(value, str) for key, value in declared.items())):
            raise ValueError("MCP stdio command, args or env is invalid.")
        environment = {**self.owner.env, **declared}
        executable = Path(command)
        if not executable.is_absolute() and executable.parent != Path("."):
            executable = self.owner.cwd / executable
        elif not executable.is_absolute():
            found = shutil.which(command, path=environment.get("PATH"))
            if found is None:
                candidate = self.owner.cwd / command
                if not candidate.is_file():
                    raise FileNotFoundError("MCP command was not found.")
                found = str(candidate)
            executable = Path(found)
        resolved = str(executable.resolve())
        if not executable.is_file():
            raise FileNotFoundError("MCP command was not found.")
        return StdioServerParameters(command=resolved, args=args, env=environment,
                                     cwd=self.owner.cwd, encoding="utf-8", encoding_error_handler="strict")

    async def _elicit(self, context: Any, params: types.ElicitRequestParams) -> types.ElicitResult:
        handler = self.owner.on_elicit
        if handler is None or not isinstance(params, types.ElicitRequestFormParams):
            return types.ElicitResult(action="decline")
        result = await handler(params.message, params.requestedSchema)
        return types.ElicitResult.model_validate(result)

    async def _message(self, message: Any) -> None:
        if isinstance(message, (httpx.TransportError, httpx.HTTPStatusError, OSError,
                                EndOfStream, BrokenResourceError, ClosedResourceError)):
            self.unavailable(message)
        elif isinstance(message, types.ServerNotification):
            method = message.root.method
            kind = {"notifications/tools/list_changed": "tools", "notifications/prompts/list_changed": "prompts",
                    "notifications/resources/list_changed": "resources"}.get(method)
            if kind is not None:
                self._changes.add(kind)
                self._changed.set()

    async def observe(self) -> None:
        while True:
            await self._changed.wait()
            self._changed.clear()
            if self._closing:
                return
            changes, self._changes = self._changes, set()
            allowed = {kind for kind in changes if self.capabilities.get(kind, {}).get("listChanged")}
            if allowed:
                try:
                    await self.owner._refresh(self.name, self, notice="tools" in allowed)
                except Exception:
                    # 能力列表刷新失败时保留当前会话，等待下一次通知或刷新。
                    pass

    async def _serve(self) -> None:
        try:
            async with AsyncExitStack() as stack:
                url = self.config.get("url")
                if url:
                    if not isinstance(url, str) or not url.startswith(("https://", "http://")):
                        raise ValueError("MCP HTTP URL must use http or https.")
                    headers = self.config.get("headers", {})
                    if not isinstance(headers, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items()):
                        raise ValueError("MCP HTTP headers must be a string mapping.")
                    def http_client(headers: dict[str, str] | None = headers,
                                    timeout: httpx.Timeout | None = None,
                                    auth: httpx.Auth | None = None) -> httpx.AsyncClient:
                        return _FetchClient(headers=headers, timeout=httpx.Timeout(60), follow_redirects=True)

                    if self.config.get("type") == "sse":
                        streams = await stack.enter_async_context(sse_client(
                            url, headers=headers, timeout=60, sse_read_timeout=60,
                            httpx_client_factory=http_client,
                        ))
                    else:
                        client = await stack.enter_async_context(http_client())
                        streams = await stack.enter_async_context(streamable_http_client(url, http_client=client))
                else:
                    errlog = stack.enter_context(open(os.devnull, "w", encoding="utf-8"))
                    streams = await stack.enter_async_context(stdio_client(self._parameters(), errlog=errlog))
                session = await stack.enter_async_context(ClientSession(
                    cast(MemoryObjectReceiveStream[SessionMessage | Exception], _ReadTap(streams[0], self)),
                    streams[1], read_timeout_seconds=_REQUEST_TIMEOUT,
                    elicitation_callback=self._elicit,
                    message_handler=self._message,
                    client_info=types.Implementation(name="ruocun", version=__version__),
                ))
                initialized = await session.initialize()
                self.capabilities = initialized.capabilities.model_dump(mode="json", exclude_none=True)
                self.session = session
                self._ready.set_result(None)
                await self._stop.wait()
        except BaseException as error:
            self.error = error
            if not self._ready.done():
                self._ready.set_exception(error)
        finally:
            self.session = None
            self.unavailable(self.error or EndOfStream())

    async def start(self) -> None:
        self._task = asyncio.create_task(self._serve(), name="ruocun-mcp-" + self.name)
        await self._ready

    async def request(self, method: str, params: dict[str, Any], signal: Any = None) -> dict[str, Any]:
        async with self._lock:
            session = self.session
            if self._stop.is_set() or self._unavailable.is_set() or session is None or signal is not None and signal.is_set():
                raise _NotSent("MCP connection is not available; request was not sent.")
            self.wire_error, self.wire_result = None, None
            if method == "tools/list":
                request = types.ClientRequest(types.ListToolsRequest())
                response_type: Any = types.ListToolsResult
            elif method == "tools/call":
                request = types.ClientRequest(types.CallToolRequest(params=types.CallToolRequestParams(**params)))
                response_type = types.CallToolResult
            elif method == "resources/list":
                request = types.ClientRequest(types.ListResourcesRequest())
                response_type = types.ListResourcesResult
            elif method == "resources/read":
                request = _ReadResourceRequest(types.ReadResourceRequest(params=_ReadResourceParams(**params)))
                response_type = types.ReadResourceResult
            elif method == "prompts/list":
                request = types.ClientRequest(types.ListPromptsRequest())
                response_type = types.ListPromptsResult
            elif method == "prompts/get":
                request = types.ClientRequest(types.GetPromptRequest(params=types.GetPromptRequestParams(**params)))
                response_type = types.GetPromptResult
            else:
                raise _NotSent("Unsupported MCP request method.")
            try:
                async with asyncio.timeout(_REQUEST_TIMEOUT.total_seconds()):
                    sending = asyncio.create_task(session.send_request(request, response_type, request_read_timeout_seconds=_REQUEST_TIMEOUT))
                    disconnected = asyncio.create_task(self._unavailable.wait())
                    try:
                        done, _ = await asyncio.wait({sending, disconnected}, return_when=asyncio.FIRST_COMPLETED)
                        if sending not in done and self.wire_result is None and self.wire_error is None:
                            assert self.transport_error is not None
                            raise self.transport_error
                        await sending
                    finally:
                        for pending in (sending, disconnected):
                            if not pending.done():
                                pending.cancel()
                        await asyncio.gather(sending, disconnected, return_exceptions=True)
            except McpError as error:
                if self.wire_error == error.error.model_dump(mode="json", exclude_none=True):
                    raise _ProtocolRejected(self.owner.redact(error.error.message)) from error
                raise
            result = self.wire_result
            if result is None:
                raise RuntimeError("MCP response had no verified wire result.")
            return copy.deepcopy(result)

    async def close(self) -> None:
        if self._observer is not None:
            self._closing = True
            self._changed.set()
            await self._observer
            self._observer = None
        self._stop.set()
        if self._task is not None:
            await self._task
        if self.error is not None and not self._ready.cancelled() and self._ready.done():
            # 连接建立失败已由 connectServer 记录和处理。
            if self._ready.exception() is None:
                raise RuntimeError("MCP transport closure was not confirmed.") from self.error


class McpManager:
    def __init__(
        self, registry: ToolRegistry, config: Mapping[str, Any], cwd: Path, env: Mapping[str, str], *,
        disabled_file: Path | None = None, on_elicit: ElicitHandler | None = None,
        on_server_change: Callable[[str], None] | None = None, redact: Callable[[str], str] | None = None,
        persist: Callable[[Path, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self.registry, self.config, self.cwd, self.env = registry, copy.deepcopy(dict(config)), cwd.resolve(), dict(env)
        self.disabled_file = disabled_file
        self.on_elicit, self.on_server_change = on_elicit, on_server_change
        self._redact = redact if redact is not None else str
        self._persist = persist
        self._disabled: dict[str, None] = {}
        self._mutation = asyncio.Lock()
        self._holders: dict[str, _Connection] = {}
        self._errors: dict[str, str] = {}
        self._closed = False
        self._secrets: set[str] = set()
        self._log_filter = _RedactLog(self.redact)
        self._logs_installed = False

    def _rememberSecrets(self, config: Mapping[str, Any]) -> None:
        for field, values in (("headers", config.get("headers", {})), ("env", config.get("env", {}))):
            if isinstance(values, dict):
                self._secrets.update(value for name, value in values.items() if isinstance(value, str) and value
                                     and (field == "headers" or isinstance(name, str)
                                          and re.search(r"KEY|TOKEN|SECRET|PASS|CREDENTIAL|COOKIE", name, re.I)))
        try:
            address = config.get("url")
            url = urlsplit(address if isinstance(address, str) else "")
            self._secrets.update(value for value in (url.username, url.password) if value)
            self._secrets.update(value for _, value in parse_qsl(url.query) if value)
            self._secrets.update(part.partition("=")[2] for part in url.query.split("&") if part.partition("=")[2])
        except ValueError:
            pass

    def redact(self, text: str) -> str:
        for config in self.config.get("mcpServers", {}).values():
            if isinstance(config, dict):
                self._rememberSecrets(config)
        for secret in sorted(self._secrets, key=lambda value: (-len(value), value)):
            text = text.replace(secret, "[REDACTED]")
        return redactSecrets(self._redact(text))

    def _notice(self, text: str) -> None:
        if self.on_server_change is not None:
            self.on_server_change(self.redact(text))

    @property
    def connectedCount(self) -> int:
        return len(self._holders)

    @property
    def executionConfigDigest(self) -> str:
        value = {name: holder.config for name, holder in self._holders.items()}
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def init(self) -> None:
        if self.disabled_file is not None:
            try:
                raw = json.loads(await asyncio.to_thread(self.disabled_file.read_text, encoding="utf-8"))
                disabled = raw.get("disabled", []) if isinstance(raw, dict) else []
                if isinstance(disabled, list):
                    self._disabled = dict.fromkeys(name for name in disabled if isinstance(name, str))
            except (OSError, ValueError):
                pass
        for name, declared in self.config.get("mcpServers", {}).items():
            if name in self._disabled:
                continue
            try:
                await self.connectServer(name, declared)
            except Exception as error:
                self._errors[name] = self.redact(f"{type(error).__name__}: {error}")

    async def connectServer(self, name: str, config: Mapping[str, Any]) -> None:
        if self._closed:
            raise ValueError("MCP manager is closed.")
        if name in self._holders:
            return
        self._rememberSecrets(config)
        if not self._logs_installed:
            for name_of_logger in _SDK_LOGGERS:
                logging.getLogger(name_of_logger).addFilter(self._log_filter)
            self._logs_installed = True
        connection = _Connection(self, name, config)
        try:
            await connection.start()
            tools = await self._buildTools(name, connection)
        except BaseException:
            await connection.close()
            raise
        self._holders[name] = connection
        self._errors.pop(name, None)
        for tool in tools:
            self.registry.register(tool)
        connection._observer = asyncio.create_task(connection.observe(), name="ruocun-mcp-changes-" + name)

    async def _buildTools(self, name: str, connection: _Connection) -> list[Tool]:
        listed = await connection.request("tools/list", {})
        tools = [self._tool(name, connection, entry) for entry in listed["tools"]]
        empty = {"type": "object", "properties": {}}

        def capability(suffix: str, description: str, schema: dict[str, Any], api: dict[str, Any],
                       method: str, format_result: Callable[[dict[str, Any]], str]) -> Tool:
            async def handler(args: dict[str, Any], ctx: ToolContext) -> str:
                params = {"uri": args["uri"]} if method == "resources/read" else {}
                if method == "prompts/get":
                    arguments = args.get("arguments", {})
                    if not all(isinstance(value, str) for value in arguments.values()):
                        raise ToolRejected("MCP prompt arguments 必须是字符串映射，请求未发送。")
                    params = {"name": args["name"], "arguments": arguments}
                result = await self._invoke(connection, method, params, ctx)
                return result if isinstance(result, str) else format_result(result)
            return Tool(name=f"mcp__{name}__{suffix}", description=description, schema=schema, apiParameters=api,
                        capability="network", approval="suggest", handler=handler, persistentEffect=True)

        if "resources" in connection.capabilities:
            tools.append(capability("list_resources", f"列出 MCP server「{name}」当前暴露的全部 resource(uri + 名称,实时查询)。",
                empty, empty, "resources/list", lambda result: "\n".join(
                    item["uri"] + (f"({item['name']})" if item.get("name") else "")
                    for item in result.get("resources", [])) or "(server 未列出任何 resource)"))
            api = {"type": "object", "properties": {"uri": {"type": "string", "description": "resource 的 uri"}}, "required": ["uri"]}
            tools.append(capability("read_resource", f"读取 MCP server「{name}」的一个 resource(按 uri)。先用 mcp__{name}__list_resources 查可用 uri。",
                {"type": "object", "properties": {"uri": {"type": "string"}}, "required": ["uri"]},
                api, "resources/read", unpackResource))
        if "prompts" in connection.capabilities:
            tools.append(capability("list_prompts", f"列出 MCP server「{name}」当前暴露的全部 prompt 模板(name + 说明,实时查询)。",
                empty, empty, "prompts/list", lambda result: "\n".join(
                    item["name"] + (f"({item['description']})" if item.get("description") else "")
                    for item in result.get("prompts", [])) or "(server 未列出任何 prompt)"))
            api = {"type": "object", "properties": {"name": {"type": "string"}, "arguments": {
                "type": "object", "description": "模板参数(字符串映射)"}}, "required": ["name"]}
            schema = {"type": "object", "properties": {"name": {"type": "string"}, "arguments": {
                "type": "object", "additionalProperties": {"type": "string"}}}, "required": ["name"]}
            tools.append(capability("get_prompt", f"取 MCP server「{name}」的 prompt 模板(按 name,可带 arguments 字符串映射)。先用 mcp__{name}__list_prompts 查可用 name。",
                schema, api, "prompts/get", unpackPrompt))
        return tools

    async def _refresh(self, name: str, connection: _Connection, *, notice: bool) -> None:
        if self._closed or connection._closing or self._holders.get(name) is not connection:
            return
        tools = await self._buildTools(name, connection)
        if self._closed or connection._closing or self._holders.get(name) is not connection:
            return
        self.registry.unregisterByPrefix(f"mcp__{name}__")
        for tool in tools:
            self.registry.register(tool)
        if notice:
            self._notice(f"MCP server「{name}」工具列表已更新(当前 {len(tools)} 个工具)。")

    async def _invoke(self, connection: _Connection, method: str, params: dict[str, Any], ctx: ToolContext) -> dict[str, Any] | str:
        if self._closed or ctx.signal.is_set():
            raise ToolRejected("MCP 请求尚未发送，连接不可用或本轮已取消。")
        work = asyncio.create_task(connection.request(method, params, ctx.signal))
        try:
            while not work.done():
                await asyncio.wait({work}, timeout=.05)
                if ctx.signal.is_set() and not work.done():
                    work.cancel()
                    await asyncio.gather(work, return_exceptions=True)
                    raise UnknownToolOutcome("MCP 请求已取消但远端结果未确认；现场保留，未自动重放。")
            return work.result()
        # 区分尚未发送的本地拒绝、服务端明确回复的错误，以及结果仍待确认的调用。
        except _NotSent as error:
            raise ToolRejected(str(error)) from error
        except _ProtocolRejected as error:
            return "Error: MCP " + self.redact(str(error))
        except (Exception, asyncio.CancelledError) as error:
            if not work.done():
                work.cancel()
                await asyncio.gather(work, return_exceptions=True)
            if isinstance(error, UnknownToolOutcome):
                raise
            raise UnknownToolOutcome(f"MCP 请求可能已执行但结果未确认（{type(error).__name__}）；现场保留，未自动重放。") from error

    def _tool(self, server: str, connection: _Connection, definition: Mapping[str, Any]) -> Tool:
        name = definition["name"]
        parameters = copy.deepcopy(definition.get("inputSchema", {"type": "object", "properties": {}}))

        async def handler(arguments: dict[str, Any], ctx: ToolContext) -> str:
            result = await self._invoke(connection, "tools/call", {"name": name, "arguments": arguments}, ctx)
            return result if isinstance(result, str) else unpack(result)

        return Tool(name=f"mcp__{server}__{name}", description=definition.get("description", f"MCP {server} 工具 {name}"),
                    schema={"type": "object"}, apiParameters=parameters, capability="network", approval="suggest",
                    handler=handler, persistentEffect=True)

    async def disconnectServer(self, name: str) -> None:
        holder = self._holders.get(name)
        if holder is None:
            return
        self.registry.unregisterByPrefix(f"mcp__{name}__")
        await holder.close()
        self._holders.pop(name, None)

    async def reconnect(self, name: str) -> None:
        async with self._mutation:
            if name in self._disabled:
                self._notice(f"MCP server「{name}」当前是禁用状态,重连前请先用 /mcp toggle {name} on 启用。")
                return
            config = self.config.get("mcpServers", {}).get(name)
            if config is None:
                raise ValueError(f"MCP server {self.redact(name)} not found")
            await self.disconnectServer(name)
            await self.connectServer(name, config)
            self._notice(f"MCP server「{name}」已重新连接。")

    async def toggle(self, name: str, on: bool) -> None:
        async with self._mutation:
            disabled = dict(self._disabled)
            if on:
                disabled.pop(name, None)
            else:
                disabled[name] = None
            if self.disabled_file is not None:
                if self._persist is None:
                    raise ValueError("MCP 状态持久化端口未装配，状态未改变。")
                await self._persist(self.disabled_file, {"disabled": list(disabled)})
            self._disabled = disabled
            if on:
                config = self.config.get("mcpServers", {}).get(name)
                if config is not None:
                    await self.connectServer(name, config)
            else:
                await self.disconnectServer(name)
            self._notice(f"MCP server「{name}」已{'启用' if on else '禁用'}。")

    async def addServer(self, name: str, config: Mapping[str, Any], config_file: Path) -> None:
        async with self._mutation:
            if self._persist is None:
                raise ValueError("MCP 配置持久化端口未装配，配置未改变。")
            try:
                raw = await asyncio.to_thread(config_file.read_text, encoding="utf-8")
            except FileNotFoundError:
                existing: Any = {}
            else:
                existing = json.loads(raw, parse_constant=_invalid_constant)
            if not isinstance(existing, dict) or not isinstance(existing.get("mcpServers", {}), dict):
                raise ValueError("MCP 配置结构损坏，原文件保留。")
            existing.setdefault("mcpServers", {})[name] = copy.deepcopy(dict(config))
            await self._persist(config_file, existing)
            self.config.setdefault("mcpServers", {})[name] = copy.deepcopy(dict(config))
            await self.connectServer(name, config)
            self._notice(f"MCP server「{name}」已添加并连接。")

    def getServerStatus(self) -> list[dict[str, Any]]:
        result = []
        for name in self.config.get("mcpServers", {}):
            connected, disabled = name in self._holders, name in self._disabled
            result.append({"name": name, "tools": self.registry.countByPrefix(f"mcp__{name}__") if connected else 0,
                           "resources": 0, "prompts": 0, "ok": connected, "disabled": disabled and not connected,
                           **({"error": self._errors.get(name, "未连接")} if not connected and not disabled else {})})
        return result

    async def close(self) -> None:
        self._closed = True
        errors: list[BaseException] = []
        for name, connection in tuple(self._holders.items()):
            self.registry.unregisterByPrefix(f"mcp__{name}__")
            try:
                await connection.close()
            except BaseException as error:
                errors.append(error)
            else:
                self._holders.pop(name, None)
        if self._logs_installed:
            for name_of_logger in _SDK_LOGGERS:
                logging.getLogger(name_of_logger).removeFilter(self._log_filter)
            self._logs_installed = False
        if errors:
            raise RuntimeError("MCP transport closure was not confirmed.") from errors[0]
