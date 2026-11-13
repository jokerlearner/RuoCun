# 31 启动记忆选择模块

领取基线 `31220a7394456bf3f5debc4274f28948c83b7c40`。唯一冻结 DAO `f17e189dc68a0a0a0b9937784e1b7ce29aed80eb`。来源、产品和复用的 30 接口字节见 [source-members.json](source-members.json)。

`await buildStartupMemory(store)` 从已审 `MemoryStore` 依序读项目、用户、知识库的 active 记录。知识库沿项目 id 匹配 `origin`，保留锁定项。逐条复用来源与有效期验证，排除 stale 并为 changed 正文加提示。少于 50 条 live 时按来源 `selectFullText(cap=50)` 输出全文，优先组在前，其余按留存分数稳定排序。达到 50 条时，高优 user、feedback、locked 全留，其余补足 40 条全文。其后至多 200 条标题或名称进入索引，已入全文的同名项排除。150 条旧选择函数保留来源断言，普通启动走两层路径。

组合根持有一次启动计算的结果。冻结源码在恢复时用旧消息覆盖新建会话消息。RuoCun 的普通入口沿既有恢复后系统提示重建与确认保存接缝消费本次快照，并在同一进程的后续轮次保持固定前缀。关闭开关、真实请求和恢复由主线的已有入口用例验收。反思尾部消息的实际生产者归后续票。

| 回执 | 实际结果 |
| --- | --- |
| [来源 red](raw/n4-31-source-red/command.json) | 新模块缺失，收集失败 |
| [来源 green](raw/n4-31-source-green/command.json) | 冻结 `inject.test.ts` 11 项通过，0.14 秒 |
| [Ruff](raw/n4-31-ruff/command.json)、[mypy](raw/n4-31-mypy/command.json) | 通过，mypy 1 源 |

命令经白名单启动器使用私有 CPython 3.11 与合成目录，敏感扫描为 false，进程已收齐。这里记录模块的来源断言，主线负责普通入口及最终安装产物。
