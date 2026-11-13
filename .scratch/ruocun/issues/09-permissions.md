# 09 — 按分层权限审批并完成一次文件写入

Type: task
Mode: AFK
Status: resolved
Assignee: /root/advanced_skills
Branch: codex/advanced-skills
Worktree: .worktrees/advanced-skills
Parent: [完整迁移规格](../spec.md)
Blocked by: [08 — 模型用TodoWrite和Read完成首个工具回合](08-readloop.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

deny/ask/allow、plan双层限制、批量/永久允许及无stdin拒绝可演示；仅批准最终参数才实际写。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-434](../module-map.md#mm-434)、[MM-436](../module-map.md#mm-436)、[MM-545](../module-map.md#mm-545)、[MM-547](../module-map.md#mm-547)、[MM-549](../module-map.md#mm-549)、[MM-554](../module-map.md#mm-554)、[MM-560](../module-map.md#mm-560)、[MM-687](../module-map.md#mm-687)、[MM-742](../module-map.md#mm-742)、[MM-437](../module-map.md#mm-437)。

## 共享接口与并行

接口领域：工具/权限。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [PERM-01](../acceptance-matrix.md#perm-01) — 规则和身份：本票路径覆盖的子案例满足“各工具匹配方言与deny>ask>allow；路径canonical化和最终参数一致，非通用fnmatch替换”。
- [x] [PERM-02](../acceptance-matrix.md#perm-02) — 模式裁决：本票路径覆盖的子案例满足“plan优先，提示与API裁剪及执行复核一致；权限拒绝可解释”。
- [x] [CFG-07](../acceptance-matrix.md#cfg-07) — 设置分层：本票路径覆盖的子案例满足“只对参考实际 gated 通道施加现有信任；defaultMode 后覆盖、规则并集；deny > ask > allow”。
- [x] [TOOL-Write](../acceptance-matrix.md#tool-write) — Write：本票路径覆盖的子案例满足“全文创建/覆盖，读前检查、mtime/size 漂移、锁与原子替换；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-EnterPlanMode](../acceptance-matrix.md#tool-enterplanmode) — EnterPlanMode：本票路径覆盖的子案例满足“切换只读规划；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-ExitPlanMode](../acceptance-matrix.md#tool-exitplanmode) — ExitPlanMode：本票路径覆盖的子案例满足“提交方案并退出规划，由上下文处理批准；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-plan](../acceptance-matrix.md#cmd-plan) — /plan：本票路径覆盖的子案例满足“进入/退出只读规划；实际可用工具裁剪；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-mode](../acceptance-matrix.md#cmd-mode) — /mode：本票路径覆盖的子案例满足“模式查询/切换；plan 不混入 auto/bypass 循环；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-bypass](../acceptance-matrix.md#cmd-bypass) — /bypass：本票路径覆盖的子案例满足“显式放行模式与状态一致性；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-yolo](../acceptance-matrix.md#cmd-yolo) — /yolo：本票路径覆盖的子案例满足“放行别名与可见模式；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-permissions](../acceptance-matrix.md#cmd-permissions) — /permissions：本票路径覆盖的子案例满足“规则/模式显示；编辑分支遮蔽另列 SOURCE-CANDIDATE；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票自动技术出口已通过。分层deny/ask/allow、完整Shell安全解析、原生与只读兼容层级、plan双层限制及普通入口最终参数裁决均已核验。来源批量/永久允许在Gate及审批模块验收，实际混合工具批统一预批由12接入；分类器24及Hook改参后置。

[N1统一集成](../../ruocun-next20h/evidence/n1-integration/README.md)：固定产品a7d803c/r1，复验源896ecaf，1154项通过、3项排除，默认mypy108、Ruff、offline、构建、121成员实际安装与独审均通过。首轮失败及最小隔离修复原样留证。结题仅覆盖本票子路径，人工体验不代填。

历史模块检查点：09模块候选A/B及层级模式装配均已独审，来源/JSON/UTF16/退出模式回修及实际范围见[权限独审](../../ruocun-next20h/evidence/review/n1-permissions-a-review.md)、[完整B](../../ruocun-next20h/evidence/review/n1-permissions-b-controls-review.md)、[装配](../../ruocun-next20h/evidence/review/n1-runtime-projection-review.md)。普通入口在途，最终参数/计划硬门模块已验；新包与完整自动出口待收口，09保持claimed。

以下领取/早期未执行文字为历史，当前正式出口仍以上述状态与最新回执为准。

2026-11-11：08固定r2自动出口与独审已通过，主协调按ADR-0013领取本票；实际实现及回执待本票执行，领取不等于通过。起点70c7464及其N0证据收口提交；共享文件由root单点拥有。

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
