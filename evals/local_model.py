"""Network restriction shared by local-model evaluation entry points."""

from __future__ import annotations

import urllib.request
from collections.abc import Iterator
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    BaseHandler,
    HTTPRedirectHandler,
    OpenerDirector,
    ProxyHandler,
    Request,
)

from ruocun.client.client import HttpResponse

_NATIVE_OPENER = urllib.request.build_opener
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


class _LoopbackOnly(BaseHandler):
    handler_order = 90

    def http_request(self, request: Request) -> Request:
        if urlsplit(request.full_url).hostname not in _LOOPBACK:
            raise OSError("离线模型入口仅允许环回地址。")
        return request

    https_request = http_request


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: object, code: int, msg: str,
                         headers: object, newurl: str) -> None:
        return None


def _offline_opener(*handlers: Any) -> OpenerDirector:
    return _NATIVE_OPENER(ProxyHandler({}), _NoRedirect(), _LoopbackOnly(), *handlers)


def installOfflineOpener() -> None:
    # Called only in an isolated eval Agent process. Retain product HTTP/HTTPS
    # observation handlers when urllib_transport constructs its own opener.
    urllib.request.build_opener = _offline_opener
    urllib.request.install_opener(_offline_opener())


def localTransport(url: str, headers: dict[str, str], body: bytes) -> HttpResponse:
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        response = _offline_opener().open(request, timeout=15)
    except HTTPError as error:
        try:
            return HttpResponse(error.code, dict(error.headers.items()), (error.read(4096),))
        finally:
            error.close()

    def chunks() -> Iterator[bytes]:
        with response:
            while chunk := response.read1(8192):
                yield chunk

    return HttpResponse(response.status, dict(response.headers.items()), chunks())
