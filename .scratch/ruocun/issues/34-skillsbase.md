# 34 — 加载技能及8个core技能并按需调用

Type: task
Mode: AFK
Status: resolved
Assignee: /root
Branch: integration/ruocun-migration
Worktree: .
Parent: [完整迁移规格](../spec.md)
Blocked by: [08 — 模型用TodoWrite和Read完成首个工具回合](08-readloop.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

frontmatter/slug/namespace/覆盖、模型与手动调用及资源根包装，全部core文本golden一致。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-606](../module-map.md#mm-606)、[MM-616](../module-map.md#mm-616)、[MM-705](../module-map.md#mm-705)。

## 共享接口与并行

接口领域：独立。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-01](../acceptance-matrix.md#ext-01) — Skills 解析与发现：本票路径覆盖的子案例满足“元信息/正文分离、model/user invocable、命名空间及用户→项目覆盖按oracle；不擅自扩大YAML方言”。
- [x] [TOOL-Skill](../acceptance-matrix.md#tool-skill) — Skill：本票路径覆盖的子案例满足“按名加载技能正文；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-skills](../acceptance-matrix.md#cmd-skills) — /skills：本票路径覆盖的子案例满足“列表/选择器、单项禁用及 bundled 批量控制；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [SKILL-simplify](../acceptance-matrix.md#skill-simplify) — core skill simplify：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-debug](../acceptance-matrix.md#skill-debug) — core skill debug：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-make-plan](../acceptance-matrix.md#skill-make-plan) — core skill make-plan：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-verify](../acceptance-matrix.md#skill-verify) — core skill verify：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-code-review](../acceptance-matrix.md#skill-code-review) — core skill code-review：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-deep-research](../acceptance-matrix.md#skill-deep-research) — core skill deep-research：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-fewer-permission-prompts](../acceptance-matrix.md#skill-fewer-permission-prompts) — core skill fewer-permission-prompts：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] [SKILL-run-skill-generator](../acceptance-matrix.md#skill-run-skill-generator) — core skill run-skill-generator：本票路径覆盖的子案例满足“冻结正文/元信息/调用包装保持；simplify与命令优先级按入口oracle；不将59当任意环境恒定总数”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

本票自动技术出口已通过。静态发现、8个core原文、模型/手动正文与资源根沿A证据；原生禁用、单项/批量控制、选择取消及TTY专用simplify优先已独审并接入固定包。动态发现与安装分别归35/36。

[N1统一集成](../../ruocun-next20h/evidence/n1-integration/README.md)：固定产品a7d803c/r1，复验源896ecaf，1154项通过、3项排除，默认mypy108、Ruff、offline、构建、121成员实际安装与独审均通过。首轮失败及最小隔离修复原样留证。结题仅覆盖本票子路径，人工体验不代填。

历史模块检查点：完整目录/单项/内置及installed批量控制与文字选择模块dbeee64已独审，10来源/必要适配及mypy2通过，见[控制模块](../../ruocun-next20h/evidence/n0-skills-controls/README.md)、[独审](../../ruocun-next20h/evidence/review/n1-permissions-b-controls-review.md)。实际TTY专用simplify优先级/选择器与管道列表路由在途，最终包/出口未通过前34保持claimed，35/36不由此解锁。

以下领取/早期未执行文字为历史，当前正式出口仍以上述状态与最新回执为准。

2026-11-11：08固定r2自动出口与独审已通过，主协调按ADR-0013领取本票；实际实现及回执待本票执行，领取不等于通过。起点70c7464及其N0证据收口提交；共享文件由root单点拥有。

待执行；当前未实现/未验收。禁止仅因任务已发布而标为完成。

## Comments

- 2026-11-11：阶段A静态发现/8core/按需正文、模型及手动调用、启动paths扫描/只读禁用集已实现并局部独审；普通入口定向通过。/skills当前仅文字列表，选择/取消/单项与bundled控制仍需N0补齐；原票不resolved，35/36不得据分片解锁。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
