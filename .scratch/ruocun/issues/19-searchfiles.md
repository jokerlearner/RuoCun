# 19 — 模型浏览与搜索项目文件

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_context
Branch: codex/advanced-context
Worktree: .worktrees/advanced-context
Parent: [完整迁移规格](../spec.md)
Blocked by: [08 — 模型用TodoWrite和Read完成首个工具回合](08-readloop.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

ListDir/Glob/Grep→模型定位证据；中文路径、正则、分页/上下文/跨行和边界符合oracle。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-655](../module-map.md#mm-655)、[MM-659](../module-map.md#mm-659)、[MM-661](../module-map.md#mm-661)、[MM-664](../module-map.md#mm-664)、[MM-684](../module-map.md#mm-684)、[MM-738](../module-map.md#mm-738)、[MM-662](../module-map.md#mm-662)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-ListDir](../acceptance-matrix.md#tool-listdir) — ListDir：本票路径覆盖的子案例满足“路径目录列表；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-Glob](../acceptance-matrix.md#tool-glob) — Glob：本票路径覆盖的子案例满足“文件/路径 glob，修改时间排序；实际导出变量名 fileSearchTool；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-Grep](../acceptance-matrix.md#tool-grep) — Grep：本票路径覆盖的子案例满足“正则、内容/文件模式、上下文、分页、跨行、类型等；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-files](../acceptance-matrix.md#cmd-files) — /files：本票路径覆盖的子案例满足“已读文件与上下文信息；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票自动技术出口已通过。ListDir/Glob/Grep来源38项、双语和schema及片段边界独审通过；固定包普通入口已消费搜索工具，受控TTY /files通过。已读事实只在本进程，Grep沿已批准Python正则差异。

[N1统一集成](../../ruocun-next20h/evidence/n1-integration/README.md)：固定产品a7d803c/r1，复验源896ecaf，1154项通过、3项排除，默认mypy108、Ruff、offline、构建、121成员实际安装与独审均通过。首轮失败及最小隔离修复原样留证。结题仅覆盖本票子路径，人工体验不代填。

历史模块检查点：ListDir/Glob/Grep与files纯查询候选f06→b2已独审，原38项/mypy4/描述及17字段逐字核对、片段零配额来源差异复验见[19独审](../../ruocun-next20h/evidence/review/n1-plan-n2-search-review.md)。注册/普通模型及files实际入口在途，最终产物待验，19仍claimed。

以下领取/早期未执行文字为历史，当前正式出口仍以上述状态与最新回执为准。

2026-11-11：08已resolved且本票全部前置满足，主协调提前派19旁线；原11仍claimed，由root继续普通入口接线，线二已交scheduler/broker/09叶子模块候选，回修优先。范围仅本票ListDir/Glob/Grep与files实际缺口，复用MVP已有来源证据，不重复实现；父票独审或本票领取不表示本票完成。

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-11：阶段A只补共享walkFiles忽略.ruocun原生状态目录的品牌边界；ListDir、完整Grep及/files仍未收口，不计19完成。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
