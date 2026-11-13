# 57 — 查看脱敏审计与可选观测轨迹

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/b07-reflect
Parent: [完整迁移规格](../spec.md)
Blocked by: [28 — 多模型用量/费用/预算跨重启连续](28-cost.md), [12 — 混合工具批次保持并发上限与写屏障](12-batch.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

trace/turn/tool/cache/skill/perms关联正确，开关和flush可验证；关闭/后端失败不改业务结果。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-498](../module-map.md#mm-498)、[MM-520](../module-map.md#mm-520)、[MM-522](../module-map.md#mm-522)、[MM-523](../module-map.md#mm-523)、[MM-525](../module-map.md#mm-525)、[MM-527](../module-map.md#mm-527)、[MM-584](../module-map.md#mm-584)、[MM-731](../module-map.md#mm-731)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-05](../acceptance-matrix.md#mem-05) — 审计与可选观测：本票路径覆盖的子案例满足“旁路失败不伪造业务失败；隐私脱敏；关闭观测时业务等效；缓存归因不冒充真实命中率”。
- [x] [CMD-audit](../acceptance-matrix.md#cmd-audit) — /audit：本票路径覆盖的子案例满足“记忆/反思/工具/权限/缓存/技能审计查询；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[本票独审](../../ruocun-next24h/evidence/review/b07-observation-final-review.md)与[集中交付](../../ruocun-next24h/evidence/batch-07/integration/README.md)已通过。

已通过本票技术出口和独审：[n57来源与真实HTTP出口](../../ruocun-next24h/evidence/batch-07/n57/README.md)、[最终独审](../../ruocun-next24h/evidence/review/b07-observation-final-review.md)。仅本地合成模型/collector，默认关闭、共享及实际Agent关联/失败/脱敏/关闭均留证；不代表远程Laminar入库或最终体验。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-12：用户授权启动[批次07](../../ruocun-next24h/batch-07.md)，已核真实前置，本票claimed，尚无通过结论。
