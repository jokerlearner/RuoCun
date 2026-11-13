# 31 — 恢复/新轮按项目加载并注入记忆

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [30 — 工具写入/查询/审核删除分域记忆](30-memorycrud.md), [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

全文/索引预算、稳定前缀与安全尾部注入可从真实请求观察，关闭时有明确语义。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-510](../module-map.md#mm-510)、[MM-514](../module-map.md#mm-514)、[MM-518](../module-map.md#mm-518)。

## 共享接口与并行

接口领域：模型。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-02](../acceptance-matrix.md#mem-02) — 注入与整理：本票路径覆盖的子案例满足“预算/稳定前缀、源引用和locked保护；模型失败不丢原数据”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

源码出口通过。9941cc6按冻结规则选全文、索引和知识范围，原11项通过。3e3eaea真实loopback证实启动、同进程前缀、恢复及禁用；与冻结恢复的已记录差异为重开使用当次启动快照，同时保留可信工具配对和图片。原CLI与提示词27项通过，模块与普通入口独审通过。自动尾反思留42、统一包留N5。

[来源证据](../../ruocun-next20h/evidence/n4-memory-inject/README.md) · [实际入口](../../ruocun-next20h/evidence/n4-shared/README.md#31普通入口) · [独审](../../ruocun-next20h/evidence/review/4-memory-inject-review.md)。

## Comments

- 2026-11-13：用户授权修复来源字段冲突。反思来源标签 `user_stated` / `inferred` 原被文件校验误判失效，已作无格式迁移的兼容修复；两个独立产品进程与本地 HTTP fixture 证明第二次全新启动已召回用户偏好和项目事实。受影响回归与独立复核通过，[任务与证据](../../memory-source-recall-20261113/README.md)。真实模型 0 调用，工作区改动未提交。

- 2026-11-11：30与11原硬前置已完成，正式领取。线二唯一写注入选择/渲染模块和来源断言，root负责CLI、system前缀、既有恢复与真实请求确认；32继续等待。按冻结源每进程启动一次选择，不加每轮重扫或后台触发。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
