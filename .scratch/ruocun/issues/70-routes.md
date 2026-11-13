# 70 — 全部CLI参数/slash按入口正确路由并收尾

Type: task
Mode: AFK
Status: resolved
Assignee: /root
Branch: integration/ruocun-migration
Parent: [完整迁移规格](../spec.md)
Blocked by: [44 — 内置命令与长任务目标驱动后续工具轮](44-builtin.md), [26 — 继续/切换/分支/命名和导出聊天](26-sessions.md), [25 — 通过工具和命令调整配置并影响后续轮](25-configtool.md), [53 — 搜索激活工具并消费MCP资源/提示更新](53-mcpcaps.md), [55 — 模型在Windows正确导航代码位置](55-lsp.md), [69 — 首次终端引导完成账户/语言/信任配置](69-onboarding.md), [67 — 任务面板/历史展开与Ctrl+B后台操作](67-tuitasks.md), [59 — 系统定时创建/查询/删除并真实触发](59-schedule.md), [57 — 查看脱敏审计与可选观测轨迹](57-obs.md), [22 — 网页抓取](22-webfetch.md), [23 — 网页搜索](23-websearch.md), [42 — 长任务反思](42-reflect.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按来源52个固定命令及别名盘点。对保留的命令逐项核对TTY、REPL与无头模式中的行为。查询保持当前运行，状态变更先暂停并等待当前操作收尾，退出时清理资源。`/plugin`、操作员`plugin`入口和自定义Markdown模板移出。保留内置命令、原生Skills调用和完整TUI的命令交互。[ADR-0014](../../../docs/adr/0014-terminal-and-scope.md)

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-483](../module-map.md#mm-483)、[MM-568](../module-map.md#mm-568)、[MM-448](../module-map.md#mm-448)、[MM-451](../module-map.md#mm-451)、[MM-564](../module-map.md#mm-564)、[MM-470](../module-map.md#mm-470)、[MM-472](../module-map.md#mm-472)。

## 共享接口与并行

接口领域：组合根。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [ENT-03](../acceptance-matrix.md#ent-03) — TTY/REPL/一次性入口：本票路径覆盖的子案例满足“按来源入口能力运行；headless 首工具批包含 TodoWrite；keepAlive 等真实后台完成”。
- [x] [ENT-04](../acceptance-matrix.md#ent-04) — CLI 参数与操作员命令：本票路径覆盖的子案例满足“大小写/未知参数 oracle 单列；帮助不充当实现证据；不得误吞 prompt”。
- [x] [ENT-06](../acceptance-matrix.md#ent-06) — 退出与资源收尾：本票路径覆盖的子案例满足“保存状态，关闭该关闭的进程/扩展/终端；保留后台时可恢复且无无主执行”。
- [x] [CFG-08](../acceptance-matrix.md#cfg-08) — 项目指令：本票路径覆盖的子案例满足“DAO 指令顺序/trim 去重沿用；AGENTS 工程规则不自动进入产品；新别名待决”。
- [x] [CFG-10](../acceptance-matrix.md#cfg-10) — 信任与校验/更新：本票路径覆盖的子案例满足“信任范围真实可见，认证错误可修正；更新失败不阻断业务，版本/URL 策略待发布决定”。
- [x] [CMD-help](../acceptance-matrix.md#cmd-help) — /help：本票路径覆盖的子案例满足“对应入口实际可用命令及帮助；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-exit](../acceptance-matrix.md#cmd-exit) — /exit：本票路径覆盖的子案例满足“正常收尾、保存、释放终端与执行资源；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-quit](../acceptance-matrix.md#cmd-quit) — /quit：本票路径覆盖的子案例满足“退出别名；显式 keep-background 时仅保留受支持后台执行；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-doctor](../acceptance-matrix.md#cmd-doctor) — /doctor：本票路径覆盖的子案例满足“账户/依赖/环境自检与平台诊断；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-agents](../acceptance-matrix.md#cmd-agents) — /agents：本票路径覆盖的子案例满足“内置/自定义代理定义清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[本票独审](../../ruocun-next24h/evidence/review/b07-cli-boundary-final-review.md)与[集中交付](../../ruocun-next24h/evidence/batch-07/integration/README.md)已通过。

2026-11-12：42、57、59已实际通过来源/普通入口/独审并集成，解锁本票。根统一持有runtime/cli/loop，A维护命令目录/形状谓词和帮助，B维护来源静态进度提醒；52条清单见批次07n70-command-inventory。71仍等本票真实通过。

普通 CLI、斜杠入口、静态进度提醒及参数安全边界通过定向验证与独审。冻结 52 项清单中保留 51 项，复用既有会话、权限和后台恢复证据。

## Comments

- 2026-11-11：阶段A已接原生/显式兼容产品指令及静态Skills/上下文文字命令子路径；AGENTS不自动注入。原70的其它整合/完整TUI仍后置，未因本子路径完成整票。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-11：批次06启动核实冻结index.ts:293–336,603–607，完整参数/Web注册/eval与反思消费22/23/42；补齐真实依赖，71经70继承。本批不实施70/71。
