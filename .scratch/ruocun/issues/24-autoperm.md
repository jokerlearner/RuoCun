# 24 — 自动权限分类失败时保守询问并留审计

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24
Parent: [完整迁移规格](../spec.md)
Blocked by: [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

分类器/熔断/秘密脱敏、自动批准开关和信任实际边界可验证，不默扩权限。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-528](../module-map.md#mm-528)、[MM-539](../module-map.md#mm-539)、[MM-541](../module-map.md#mm-541)、[MM-552](../module-map.md#mm-552)、[MM-556](../module-map.md#mm-556)、[MM-558](../module-map.md#mm-558)。

## 共享接口与并行

接口领域：权限。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [PERM-04](../acceptance-matrix.md#perm-04) — 审批持久化/分类器：本票路径覆盖的子案例满足“自动批准仅显式配置；无交互不挂死/不默许；拒绝原因、审计和保存规则一致”。
- [ ] [PERM-05](../acceptance-matrix.md#perm-05) — 秘密与信任边界：本票路径覆盖的子案例满足“按实际边界脱敏与裁决；来源信任缺口/扩大gate的建议单列差异待决，不谎报隔离”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11 09:50 +08:00：按下一轮24小时计划领取，前置已核对。独立 worktree 实施，完成状态等待实际证据及独审。

- 2026-11-11：N24-B 分类器/模型回退/审计候选完成，独立 worktree 为 `.worktrees/n24-permissions`，分支 `codex/n24-permissions`，基线 `1271687`。来源定向117通过、权限mypy和Ruff通过。见[候选证据](../../ruocun-next24h/evidence/n24-permissions/README.md)。生产装配由主协调维护，当前未因模块候选将整票标为resolved；Windows未知方言Shell仍人工确认，等待13。

- 2026-11-11：主协调已集成本票来源模块、普通入口接线和独立复核。118项与普通TTY分类放行/回退拒绝/脱敏审计已实际通过，[独审记录](../../ruocun-next24h/evidence/review/permissions-review.md)。本票技术完成，N24整体固定包及全量出口尚待后续候选统一执行。
