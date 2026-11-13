# 16 — 后台事件持久投递并以TaskWait唤醒

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [15 — Shell转后台后可重连、读输出和停止](15-runner.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

any/all和1–32限制、run身份固定；run/event与消息/delivered原子，溢写附件缺失变未决。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-381](../module-map.md#mm-381)、[MM-383](../module-map.md#mm-383)、[MM-385](../module-map.md#mm-385)、[MM-726](../module-map.md#mm-726)、[MM-709](../module-map.md#mm-709)、[MM-384](../module-map.md#mm-384)。

## 共享接口与并行

接口领域：调度/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-TaskWait](../acceptance-matrix.md#tool-taskwait) — TaskWait：本票路径覆盖的子案例满足“对当前会话后台代理或 Shell 的 any/all 事件等待；单独调用，不等待手工/前台任务；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [RUN-03](../acceptance-matrix.md#run-03) — TaskWait：本票路径覆盖的子案例满足“固定 task+run，去重与上限；错误/取消/attention唤醒；存失败 rollback consumed”。
- [x] [RUN-11](../acceptance-matrix.md#run-11) — 事件投递与通知：本票路径覆盖的子案例满足“先run+event落盘；消息+delivered同事务后ack；进展与用户指令分离，无重复投递”。
- [x] [RUN-12](../acceptance-matrix.md#run-12) — 前台/退出/keepAlive：本票路径覆盖的子案例满足“scheduler基于事件等待而非不断模型poll；仅明确保留的runner跨owner存在；后续可接管/取消”。
- [x] [REC-06](../acceptance-matrix.md#rec-06) — checkpoint/事件故障切点：本票路径覆盖的子案例满足“消息/事件一致、不重投不丢已确认checkpoint；保存失败rollback wait consumed”。
- [x] [REC-11](../acceptance-matrix.md#rec-11) — 大结果附件：本票路径覆盖的子案例满足“先文件持久再登记hash；显示溢写路径；恢复异常形成未决，不伪装完整”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

P1事务段e495efc和P2等待/观察候选已形成；最终55项定向、11源mypy/Ruff通过，见[16分段证据](../../ruocun-next24h/evidence/n16-background/README.md)。本票保持claimed，等待root普通入口组合及高风险独审；未宣告17/63完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 批次02验收：310057b最终unknown回执守卫经独审原真实runner-loss一例通过，之前普通CLI三请求闭环有效，整16剩余阻断0。登记前回执竞态、未绑定覆盖waiting快照与精确eventId/seq消息ack修复均保留红绿；17/63前置解锁。固定包及全量在批次里程碑集中。
