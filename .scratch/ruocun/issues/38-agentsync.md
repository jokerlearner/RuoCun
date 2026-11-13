# 38 — 调用内置子代理并收集同步结果

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [34 — 加载技能及8个core技能并按需调用](34-skillsbase.md), [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

独立子Session→允许工具→父结果/摘要，主/子模型与轮数隔离，失败不污染父历史。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-388](../module-map.md#mm-388)、[MM-420](../module-map.md#mm-420)、[MM-621](../module-map.md#mm-621)、[MM-378](../module-map.md#mm-378)、[MM-372](../module-map.md#mm-372)。

## 共享接口与并行

接口领域：调度/工具。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-Agent](../acceptance-matrix.md#tool-agent) — Agent：本票路径覆盖的子案例满足“单/多任务、同步/后台、fork/worktree/model/plan；继续代理由 TaskSend/recovery 路径处理；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [RUN-07](../acceptance-matrix.md#run-07) — 子代理与 fork：本票路径覆盖的子案例满足“保留实际工具裁剪差异并测试；父子消息/预算/权限/目录不串；不宣称 prompt 等于硬墙”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

普通 CLI 已通过真实本地请求链。父会话发起派发，子会话使用独立模型、提示、工具和轮数，父会话收到工具结果。合成执行覆盖单任务、批量顺序、权限裁剪、取消、失败和真实写入。独立复验确认子工具写入后回执丢失会暂停，重开依据 SQLite 原记录判定，旧写入只发生一次。39/40可使用已验证的前置。后台、fork和特殊恢复各由后继验收。[定向证据](../../ruocun-next24h/evidence/n38-agent-sync/README.md) · [独立审查](../../ruocun-next24h/evidence/review/b02-agent-sync-review.md)

## Comments

- 用户恢复未完的17号路径。核对34和09已resolved，领取38，复用执行负责人及其工作树。38是39和40的实际前置，主协调负责普通入口接线。各后继按硬依赖验收。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
