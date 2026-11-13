# 13 — Shell命令按实际方言审批后执行

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24-B
Parent: [完整迁移规格](../spec.md)
Blocked by: [09 — 按分层权限审批并完成一次文件写入](09-permissions.md), [D10 — 确定终端框架与Windows平台适配方案](../../ruocun-discovery/issues/10-terminal-windows-decision.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

Bash AST及PowerShell/cmd复杂语法裁决与真实argv一致；允许命令产生受控文件，拒绝不执行。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-529](../module-map.md#mm-529)、[MM-531](../module-map.md#mm-531)、[MM-532](../module-map.md#mm-532)、[MM-533](../module-map.md#mm-533)、[MM-535](../module-map.md#mm-535)、[MM-537](../module-map.md#mm-537)、[MM-543](../module-map.md#mm-543)、[MM-637](../module-map.md#mm-637)、[MM-685](../module-map.md#mm-685)。

## 共享接口与并行

接口领域：权限/平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [PERM-03](../acceptance-matrix.md#perm-03) — Shell 安全：本票路径覆盖的子案例满足“未知复杂语义ask，拒绝不能借换shell绕过；审批文本等于实际执行语义”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：工程入口03解耦完整发布前置后，将本票真正需要的兼容/平台决定显式列为依赖；未关闭前不得调度本票，不减少已确认验收范围。

- 2026-11-11：24权限接缝独审通过后，按24小时计划领取。实现采用实际Shell方言和ContextVar批次执行快照，公共入口由主协调绑定。

- 2026-11-11：实际Shell计划候选已完成，185项定向来源/适配回归通过，权限/平台/工具mypy及Ruff通过。见[候选证据](../../ruocun-next24h/evidence/n13-shell-plan/README.md)。Windows默认cmd，复杂语义人工、内层deny、批次ContextVar快照已确认。原Shell测试的Windows命令改为显式PS，保留原断言。公共入口、独审与固定包出口等待主协调，14未启动。

- 2026-11-11：主协调已集成本票来源模块、普通入口接线和独立复核。186项与普通TTY批准写入/拒绝零执行，执行计划与实际参数一致已实际通过，[独审记录](../../ruocun-next24h/evidence/review/shell-plan-review.md)。本票技术完成，N24整体固定包及全量出口尚待后续候选统一执行。
