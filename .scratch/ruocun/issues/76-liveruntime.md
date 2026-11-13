# 76 — 离线运行时/协议验证后台、恢复与扩展

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: codex/b09-eval
Parent: [完整迁移规格](../spec.md)
Blocked by: [71 — eval及禁用开关贯穿启动/文件访问/恢复](71-isolation.md), [73 — 执行记忆/缓存验收并生成脱敏报告](73-memoryeval.md), [74 — 执行反思验收并识别正控/失败](74-reflecteval.md), [49 — 代理启动/停止及会话Hooks不重复注入](49-agenthooks.md), [46 — Monitor输出事件可观察并可靠停止](46-monitor.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按本轮保留功能复用来源既有离线/runtime/protocol资产，验证等待、取消、恢复及扩展接线；不新增全规格组合测试框架，不要求真实模型评分。V1移出的成套live成绩不再是本票前置或结题条件；71/73/74及49/46前置直接保留，避免绕过能力实现与评估工具。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。离线产品输入/结果预期须来自来源，不造模型答案；未运行的live结果保持未验，本次不改变blocked或运行产品。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-383](../module-map.md#mm-383)、[MM-417](../module-map.md#mm-417)、[MM-496](../module-map.md#mm-496)、[MM-326](../module-map.md#mm-326)、[MM-328](../module-map.md#mm-328)。

## 共享接口与并行

接口领域：HITL/证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TEST-02](../acceptance-matrix.md#test-02) — 离线/协议确定性：复用来源已有fixture/轨迹与独立预期，覆盖本轮保留的运行时接线；未跑live不写真实模型通过，不引入新增组合门槛。
- [x] [RUN-09](../acceptance-matrix.md#run-09) — 异构任务恢复：本票路径覆盖的子案例满足“Shell重连；代理显式checkpoint继续；Monitor不冒充代理；manual不启动执行；loop不是OS定时”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

复用冻结来源后台等待、恢复及协议语义，三组实际 59 项通过。[实施回执](../../ruocun-next24h/evidence/batch-09/eval/n76/README.md)记录输入、期望、清理和复跑环境。独立复跑 4 项通过，覆盖事件等待、真实 Shell 取消、SQLite 原子恢复和 SSE MCP 结果不明后不重放。[独审回执](../../ruocun-next24h/evidence/batch-09/eval/n76/review/README.md)。真实模型与人工终端验收单列。

## Comments

- 2026-11-10：V1后本票保留为离线运行时/协议接线验收，移出TEST-04成套live责任并直接继承75的有效前置；功能、来源资产及失败证据不被删除，尚未实现/验收。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
