# 41 — fork/exactTools及可准确恢复的现场边界

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: /root
Parent: [完整迁移规格](../spec.md)
Blocked by: [40 — 后台代理可查询、停止并从checkpoint继续](40-agentbg.md), [39 — 自定义代理定义约束真实派发](39-agentdefs.md), [27 — 在worktree修改文件并用检查点回退](27-gitpaths.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

保留当前运行的fork/exactTools、普通代理checkpoint恢复、worktree/remote实际语义及嵌套路径/权限边界。R3取消补足特殊fork现场材料的完整恢复保证：重启后若缺少原工具集、提示或其它必要现场，明确拒绝继续，允许查看已有转录后由用户新建任务，不悄悄按普通agent运行。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。40的普通恢复及42/44实际消费的能力继续保留；本次不改变blocked或执行产品。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-401](../module-map.md#mm-401)、[MM-417](../module-map.md#mm-417)、[MM-420](../module-map.md#mm-420)、[MM-380](../module-map.md#mm-380)。

## 共享接口与并行

接口领域：调度/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [RUN-07](../acceptance-matrix.md#run-07) — 子代理与 fork：本票路径覆盖的子案例满足“保留实际工具裁剪差异并测试；父子消息/预算/权限/目录不串；不宣称 prompt 等于硬墙”。
- [x] [RUN-08](../acceptance-matrix.md#run-08) — worktree 隔离：本票路径覆盖的子案例满足“Git边界/路径/权限正确；remote 原为worktree不能宣称真远程；未提交用户改动不被清理”。
- [x] [RUN-09](../acceptance-matrix.md#run-09) — 异构任务恢复：普通代理在材料完整时显式checkpoint继续；特殊fork/exactTools现场不足时拒绝继续，不扩大工具或更换角色；Shell/Monitor/manual/loop保持各自类型语义。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

主线f8a4d33、7baf62f和d4046bd。普通入口验证fork沿真实父模型与工具，后台fork可以执行子Read，强杀重开后缺材料的继续不产生模型请求。真实Git验证remote落同机工作树，只有干净自有工作树清理，有改动或独有提交保留。已知创建失败拒绝派发。创建调用实际发生但回执不明时，独审确认保持原目录、工作树和未决Agent记录，子请求数为零。合成服务验证通过。[fork](../../ruocun-next24h/evidence/n41-fork-core/README.md) · [工作树](../../ruocun-next24h/evidence/n41-worktree/README.md) · [独审](../../ruocun-next24h/evidence/review/b02-fork-isolation-review.md)

## Comments

- 2026-11-11：用户确认隔离创建失败就拒绝派发，见[ADR-0017](../../../docs/adr/0017-agent-isolation-failure.md)。前置27、39、40已通过，41接续实现，未结票。

- 2026-11-10：用户按表缩减R3；只取消特殊现场完整恢复增强，未取消来源已有fork、工具裁剪、普通代理恢复或工作区隔离。尚未实现/验收，不因范围缩减结题。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
