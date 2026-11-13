# 26 — 继续/切换/分支/命名和导出聊天

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [11 — 忙时排队、暂停及取消流不会污染新轮](11-scheduler.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

同cwd最近未完/显式ID筛选；分支不复制后台，清理不删活会话，导出可读。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-595](../module-map.md#mm-595)、[MM-600](../module-map.md#mm-600)、[MM-392](../module-map.md#mm-392)。

## 共享接口与并行

接口领域：存储。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [REC-04](../acceptance-matrix.md#rec-04) — 会话筛选/切换：本票路径覆盖的子案例满足“列表排序/continue精确；存在活owner/运行代理时拒危险切换；done判据不漏后台未决”。
- [x] [REC-14](../acceptance-matrix.md#rec-14) — 分支/导出/清理：本票路径覆盖的子案例满足“分支聊天不复制运行副作用；清理不得删除活动/可恢复数据；修复源mtime风险单列差异”。
- [x] [CMD-session](../acceptance-matrix.md#cmd-session) — /session：本票路径覆盖的子案例满足“当前会话身份、保存与状态；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-resume](../acceptance-matrix.md#cmd-resume) — /resume：本票路径覆盖的子案例满足“列表/显式会话切换、活 owner 与运行代理保护；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-branch](../acceptance-matrix.md#cmd-branch) — /branch：本票路径覆盖的子案例满足“复制聊天分支；不重复启动原后台副作用；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-rename](../acceptance-matrix.md#cmd-rename) — /rename：本票路径覆盖的子案例满足“会话标题保存及重启一致性；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-export](../acceptance-matrix.md#cmd-export) — /export：本票路径覆盖的子案例满足“会话 Markdown 导出与路径显示；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-clear](../acceptance-matrix.md#cmd-clear) — /clear：本票路径覆盖的子案例满足“清空当前上下文，保留明确的会话生命周期处理；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

普通会话切换/分支/命名/清空/导出、Hooks生命周期及活动owner保护独审通过，来源4项通过；真实流中断后paused/未完成及latest原ID恢复已独立验证。清理先封执行权，再按身份处置，保留所有活动/未决及附件引用材料。[实现](../../ruocun-next24h/evidence/batch-05/n26/README.md) · [独审](../../ruocun-next24h/evidence/review/b05-sessions-review.md)

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
