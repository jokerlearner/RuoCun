# 43 — 批量派发代理并双向追加消息

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/b04-agents
Parent: [完整迁移规格](../spec.md)
Blocked by: [40 — 后台代理可查询、停止并从checkpoint继续](40-agentbg.md), [39 — 自定义代理定义约束真实派发](39-agentdefs.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

最多20任务/默认10worker、排队/取消、结束后TaskSend恢复与父子attention消息不串。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-621](../module-map.md#mm-621)、[MM-674](../module-map.md#mm-674)、[MM-721](../module-map.md#mm-721)、[MM-368](../module-map.md#mm-368)。

## 共享接口与并行

接口领域：调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-TaskSend](../acceptance-matrix.md#tool-tasksend) — TaskSend：本票路径覆盖的子案例满足“向代理追加指令，已结束任务的恢复转交 ctx.resumeAgent；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-MessageParent](../acceptance-matrix.md#tool-messageparent) — MessageParent：本票路径覆盖的子案例满足“子代理发送进展或 attention 给父；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [RUN-07](../acceptance-matrix.md#run-07) — 子代理与 fork：本票路径覆盖的子案例满足“保留实际工具裁剪差异并测试；父子消息/预算/权限/目录不串；不宣称 prompt 等于硬墙”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

冻结 DAO 定向用例与原生受控 SQLite 通过，[实现回执](../../ruocun-next24h/evidence/batch-04/n43/README.md)、[普通入口](../../ruocun-next24h/evidence/batch-04/ordinary/README.md)、[独立复核](../../ruocun-next24h/evidence/review/b04-agent-messages-review.md)。独审覆盖批量派发 worker 默认并发、排队取消、双向消息、结束后续跑，以及未知写入后停止剩余派发。常规托管子代理显式暴露 MessageParent，以支持已批准的真实双向消息。父入口沿用原来的延迟可见性。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
