# 66 — 在终端审批/回答问题并选择账户或技能

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [65 — 内联转录、中英文主题及scrollback稳定](65-tuirender.md), [21 — 终端/REPL问题与用户消息可往返](21-usertools.md), [24 — 自动权限分类失败时保守询问并留审计](24-autoperm.md), [35 — 文件访问动态激活/禁用条件技能](35-skillsdynamic.md), [58 — Windows系统凭据存取及fallback可用于请求](58-credentials.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

焦点/模态Esc/单多选/永许/拒绝/模型账户选择，生效后实际后续请求与权限正确。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-747](../module-map.md#mm-747)、[MM-776](../module-map.md#mm-776)、[MM-453](../module-map.md#mm-453)。

## 共享接口与并行

接口领域：终端。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WT-06](../acceptance-matrix.md#wt-06) — 面板/快捷键/审批：本票路径覆盖的子案例满足“焦点与模态层级正确，无stdin竞争，选择/拒绝和状态反馈一致”。
- [x] [CMD-model](../acceptance-matrix.md#cmd-model) — /model：本票路径覆盖的子案例满足“模型查询/切换、provider/账户约束及持久化；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-account](../acceptance-matrix.md#cmd-account) — /account：本票路径覆盖的子案例满足“账户列表/选择/新增/删除/切换；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-accounts](../acceptance-matrix.md#cmd-accounts) — /accounts：本票路径覆盖的子案例满足“账户别名入口；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

用户在真实 Windows Terminal 完成问答方向键、空格多选、提交及账户面板 Esc，焦点返回正常。合成HTTP的账户/模型选择、审批owner与回执未明边界已独审；对比度修复后的普通输入实机通过。完整体验归77。[独审](../../ruocun-next24h/evidence/review/b02-modals-notify-review.md) · [实机回执](../../ruocun-next24h/evidence/n18/wt/runs/20261111T075358Z-ea4e4c/README.md)

批次02面板候选已实现：同owner审批排队/取消、单多选/自填/讨论、通用Select、账户/模型UI动作壳、Skills快捷开关、Shift+Tab及注入式KeyWizard。11项DAO来源语义用例、9源静态检查通过；发现同输入批确认Enter下溢后沿单一红复现修复。普通runtime/backend及审批/账户接缝独审待主协调接续，仍claimed；69不由本候选自行解锁。见[66证据](../../ruocun-next24h/evidence/batch-02/n66/README.md)。

## Comments

- 2026-11-11暂停保存：候选已纳入固定b02-r1，来源/独审及集中工程结果见批次02构建记录。用户要求完成当前构建后暂停，当前不再执行；本票真实Windows Terminal技术范围尚待验，维持在途，不虚报resolved。

- 2026-11-11：用户明确选择当前账户删除后沿用DAO的旧连接，手动切换或重启；配置与进程连接暂时不一致的代价见[ADR-0016](../../../docs/adr/0016-active-account-deletion-parity.md)。原临时等待选择分支已移除，保存确认与未知停机规则保持。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 批次02批内许可：65已形成可调用端口和来源/普通TTY回执，候选3be7fff/cf00bb7/bf49b04及19e5786入口经独审源码0阻断。66可由同一终端负责人在64后接续，65整票与真实终端待验项据实保留。66审批/输入所有权接缝独审集成后，69才消费。
