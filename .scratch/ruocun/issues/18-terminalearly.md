# 18 — 在真实WT边流式边编辑并中断/缩放

Type: task
Mode: AFK
Status: resolved
Assignee: Codex N24
Parent: [完整迁移规格](../spec.md)
Blocked by: [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md), [D10 — 确定终端框架与Windows平台适配方案](../../ruocun-discovery/issues/10-terminal-windows-decision.md)
用户体验验收：pending（ADR-0004，统一由77最终验收）

## What to build

最小产品UI实际Python可见运行；IME/粘贴不自动提交/流式草稿/Esc/CtrlC/resize提前验，未覆盖项不报全通过。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-747](../module-map.md#mm-747)、[MM-751](../module-map.md#mm-751)、[MM-753](../module-map.md#mm-753)、[MM-794](../module-map.md#mm-794)、[MM-800](../module-map.md#mm-800)。

## 共享接口与并行

接口领域：终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WT-01](../acceptance-matrix.md#wt-01) — 真实中文IME/Unicode编辑：本票路径覆盖的子案例满足“候选窗/光标/提交内容正确，字符不丢不劈，hash与用户输入一致”。
- [x] [WT-02](../acceptance-matrix.md#wt-02) — 粘贴/折叠/图片：本票路径覆盖的子案例满足“粘贴不自动提交，折叠提交展开原文；不吞真实文本；图片类型/5MB边界准确”。
- [x] [WT-03](../acceptance-matrix.md#wt-03) — 流式与忙时输入：本票路径覆盖的子案例满足“草稿稳定，队列保序，可见等待状态，工具对不被插断”。
- [x] [WT-04](../acceptance-matrix.md#wt-04) — 中断与退出：本票路径覆盖的子案例满足“Esc按模态优先/先清队列再暂停；2秒双Ctrl+C退出；后台不被旧前台取消”。
- [x] [WT-05](../acceptance-matrix.md#wt-05) — 缩放/原生scrollback：本票路径覆盖的子案例满足“清理旧物理行无残影/吞历史，重绘不丢草稿；仅owned窗口按确认策略清理自有视口”。
- [x] [WT-09](../acceptance-matrix.md#wt-09) — 管道与终端恢复：本票路径覆盖的子案例满足“可读文本无光标控制污染；可控退出恢复mode/cursor/paste/focus/title；强杀后给出可执行恢复说明”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

文本输入与同reader协议、调度接线及来源定向回归已集成。用户在真实Windows Terminal对流式期间编辑/排队、Esc清队与暂停、7行粘贴折叠、缩放、双Ctrl+C五项回复“全部正常”。实际安装入口退出0、无强停，input/output mode前后503/7相等。见[真实窗口证据](../../ruocun-next24h/evidence/n18/wt/runs/20261111T044203Z-514e10/README.md)与[独立复核](../../ruocun-next24h/evidence/review/terminal-wt-review.md)。本票文本技术前置resolved，65依赖已满足。IME候选窗、图片、完整主题及77整体体验保持各自未验状态。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：按[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md)，本票先验完整产品可运行路径和自动证据，人工体验统一交77/78/85；不再逐票要求用户操作，不改WT范围。

- 2026-11-05：工程入口03解耦完整发布前置后，将本票真正需要的兼容/平台决定显式列为依赖；未关闭前不得调度本票，不减少已确认验收范围。

- 2026-11-11 09:50 +08:00：按下一轮24小时计划领取，前置已核对。独立 worktree 实施，完成状态等待实际证据及独审。

- 2026-11-11：本候选在唯一ptk输入owner接来源文本折叠/Enter展开、Unicode整簇移动删除、模态优先、Esc回填及两秒双Ctrl+C退出。新增on_escape/set_status供主协调接真实调度器。关键接缝等待独立审查，65尚未启动。

- 2026-11-11：D10同reader协议隔离已产品化，保留ptk自身CPR定位，focus/DA/cell与普通文本隔离，paste内相似序列原样保留，退出恢复parser。协议/编辑/旧runtime共11项通过，mypy/Ruff通过。原失败和回修见同一候选证据。21仍未领取。

- 2026-11-11：按D10登记单次paste正文8MiB UTF8上限，超过后整次拒收、显示原因并保留原草稿，持续吞到END。原1MiB、实际8MiB多字节边界及产品反馈路径已验，合计13通过，mypy/Ruff通过；详见同一候选记录资源边界段。
