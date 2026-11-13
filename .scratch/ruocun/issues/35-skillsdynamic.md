# 35 — 文件访问动态激活/禁用条件技能

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [34 — 加载技能及8个core技能并按需调用](34-skillsbase.md), [19 — 模型浏览与搜索项目文件](19-searchfiles.md), [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

paths扫描、嵌套发现/realpath去重、禁用/排序和边界注入生效，原隔离疑点不当正确预期。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-610](../module-map.md#mm-610)、[MM-619](../module-map.md#mm-619)、[MM-614](../module-map.md#mm-614)。

## 共享接口与并行

接口领域：工具/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-02](../acceptance-matrix.md#ext-02) — Skills 动态激活/禁用：本票路径覆盖的子案例满足“保留缓存/边界注入与顺序；no-skills/eval动态泄漏按缺陷登记不当正确预期”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票已独审集成。ab43261/0d3313f覆盖启动paths、嵌套真实目录发现、禁用、用量和审计；模块定向36项及受影响复验，双P2已关闭。真实普通入口f4dbdca/09e39f1保留固定前缀、在完整工具结果后发布，手动及模型实际调用，普通配置根下私有子目录首次保存用量/trace。入口独审c53ef18通过。no-skills动态隔离已核，完整eval、36安装与真实Terminal不代填。

[模块证据](../../ruocun-next20h/evidence/n3-skills-discovery/README.md) · [普通入口与修复](../../ruocun-next20h/evidence/n3-shared/README.md) · [入口独审](../../ruocun-next20h/evidence/review/n3-skills-entry-review.md)。本票源码出口通过；固定安装包由本轮统一构建，不冒称已发布。

## Comments

- 2026-11-11：N1固定r1完整出口通过，原票全部硬前置resolved。按ADR-0013领取并与独立任务并行。线二独占动态Skills的discover/usage/audit及本票来源测试；共享入口、ToolContext、Read与会话边界归root，Edit/Write由10持有。先交共享接缝与候选，不改36安装。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
