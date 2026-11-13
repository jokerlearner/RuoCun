# 42 — 长任务触发反思并在恢复后继续

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/b07-reflect
Parent: [完整迁移规格](../spec.md)
Blocked by: [32 — 蒸馏合并清理记忆并保留来源和锁定项](32-memorymaint.md), [29 — 上下文压缩及模型错误后继续任务](29-compact.md), [41 — fork/exactTools恢复保持消息与工作区边界](41-fork.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

间隔/同步/异步fork蒸馏与失败fallback按来源；结果仅安全边界注入且重启不重复。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-408](../module-map.md#mm-408)、[MM-410](../module-map.md#mm-410)、[MM-413](../module-map.md#mm-413)、[MM-415](../module-map.md#mm-415)、[MM-430](../module-map.md#mm-430)。

## 共享接口与并行

接口领域：调度/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [MEM-03](../acceptance-matrix.md#mem-03) — 压缩与反思：本票路径覆盖的子案例满足“保留用户目标/工具对/背景等待状态；提示、触发/预算与注入边界按oracle”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[本票独审](../../ruocun-next24h/evidence/review/b07-reflection-platform-final-review.md)与[集中交付](../../ruocun-next24h/evidence/batch-07/integration/README.md)已通过。

技术出口已通过：来源模块、普通入口及高风险接缝独审见[批次07核心回执](../../ruocun-next24h/evidence/batch-07/root-core/README.md)及[最终独审](../../ruocun-next24h/evidence/review/b07-reflection-platform-final-review.md)。批末集中包另行绑定；不代表母案例全部完成或最终用户体验已通过。

## Comments

- 2026-11-13：用户授权核实来源字段冲突，已确认反思写入成功、下一次启动却因标签被当作文件路径而漏召回。`memory/validate.py` 精确兼容 `user_stated` / `inferred`，保留原来源值与有效期；无需改写既有记录。146 项受影响回归、跨进程普通入口与独立复核通过，[任务与证据](../../memory-source-recall-20261113/README.md)。未改反思开关、存储结构或其它来源行为。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-12：用户授权启动[批次07](../../ruocun-next24h/batch-07.md)，已核真实前置，本票claimed，尚无通过结论。
