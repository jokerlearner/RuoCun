# 06 — 模型断流/限流后可重试或可靠停止

Type: task
Mode: AFK
Status: resolved
Assignee: /root/takeover06
Branch: impl/06-resilient
Worktree: .worktrees/wb-i06
Parent: [完整迁移规格](../spec.md)
Blocked by: [04 — 用兼容账户配置完成首轮流式对话](04-chat.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

前产出重试/非流式fallback、240秒idle、429/529分支、部分输出不重复。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-439](../module-map.md#mm-439)、[MM-404](../module-map.md#mm-404)。

## 共享接口与并行

接口领域：模型。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIRE-07](../acceptance-matrix.md#wire-07) — 重试与非流式 fallback：本票路径覆盖的子案例满足“只在参考允许阶段/次数重试；已有内容不从头重复；529 background、无 Retry-After 的429保留分支”。
- [x] [WIRE-08](../acceptance-matrix.md#wire-08) — idle watchdog：本票路径覆盖的子案例满足“默认240秒仅有效 delta 重置；用户取消保留部分；产出后 idle 显示明确错误”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

已集成独立复核提交 `daf2f5dd93348298acfa00e439e37242c5343e97`，实现候选 `f12f949`（回修代码 `bb22239`）。见[独立复核及原失败](../integration-evidence/sprint06/README.md)、[实现者证据](../evidence/06-resilient/README.md)、[冲刺红绿回修](../evidence/06-resilient/sprint-fixes/README.md)。公开streamChat已接入重试、取消与fallback；独立全量319 passed / 3 deselected、21边界passed，五入口/pip check及仓库外wheel路径全部通过，34回执无敏感值命中。四类来源差异已闭环；真实模型、完整来源CLI oracle、最终WT/其它平台/standalone未验，CPython私有接口及证书限制保留。本票只关闭WIRE-07/08已覆盖路径，不代表母案例族或全量Agent完成。

## Comments

- 2026-11-10冲刺：主协调接收独立复核`daf2f5d`并将本票resolved，正式完成5/84。初始四类阻断的红日志保持，修复后的独立绿证据另记；当前已集成原候选和新回修，未把未跑真实模型/最终WT等标通过。

- 2026-11-10：用户指定改由 Codex 接手；保留 WorkBuddy 原分支、worktree 和未提交成果，在原票继续，须完成实现、隔离验证及独立集成复核后才能结题。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：主代理确认前置 [04](04-chat.md) 已 resolved 并集成至 `dbdd0bc`，按 `issue_graph.py` 真实 frontier 将本票由 blocked 释放为 ready-for-agent。接口领域与共享 client/session 契约由主代理统筹；05/06 均涉及 `src/ruocun/client/client.py`，并行时须按主代理分派的边界避免各自重定义。

- 2026-11-10：05 已 resolved 并集成至 `637fc37`，共享 client 契约（含 05 新增的 `chunks` 消费与 Responses 路由分支）已稳定。主代理按 `issue_graph.py` 真实 frontier 与 implement-spec Step 6 的并发精神，将 06/07/58 作为**同一批并行**领取，各自独立分支/worktree（impl/06-resilient / .worktrees/wb-i06），起点为含本批领取记录的集成 tip。共享文件边界由主代理统筹：`cli.py` 只允许各自追加一个独立的显式 demo 分发分支、不得改写既有分支；06 不改 `types.py`/`responses.py`/`sse.py` 与 `session/`，07 不改 `client/`，58 不改 `client/` 与 `session/`；若必须改变共享接口，先向主代理报告具体契约差异，不在多个分支各自重定义。实现与独立 merger 分别派发，人工体验按 ADR-0004 集中最终验收。
