"""为当前项目解析语言服务器，把定义、引用和符号等导航请求发给相应客户端。"""

from collections.abc import Awaitable, Callable
from typing import Any

from ..lsp.client import LspClient
from ..lsp.descriptions import DESCRIPTION, DESCRIPTION_EN
from .schema import objectSchema
from .types import Tool, ToolContext

OPS = ("goToDefinition", "findReferences", "hover", "documentSymbol", "workspaceSymbol",
       "goToImplementation", "prepareCallHierarchy", "incomingCalls", "outgoingCalls")
_METHODS = {"goToDefinition": "definition", "findReferences": "references", "goToImplementation": "implementation"}


async def _handler(args: dict[str, Any], ctx: ToolContext) -> str:
    if ctx.lsp is None:
        return "当前环境不支持 LSP。"
    resolved = ctx.lsp.resolve(args["filePath"])
    if "error" in resolved:
        return str(resolved["error"])
    client: LspClient = resolved["client"]
    operation = args["operation"]
    if operation == "workspaceSymbol":
        if not args.get("query"):
            return "workspaceSymbol 需要 query 参数。"
        return await client.workspaceSymbol(args["query"], signal=ctx.signal)
    if operation == "documentSymbol":
        return await client.documentSymbol(args["filePath"], signal=ctx.signal)
    if "line" not in args or "character" not in args:
        return f"{operation} 需要 line 和 character 参数。"
    method: Callable[..., Awaitable[str]] = getattr(client, _METHODS.get(operation, operation))
    return await method(args["filePath"], args["line"], args["character"], signal=ctx.signal)


lspTool = Tool(
    name="LSP", description=DESCRIPTION, descriptionEn=DESCRIPTION_EN,
    schema=objectSchema({
        "operation": {"type": "string", "enum": list(OPS), "description": "要执行的 LSP 操作"},
        "filePath": {"type": "string", "minLength": 1, "description": "文件路径(相对工作区根目录);workspaceSymbol 时用它决定去哪个 server 查"},
        "line": {"type": "integer", "minimum": 1, "description": "行号(1-based,同编辑器习惯)。除 workspaceSymbol 外必填"},
        "character": {"type": "integer", "minimum": 1, "description": "列号(1-based,同编辑器习惯)。除 workspaceSymbol 外必填"},
        "query": {"type": "string", "description": "符号名/部分名(仅 workspaceSymbol 用)"},
    }, ["operation", "filePath"]), capability="read", approval="auto", shouldDefer=True, handler=_handler,
)
