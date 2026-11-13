# 54 — MCP不确定结果断线后不盲目重做

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [52 — 同一MCP能力经HTTP/SSE连接并可关闭](52-mcphttp.md), [53 — 搜索激活工具并消费MCP资源/提示更新](53-mcpcaps.md), [17 — 恢复查询及显式决定解开未知工具/执行](17-recovery.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

服务端已执行再断线/普通错误区分，按确认策略重连/未知，保留副作用证据。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-496](../module-map.md#mm-496)、[MM-598](../module-map.md#mm-598)。

## 共享接口与并行

接口领域：协议/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-10](../acceptance-matrix.md#ext-10) — MCP 断线/副作用：本票路径覆盖的子案例满足“来源自动重试风险与ADR-0003确认差异分别登记；不可因本地journal声称远端exactly-once；未知结果持久保留、重开不自动重放”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

主协调已集成并验收，独立复核通过。[54实现与红绿](../../ruocun-next24h/evidence/n54-mcp-recovery/README.md) · [HTTP/SSE最终独审](../../ruocun-next24h/evidence/review/b05-mcp-recovery-review.md) · [子专属MCP独审](../../ruocun-next24h/evidence/review/b05-agent-mcp-review.md)。三传输均有普通CLI实际副作用证据：明确RPC错误保存已确认结果，副作用后断线退出74、持久unknown；同会话重开换ID没有新模型/远端执行。保留SDK日志诊断并脱敏，未知74不被关闭异常覆盖。子连接在正常结束/拒绝/转交时收口，恢复绑定实际连接配置及精确工具目录，不自动重放。

最终产品候选`c85b80d5`；批末全量、标准包与隔离安装结果另见[集中交付](../../ruocun-next24h/evidence/batch-05/integration/README.md)。未代填77/78人工体验、不声明远端exactly-once。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：用户已确认[ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md)：可能已执行且结果不明的MCP工具请求停止自动重放，持久保留未决；连接/能力发现可重连。来源effect2与目标保持1次的断线/重启反例为独立测试依据，不再询问此取舍。
