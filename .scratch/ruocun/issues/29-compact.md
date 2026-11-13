# 29 — 上下文压缩及模型错误后继续任务

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [08 — 模型用TodoWrite和Read完成首个工具回合](08-readloop.md), [28 — 多模型用量/费用/预算跨重启连续](28-cost.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

85%主动/超限反应式压缩、空响应恢复、工具消息对与等待/目标保留；持续不可用明确停止。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-394](../module-map.md#mm-394)、[MM-404](../module-map.md#mm-404)、[MM-428](../module-map.md#mm-428)、[MM-627](../module-map.md#mm-627)。

## 共享接口与并行

接口领域：模型/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIRE-09](../acceptance-matrix.md#wire-09) — loop 错误与限流：本票路径覆盖的子案例满足“压缩上限/有界重试/账户选择/ModelUnavailableStop 保持；不自动换业务主模型”。
- [x] [MEM-03](../acceptance-matrix.md#mem-03) — 压缩与反思：本票路径覆盖的子案例满足“保留用户目标/工具对/背景等待状态；提示、触发/预算与注入边界按oracle”。
- [x] [CMD-compact](../acceptance-matrix.md#cmd-compact) — /compact：本票路径覆盖的子案例满足“主动压缩、工具消息配对及可恢复检查点；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-context](../acceptance-matrix.md#cmd-context) — /context：本票路径覆盖的子案例满足“上下文组成/预算显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

真实本地 HTTP 限流与显式账户切换、同模型有界重试、部分响应保留、已配对工具、等待中压缩和失败后重开均通过定向与独立复核。失败后原上下文、等待句柄及未投递事件保留，显式继续前不唤醒原回合。未调用真实模型。[源码与回执](../../ruocun-next24h/evidence/n29-model-recovery/README.md) [独立复核](../../ruocun-next24h/evidence/review/b03-model-recovery-review.md)禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-11：阶段A已实现成功压缩、实际API85%触发、最多两次上下文错误压缩、/compact及提交后交换；用户选摘要失败/空摘要保留原上下文停止，取消/保存未确认不继续。模块及CLI定向通过，反思/后台等原规格剩余不代填。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
