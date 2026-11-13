# 27 — 在worktree修改文件并用检查点回退

Type: task
Mode: AFK
Status: resolved
Assignee: /root/n24_terminal
Branch: codex/n24-terminal
Parent: [完整迁移规格](../spec.md)
Blocked by: [10 — 编辑文件并在崩溃后识别未知副作用](10-editjournal.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

进入/退出/嵌套工作区边界正确；shadow检查点恢复前存快照，未提交/忽略/大文件行为有证据。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-432](../module-map.md#mm-432)、[MM-588](../module-map.md#mm-588)、[MM-635](../module-map.md#mm-635)、[MM-645](../module-map.md#mm-645)。

## 共享接口与并行

接口领域：存储/平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [RUN-08](../acceptance-matrix.md#run-08) — worktree 隔离：本票路径覆盖的子案例满足“Git边界/路径/权限正确；remote 原为worktree不能宣称真远程；未提交用户改动不被清理”。
- [x] [REC-13](../acceptance-matrix.md#rec-13) — 工作区检查点：本票路径覆盖的子案例满足“聊天/代理/影子Git三类检查点分开；回退前保存；范围可解释、不误删用户外部数据”。
- [x] [TOOL-EnterWorktree](../acceptance-matrix.md#tool-enterworktree) — EnterWorktree：本票路径覆盖的子案例满足“当前代理进入隔离树，记录 previousCwd；不允许叠加进入；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [TOOL-ExitWorktree](../acceptance-matrix.md#tool-exitworktree) — ExitWorktree：本票路径覆盖的子案例满足“keep/remove，丢弃有改动或新增提交需 discard_changes；恢复 cwd；schema/描述/required/默认/可见性与冻结 oracle 一致；失败保留可配对工具结果；副作用不盲重放”。
- [x] [CMD-diff](../acceptance-matrix.md#cmd-diff) — /diff：本票路径覆盖的子案例满足“工作区 Git 未提交差异；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-rewind](../acceptance-matrix.md#cmd-rewind) — /rewind：本票路径覆盖的子案例满足“按用户消息截断；显式 code 时关联工作区检查点；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] [CMD-restore](../acceptance-matrix.md#cmd-restore) — /restore：本票路径覆盖的子案例满足“工作区恢复前先建自动快照；查询命令不无故暂停；操作命令按 pause→settled；无副作用重复提交幂等性按来源判断”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

工作树的真实 Git 入口、退出保留、身份校验和显式丢弃通过定向验证。影子快照独立于真实 Git，恢复前保存当前状态。普通终端验证 `/rewind 2 code`、`/restore` 与 `/diff`，恢复可逆且真实 HEAD、索引字节未变。独审复验未提交/独有提交、工作树身份变化和未管理文件碰撞，确认保留原数据。41可消费已验证的工作区端口。[实现证据](../../ruocun-next24h/evidence/batch-02/n27/README.md) · [独立核验](../../ruocun-next24h/evidence/review/b02-worktree-review.md)

## Comments

- 恢复17的依赖链时核对10已resolved，27与38独立并行。实现负责人写worktree、影子Git及工具模块，主协调负责会话与权限接线。41继续等待27完整出口。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
