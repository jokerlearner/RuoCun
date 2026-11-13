# 31 启动记忆选择独审

固定 `9941cc6f39ca0b09243e38e84de8894120837bb4`。静态核对冻结 `index.ts:705–732` 与 `memory/inject.ts`。按项目、用户、知识库加载 active，知识库保留同项目 origin 或 locked。逐条验证来源及有效期，stale 排除，changed 正文加来源变化提示。live 少于 50 时按优先级和稳定留存排序输出全部正文。达到 50 时保留所有高价值 user、feedback、locked，其余补足 40 条正文，长尾按留存取至多 200 个标题或名称并排除已入全文的同名项。旧 150 项选择保留来源纯断言。

独立复用 stale/changed、全文高优与留存、索引顺序和限额四项，`4 passed in 0.15s`。回执 `raw/review-31-memory-inject-subset01`。合成配置与既有私有 Python 3.11，秘密扫描未命中。剩余模块阻断 0。

## 普通入口

固定 `3e3eaeafee5f96bae7ea78aca1e2be62e6dab67a`，独立复用原普通 CLI 和真实 loopback 用例，`1 passed in 10.90s`。合成 HTTP 首请求期间改动原生记忆，同进程请求保留旧快照。重开原 SQLite 会话后用新快照，旧回复和原图仍在。关闭 `--no-memory` 启动注入时，实际请求仍提供 MemoryRead 和 MemoryWrite。回执 `raw/review-31-entry-cli01`。

冻结 DAO 恢复时以旧消息覆盖初始消息。RuoCun 复用现有恢复接缝读取可信工具配对与图片，先按既有规则处理旧工具参数，再只重建首 system 并确认保存，最后恢复调度。新系统前缀不会丢掉旧工具或图片历史。剩余入口阻断 0，验证未访问真实模型。
