# 17 — 恢复查询及显式决定解开未知工具/执行

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [16 — 后台事件持久投递并以TaskWait唤醒](16-wait.md), [10 — 编辑文件并在崩溃后识别未知副作用](10-editjournal.md), [40 — 后台代理可查询、停止并从checkpoint继续](40-agentbg.md), [39 — 自定义代理定义约束真实派发](39-agentdefs.md), [41 — fork/exactTools及可准确恢复的现场边界](41-fork.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

resolve/decide/continue持久化；不同故障点重复恢复不重投、不重启未知副作用，清理受管残留。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-598](../module-map.md#mm-598)、[MM-602](../module-map.md#mm-602)、[MM-668](../module-map.md#mm-668)、[MM-327](../module-map.md#mm-327)、[MM-329](../module-map.md#mm-329)、[MM-351](../module-map.md#mm-351)、[MM-352](../module-map.md#mm-352)。

## 共享接口与并行

接口领域：存储/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [REC-08](../acceptance-matrix.md#rec-08) — 恢复决定：本票路径覆盖的子案例满足“决定与消息持久化、同ID不能重复执行；用户显式承担未知处理，无自动猜测”。
- [x] [CMD-recovery](../acceptance-matrix.md#cmd-recovery) — /recovery：本票路径覆盖的子案例满足“未决查询/resolve/decide/continue，决定持久化；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

普通CLI实际终止后从同一SQLite重开。用户显式核实旧父调用后，普通同步与后台代理均可按原转录、权限、目录和工具策略启动新run。动态只读计划与已激活工具按保存的定义严格复核。旧操作和重复决定均未再次派发。自动通过。[实现](../../ruocun-next24h/evidence/n17-recovery/README.md) · [独审](../../ruocun-next24h/evidence/review/b02-sync-recovery-review.md)

候选已实现恢复查询、原消息/结果配对修复、resolve/decide及持久一次性continue授权端口。实际SQLite、原生runner丢失与坏材料路径及静态回执见[17证据](../../ruocun-next24h/evidence/n17-recovery/README.md)。普通入口由主协调组合，高风险独审待验；保持claimed。

普通后台代理的continue已接入主线fbbcaca。用真实CLI退出、原SQLite重开和回环模型确认旧工具结果保留、新run执行一次、重复决定不启动新请求。41的特殊现场恢复边界及整票独审仍待完成。用户显式接受坏附件或人工核实的状态继续保留来源与原始事实。[普通入口回执](../../ruocun-next24h/evidence/n40-agent-background/README.md)

## Comments

- 暂停收口：查询/resolve/decide与普通CLI已独审，完整continue所需39/40/41尚未实施，整票按真实硬依赖blocked。既有候选与全部回执保留；不再启动新代理或重放未知操作。

- 2026-11-11：实施核对确认完整continue需消费40/39/41，已补真实整票依赖。当前批内只实施不依赖这些模块的查询、resolve、decide及恢复事务；产品未绑定真实代理dispatcher时明确拒绝continue，该拒绝不是全功能通过。完整出口待对应实现后接续，不能向下游虚报resolved。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
