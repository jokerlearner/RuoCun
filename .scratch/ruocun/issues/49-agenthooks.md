# 49 — 代理启动/停止及会话Hooks不重复注入

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [48 — Hook拦截/改写一次工具调用并参与journal](48-hooks.md), [39 — 自定义代理定义约束真实派发](39-agentdefs.md), [40 — 后台代理可查询、停止并从checkpoint继续](40-agentbg.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

子代理独立hook注册表/上下文、SessionStart恢复哨兵、SessionEnd正常路径与失败边界可验证。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-370](../module-map.md#mm-370)、[MM-372](../module-map.md#mm-372)、[MM-420](../module-map.md#mm-420)。

## 共享接口与并行

接口领域：调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-07](../acceptance-matrix.md#ext-07) — Hook 生命周期：本票路径覆盖的子案例满足“只保证实际有调用点的事件；PostToolUse不回滚副作用；子代理hook独立注册表”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

受控 SQLite 验证子代理 Start 先于模型、仅子代理注入，Stop 在确认取消时使用独立信号，取消抢在启动前时零 Start 和零模型请求。普通会话恢复替换哨兵，拒绝提交零模型请求，正常退出触发 SessionEnd。独审注入丢回执，确认原排队输入或旧前缀保持、重开零副作用重放。[子生命周期](../../ruocun-next24h/evidence/n49-agent-lifecycle/README.md) · [普通入口](../../ruocun-next24h/evidence/batch-04/ordinary/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
