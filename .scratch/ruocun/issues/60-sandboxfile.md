# 60 — 沙箱按来源路由并准确报告平台能力

Type: task
Mode: AFK
Status: resolved
Assignee: codex/b08-platform
Parent: [完整迁移规格](../spec.md)
Blocked by: [14 — 前台Shell输出及整个受管进程树可取消](14-shell.md)
用户体验验收：not-required（最终体验由对应HITL票验收）

## What to build

按DAO sandbox.ts迁移默认关闭、disableSandbox、Seatbelt/bwrap文件隔离路由及缺工具错误；Windows显式启用返回不支持，未启用按普通Shell运行。启用不可用明确拒绝，Job不冒充沙箱。来源行为及平台差异见[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)。

## Context pointers

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-698](../module-map.md#mm-698)、[NEW-08](../module-map.md#新增适配层候选位置)。

## 共享接口与并行

接口领域：平台。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [WIN-09](../acceptance-matrix.md#win-09) — OS文件/网络隔离：本票路径覆盖的子案例满足“按ADR-0008沿用DAO平台能力；Windows启用时明确不支持，普通Shell不冒充隔离；支持平台与实机状态单列”。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

[批末集中验收](../../ruocun-next24h/evidence/batch-08/integration/README.md)通过。
[批次08实施回执](../../ruocun-next24h/evidence/batch-08/n60/README.md)。候选 `2ef88089` 已独立复核，和共享一次性审批 `45db2f6c` 集成。Windows 实际前后台显式启用拒绝，普通命令及受审批前台绕过可执行。已有 Ubuntu WSL 实测区内写、区外读及区外写拒绝。macOS Seatbelt 路由按冻结来源参数核对，实机待验证。

## Comments

- 2026-11-10：[ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md)按用户新要求模仿DAO，撤销新增Windows隔离后端和D22前置；Linux/macOS路由、缺工具、默认关闭和Windows显式拒绝仍待实际实现/验证，状态保持blocked，不将范围修订当作通过。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。

- 2026-11-05：D10公共端口可用不表示完整backend达标；22作为精确新增前置，已知WRITE_DAC缺口不能以xfail或普通Shell回落代替本票验收。
