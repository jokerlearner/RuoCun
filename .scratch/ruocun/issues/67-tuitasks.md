# 67 — 任务面板/历史展开与Ctrl+B后台操作

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [65 — 内联转录、中英文主题及scrollback稳定](65-tuirender.md), [45 — 创建/查询/更新/停止手工任务记录](45-manual.md), [47 — 会话loop按周期排队且退出清理](47-loop.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

Ctrl+T/G/O、Ctrl+B/ShiftTab状态反馈，前台转后台与后续Esc不误杀；文本copy不丢Unicode。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-745](../module-map.md#mm-745)、[MM-747](../module-map.md#mm-747)、[MM-762](../module-map.md#mm-762)、[MM-755](../module-map.md#mm-755)。

## 共享接口与并行

接口领域：终端/调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 普通入口已接只读任务/历史面板、Shell、普通 Agent、fork、remote 的已确认后台交接和 `/copy`。
- [x] [WT-04](../acceptance-matrix.md#wt-04) — 实机 Ctrl+B 后同一 Shell run 完成，Esc 停止新一轮，正常退出。旧取消信号与后台运行交叠由独立 runner 用例覆盖。
- [x] [WT-06](../acceptance-matrix.md#wt-06) — 实机确认 Ctrl+T/G、历史定位和草稿保留。焦点、模态和审批按定向回归及既有实机证据。
- [x] [CMD-copy](../acceptance-matrix.md#cmd-copy) — 实机复制末条 Unicode 回答并粘贴回草稿，空回答和查询边界经定向验证。
- [x] 保存按键层、真实 SQLite/Git 及受认证 Windows runner 的定向红绿和独立复核。
- [x] 自动测试、可见 Windows Terminal 及人工体验结果分别保留。
- [x] 实现与独立审查已集成，可见窗口复验通过。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

实现及定向独审已通过。普通、fork 和 remote 在已保存工具边界交接，显式 worktree 维持前台。首次可见窗口的提前退出保留为历史异常。可见窗口复验确认 Ctrl+B、Esc、任务与历史面板和 Unicode 剪贴板正常，同一 Shell run 在交接后继续并取得签名完成回执。[实现证据](../../ruocun-next24h/evidence/batch-03/n67/README.md) · [独立复核](../../ruocun-next24h/evidence/review/b03-agent-special-handoff-review.md) · [实机复验](../../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
