# 74 — 执行反思验收并识别正控/失败

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b09-eval
Parent: [完整迁移规格](../spec.md)
Blocked by: [42 — 长任务触发反思并在恢复后继续](42-reflect.md), [72 — 运行一个评估任务并生成可评分轨迹](72-evalrunner.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

来源reflect评估fixture/grade/正控与报告可跑，模型质量不以字符串golden代替。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-430](../module-map.md#mm-430)、[MM-413](../module-map.md#mm-413)、[MM-353](../module-map.md#mm-353)、[MM-225](../module-map.md#mm-225)、[MM-224](../module-map.md#mm-224)。

## 共享接口与并行

接口领域：证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TEST-03](../acceptance-matrix.md#test-03) — 回放与评估入口：本票路径覆盖的子案例满足“区分确定性/联网/live/第三方；入口替换、评分/超时/样本污染与环境无效如实记录”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

六个冻结场景通过真实回环评估入口验证。正常、报警、误判和无效 JSON 分别登记，非法 NaN 从计分集合移出，advisory 在进入 judge 与写报告前脱敏。独立复跑通过，真实模型反思质量待单独验证。[来源、红绿和类型检查](../../ruocun-next24h/evidence/batch-09/eval/n74/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
