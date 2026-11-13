# 61 — 网络隔离开关保持来源语义与平台限制

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b08-platform
Parent: [完整迁移规格](../spec.md)
Blocked by: [60 — 受隔离命令能写允许根且不能越界写](60-sandboxfile.md), [22 — 模型按权限抓取URL并抽取内容](22-webfetch.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按DAO默认允许网络、SANDBOX_NO_NET=1才加禁网配置的语义迁移；未启用沙箱时no-net不单独产生隔离，Windows显式启用仍拒绝不支持。支持平台路由/真实验证和未实机项分列，见ADR-0008。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-698](../module-map.md#mm-698)、[NEW-08](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-09](../acceptance-matrix.md#win-09) — OS文件/网络隔离：本票路径覆盖的子案例满足“按ADR-0008沿用DAO平台能力；Windows启用时明确不支持，普通Shell不冒充隔离；支持平台与实机状态单列”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[批末集中验收](../../ruocun-next24h/evidence/batch-08/integration/README.md)通过。
[本机来源回执](../../ruocun-next24h/evidence/batch-08/n61/README.md)。Windows 显式启用按已有平台拒绝路径执行。Ubuntu WSL 的三种状态实际验证：默认沙箱可访问回环，显式禁网时连接拒绝，只设置禁网开关而未启用沙箱时仍可访问。三种都可写工作区。macOS 配置参数已核对，实际隔离待实机。候选 `efa772c6` 已独立复跑并集成。

## Comments

- 2026-11-10：[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)按DAO实际开关和平台能力迁移，不增加Windows禁网后端；有效/缺工具/未启用/Windows不支持各路径须真实验证，已有60/22前置保持，本票未实现/未验。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
