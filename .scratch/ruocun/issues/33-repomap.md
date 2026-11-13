# 33 — 模型按预算读取和刷新代码图

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/b06-code
Parent: [完整迁移规格](../spec.md)
Blocked by: [19 — 模型浏览与搜索项目文件](19-searchfiles.md), [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

多语言符号/排名/裁剪、2048预算、4000文件/512KiB与mtime-size缓存可验证。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-570](../module-map.md#mm-570)、[MM-572](../module-map.md#mm-572)、[MM-574](../module-map.md#mm-574)、[MM-575](../module-map.md#mm-575)、[MM-576](../module-map.md#mm-576)、[MM-578](../module-map.md#mm-578)、[MM-579](../module-map.md#mm-579)、[MM-695](../module-map.md#mm-695)、[MM-580](../module-map.md#mm-580)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-04](../acceptance-matrix.md#mem-04) — 代码地图：本票路径覆盖的子案例满足“默认2048 token预算、符号/排名/裁剪与mtime+size缓存语义；失败不污染主历史”。
- [x] [TOOL-RepoMap](../acceptance-matrix.md#tool-repomap) — RepoMap：本票路径覆盖的子案例满足“获取/刷新代码地图；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[普通入口独审](../../ruocun-next24h/evidence/review/b06-repomap-review.md)已通过，来源回执按固定候选复用；主协调已验收，范围与未验边界见报告。批末全量、隔离安装和包指纹另记。

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：用户授权执行[批次06](../../ruocun-next24h/batch-06.md)，已核前置，领取本票；尚无通过结论。
