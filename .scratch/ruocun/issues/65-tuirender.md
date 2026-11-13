# 65 — 内联转录、中英文主题及scrollback稳定

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [18 — 在真实WT边流式边编辑并中断/缩放](18-terminalearly.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

Markdown/工具输出/宽字符/长历史流式布局与语言主题切换，连续resize不残影/删共享历史。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-480](../module-map.md#mm-480)、[MM-481](../module-map.md#mm-481)、[MM-482](../module-map.md#mm-482)、[MM-749](../module-map.md#mm-749)、[MM-765](../module-map.md#mm-765)、[MM-786](../module-map.md#mm-786)、[MM-796](../module-map.md#mm-796)、[MM-800](../module-map.md#mm-800)、[MM-788](../module-map.md#mm-788)、[MM-797](../module-map.md#mm-797)。

## 共享接口与并行

接口领域：终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [CMD-lang](../acceptance-matrix.md#cmd-lang) — /lang：本票路径覆盖的子案例满足“中英文查询/切换与存储；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-theme](../acceptance-matrix.md#cmd-theme) — /theme：本票路径覆盖的子案例满足“会话主题切换，不改变调度器状态；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [WT-03](../acceptance-matrix.md#wt-03) — 流式与忙时输入：本票路径覆盖的子案例满足“草稿稳定，队列保序，可见等待状态，工具对不被插断”。
- [x] [WT-05](../acceptance-matrix.md#wt-05) — 缩放/原生scrollback：本票路径覆盖的子案例满足“清理旧物理行无残影/吞历史，重绘不丢草稿；仅owned窗口按确认策略清理自有视口”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

用户在真实 Windows Terminal 确认中文、主题切换、草稿、缩放和滚动正常。输入区前景与底色成对修复后，深浅主题输入均清楚，复测进程退出0且控制台模式一致。来源定向与渲染独审已通过。欢迎形象的清晰度归68，完整体验归77。[实机初验](../../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md) · [对比度复测](../../ruocun-next24h/evidence/n18/wt/runs/20261111T090042Z-01327b/README.md)

基础显示、双语、同owner动态渲染区及普通入口已形成在途候选。18项来源和broker定向结果见[65证据](../../ruocun-next24h/evidence/batch-02/n65/README.md)，普通TTY、七工具及静态接线见[主协调证据](../../ruocun-next24h/evidence/batch-02/root/README.md)。保持claimed，独审与本票未完成技术项继续核对，来源背景探测缺口据实际归属补齐。

App/render转录、工具diff/todo/折叠、Ctrl+O、有界live及同InputBroker输出已实现；基础+来源展示/resize/旧输入owner合计18项通过，静态检查通过。普通入口接线由主协调持有，真实WT视觉不由受控输出代填；本票仍claimed。

## Comments

- 2026-11-11暂停保存：候选已纳入固定b02-r1，来源/独审及集中工程结果见批次02构建记录。用户要求完成当前构建后暂停，当前不再执行；本票真实Windows Terminal技术范围尚待验，维持在途，不虚报resolved。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
