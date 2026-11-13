# 84 — Python安装产物跑本轮Windows集成门禁

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: codex/b09-coordinator
Parent: [完整迁移规格](../spec.md)
Blocked by: [76 — 离线运行时/协议验证后台、恢复与扩展](76-liveruntime.md), [77 — 最终产品完成Windows Terminal真实操作验收](77-wtaccept.md), [81 — Python包手动安装升级及数据保留](81-upgrade.md), [82 — 各平台按支持矩阵运行质量/构建门禁](82-crossci.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

标准Python安装产物覆盖本轮保留功能的工具/命令/8core技能及既有来源离线/协议资产。系统定时等已缩减入口验证准确的不支持/渠道/统计范围，不把“原43工具全部原生功能可用”当作当前支持声明；source缺陷和port回归分开，修复归责任票复验。不新增组合测试框架，不要求V1成套live成绩或V2量化性能达标。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。D2下安装产物为wheel/sdist，不等待80独立程序；81仍须完成标准包手动更新和数据保护，76离线运行时/协议前置保留。

## Context pointers

本票通过 `dependency_exits.wtaccept=automatic` 消费 [77 的自动技术出口](../evidence/b09-r3-automatic/README.md)。任务图在 76、81、82 及该出口均有效后放行，已使用固定 b09-r3 安装包实际运行门禁。77 的真实 Windows Terminal 用户操作仍归人工出口。

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-483](../module-map.md#mm-483)、[MM-404](../module-map.md#mm-404)、[MM-642](../module-map.md#mm-642)。

## 共享接口与并行

接口领域：HITL/证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TEST-01](../acceptance-matrix.md#test-01) — 来源断言迁移：本票路径覆盖的子案例满足“没有漏项或无理由跳过；未执行来源行为不写passed，材料缺失先物化受控fixture”。
- [x] [TEST-02](../acceptance-matrix.md#test-02) — 离线/协议确定性：本票路径覆盖的子案例满足“优先现有高层CLI与协议，缺实模型不造测试答案；不读真实用户配置/凭据”。
- [x] [TEST-05](../acceptance-matrix.md#test-05) — 故障归因：本票路径覆盖的子案例满足“SOURCE-DEFECT/PORT-REGRESSION/INTENTIONAL-DELTA/ENV/UNVERIFIED分开；原故障不稀释迁移完成门禁”。
- [x] [TEST-06](../acceptance-matrix.md#test-06) — 验收证据：本票路径覆盖的子案例满足“证据脱敏入Git且可复跑，自动与HITL独立；技术probe不继承为产品通过”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

同一 b09-r3 的仓外非 editable QA 安装逐字节核对 309 个产品成员。实际 61 项来源用例通过，覆盖工具注册与权限、固定命令、八项 core Skills、eval 通道和 Windows 沙箱边界。复用 76、79、81、82 与 77 自动出口的同包证据，故障分类和真实模型/终端人工边界按记录保存。[安装集成回执](../../ruocun-next24h/evidence/batch-09/n84-installed/README.md)

[独立复核](../../ruocun-next24h/evidence/batch-09/n84-installed/review/README.md)

## Comments

- 2026-11-10：按九项已选缩减改本轮安装集成口径；76不再要求成套live、81不再依赖80。未选界面/凭据/图片剪贴板/评估工具/CI/文档仍在范围，所有通过结果待真实实施。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
