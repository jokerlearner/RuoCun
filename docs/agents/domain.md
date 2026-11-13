# Domain Docs

采用 single-context：根目录 CONTEXT.md + docs/adr/。

## 阅读规则

- 探索项目之前读取 [CONTEXT.md](../../CONTEXT.md)。
- 设计、实施或审查某个模块之前，读取 [docs/adr/](../adr/) 下相关 ADR。
- 迁移任务同时读取 [baseline.md](../migration/baseline.md)、[module-map.md](../migration/module-map.md)、[acceptance-matrix.md](../migration/acceptance-matrix.md) 和对应规格。
- 文件缺失时可继续只读探索；依赖缺失决定的实施，先在任务票中补齐依据。

## 内容边界

- CONTEXT.md 保存用户确定的目标、边界、术语和文档入口。
- 规格保存功能要求和验收条件。
- ADR 保存架构决定及取舍。
- 任务票保存执行进展、讨论和验证证据。
- 对应表保存 DAO 与 Python 实现之间的关系。

使用 domain-modeling 等技能时，保留 CONTEXT.md 的目标和边界；术语维护不得删除这些用户明确要求的内容。

## 冲突处理

使用 CONTEXT.md 定义的术语。
发现方案与既有 ADR 冲突时，明确引用冲突的 ADR，提出修改理由，经决定后更新或新增替代 ADR。
