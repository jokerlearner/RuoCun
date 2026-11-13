# 确定 Python 并发、任务与恢复技术路线

Labels: wayfinder:research
Mode: AFK
Status: resolved
Assignee: /root/decision_08_runtime
Branch: research/d08-runtime
Worktree: .worktrees/r08
Parent: [RuoCun 迁移决策地图](../map.md)
Blocked by: [查清完整功能、模块职责与运行时调用链](02-function-runtime-research.md), [查清 SQLite、配置与扩展兼容契约](03-data-extension-research.md), [用最小 Python 实验验证取消与崩溃恢复契约](05-runtime-recovery-experiment.md), [用最小 Python 探针验证 Windows 持久文件与 IPC 权限](18-windows-durable-io-experiment.md), [验证含 WAL 修复的 SQLite 运行环境](19-patched-sqlite-runtime-experiment.md)

## Question

基于冻结源码及最小实验，Python 的事件循环、工具执行、后台 runner、取消传播和恢复协议应采用什么组合，才能保持已识别的可观察行为和模块职责？

## 依据与边界

沿用 [CONTEXT.md](../../../CONTEXT.md) 已确认目标。
唯一来源为 [冻结参考快照](../reference/README.md)。
本票解决决策或其必要前置事实，业务迁移实施另行建票。

## 完成条件

- 比较 asyncio、线程/进程及独立 runner 的职责边界，给出选择理由与失败路径。
- 约定流式事件、执行身份、工具结果提交、取消和退出的顺序。
- 对 Monitor、fork、后台 Shell、代理和手工任务分别给出状态/恢复契约；明确会话退出保留后台与显式取消的区别，以及统计、审批/问题、队列和附件的持久边界。
- 逐项关联原模块、验收项和实验；不把库名称当作完整架构。
- 区分既定目标、已验证事实、选择与仍需验证的假设。
- 发现目标冲突才请求用户决策；符合既定目标的工程细节给出有证据的路线。

## Assets

- [运行时路线](../research/08-python-runtime-route.md)，研究分支`research/d08-runtime`提交`e4fd721b1bc670325591e72108e1796d1015a07c`，只收录报告不合并分支。
- [ADR-0005](../../../docs/adr/0005-runtime-storage-compatibility.md)与[D09唯一持久契约](../research/09-storage-extension-route.md#storage-port-v1)。

## Comments

- 2026-11-05：建图时建立；前置票闭合后领取，本轮尚未执行。

- 2026-11-05：D18二次修正已独立通过并收录，前置全部满足，领取路线研究；来源/实验/目标差异分列，不重新询问既定目标和测试入口。

## Answer

采用单asyncio业务循环、每会话DB串行线程、独立Shell runner及受监督原生IPC helper；保持来源业务所有权和模块调用链。工具批次all-settled/写屏障、流代次、三epoch、意图/副作用/结果/消息/ack顺序、取消确认与各类任务恢复已明确。持久字段仅引用D09唯一StoragePort，不另造schema。

805快照及39处源码范围核对；没有新大型probe/产品/模型验证。现有规格内工程细节已决定，无新用户取舍。实际编码和真实产品恢复/取消/安装仍由各实现票完成。
