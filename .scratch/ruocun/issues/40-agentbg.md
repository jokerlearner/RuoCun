# 40 — 后台代理可查询、停止并从checkpoint继续

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [38 — 调用内置子代理并收集同步结果](38-agentsync.md), [16 — 后台事件持久投递并以TaskWait唤醒](16-wait.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

后台进度/attention/终态→事件投递；停止先canceling，重启显式继续不重放工具。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-417](../module-map.md#mm-417)、[MM-424](../module-map.md#mm-424)、[MM-719](../module-map.md#mm-719)、[MM-723](../module-map.md#mm-723)。

## 共享接口与并行

接口领域：调度/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [RUN-09](../acceptance-matrix.md#run-09) — 异构任务恢复：本票路径覆盖的子案例满足“Shell重连；代理显式checkpoint继续；Monitor不冒充代理；manual不启动执行；loop不是OS定时”。
- [x] [TOOL-TaskStop](../acceptance-matrix.md#tool-taskstop) — TaskStop：本票路径覆盖的子案例满足“代理 abort→canceling→执行器确认 canceled，手工任务直接取消；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-TaskOutput](../acceptance-matrix.md#tool-taskoutput) — TaskOutput：本票路径覆盖的子案例满足“代理转录增量，WeakMap 游标；手工任务无转录；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

fc77aac接入持久任务，fbbcaca接入普通入口，797ee0b通过同一后台执行器的分类、交接和取消独审。实际CLI强制退出后继续用新run保留原配对，重复决定不触发请求。真实SQLite覆盖父回执后的子工具、取消与未知回执、单次继续。本票自动通过。定向回归17项通过，无真实模型请求。[实现](../../ruocun-next24h/evidence/n40-agent-background/README.md) · [独审](../../ruocun-next24h/evidence/review/b02-agent-background-review.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
