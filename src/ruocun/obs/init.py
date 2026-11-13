"""Optional official OTLP HTTP exporter with frozen Laminar attributes.

Laminar Python requires a grpcio DLL rejected by this Windows application policy.
The official HTTP exporter avoids importing grpc or auto-instrumenting business I/O.
"""

from __future__ import annotations

import importlib
import json
import logging
import os
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import Any, cast
from urllib.parse import urlsplit

from .backend import ObsSpan, safeValue, setBackend, setObsRedactor, setObsStatus


def _attribute(value: Any) -> Any:
    if isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, (tuple, list)) and all(isinstance(v, str) for v in value):
        return value
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class _OtelSpan:
    def __init__(self, raw: Any) -> None:
        self.raw = raw

    def setAttributes(self, attrs: Mapping[str, Any]) -> None:
        self.raw.set_attributes({k: _attribute(v) for k, v in attrs.items()})

    def end(self) -> None:
        self.raw.end()


class _OtelBackend:
    def __init__(self, provider: Any, trace: Any, session: Any) -> None:
        self.provider, self.trace, self.session = provider, trace, session
        self.tracer = provider.get_tracer("ruocun.obs")

    def startSpan(self, options: Mapping[str, Any]) -> ObsSpan:
        previous = getattr(self.trace.get_current_span(), "attributes", {}) or {}
        parent_path = list(previous.get("lmnr.span.path", ()))
        parent_ids = list(previous.get("lmnr.span.ids_path", ()))
        attrs = {"lmnr.span.type": options.get("spanType", "DEFAULT"),
            "lmnr.span.input": json.dumps(options.get("input"), ensure_ascii=False, separators=(",", ":")),
            "lmnr.span.path": [*parent_path, options["name"]], "lmnr.span.parent_path": parent_path,
            "lmnr.span.parent_ids_path": parent_ids,
            **{"lmnr.association.properties.metadata." + str(k): _attribute(v)
               for k, v in (options.get("metadata") or {}).items()}}
        if options.get("sessionId") is not None:
            attrs["lmnr.association.properties.session_id"] = options["sessionId"]
        raw = self.tracer.start_span(options["name"], attributes=attrs)
        raw.set_attribute("lmnr.span.ids_path", [*parent_ids, f"{raw.get_span_context().span_id:016x}"])
        return _OtelSpan(raw)

    def activate(self, span: ObsSpan) -> AbstractContextManager[Any]:
        if not isinstance(span, _OtelSpan):
            raise TypeError("invalid observation span")
        return cast(AbstractContextManager[Any], self.trace.use_span(span.raw, end_on_exit=False,
                    record_exception=False, set_status_on_exception=False))

    def event(self, name: str, attributes: Mapping[str, Any]) -> None:
        self.trace.get_current_span().add_event(name, {k: _attribute(v) for k, v in attributes.items()})

    def flush(self) -> Any:
        return self.provider.force_flush(timeout_millis=1000)

    def shutdown(self) -> None:
        try:
            self.provider.shutdown()
        finally:
            self.session.close()


class _SafeSdkLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # SDK error messages can echo collector response bodies, headers or span values.
        record.msg = "[obs] 导出器报告异常，详细内容已省略"
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


async def initObs(on: bool, *, environ: Mapping[str, str] | None = None,
                  redact: Callable[[str], str] | None = None,
                  warn: Callable[[str], None] | None = None) -> None:
    setObsStatus({"requested": on, "endpoint": None})
    setObsRedactor(redact)
    setBackend(None)
    if not on:
        return
    env = os.environ if environ is None else environ
    provider = None
    try:
        versions = importlib.import_module("importlib.metadata")
        for name, expected in {"opentelemetry-api": "1.45.2", "opentelemetry-sdk": "1.45.2",
            "opentelemetry-exporter-otlp-proto-http": "1.45.2",
            "opentelemetry-exporter-otlp-common": "0.66b2",
            "opentelemetry-exporter-http-transport": "0.66b2"}.items():
            if versions.version(name) != expected:
                raise RuntimeError("unsupported optional observation SDK version")
        base = env.get("LMNR_BASE_URL", "http://localhost").rstrip("/")
        parsed = urlsplit(base)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username
                or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise ValueError("invalid observation endpoint")
        http_port = int(env.get("LMNR_HTTP_PORT") or parsed.port or 8000)
        if not 0 < http_port <= 65535:
            raise ValueError("invalid observation port")
        host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
        endpoint = f"{parsed.scheme}://{host}:{http_port}/v1/traces"
        # Explicit local endpoint and headers: no SDK .env fallback or global tracer provider.
        trace = importlib.import_module("opentelemetry.trace")
        sdk = importlib.import_module("opentelemetry.sdk.trace")
        exports = importlib.import_module("opentelemetry.sdk.trace.export")
        resource = importlib.import_module("opentelemetry.sdk.resources")
        http = importlib.import_module("opentelemetry.exporter.otlp.proto.http.trace_exporter")
        compression = importlib.import_module("opentelemetry.exporter.otlp.proto.http").Compression
        transport = importlib.import_module("opentelemetry.exporter.http.transport._requests")
        requests = importlib.import_module("requests")
        sampling = importlib.import_module("opentelemetry.sdk.trace.sampling")
        for name in ("opentelemetry.exporter.otlp.proto.http.trace_exporter",
                     "opentelemetry.exporter.otlp.proto.http._common",
                     "opentelemetry.sdk._shared_internal"):
            logger = logging.getLogger(name)
            if not any(isinstance(f, _SafeSdkLog) for f in logger.filters):
                logger.addFilter(_SafeSdkLog())
        key = env.get("LMNR_PROJECT_API_KEY")
        provider = sdk.TracerProvider(resource=resource.Resource({"service.name": "ruocun"}),
                                      sampler=sampling.ALWAYS_ON)
        session = requests.Session()
        session.trust_env = False
        wire_transport = transport.RequestsHTTPTransport(session=session, verify=True, cert=None)
        exporter = http.OTLPSpanExporter(endpoint=endpoint, headers={}, timeout=1,
            compression=compression.NoCompression, _transport=wire_transport)
        # OTel 1.45.2 unconditionally merges ambient OTEL headers even with headers={}.
        # Fixed-version narrow seam: replace before any span can be queued/exported.
        exporter._client._headers = {"Content-Type": "application/x-protobuf",
            **({"Authorization": f"Bearer {key}"} if key else {})}
        provider.add_span_processor(exports.BatchSpanProcessor(exporter, max_queue_size=2048,
            schedule_delay_millis=5000, max_export_batch_size=512, export_timeout_millis=1000))
        setBackend(_OtelBackend(provider, trace, session))
        setObsStatus({"endpoint": f"{host}:{http_port}/v1/traces"})
        if not key and warn:
            warn("[obs] 未设 LMNR_PROJECT_API_KEY，trace 可能无法入库")
    except Exception as error:
        setBackend(None)
        if provider is not None:
            try:
                provider.shutdown()
            except Exception:
                pass
        if warn:
            try:
                warn(safeValue(f"[obs] 初始化失败，已降级关闭:{type(error).__name__}"))
            except Exception:
                pass
