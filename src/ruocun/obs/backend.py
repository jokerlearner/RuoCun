"""为模型和工具提供可选观测接口。业务动作只执行一次，观察器异常由接口层消化。"""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from typing import Any, Literal, Protocol, TypedDict

from ..memory.secrets import redactSecrets

SpanType = Literal["DEFAULT", "LLM", "TOOL"]


class ObsSpan(Protocol):
    def setAttributes(self, attrs: Mapping[str, Any]) -> None: ...
    def end(self) -> None: ...


class ObsBackend(Protocol):
    def startSpan(self, options: Mapping[str, Any]) -> ObsSpan: ...
    def activate(self, span: ObsSpan) -> AbstractContextManager[Any]: ...
    def event(self, name: str, attributes: Mapping[str, Any]) -> None: ...
    def flush(self) -> Any: ...


class ObsStatus(TypedDict):
    requested: bool
    on: bool
    endpoint: str | None


_backend: ObsBackend | None = None
_session: str | None = None
_meta: dict[str, Any] = {}
_scope: ContextVar[dict[str, Any]] = ContextVar("ruocun_obs_scope", default={})
_redact: Callable[[str], str] | None = None
_requested = False
_endpoint: str | None = None
_flush_lock = threading.Lock()
_flushing: set[tuple[int, str]] = set()


def setBackend(backend: ObsBackend | None) -> None:
    global _backend
    _backend = backend


def getBackend() -> ObsBackend | None:
    return _backend


def isObsOn() -> bool:
    return _backend is not None


def setObsSession(sessionId: str | None) -> None:
    global _session
    _session = sessionId


def getObsSession() -> str | None:
    return _scope.get().get("sessionId", _session)


def setObsMeta(meta: Mapping[str, Any]) -> None:
    _meta.update(meta)


def getObsMeta() -> dict[str, Any]:
    return {**_meta, **{key: value for key, value in _scope.get().items() if key != "sessionId"}}


def setObsStatus(status: Mapping[str, Any]) -> None:
    global _requested, _endpoint
    if "requested" in status:
        _requested = bool(status["requested"])
    if "endpoint" in status:
        _endpoint = status["endpoint"]


def obsStatus() -> ObsStatus:
    return {"requested": _requested, "on": isObsOn(), "endpoint": _endpoint}


def setObsRedactor(redact: Callable[[str], str] | None) -> None:
    global _redact
    _redact = redact


def safeValue(value: Any) -> Any:
    """生成用于观测的副本，保留原模型和工具数据。"""
    if isinstance(value, str):
        text = _redact(value) if _redact else value
        return redactSecrets(text)
    if isinstance(value, Mapping):
        return {str(key): ("[redacted]" if str(key).lower() in {
            "apikey", "api_key", "authorization", "base64", "key", "password", "secret"
        } else safeValue(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [safeValue(item) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return safeValue(str(value))


@contextmanager
def observationScope(*, sessionId: str | None = None, identity: str | None = None,
                     depth: int | None = None, taskId: str | None = None,
                     runId: str | None = None, toolCallId: str | None = None) -> Iterator[None]:
    fields = {"sessionId": sessionId, "identity": identity, "depth": depth, "taskId": taskId,
              "runId": runId, "toolCallId": toolCallId}
    token = _scope.set({**_scope.get(), **{k: v for k, v in fields.items() if v is not None}})
    try:
        yield
    finally:
        _scope.reset(token)


class _SafeSpan:
    def __init__(self, raw: ObsSpan | None) -> None:
        self.raw = raw

    def setAttributes(self, attrs: Mapping[str, Any]) -> None:
        try:
            if self.raw:
                self.raw.setAttributes(safeValue(attrs))
        except Exception:
            pass

    def end(self) -> None:
        try:
            if self.raw:
                self.raw.end()
        except Exception:
            pass


def startSpan(name: str, *, spanType: SpanType = "DEFAULT", input: Any = None,
              metadata: Mapping[str, Any] | None = None) -> _SafeSpan:
    raw = None
    try:
        if _backend:
            raw = _backend.startSpan(safeValue({"name": name, "spanType": spanType, "input": input,
                "sessionId": getObsSession(), "metadata": {**getObsMeta(), **(metadata or {})}}))
    except Exception:
        pass
    return _SafeSpan(raw)


@contextmanager
def spanScope(name: str, *, spanType: SpanType = "DEFAULT", input: Any = None,
              metadata: Mapping[str, Any] | None = None) -> Iterator[_SafeSpan]:
    backend = _backend
    span = startSpan(name, spanType=spanType, input=input, metadata=metadata)
    activation = None
    try:
        if backend and span.raw:
            activation = backend.activate(span.raw)
            activation.__enter__()
    except Exception:
        activation = None
    # 业务操作可能已经发生副作用，观测层不得以异常为由重做本次业务。
    try:
        yield span
    finally:
        if activation is not None:
            try:
                activation.__exit__(None, None, None)
            except Exception:
                pass
        span.end()


def obsEvent(name: str, attributes: Mapping[str, Any] | None = None) -> None:
    try:
        if _backend:
            _backend.event(safeValue(name), safeValue({**getObsMeta(), **(attributes or {})}))
    except Exception:
        pass


async def _bounded(callback: Callable[[], Any], key: tuple[int, str], timeoutMs: int) -> None:
    done = threading.Event()
    with _flush_lock:
        if key in _flushing:
            return
        _flushing.add(key)

    def flush() -> None:
        try:
            result = callback()
            if inspect.isawaitable(result):
                async def wait_flush() -> None:
                    await result
                asyncio.run(wait_flush())
        except Exception:
            pass
        finally:
            with _flush_lock:
                _flushing.discard(key)
            done.set()

    # 观测线程采用守护方式，避免退出时被卡住的观察器阻塞 asyncio.run 清理。
    threading.Thread(target=flush, name="ruocun-obs-flush", daemon=True).start()
    deadline = asyncio.get_running_loop().time() + max(0, timeoutMs) / 1000
    while not done.is_set() and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(min(0.01, max(0, deadline - asyncio.get_running_loop().time())))


async def flushObs(timeoutMs: int = 2000) -> None:
    backend = _backend
    if backend is not None:
        await _bounded(backend.flush, (id(backend), "flush"), timeoutMs)


async def closeObs(timeoutMs: int = 2000) -> None:
    backend = _backend
    setBackend(None)
    if backend is not None:
        shutdown = getattr(backend, "shutdown", None)
        await _bounded(shutdown if callable(shutdown) else backend.flush, (id(backend), "close"), timeoutMs)
