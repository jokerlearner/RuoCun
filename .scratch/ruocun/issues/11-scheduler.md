# 11 — 忙时排队、暂停及取消流不会污染新轮

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [08 — 模型用TodoWrite和Read完成首个工具回合](08-readloop.md), [06 — 模型断流/限流后可重试或可靠停止](06-resilient.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

多输入安全边界保序；pause清队列/当前轮、迟到回调隔离，paused可再次继续。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-422](../module-map.md#mm-422)、[MM-385](../module-map.md#mm-385)、[MM-762](../module-map.md#mm-762)。

## 共享接口与并行

接口领域：调度。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [RUN-01](../acceptance-matrix.md#run-01) — 安全边界与队列：本票路径覆盖的子案例满足“边界合并、保序不丢失；不得插断 assistant/tool 对；提交 hook 拦截不入历史”。
- [x] [RUN-02](../acceptance-matrix.md#run-02) — 状态机区分：本票路径覆盖的子案例满足“单轮 completed/waiting/interrupted/failed 与执行状态独立；paused 可继续，closed 不再 pump”。
- [x] [RUN-04](../acceptance-matrix.md#run-04) — 输入暂停与后台解绑：本票路径覆盖的子案例满足“pause 清队列/释放等待/停当前轮但不 cancelAll；已转后台不被旧前台 signal 杀死”。
- [x] [WIRE-12](../acceptance-matrix.md#wire-12) — 取消流与迟到事件：本票路径覆盖的子案例满足“当前运行不再消费旧事件；部分内容只提交一次；网络取消与底层副作用分开确认”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票自动技术出口已通过。已确认FIFO、安全边界及输入账本、暂停/继续、单输入owner、旧事件隔离、可信结果与关闭。关闭/后台解绑母族的后台15–17不在本票前台出口，真实Terminal/resize单列。

[N1统一集成](../../ruocun-next20h/evidence/n1-integration/README.md)：固定产品a7d803c/r1，复验源896ecaf，1154项通过、3项排除，默认mypy108、Ruff、offline、构建、121成员实际安装与独审均通过。首轮失败及最小隔离修复原样留证。结题仅覆盖本票子路径，人工体验不代填。

历史模块检查点：前台FIFO/边界/代次、可信输入投影/恢复、单owner草稿/审批及close模块已独审，见[调度](../../ruocun-next20h/evidence/n1-scheduler/README.md)、[输入](../../ruocun-next20h/evidence/review/n1-input-review.md)、[投影](../../ruocun-next20h/evidence/review/n1-runtime-projection-review.md)。普通入口在途；新包/自动完整出口待收口，后台15–17与真实Terminal不据模块结果通过。

以下领取/早期未执行文字为历史，当前正式出口仍以上述状态与最新回执为准。

2026-11-11：08固定r2自动出口与独审已通过，主协调按ADR-0013领取本票；实际实现及回执待本票执行，领取不等于通过。起点70c7464及其N0证据收口提交；共享文件由root单点拥有。

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
