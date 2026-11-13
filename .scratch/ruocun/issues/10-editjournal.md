# 10 — 编辑文件并在崩溃后识别未知副作用

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_skills
Branch: codex/advanced-skills
Worktree: .worktrees/advanced-skills
Parent: [完整迁移规格](../spec.md)
Blocked by: [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

读后Edit/Write、并发改动检测/锁/原子替换；意图前后/结果前后kill，三次恢复不盲重放。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-631](../module-map.md#mm-631)、[MM-633](../module-map.md#mm-633)、[MM-653](../module-map.md#mm-653)、[MM-657](../module-map.md#mm-657)、[MM-602](../module-map.md#mm-602)、[MM-629](../module-map.md#mm-629)。

## 共享接口与并行

接口领域：存储/工具。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-Edit](../acceptance-matrix.md#tool-edit) — Edit：本票路径覆盖的子案例满足“old/new string，唯一匹配或 replace_all，锁与 diff；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [REC-05](../acceptance-matrix.md#rec-05) — 工具journal故障切点：本票路径覆盖的子案例满足“已知结果复用；无意图可证未执行；started→outcome_unknown；禁止盲重放含prehook”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票前台真实Edit/Write及恢复出口通过。固定来源切片2fcdbf1：49项来源和既有适配、Ruff、mypy2，独审14项。固定恢复8ccc683：实际五切点、15次独立重开，原字节/派发/原子替换计数已核；未知停止，已知复用，无意图可证未执行。独审0b54fa9再复代表未知/已知两切点及6次重开。

[来源证据](../../ruocun-next20h/evidence/n2-editjournal/source.md) · [恢复证据](../../ruocun-next20h/evidence/n2-editjournal/recovery.md) · [恢复独审](../../ruocun-next20h/evidence/review/n2-edit-recovery-review.md)。本票完整路径已独审集成，12可消费；Hook路径与全部母族未据此前移。此处源码验收不冒称新版固定包已构建，人工仍独立。

## Comments

- 2026-11-11：N1固定r1完整出口通过，原票全部硬前置resolved。按ADR-0013领取并与独立任务并行。线一独占Edit/Write、diff/mismatch和本票测试/证据；共享paths、Conversation、loop仍归root。复用现有子进程与存储接缝，走实际Edit/Write恢复，不加产品故障开关。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
