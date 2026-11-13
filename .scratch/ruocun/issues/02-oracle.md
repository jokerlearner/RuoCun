# 02 — 隔离运行冻结参考并生成一条可比对轨迹

Type: task
Mode: AFK
Status: resolved
Assignee: /root/implement_02_oracle
Branch: impl/02-oracle
Worktree: .worktrees/impl-02-oracle
Parent: [完整迁移规格](../spec.md)
Blocked by: none
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

用受控配置/Git fixture跑通参考任务，产请求/schema/结果与原故障分类；解锁所有迁移oracle。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-483](../module-map.md#mm-483)、[MM-305](../module-map.md#mm-305)、[MM-805](../module-map.md#mm-805)。

## 共享接口与并行

接口领域：证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [TEST-01](../acceptance-matrix.md#test-01) — 来源断言迁移：本票路径覆盖的子案例满足“没有漏项或无理由跳过；未执行来源行为不写passed，材料缺失先物化受控fixture”。
- [x] [TEST-02](../acceptance-matrix.md#test-02) — 离线/协议确定性：本票路径覆盖的子案例满足“优先现有高层CLI与协议，缺实模型不造测试答案；不读真实用户配置/凭据”。
- [x] [TEST-05](../acceptance-matrix.md#test-05) — 故障归因：本票路径覆盖的子案例满足“SOURCE-DEFECT/PORT-REGRESSION/INTENTIONAL-DELTA/ENV/UNVERIFIED分开；原故障不稀释迁移完成门禁”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

实现提交f99ae1ef，独立merger提交eefab839已接收。见[本票证据](../evidence/02-oracle/README.md)和[驱动说明](../../../tests/support/oracle/README.md)。独立pytest 12 passed；Node22的6个来源文件190 passed；90绑定文件与Git blob一致，805来源成员无变。真实模型调用0、port未运行；Node24退出失败按ENV保留。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：主代理按已满足的前置领取，分派给/root/implement_02_oracle；用户已授权独立worktree及已确认入口上的TDD。

- 2026-11-05：独立merger复验通过，主集成分支已快进eefab839，本票路径完成并resolved。遗留Temp目录pytest-1612因自动审查拒绝删除而保留；进程/服务已关闭。产品功能与其余TEST母案例未标全量通过。
