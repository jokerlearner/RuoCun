# 30 — 工具写入/查询/审核删除分域记忆

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_skills
Branch: codex/advanced-skills
Worktree: .worktrees/advanced-skills
Parent: [完整迁移规格](../spec.md)
Blocked by: [09 — 按分层权限审批并完成一次文件写入](09-permissions.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

五类型/三scope、来源校验/locked/手改与删除真实落盘，错误输入不改原数据。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-504](../module-map.md#mm-504)、[MM-508](../module-map.md#mm-508)、[MM-514](../module-map.md#mm-514)、[MM-516](../module-map.md#mm-516)、[MM-518](../module-map.md#mm-518)、[MM-670](../module-map.md#mm-670)、[MM-672](../module-map.md#mm-672)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-01](../acceptance-matrix.md#mem-01) — 记忆存储与来源：本票路径覆盖的子案例满足“类型/项目过滤、来源验证/审计及删除正确；session与长期记忆分开”。
- [x] [TOOL-MemoryRead](../acceptance-matrix.md#tool-memoryread) — MemoryRead：本票路径覆盖的子案例满足“取记忆正文；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-MemoryWrite](../acceptance-matrix.md#tool-memorywrite) — MemoryWrite：本票路径覆盖的子案例满足“五种类型、三作用域、重要度/来源，或明确删除；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-memory](../acceptance-matrix.md#cmd-memory) — /memory：本票路径覆盖的子案例满足“查看、审核、删除记忆；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

源码出口通过。3366a17存储回修保留不可往返输入命中的旧记录，c21f34f将原凭据规则覆盖正文、标题和来源，兼容目录只读。f0c3488实际CLI/受控TTY覆盖busy查询、plan写→读、持久意图、审核与删除；模块及入口独审通过。自动注入/维护、统一安装包及真实Terminal体验分别记录。

[来源证据](../../ruocun-next20h/evidence/n4-memory/README.md) · [普通入口](../../ruocun-next20h/evidence/n4-shared/README.md) · [存储独审](../../ruocun-next20h/evidence/review/4-memory-storage-review.md) · [工具与入口独审](../../ruocun-next20h/evidence/review/4-memory-tools-review.md)。

## Comments

- 2026-11-11：09硬前置已满足，12公共基础与35/36已独审集成；按批准优先级领取。线一独占memory存储/工具/本票测试与证据。root负责Tool真实持久副作用标志、执行器消费、普通入口/命令与公共记录。保留plan能力标签和按源可见性，MemoryWrite在现账本独占确认；兼容目录只读，坏原件/locked及未知结果不覆盖。31/32仍守原依赖。

- 2026-11-11：N1完整出口通过，原硬前置已满足；按连续计划顺序和空闲实现槽排队，未领取、未启动产品实现。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
