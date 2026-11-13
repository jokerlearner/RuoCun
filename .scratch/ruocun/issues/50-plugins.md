# 50 — 安装一个组合插件后使用并安全卸载

Type: task
Mode: AFK
Status: blocked
Scope: excluded
Scope reason: [ADR-0014](../../../docs/adr/0014-terminal-and-scope.md)。本轮移出组合插件发现、安装、卸载及`/plugin`，独立Skills、Hooks和代理仍按各自任务交付。
Assignee: none
Parent: [完整迁移规格](../spec.md)
Blocked by: [36 — 安装外部技能后立即调用与适配](36-skillinstall.md), [37 — 自定义Markdown命令在TTY展开并续轮](37-customcmd.md), [39 — 自定义代理定义约束真实派发](39-agentdefs.md), [48 — Hook拦截/改写一次工具调用并参与journal](48-hooks.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

两种manifest及skills/commands/agents/hooks联动、命名空间与重启；名称/删除约束插件根。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-562](../module-map.md#mm-562)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [ ] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [ ] [EXT-04](../acceptance-matrix.md#ext-04) — 插件与自定义命令：本票路径覆盖的子案例满足“发现/覆盖及字符串替换等价；安装/删除约束插件根，路径逃逸作为原版缺陷修复记录”。
- [ ] [CMD-plugin](../acceptance-matrix.md#cmd-plugin) — /plugin：本票路径覆盖的子案例满足“已安装插件清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [ ] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [ ] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [ ] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
