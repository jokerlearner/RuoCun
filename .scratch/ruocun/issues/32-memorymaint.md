# 32 — 蒸馏合并清理记忆并保留来源和锁定项

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [31 — 恢复/新轮按项目加载并注入记忆](31-memoryinject.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

真实工具轨迹→固定模型fixture蒸馏→合并/衰减；失败不丢原文、locked与source保护有效。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-500](../module-map.md#mm-500)、[MM-502](../module-map.md#mm-502)、[MM-506](../module-map.md#mm-506)、[MM-512](../module-map.md#mm-512)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-02](../acceptance-matrix.md#mem-02) — 注入与整理：本票路径覆盖的子案例满足“预算/稳定前缀、源引用和locked保护；模型失败不丢原数据”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

源码技术出口通过。32沿原生三域清理、实际保存工具轨迹→固定响应蒸馏→原生保存/新进程读入，以及实际门控合并验证；门控整理不阻塞前台，前缀不变。49c95ca和独立同探针确认已替换但同步未知时，原始字节在同目录.bak保留，其它旧项不动、无成功marker或审计。594c083普通入口及独审通过。实际应用报告受影响域停止，可人工对照当前Markdown和恢复副本；没有重放未确认操作。只读兼容未写，42反思未前移。真实模型和终端体验未验，固定包结果见N5。

[模块](../../ruocun-next20h/evidence/n4-memory-maint/README.md) · [GC与恢复办法](../../ruocun-next20h/evidence/n4-memory-gc/README.md) · [实际入口](../../ruocun-next20h/evidence/n4-shared/README.md#32普通入口) · [独审](../../ruocun-next20h/evidence/review/4-memory-maintenance-review.md)。

## Comments

- 2026-11-11：31已独审集成。线一独占原生存储维护端口、gc及对应断言；线二独占distill/consolidate/memory_audit及来源断言。root负责普通启动时序、实际保存轨迹和最小入口验收。源普通轮不直接启动distill；不新增42反思、通用后台、付费验收或兼容写入。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
