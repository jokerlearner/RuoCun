# 36 — 安装外部技能后立即调用与适配

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [34 — 加载技能及8个core技能并按需调用](34-skillsbase.md), [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

本地/Git完整资源安装、正文适配缓存/失败原文fallback，源文件不改，安装失败不留半成品。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-604](../module-map.md#mm-604)、[MM-608](../module-map.md#mm-608)、[MM-612](../module-map.md#mm-612)、[MM-707](../module-map.md#mm-707)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-03](../acceptance-matrix.md#ext-03) — 技能安装/适配：本票路径覆盖的子案例满足“完整目录安装、原文不修改、适配缓存/失败fallback可观察；真实生成不作逐字golden”。
- [x] [TOOL-SkillInstall](../acceptance-matrix.md#tool-skillinstall) — SkillInstall：本票路径覆盖的子案例满足“Git/本地技能安装；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票源码出口已通过。13a3807/022aa3a安装、完整复制、回滚、缓存/原文回退及三处Windows路径边界均独审。bf7f10e普通入口核实际source/scope审批、源资源保留、配对确认后同会话刷新与合成适配/缓存；原CLI/TTY和独立TTY通过。真实Git远端及模型未运行，标准包在本轮统一验收。

[来源证据](../../ruocun-next20h/evidence/n3-skill-install/README.md) · [普通入口](../../ruocun-next20h/evidence/n3-install-shared/README.md) · [独审](../../ruocun-next20h/evidence/review/3-skill-install-module-review.md)。

## Comments

- 2026-11-11：34/09已resolved，35模块已交独审，由root继续共享入口；线二按35∥36的已批准并行关系领取本票。独占安装/适配模块、SkillInstall工具与本票测试；root独占argv进程口、ToolContext/Registry、主入口与已确认后的刷新。当前只做工具入口与适配，不扩大到另一个安装命令。

- 2026-11-11：N1完整出口通过，原硬前置已满足；按连续计划顺序和空闲实现槽排队，未领取、未启动产品实现。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
