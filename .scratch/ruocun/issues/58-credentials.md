# 58 — Windows系统凭据存取及fallback可用于请求

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24 terminal
Branch: codex/n24-terminal
Worktree: .worktrees/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [04 — 用兼容账户配置完成首轮流式对话](04-chat.md), [07 — 保存一次会话并拒绝并发owner写入](07-store.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

假秘密写取删/同名大小写、拒绝和超时，准确显示存储后端，验证日志无秘密。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-458](../module-map.md#mm-458)、[MM-455](../module-map.md#mm-455)、[NEW-04](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台/配置。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [WIN-05](../acceptance-matrix.md#win-05) — 系统凭据：本票路径覆盖的子案例满足“Credential Manager或等效后端，case collision可区分，失败不误报系统保存，秘密不入日志”。
- [ ] [CFG-04](../acceptance-matrix.md#cfg-04) — 凭据优先级：本票路径覆盖的子案例满足“inline 优先；缺 key 不靠通用环境变量自动挑账户；fallback 准确显示且不泄漏”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

候选已接续旧窄端口并补私有ACL/原子保存，68项定向及Ruff/mypy通过。新UUID真实系统写取删/大小写确认通过，精确清理回读1168，pending为空。普通runtime装配与独审待执行，状态保持claimed。见[本轮58证据](../../ruocun-next24h/evidence/n58/README.md)。

## Comments

- 2026-11-10 工作流补依赖：当前候选的私密配置/fallback文件端口依赖07，任务图同步增加store硬边。既有候选、claimed状态和停止边界保留；本轮未恢复执行、未运行demo或补写验证通过。

- 2026-11-10：用户指定改由 Codex 接手；保留 WorkBuddy 原分支、worktree 和未提交成果，在原票继续，须完成实现、隔离验证及独立集成复核后才能结题。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：主代理复核 `issue_graph.py` 真实 frontier：本票 Blocked by 仅 [04](04-chat.md)，04 已 resolved 且集成至 `7623e7d`，故将状态由 blocked 修正为 ready-for-agent，保持状态列与依赖图一致。本票涉及 Windows 系统凭据后端与真实系统交互，派发时按 D10/D17 已验证窄端口候选与合成秘密执行，不读取真实用户凭据。

- 2026-11-10：05 已 resolved 并集成至 `637fc37`，共享 client 契约（含 05 新增的 `chunks` 消费与 Responses 路由分支）已稳定。主代理按 `issue_graph.py` 真实 frontier 与 implement-spec Step 6 的并发精神，将 06/07/58 作为**同一批并行**领取，各自独立分支/worktree（impl/58-credentials / .worktrees/wb-i58），起点为含本批领取记录的集成 tip。共享文件边界由主代理统筹：`cli.py` 只允许各自追加一个独立的显式 demo 分发分支、不得改写既有分支；06 不改 `types.py`/`responses.py`/`sse.py` 与 `session/`，07 不改 `client/`，58 不改 `client/` 与 `session/`；若必须改变共享接口，先向主代理报告具体契约差异，不在多个分支各自重定义。实现与独立 merger 分别派发，人工体验按 ADR-0004 集中最终验收。

- 2026-11-11：按24小时计划备选接续58，原433d980及wb-i58所有材料原样保留。仅提取配置/Win32窄端口，旧demo未运行。普通入口通过createKeychain(env)装配，由主协调维护。系统未知写/删保留未决不fallback重放，Windows文件落盘复用07私有ACL和atomic_publish。真实系统仅新UUID合成target并已精确清理。

- 2026-11-11：主协调接收来源与实际产品路径候选，[独审](../../ruocun-next24h/evidence/review/credentials-review.md)已通过。本票技术完成，N24整体固定包及全量出口待后续统一验证。
