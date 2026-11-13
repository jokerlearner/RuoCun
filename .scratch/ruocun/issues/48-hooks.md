# 48 — Hook拦截/改写一次工具调用并参与journal

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_permissions
Branch: codex/b04-hooks
Parent: [完整迁移规格](../spec.md)
Blocked by: [10 — 编辑文件并在崩溃后识别未知副作用](10-editjournal.md), [24 — 自动权限分类失败时保守询问并留审计](24-autoperm.md), [14 — 前台Shell输出及整个受管进程树可取消](14-shell.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

5事件、顺序/matcher/if/stdin/out/exit2/timeout；updatedInput最终裁决、prehook只跑一次。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-477](../module-map.md#mm-477)、[MM-642](../module-map.md#mm-642)。

## 共享接口与并行

接口领域：工具/权限/存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [EXT-06](../acceptance-matrix.md#ext-06) — Hook 选择与命令协议：本票路径覆盖的子案例满足“顺序附加；仅command实际执行；stdin字段/args字符串、exit2、block/context/input/permission按事件消费”。
- [x] [RUN-06](../acceptance-matrix.md#run-06) — 审批与 prehook 一次性：本票路径覆盖的子案例满足“hook只执行一次，最终参数用于 gate/审计/handler；deny也返回对应结果；hook自身副作用journal”。
- [x] [CMD-hooks](../acceptance-matrix.md#cmd-hooks) — /hooks：本票路径覆盖的子案例满足“实际载入 Hook 清单；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

命令协议、Pre/Post 工具执行、最终参数审批及普通 /hooks 入口通过。独立复验确认超时整树停止，Pre 回执未知后不进入审批或 handler，Post 回执未知时原工具结果仍可配对。会话及子代理生命周期见49。完整 JS RegExp 兼容尚无验证。[实现证据](../../ruocun-next24h/evidence/n48-tool-hooks/README.md) · [进程复核](../../ruocun-next24h/evidence/review/b04-native-hook-review.md) · [工具权限和恢复复核](../../ruocun-next24h/evidence/review/b04-hook-tool-review.md) · [普通入口](../../ruocun-next24h/evidence/batch-04/ordinary/README.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
