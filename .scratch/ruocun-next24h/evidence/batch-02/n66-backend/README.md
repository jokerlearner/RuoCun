# 66后端接口切片

Conversation.remember_secret登记本进程显式提供的非空key；redact同时覆盖构造时旧key、已登记新key及兼容secret字段当前值。按长key优先的一次匹配替换，防前缀泄漏且不再处理已生成脱敏标记。集合仅在内存，不写DB，不读取其它profile。

最小合成直接调用确认旧/新/前缀及空key行为，无存储调用，mypy/Ruff通过。66账户切换、面板及权限真实入口由root/A后续验收；这不是整票通过。未扩测试矩阵或构包。
