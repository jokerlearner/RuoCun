# 03 — 安装开发包并从仓库外调用ruocun

Type: task
Mode: AFK
Status: resolved
Assignee: /root/implement_03_boot
Branch: impl/03-boot
Worktree: .worktrees/i03
Parent: [完整迁移规格](../spec.md)
Blocked by: [D11 — 确定测试、回放与评估的复用门禁](../../ruocun-discovery/issues/11-test-replay-decision.md), [D21 — 确定最小开发工程的已验证工具链](../../ruocun-discovery/issues/21-development-bootstrap-decision.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

版本/帮助与五个已确认开发入口可运行；统一驱动先完成offline最小套件，解锁后续切片。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-305](../module-map.md#mm-305)、[MM-801](../module-map.md#mm-801)、[NEW-11](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：工程。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [ENT-01](../acceptance-matrix.md#ent-01) — 安装后的启动/版本/帮助：本票路径覆盖的子案例满足“名称 RuoCun、版本一致，资源可读，退出码正确”。
- [x] [TEST-07](../acceptance-matrix.md#test-07) — 已确认入口的工程落地：本票路径覆盖的子案例满足“五项入口已获用户确认（见[确认票](01-test-entrypoints.md)）；既有语义seams沿用；工程实现及执行仍须实际验证，不因确认即宣称可运行”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

修复实现提交`90efe4f7a271c8c39f9fc6d35479bdeed6813028`，独立复核`d80586ec18999e8975a75b5ea80d3eaeb51faeb4`已快进集成。见[初轮实现](../evidence/03-boot/README.md)、[修复实现](../evidence/03-boot/r2/README.md)、[独立初轮失败](../integration-evidence/03-boot/README.md)及[独立修复通过](../integration-evidence/03-boot/r2/README.md)。修复后默认pytest29 passed/3 deselected，Ruff、mypy11文件、build和pipcheck通过；仓库外空venv只装最终wheel，offline4 passed，四项真实owned-child故障/取消边界另经独立验证。原来源12项输入核hash不变，修复轮未重复跑；来源/产品/真实模型/终端分别记录，真实模型0，未代填HITL。

## Comments

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：按真实信息依赖将完整发布D12前置细化为最小开发工具链D21；本票的版本/帮助和offline工程入口不依赖完整OS沙箱。D12、60/61、78–85和完整规格门禁保持原范围，D21未resolved前本票仍blocked。

- 2026-11-05：D11/D21已resolved，按真实frontier领取，开始正式工程实现。Ruff/mypy仅元数据阶段，须本票实际安装/运行；读D21拒绝记录，不重试被拒复合helper，必要步骤若被拒保留并上报。

- 2026-11-05：首次独立复核25c56bc发现P-01清理/退出码证据缺陷，修复90efe4f并独立复验d80586e后接收；保留所有失败raw，不把版本/帮助工程通过当Agent/完整发布通过。按用户最新要求完成本票后交接WorkBuddy，本会话不启动04。
