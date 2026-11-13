# 12 — 混合工具批次保持并发上限与写屏障

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_skills
Branch: codex/advanced-skills
Worktree: .worktrees/advanced-skills
Parent: [完整迁移规格](../spec.md)
Blocked by: [10 — 编辑文件并在崩溃后识别未知副作用](10-editjournal.md), [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

读类最多8并行、写/exec屏障、结果原序和allSettled；source失败标记疑点独立oracle。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-642](../module-map.md#mm-642)、[MM-693](../module-map.md#mm-693)。

## 共享接口与并行

接口领域：工具/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [RUN-05](../acceptance-matrix.md#run-05) — 工具批并发/屏障：本票路径覆盖的子案例满足“最多8并行，write/exec 串行屏障、原序收结果；allSettled收齐后传播失败；plan标签不当纯函数”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票源码自动出口通过。1daa/77dc安全并发、原序、写/exec屏障、Bash级联、allSettled、Read图与最终参数一次预批；5个既有REC-05恢复复验，S-05冻结文本oracle；d184关闭旧审批异常掩盖真实存储失败。普通入口aed4实际wire、混合CLI及受控TTY通过，独审393fc与2a9bd68已收。当前组为原生read/plan，后续network/Hook不代填，固定包留统一验收。

[批执行来源](../../ruocun-next20h/evidence/n2-batch/README.md) · [普通入口](../../ruocun-next20h/evidence/n2-shared/README.md) · [独审](../../ruocun-next20h/evidence/review/2-batch-executor-review.md)。

## Comments

- 2026-11-11：10实际前台恢复与11已独审集成，全部硬前置满足。线一唯一写工具执行器、agent/loop.py、permissions/runtime.py及本票相关原测试；root保有agent/runtime.py、ToolContext、InputBroker及公共契约，普通入口只在接缝审定后消费。原序、最多8安全并发、写/exec独占、一次预批与可信恢复均须实际通过。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
