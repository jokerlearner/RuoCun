# 63 — 终端通知及标题注意状态（无桌面通知）

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [16 — 后台事件持久投递并以TaskWait唤醒](16-wait.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按W6移出本轮Windows系统桌面通知，保留终端内完成、待审批等提示及安全标题注意状态。NotifyUser的响应准确说明仅显示终端提示、未发送桌面通知；载荷作为数据处理，不注入控制字符或启动Windows通知PowerShell/隐藏窗口后端。其它平台保留来源模块路径、实机状态未验，不冒用Windows结果。后台运行与提示失败不能改变任务真实结果。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。DAO已有桌面通知分支属于本轮明确缩减的来源功能，不能称完整来源通知已迁移；本轮只验终端渠道。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-680](../module-map.md#mm-680)、[MM-772](../module-map.md#mm-772)、[MM-790](../module-map.md#mm-790)、[NEW-09](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台/终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-10](../acceptance-matrix.md#win-10) — 通知范围与数据：本轮不发送系统桌面通知；终端提示/标题载荷只作数据，无控制字符注入，准确报告实际渠道，失败不阻主任务。
- [x] [TOOL-NotifyUser](../acceptance-matrix.md#tool-notifyuser) — NotifyUser：保留来源工具定义及运行上下文调用；本轮只发终端提示，结果明确未发桌面通知，不用成功文案冒充原通知渠道。
- [x] [WT-07](../acceptance-matrix.md#wt-07) — 焦点/标题/提示：终端标题/状态随任务变化且不注入控制字符；桌面通知和Windows防休眠按W6/W5移出，提示范围真实。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

来源定向、同一输入 owner 回归及独立审查通过。批次03真实 Windows Terminal 显示 `NotifyUser` 合成提示，设备回传失焦和聚焦，依次记录黄标、绿标、普通标题和退出恢复请求。用户确认标签黄标转绿及聚焦后清除正常。[自动回执](../../ruocun-next24h/evidence/batch-02/n63/README.md) · [焦点轨迹](../../ruocun-next24h/evidence/n18/wt/runs/20261111T100558Z-4260db/README.md) · [用户反馈](../../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md)

## Comments

- 2026-11-11暂停保存：候选已纳入固定b02-r1，来源/独审及集中工程结果见批次02构建记录。用户要求完成当前构建后暂停，当前不再执行；本票真实Windows Terminal技术范围尚待验，维持在途，不虚报resolved。

- 2026-11-10：用户按表缩减W6；保留终端提示和标题，不开发桌面通知后端；相关图形欢迎功能W1未选，68仍须基于本票实际标题/状态接口接线。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
