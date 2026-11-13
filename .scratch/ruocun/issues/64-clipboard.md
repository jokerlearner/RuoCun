# 64 — Windows粘贴图片进入视觉模型请求

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [18 — 在真实WT边流式边编辑并中断/缩放](18-terminalearly.md), [05 — 通过Responses路由完成同一对话/工具回合](05-responses.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

clipboard/路径两入口、MIME/magic/5MB/RGBA/不支持模型与失败不吞文本；接收内容可核对。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-763](../module-map.md#mm-763)、[MM-691](../module-map.md#mm-691)、[NEW-07](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台/终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-08](../acceptance-matrix.md#win-08) — 图片/文本clipboard：本票路径覆盖的子案例满足“Windows原生读取，图片类型/上限一致；失败不吞原文本、不执行路径为命令”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

同InputBroker的Alt+V附图、图片路径、视觉请求及Windows只读PNG/DIB端口已实现。4项来源/D10合成场景及3项输入owner回归通过，Ruff与mypy通过。用户在真实Windows Terminal用画图复制合成图，Alt+V与请求正常。回环端收到的PNG与合成文件字节哈希一致。技术通过，最终体验按77记录。[源码证据](../../ruocun-next24h/evidence/batch-02/n64/README.md) · [实机字节链](../../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md)

## Comments

- 2026-11-11暂停保存：候选已纳入固定b02-r1，来源/独审及集中工程结果见批次02构建记录。用户要求完成当前构建后暂停，当前不再执行；本票真实Windows Terminal技术范围尚待验，维持在途，不虚报resolved。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
