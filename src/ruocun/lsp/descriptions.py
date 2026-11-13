"""Frozen LSP bilingual descriptions, product path adapted (MIT)."""

DESCRIPTION = (
    "用配置好的语言服务器定位符号。goToDefinition 查定义，findReferences 查引用，hover 查看类型，goToImplementation "
    "找实现。documentSymbol 列文件符号，workspaceSymbol 按 query 搜全仓；其余位置操作用从 1 开始的 line 和 "
    "character。prepareCallHierarchy 建立调用项，incomingCalls 和 outgoingCalls 会自行准备调用项。需要在 "
    ".ruocun/lsp.json 配置语言服务。"
)
DESCRIPTION_EN = (
    "Query a configured language server for definitions, references, type information, "
    "and implementations with goToDefinition, findReferences, hover, or "
    "goToImplementation. Use documentSymbol for one file and workspaceSymbol with query "
    "for a workspace lookup. Other position queries use one-based line and character. "
    "incomingCalls and outgoingCalls prepare their own call hierarchy item. Configure "
    "the language server in .ruocun/lsp.json."
)
