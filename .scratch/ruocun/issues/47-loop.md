# 47 — 会话loop按周期排队且退出清理

Type: task
Mode: AFK
Status: resolved
Assignee: /root
Branch: integration/ruocun-migration
Parent: [完整迁移规格](../spec.md)
Blocked by: [18 — 在真实WT边流式边编辑并中断/缩放](18-terminalearly.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

s/m/h与off、忙时排队/取消、关闭不再触发；与OS定时清晰区分。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-747](../module-map.md#mm-747)、[MM-422](../module-map.md#mm-422)。

## 共享接口与并行

接口领域：终端/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 普通入口可设置、关闭会话定时器。调度失败立即停止原定时器，手工继续不会重新启动它。
- [x] [CMD-loop](../acceptance-matrix.md#cmd-loop)：整数 s/m/h，忙时同一提示仅保留一条待处理输入，off 不取消当前轮，退出后不再触发。
- [x] [RUN-09](../acceptance-matrix.md#run-09)：本票只覆盖当前会话进程内的循环，重开后需显式设置。
- [x] 保存冻结来源、普通入口与队列测试的定向回执，以及旧定时器误恢复的独立红绿复跑。
- [x] `b4b484c` 与 `72a4076` 已集成。真实模型及最终体验不在本票验收范围。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

普通入口、合成调度、off 与退出定向通过。独立复核发现失败后手工恢复可误启动旧定时器，修复后原复现通过。[候选证据](../../ruocun-next24h/evidence/batch-03/n47/README.md) [独立复核](../../ruocun-next24h/evidence/review/b03-loop-review.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
