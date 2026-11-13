# 45 — 创建/查询/更新/停止手工任务记录

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [40 — 后台代理可查询、停止并从checkpoint继续](40-agentbg.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

手工状态与agent/Shell执行区分，无转录不伪造；列表/更新/取消跨保存一致。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-713](../module-map.md#mm-713)、[MM-715](../module-map.md#mm-715)、[MM-717](../module-map.md#mm-717)、[MM-725](../module-map.md#mm-725)、[MM-424](../module-map.md#mm-424)。

## 共享接口与并行

接口领域：调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-TaskCreate](../acceptance-matrix.md#tool-taskcreate) — TaskCreate：本票路径覆盖的子案例满足“只建手工任务记录，不启动进程；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-TaskList](../acceptance-matrix.md#tool-tasklist) — TaskList：本票路径覆盖的子案例满足“taskManager 当前/含已结束清单；不是 Shell 统一清单；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-TaskGet](../acceptance-matrix.md#tool-taskget) — TaskGet：本票路径覆盖的子案例满足“taskManager 单任务详情；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-TaskUpdate](../acceptance-matrix.md#tool-taskupdate) — TaskUpdate：本票路径覆盖的子案例满足“手工任务描述/状态/结果；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-tasks](../acceptance-matrix.md#cmd-tasks) — /tasks：本票路径覆盖的子案例满足“TaskManager 当前运行项；不假装包含全部 Shell；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

合成真实 SQLite 验证四个手工任务工具、正常退出、旧记录重开及编号连续。普通入口已注册四工具并接入只读 `/tasks`。独立复核已通过，真实模型和最终体验单列。[候选证据](../../ruocun-next24h/evidence/batch-03/n45/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
