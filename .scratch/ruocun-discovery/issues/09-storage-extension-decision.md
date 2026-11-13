# 确定持久化与外部扩展的兼容边界

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/decision_09_compat
Branch: research/d09-compat
Worktree: .worktrees/r09
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清 SQLite、配置与扩展兼容契约](03-data-extension-research.md), [用最小 Python 实验验证取消与崩溃恢复契约](05-runtime-recovery-experiment.md), [用最小 Python 适配器验证扩展协议与兼容解析](15-extension-protocol-experiment.md), [用最小 Python 探针验证 Windows 持久文件与 IPC 权限](18-windows-durable-io-experiment.md), [验证含 WAL 修复的 SQLite 运行环境](19-patched-sqlite-runtime-experiment.md)

## Question

RuoCun 的数据库和持久文件可改变到什么程度，配置、Skills、Hooks、MCP 等哪些外部契约必须保持，命名与发现规则如何同时满足独立项目身份和兼容目标？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 给出内部 schema/会话格式与外部协议的边界清单。
- 明确配置目录、别名、覆盖顺序和凭据读取/写入范围，避免共享会话数据导致干扰。
- 将协议字段、Hook 事件/退出行为、MCP 传输与扩展错误处理转成可测试契约。
- 区分冻结版本实际支持的协议子集、文档宣传和目标兼容要求；来源中的信任门槛与错误路径逐项登记，不能凭名称假定完整兼容其他产品。
- 独立实现自身会话保存和恢复；旧 DAO 会话迁移保持范围外。
- 需要改变已确认兼容目标时，明确冲突并保留用户问题，不能静默缩小范围。

## Assets

- [存储/兼容路线与唯一公共契约](../research/09-storage-extension-route.md)、[静态校验](../research/09-storage-extension-route.validation.json)。研究分支`research/d09-compat`提交`5415b2520228b08e4b2e5b4c942537b14fa7f9eb`本地保留未合并。
- [ADR-0005](../../../docs/adr/0005-runtime-storage-compatibility.md)。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：D18/D19/D15已具备独立技术证据，前置全部满足，领取兼容路线研究；ADR0003未知结果不重放已获用户决定，不再提问。

## Answer

内部RuoCun会话独立产品标识/版本、两原子域、StoragePort、三epoch与管道帧/时限已与D08统一。Windows固定SQLite3.54.1+stdlib、MCP1.30.0与窄LSP/Hook/Deck适配路线有来源与技术依据。

原生.ruocun数据与状态独立；compatibility.json默认空、显式只读source map，各资源原有顺序/信任/覆盖独立保持。DAO环境别名按键存在含空值回退，旧keyRef按准确来源只读，新保存/删除不碰旧服务；不自动扫描或接管DAO会话/信任/凭据。

805来源字节、41链接及契约/MM锚点静态核对；不代表产品通过。SDK重定向/60秒实际deadline、JS RegExp/UTF16、产品IPC/helper和安装库清单已交原实现任务验证，不新增大型前置，不缩减范围。无新用户取舍冲突。
