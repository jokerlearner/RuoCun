# 83 — 交付可重建产物、使用恢复文档和许可清单

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b09-coordinator
Parent: [完整迁移规格](../spec.md)
Blocked by: [81 — Python包手动安装升级及数据保留](81-upgrade.md), [82 — 各平台按支持矩阵运行质量/构建门禁](82-crossci.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

版本/commit/lock/hash、Python包安装/扩展/恢复/权限文档、第三方/帧来源及发布说明齐全，资源缺口不伪称再生。D5未选，完整文档配套仍保留，但支持清单按[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)准确说明：需兼容Python，无独立exe，手动停进程/备份/更新；Windows无系统定时/防休眠/桌面通知；历史费用与特殊fork恢复边界明确；无成套真实模型成绩或量化性能达标保证。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-017](../module-map.md#mm-017)、[MM-018](../module-map.md#mm-018)、[MM-019](../module-map.md#mm-019)、[MM-013](../module-map.md#mm-013)、[MM-801](../module-map.md#mm-801)、[MM-768](../module-map.md#mm-768)。

## 共享接口与并行

接口领域：工程/证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [PKG-05](../acceptance-matrix.md#pkg-05) — 资源与许可：本票路径覆盖的子案例满足“全部随包可读、hash/provenance与许可齐全；缺外部PNG生成源如实登记，不把注释当授权”。
- [x] [PKG-06](../acceptance-matrix.md#pkg-06) — CI和发布配套：本票路径覆盖的子案例满足“测试、文档、恢复/兼容差异/支持矩阵/构建指令配套；交叉编译不作实机验收；不在本轮公开发布”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[中文使用入口](../../../README.zh-CN.md)、[安装更新和恢复](../../../docs/install-and-recovery.md)及[固定候选发布、构建和许可](../../../docs/release/batch-09.md)已交付。31 个本地链接、两份包、三份锁和 44 个运行 wheel 许可均已核对。外部原始帧和独立授权缺口按 E-02 留存。[核对回执](../../ruocun-next24h/evidence/batch-09/n83-docs/README.md)

[独立复核](../../ruocun-next24h/evidence/batch-09/n83-docs/review/README.md)

## Comments

- 2026-11-10：只更新已选范围的发布说明，不取消完整文档/来源/许可责任；81改为标准Python包手动更新策略，82CI保持。没有发布或产品通过被新增。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
