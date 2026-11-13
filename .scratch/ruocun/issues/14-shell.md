# 14 — 前台Shell输出及整个受管进程树可取消

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24-B
Parent: [完整迁移规格](../spec.md)
Blocked by: [13 — Shell命令按实际方言审批后执行](13-shellpolicy.md), [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

中文/空格/引号/env/管道/.cmd和退出码正确；子孙忽略温和取消仍可有界收口。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-637](../module-map.md#mm-637)、[MM-689](../module-map.md#mm-689)、[MM-696](../module-map.md#mm-696)、[NEW-01](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [TOOL-Bash](../acceptance-matrix.md#tool-bash) — Bash：本票路径覆盖的子案例满足“前台命令、显式后台、沙箱开关、进程转后台；前台当前无超时参数；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [ ] [WIN-01](../acceptance-matrix.md#win-01) — Shell/环境探测：本票路径覆盖的子案例满足“方言显式、编码/argv不损坏，doctor与env不执行POSIX误语法，审批与执行一致”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：13独审及普通入口实际执行已通过并集成，11已完成，主协调领取14交执行线接续。

- 2026-11-11：N24-B前台输出候选完成，46项定向回归、相关mypy/Ruff通过；既有Job取消用例增加真实孙进程写入和返回后回调/文件稳定确认。见[候选证据](../../ruocun-next24h/evidence/n14-foreground/README.md)。实际cmd/.cmd/argv/环境、PS5.1 CLIXML和两路增量已确认，任意混合编码及pwsh实机状态如实保留。普通入口live回调及独审等待主协调，15未启动。

- 2026-11-11：主协调接收来源与实际产品路径候选，[独审](../../ruocun-next24h/evidence/review/foreground-review.md)已通过。本票技术完成，N24整体固定包及全量出口待后续统一验证。
