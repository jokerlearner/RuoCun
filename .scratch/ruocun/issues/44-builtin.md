# 44 — 内置命令与长任务目标驱动后续工具轮

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [18 — 在真实WT边流式边编辑并中断/缩放](18-terminalearly.md), [29 — 上下文压缩及模型错误后继续任务](29-compact.md), [41 — fork/exactTools恢复保持消息与工作区边界](41-fork.md), [43 — 批量派发代理并双向追加消息](43-scatter.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

6内置prompt与长任务开关/别名/备注产生正确请求并续轮；batch真实派发在代理任务串联验收。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-446](../module-map.md#mm-446)、[MM-566](../module-map.md#mm-566)、[MM-404](../module-map.md#mm-404)。

## 共享接口与并行

接口领域：模型/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [CMD-simplify](../acceptance-matrix.md#cmd-simplify) — /simplify：本票路径覆盖的子案例满足“内置简化 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-remember](../acceptance-matrix.md#cmd-remember) — /remember：本票路径覆盖的子案例满足“内置记忆 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-review](../acceptance-matrix.md#cmd-review) — /review：本票路径覆盖的子案例满足“内置审查 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-init](../acceptance-matrix.md#cmd-init) — /init：本票路径覆盖的子案例满足“内置项目初始化 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-batch](../acceptance-matrix.md#cmd-batch) — /batch：本票路径覆盖的子案例满足“内置并行任务/worktree prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-skillify](../acceptance-matrix.md#cmd-skillify) — /skillify：本票路径覆盖的子案例满足“内置技能提取 prompt 展开；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-goal](../acceptance-matrix.md#cmd-goal) — /goal：本票路径覆盖的子案例满足“长任务开启/关闭、目标提示与边界；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-task](../acceptance-matrix.md#cmd-task) — /task：本票路径覆盖的子案例满足“长任务别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-coordinator](../acceptance-matrix.md#cmd-coordinator) — /coordinator：本票路径覆盖的子案例满足“合并后的长任务别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-btw](../acceptance-matrix.md#cmd-btw) — /btw：本票路径覆盖的子案例满足“备注注入而不立即请求模型；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

六条冻结命令与中英文长任务指令通过来源对照。普通入口验证实际两个子代理派发、目标入轮、备注零请求及开关状态，关闭时移除专用指令，保留已提交目标与备注。启动别名使用同一模式，plan 和显式免审批优先级保留。未提高全局 MAX_TURNS 上限。[提示对照](../../ruocun-next24h/evidence/batch-04/n44/README.md) · [普通入口](../../ruocun-next24h/evidence/batch-04/ordinary/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
