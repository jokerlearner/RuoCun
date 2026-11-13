# 08 — 模型用TodoWrite和Read完成首个工具回合

Type: task
Mode: AFK
Status: resolved
Assignee: /root
Branch: integration/ruocun-migration
Worktree: D:\java supplement\Firstcode\RuoCun
Batch: N0（原B01候选保留）
Parent: [完整迁移规格](../spec.md)
Blocked by: [07 — 保存一次会话并拒绝并发owner写入](07-store.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

请求→校验/注册→计划与读文件→journal/结果→模型回答；headless首批和非法JSON明确拒绝。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-404](../module-map.md#mm-404)、[MM-642](../module-map.md#mm-642)、[MM-691](../module-map.md#mm-691)、[MM-693](../module-map.md#mm-693)、[MM-702](../module-map.md#mm-702)、[MM-729](../module-map.md#mm-729)、[MM-735](../module-map.md#mm-735)、[MM-736](../module-map.md#mm-736)、[MM-727](../module-map.md#mm-727)、[MM-682](../module-map.md#mm-682)。

## 共享接口与并行

接口领域：工具。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TOOL-Read](../acceptance-matrix.md#tool-read) — Read：本票路径覆盖的子案例满足“文本带行号、offset/limit、图片；二进制/大文件护栏，记录编辑前读取元信息；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-TodoWrite](../acceptance-matrix.md#tool-todowrite) — TodoWrite：本票路径覆盖的子案例满足“整表替换的扁平清单，无独立 task id；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [WIRE-10](../acceptance-matrix.md#wire-10) — 空响应/坏工具 JSON：本票路径覆盖的子案例满足“不把空坏 assistant 永久污染历史；有界修复与诊断，参数非法不调用 handler”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

当前自动出口：固定源码70c7464（产品908cd14）、n0-r2 wheel SHA256 `0cde376cc91c92db98964342f0381d26f5979bfed000147c6453d70672c89692`；687项通过/3项显式排除、五入口/构建/90成员实际安装绑定及独审通过。Read图片、完整Todo、headless首批、空截断和恢复坏JSON均已接普通CLI；[集成回执](../../ruocun-next20h/evidence/n0-integration/README.md)、[独审](../../ruocun-next20h/evidence/review/n0-integration-review.md)。原B01交接和失败证据保留如下，历史停止由ADR-0013授权替代。人工/真实模型/Terminal仍pending；不推定母案例族或34及后继完成。

已保存[未完成交接](../evidence/08-readloop/HANDOFF.md)，分支提交`a6d49237c2cade07199fe2e0307ed6ce27fad7df`。只完成来源阅读和环境准备，产品代码/测试未开始，08保持claimed。开发依赖离线安装成功，editable安装缺少editables失败，细节与合成日志位置见交接；不能由环境准备推定产品可运行。用户要求最后收口28的基础小模块后停止，本票不再执行，09未开始。

## Comments

- 2026-11-11：用户明确“开始执行”，root在f5bc444干净基线按ADR-0013接续N0。主协调拥有loop/runtime/client types/ToolContext；advanced_skills在原私有worktree补Read图片及detectImageFormat，advanced_context临时负责唯一session contract/worker/store/conversation的图片结果兼容扩展；advanced_review先审共享接口，再审候选。当前只消费已审类型后实施，原B01分支/记录保留；09/11/19/34仍等08完整独审集成。

- 2026-11-11：阶段A在MVP前台循环补预算/轮数、有界压缩、Skill注册等接缝，定向17项通过；Read图片/headless等仍按原票逐项核对，未据此结题。 阶段A最终r2自动出口已通过（669项/五入口/独审），原票未因局部覆盖结题。实际实现/源差异/最终结果统一见[阶段A集成](../../ruocun-advanced-a/evidence/integration/README.md)；[后续20小时计划](../../ruocun-next20h/plan.md)已批准，人工仍单列pending。

- 2026-11-10：07已独立接收并resolved，主协调按真实frontier领取本票为B01首票；派/root/b01_tools到codex/b01-tools。09仅为同领域下一票，未满足前置不得实施。Session由并行28单点实现，沿冻结session.ts共享契约，08不另造Session/StoragePort；只消费已稳定的07端口。源码优先和测试范围按ADR-0008/9。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
