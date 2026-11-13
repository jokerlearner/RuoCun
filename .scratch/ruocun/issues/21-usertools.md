# 21 — 终端/REPL问题与用户消息可往返

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24 terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

单选/多选/拒绝/取消→工具结果→模型续轮；用户消息与附件呈现，TUI模态在后续绑定。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-623](../module-map.md#mm-623)、[MM-703](../module-map.md#mm-703)。

## 共享接口与并行

接口领域：工具。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [TOOL-AskUserQuestion](../acceptance-matrix.md#tool-askuserquestion) — AskUserQuestion：本票路径覆盖的子案例满足“询问、选项/多选，由上下文提供 UI；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [ ] [TOOL-SendUserMessage](../acceptance-matrix.md#tool-sendusermessage) — SendUserMessage：本票路径覆盖的子案例满足“用户可见消息、附件路径、normal/proactive 状态；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

工具层候选已实现，首次定向10通过/1失败。失败为共享schema缺少数组长度校验，等待主协调补齐。Ruff/mypy通过。普通runtime注册、问答取消和消息可见输出接线等待集成独审。详见[21候选证据](../../ruocun-next24h/evidence/n21/README.md)。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：主协调按24小时计划备选授权推进21。来源工具和测试已读取，独占ask_user.py/send_message.py及本票用例，共享runtime/schema/types由主协调接线。保留claimed，未验完整用户可见往返。

- 2026-11-11：主协调已集成本票来源模块、普通入口接线和独立复核。25项与普通TTY多选/讨论/用户消息/中断配对已实际通过，[独审记录](../../ruocun-next24h/evidence/review/user-tools-review.md)。本票技术完成，N24整体固定包及全量出口尚待后续候选统一执行。
