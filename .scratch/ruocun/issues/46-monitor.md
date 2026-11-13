# 46 — Monitor输出事件可观察并可靠停止

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [45 — 创建/查询/更新/停止手工任务记录](45-manual.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按行批量通知、超时/persistent/停止和重启真实执行器边界有证据，不伪装agent恢复。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-676](../module-map.md#mm-676)、[MM-424](../module-map.md#mm-424)。

## 共享接口与并行

接口领域：调度/平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-Monitor](../acceptance-matrix.md#tool-monitor) — Monitor：本票路径覆盖的子案例满足“后台监控命令，stdout 按行批量通知，persistent/超时与 TaskStop；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [RUN-09](../acceptance-matrix.md#run-09) — 异构任务恢复：本票路径覆盖的子案例满足“Shell重连；代理显式checkpoint继续；Monitor不冒充代理；manual不启动执行；loop不是OS定时”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

来源测试与普通CLI独审通过，覆盖实际按行推送、persistent/超时、TaskStop真实进程停止与owner丢失重开保留interrupted而不重启。Windows审批保留Monitor身份并绑定实际ShellExecutionPlan，来源粗粒度检查的差异已记录。[实现](../../ruocun-next24h/evidence/batch-05/n46/README.md) · [独审](../../ruocun-next24h/evidence/review/b05-monitor-review.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
