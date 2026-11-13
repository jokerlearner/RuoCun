# 28 — 多模型用量与本次运行费用/预算

Type: task
Mode: AFK
Status: resolved
Scope: reduced
Assignee: /root/n24_permissions
Branch: codex/n24-permissions
Worktree: .worktrees/n24-permissions
Batch: 03
Parent: [完整迁移规格](../spec.md)
Blocked by: [07 — 保存一次会话并拒绝并发owner写入](07-store.md), [05 — 通过Responses路由完成同一对话/工具回合](05-responses.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

cache归一、当前运行的模型桶、价格/硬停/轮数及context-window覆盖生效。R1取消跨重启分模型费用完整连续：保留来源四项累计token、消息、模型、模式与标题；恢复后费用只累计新产生部分，历史费用明确标为不完整，费用预算据此口径重新计数，不能显示为整段历史的总费用或硬上限。

范围依据：[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md)。本票命令、预算与必要保存恢复接线仍须实现，当前claimed及既有19项基础测试证据不变；本次不恢复开发。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-426](../module-map.md#mm-426)、[MM-590](../module-map.md#mm-590)、[MM-586](../module-map.md#mm-586)、[MM-600](../module-map.md#mm-600)。

## 共享接口与并行

接口领域：模型/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIRE-06](../acceptance-matrix.md#wire-06) — usage/缓存/费用：原字段优先、miss非负；来源累计token保留；本次运行按模型累计费用，不保证跨重启历史费用完整，摘要明确标注统计范围；不保证供应商命中率。
- [x] [WIRE-11](../acceptance-matrix.md#wire-11) — 预算与轮数：本票路径覆盖的子案例满足“默认主轮数无上限、子代理规则和硬停开关精确保留；完成不等于质量验收”。
- [x] [REC-07](../acceptance-matrix.md#rec-07) — 本轮会话状态：保留已选范围内的必要恢复状态与累计token；分模型费用跨重启连续已移出，重启后的费用/预算起点及历史不完整提示真实；缓存本地元数据可重建且不误报。
- [x] [CMD-cost](../acceptance-matrix.md#cmd-cost) — /cost：本票路径覆盖的子案例满足“用量、缓存与费用统计；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-effort](../acceptance-matrix.md#cmd-effort) — /effort：本票路径覆盖的子案例满足“思考强度查询/设置并应用后续请求；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-context-window](../acceptance-matrix.md#cmd-context-window) — /context-window：本票路径覆盖的子案例满足“查询、K/M 解析/设置、手动锁定窗口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-status](../acceptance-matrix.md#cmd-status) — /status：本票路径覆盖的子案例满足“运行状态/模式/预算显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

Session／费用基础已局部实现，候选`c8b30e3e06f1a4d1f8214e3e80100c8295bbe04b`经主协调在独立worktree复核并集成`f51d214`。10项Session＋9项cost来源语义测试均通过；独立Ruff/mypy、sdist→wheel构建与非editable安装通过，详见[实现](../evidence/28-context/session-cost/README.md)及[独立复核](../integration-evidence/session-cost/README.md)。价格保留冻结数据，无模型调用。

批次03补齐普通入口真实权限模式和模型请求缓存前缀归因，重开保留累计 token，本次费用与硬预算从新进程重新计数。普通 CLI 重开、查询无模型副作用及来源缓存断言独立复核通过。跨重启完整费用口径沿 R1。[候选证据](../../ruocun-next24h/evidence/n28-cost/README.md)

## Comments

- 2026-11-11：原内存基础之外，阶段A已接本次费用/预算/轮数、cache_audit、窗口及文字cost/usage/context/status/effort；模块独审/17项CLI定向通过，整票剩余案例及最终批出口待收口。历史“命令未接/29未启动”仅为当时保存点。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-10：用户按表缩减R1，仅收缩跨重启费用保证；实际代码、既有证据和完成状态不变。恢复后的费用阈值不再冒充历史全会话总额限制，见ADR-0010。

- 2026-11-10：按用户最新停止边界只收口上述基础小模块；实际addUsage仅来源签名，不提供早期讨论的请求去重或Checkpoint桥。所有自有工程进程退出，原worktree/环境保留；重新实施前核对用户恢复授权和集成代码。

- 2026-11-10：07与05前置已resolved，主协调领取本票为E01首票，派/root/e01_context到codex/e01-context；29待08及28独立接收后才实施。本票单点负责Session和费用持久状态的兼容扩展，方法/字段沿冻结session.ts，先向B01给出稳定契约及可消费提交；不改agent/loop、client或07平台。测试按ADR-0009沿来源，不扩额外用例。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
