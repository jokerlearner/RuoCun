# 53 — 搜索激活工具并消费MCP资源/提示更新

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Parent: [完整迁移规格](../spec.md)
Blocked by: [51 — 模型调用stdio MCP工具并得到结果](51-mcpstdio.md), [21 — 终端/REPL问题与用户消息可往返](21-usertools.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

前5可见/延迟搜索、resources/prompts、listChanged/elicitation与toggle/reconnect可演示。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-496](../module-map.md#mm-496)、[MM-693](../module-map.md#mm-693)、[MM-733](../module-map.md#mm-733)。

## 共享接口与并行

接口领域：工具/协议。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-09](../acceptance-matrix.md#ext-09) — MCP 能力/可见性：本票路径覆盖的子案例满足“前5自动可见其余搜索，schema原样；结果格式按oracle；UI未绑定elicitation拒绝；不凭SDK推断未接线能力”。
- [x] [TOOL-ToolSearch](../acceptance-matrix.md#tool-toolsearch) — ToolSearch：本票路径覆盖的子案例满足“搜索激活 MCP 和延迟内置工具；无 MCP 也注册；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-mcp](../acceptance-matrix.md#cmd-mcp) — /mcp：本票路径覆盖的子案例满足“列表、重连、开关与 add；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

普通入口与独审已通过。见[53实现](../../ruocun-next24h/evidence/n53-mcp-caps/README.md)，真实resources/prompts、前5可见与搜索、listChanged、elicitation、原生add确认；53两项＋51/52七项共9 passed，Ruff/Mypy通过。独审另跑来源两项，并用普通 `/mcp` 验证列表、开关、重连和原生私密配置写回。[独审回执](../../ruocun-next24h/evidence/review/b05-caps-paused-review.md)。保留冻结add禁用名连接的已知不一致，54恢复出口单独验收。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
