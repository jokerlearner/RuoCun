# 56 — 外部Deck面板控制同一持久会话

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b08-app
Parent: [完整迁移规格](../spec.md)
Blocked by: [16 — 后台事件持久投递并以TaskWait唤醒](16-wait.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

loopback/token/Origin、snapshot/messages/command、重复ID与409，面板关闭不结束Agent。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-396](../module-map.md#mm-396)、[MM-399](../module-map.md#mm-399)。

## 共享接口与并行

接口领域：调度/协议。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-12](../acceptance-matrix.md#ext-12) — Agent Deck：本票路径覆盖的子案例满足“仅loopback认证、幂等和409；面板关闭不等于Agent退出；身份/会话/事件不串”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[批末集中验收](../../ruocun-next24h/evidence/batch-08/integration/README.md)通过。
冻结 DAO 协议、历史投影和普通托管入口测试已通过。合成 SSE 会话由同一个调度器、审批和持久化处理。首轮[独审](../../ruocun-next24h/evidence/batch-08/review/n56-deck-initial.md)复现同文本输入回执串线，修复 `8d7f3845` 将回执绑到已保存的输入 ID，并让子任务取消仅终止自己的待批请求。修后真实协议和 CLI 路径经独立复跑通过。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
