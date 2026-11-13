# 68 — 欢迎Sixel/终端回包与文本降级稳定

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [65 — 内联转录、中英文主题及scrollback稳定](65-tuirender.md), [63 — 后台任务触发安全通知及标题注意状态](63-notify.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

单reader/输出owner、DA/CPR分片/迟到/paste/背压/epoch，窗口缩放与模态时图形无残留。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-744](../module-map.md#mm-744)、[MM-760](../module-map.md#mm-760)、[MM-767](../module-map.md#mm-767)、[MM-768](../module-map.md#mm-768)、[MM-794](../module-map.md#mm-794)、[MM-757](../module-map.md#mm-757)、[MM-758](../module-map.md#mm-758)、[MM-473](../module-map.md#mm-473)、[MM-770](../module-map.md#mm-770)、[MM-792](../module-map.md#mm-792)。

## 共享接口与并行

接口领域：终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WT-08](../acceptance-matrix.md#wt-08) — Sixel欢迎区与回包：本票路径覆盖的子案例满足“单owner解析，粘贴不吞；图形最多一帧在途/旧epoch丢弃；失败回文本且无转义泄露”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

用户对备用字符图反馈低清，实机确认设备支持 Sixel 且启动时未发帧。`fe046b9` 在附加文字前写出第一帧，复验 119×30 真实 Windows Terminal 收到原 256×244 图形，用户确认清楚。9 项欢迎定向验证通过。批次03复验再次实际写出首帧，63 的焦点和注意状态实机已通过，整体体验归77。[原图确认](../../ruocun-next24h/evidence/n18/wt/runs/20261111T092536Z-1592d0/README.md) · [批次03复验](../../ruocun-next24h/evidence/n18/wt/runs/20261111T101837Z-52f7cc/README.md)

### 历史候选

源码候选与7项来源/产品seam回执见[batch-02/n68](../../ruocun-next24h/evidence/batch-02/n68/README.md)。受控同reader探测、原始帧写入、粘贴、缩放和主题降级已通过；当时实际 Windows Terminal 图形与普通入口接线等待集中验证。

## Comments

- 2026-11-11暂停保存：候选已纳入固定b02-r1，来源/独审及集中工程结果见批次02构建记录。用户要求完成当前构建后暂停，当前不再执行；本票真实Windows Terminal技术范围尚待验，维持在途，不虚报resolved。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 批次02同负责人批内许可：65已保存可调用源码/普通TTY及独审0阻断，63源码候选e3720ad及50a84e6通知清理修复已来源定向通过。68可由同一终端负责人接续，65/63整票与集中真实终端项据实待验，后继不据本许可对外解锁。
