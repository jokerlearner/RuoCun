"""Frozen lsp/manager.ts extension routing and shared clients (MIT)."""

from collections.abc import Mapping
from typing import Any

from .client import LspClient
from .config import resolveServerForFile


class LspManager:
    def __init__(self, config: dict[str, Any], rootUri: str, *, environ: Mapping[str, str] | None = None) -> None:
        self.config, self.rootUri, self.environ = config, rootUri, environ
        self.clients: dict[str, LspClient] = {}

    def resolve(self, filePath: str) -> dict[str, Any]:
        found = resolveServerForFile(self.config, filePath)
        if found is None:
            return {"error": f"没有为「{filePath}」这类文件配置 language server。在 .ruocun/lsp.json 里加一条(格式见项目LSP配置说明)。"}
        name, server = found["name"], found["server"]
        if name not in self.clients:
            self.clients[name] = LspClient(server["command"], server.get("args", []), self.rootUri, environ=self.environ)
        return {"client": self.clients[name]}

    async def disposeAll(self) -> None:
        import asyncio

        clients = tuple(self.clients.values())
        outcomes = await asyncio.gather(*(client.dispose() for client in clients), return_exceptions=True)
        if any(isinstance(outcome, BaseException) for outcome in outcomes):
            raise RuntimeError("部分LSP进程关闭未确认，原实例保留。")
        self.clients.clear()
