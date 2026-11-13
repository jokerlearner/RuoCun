# 80 — Windows独立产物（本轮移出）

Type: task
Mode: AFK
Status: blocked
Scope: excluded
Scope reason: ADR-0010 / D2；本轮仅交付需兼容Python环境的wheel/sdist，不交付独立程序，非通过。
Assignee: none
Parent: [完整迁移规格](../spec.md)
Blocked by: [79 — 构建并在隔离环境安装完整wheel/sdist](79-wheel.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

本轮D2取消Windows独立程序产物与其专属打包生命周期验收，只交付可安装wheel/sdist，使用者须先准备受支持的Python环境。保留原来源、研究实验及历史编号，不承诺无需Python运行；标准包中的runner/helper同版本角色、后台控制、取消与恢复继续归79/81/84实际验证，不随独立产物取消。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。Status保留blocked，Scope excluded不是已完成；81改以79标准包为前置。本轮仍停止，工具Scope适配前不能直接按旧frontier派发。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-483](../module-map.md#mm-483)、[MM-668](../module-map.md#mm-668)、[MM-704](../module-map.md#mm-704)、[MM-801](../module-map.md#mm-801)。

## 共享接口与并行

接口领域：工程/平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## 历史验收条件（本轮不适用，未通过）

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [PKG-02](../acceptance-matrix.md#pkg-02) — Windows独立程序：本票路径覆盖的子案例满足“console输入/退出正常，资源/SQLite/外部扩展可用；自spawn内部角色不递归主UI；最终产物形态依路线决定”。
- [ ] [PKG-03](../acceptance-matrix.md#pkg-03) — runner打包生命周期：本票路径覆盖的子案例满足“恢复/取消/能力与receipt不依赖已消失资源；sys.executable不被误当通用解释器”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

原独立产物未实现/未验收，按D2移出本轮；D07等研究原型不替代最终产物通过，历史复选框保持未勾选。

## Comments

- 2026-11-10：用户按表缩减D2，本轮无Windows独立程序；原独立产物研究与资产保留，标准Python包安装及后台角色运行仍须实际交付。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
