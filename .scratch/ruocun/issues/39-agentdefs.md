# 39 — 自定义代理定义约束真实派发

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [38 — 调用内置子代理并收集同步结果](38-agentsync.md), [31 — 恢复/新轮按项目加载并注入记忆](31-memoryinject.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

支持字段/白黑名单/inherit/skills/memory/permissionMode实际生效，非法定义与覆盖顺序可演示。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-366](../module-map.md#mm-366)、[MM-376](../module-map.md#mm-376)、[MM-380](../module-map.md#mm-380)、[MM-374](../module-map.md#mm-374)。

## 共享接口与并行

接口领域：工具/权限。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-05](../acceptance-matrix.md#ext-05) — agent 文本格式：本票路径覆盖的子案例满足“按实际简化parser接纳边界；内联MCP类型不当完整支持；bundled覆盖与生命周期一致”。
- [x] [CFG-03](../acceptance-matrix.md#cfg-03) — 模型继承：本票路径覆盖的子案例满足“override > agent > parent；缺 parent 明确报错，不暗换 provider”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

主线a476233、f01e5e0及bf3a4e2覆盖真实定义读取和执行。普通入口以合成服务确认父会话发现角色、子模型选择、只暴露Read及父子消息分离。独审固定复现并复验父区外授权和原项目记忆归属。Hook/MCP生命周期仍由对应后续票承接，当前拒绝派发声明了未装配资源的角色。自动通过，无真实模型调用。[实现回执](../../ruocun-next24h/evidence/n39-agent-defs/README.md) · [独审](../../ruocun-next24h/evidence/review/b02-agent-definition-review.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
