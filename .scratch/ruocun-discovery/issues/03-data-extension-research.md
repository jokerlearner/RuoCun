# 查清 SQLite、配置与扩展兼容契约

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: Codex/compatibility-research
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [冻结可复现参考快照](01-reference-snapshot.md)

## Question

哪些 SQLite 持久化保证、配置结构与发现顺序、Skills/Hooks/MCP/插件协议是 Python 迁移必须保留的契约？哪些存储细节可以在不迁移旧 DAO 会话的前提下调整？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 列出数据库 schema、事务、WAL/同步设置、持久文件、执行标识、会话恢复所依赖的关联。
- 覆盖凭据、配置发现/覆盖、环境变量、项目指令、Skills、Hooks、MCP 各传输、LSP、插件和自定义命令。
- 明确格式兼容、协议语义兼容、配置路径命名及内部实现替换的区别。
- 列出真实来源 fixture、跨语言 golden cases 和需要实测的边界。
- 既定“不迁移旧会话”不重新提问；发现新的范围冲突时才上报。

## Assets

- [SQLite、配置与扩展兼容契约研究](../research/03-data-extension.md)
- 本地研究分支：research/ruocun-compatibility；提交：3cdcb246ceefe59be07990175fdf08874114edef。

## Comments

- 2026-11-05：建图时先认领，委派本地独立 research 分支进行只读调查。
- 2026-11-05：研究报告已提交并由主会话收录；静态研究完成，产品及协议实验尚未执行。

## Answer

已核实 SQLite 五表、事务/所有权与工具未知结果保护、会话和 runner 文件契约，并完整登记各配置/扩展通道实际的发现、覆盖和信任规则。
报告区分内部存储可调整部分、外部协议必须保留部分、候选建议及未实测项；旧 DAO 会话迁移仍为范围外，未发现新的范围冲突。
Python SDK 默认值与协议边界需实测的问题已收敛为 [用最小 Python 适配器验证扩展协议与兼容解析](15-extension-protocol-experiment.md)。后续兼容路线由对应决策票收口。
