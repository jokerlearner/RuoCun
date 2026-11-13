# 85 — 核验本轮覆盖并完成用户交付验收

Type: task
Mode: HITL
Status: resolved
Scope: reduced
Assignee: none
Parent: [完整迁移规格](../spec.md)
Blocked by: [84 — Python安装产物跑本轮Windows集成门禁](84-winintegrate.md), [83 — 交付可重建产物、使用恢复文档和许可清单](83-docsrelease.md), [D14 — 核验地图已足以生成完整迁移规格](../../ruocun-discovery/issues/14-spec-readiness-check.md), [77 — 最终产品完成Windows Terminal真实操作验收](77-wtaccept.md), [78 — 本轮Windows能力及不支持边界最终验证](78-wincaps.md)
用户体验验收：accepted

## What to build

逐项核对805个来源成员、215个案例族及来源脚本的实际处置。保留项须有对应实现、来源测试及结果。20/37/50/75/80保留历史编号、来源和原任务状态，并登记范围决定。用户验收本轮保留的Windows能力、标准Python包及完整TUI。按平台记录实际结果。[ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md) · [ADR-0014](../../../docs/adr/0014-terminal-and-scope.md)

范围以规格和当前范围决定为准，接续以实施进度记录为准。[规格](../spec.md) · [实施进度](../implementation.md)

## Context pointers

77/78仍是本票完整人工验收依赖，不使用自动出口覆盖；可单独报告本轮实现及自动门禁完成、HITL待验，最终resolved仍等用户accepted及交付确认。V2已取消20%/30%量化性能保证与正式采样门禁，原PKG-07性能子项保留历史及移出处置，不回填达标；明显卡顿、失控内存、取消或稳定性缺陷仍须修复。

从项目AGENTS、CONTEXT和相关ADR开始，读取[完整规格](../spec.md)、[模块对应表](../module-map.md)及[验收矩阵](../acceptance-matrix.md)。
来源为[唯一冻结快照](../../ruocun-discovery/reference/README.md)，必须读取本票对应原版源码和测试；实际路径在对应表定位，不从活动DAO取新版本。

对应条目：[MM-483](../module-map.md#mm-483)。

## 共享接口与并行

接口领域：HITL/证据。主代理统筹共享契约、任务状态、对应表与验收矩阵；实现子代理只改自己的分支/worktree及本票实现、测试、证据。
前置未满足不得执行。本票与无依赖关系的票可在接口稳定后并行；若需改变共享接口，先向主代理报告具体差异，按兼容扩展/迁移/收缩组织，不在多个分支各自重定义。

## Acceptance criteria

- [x] 本票完整路径可实际运行或演示，有独立来源的预期和明确失败/取消边界；不以占位返回或只声明接口算完成。
- [x] [PKG-07](../acceptance-matrix.md#pkg-07) — 核对79张有效票的交付范围、来源证据、Windows验证与用户确认。逐项核对20/37/50/75/80的移出记录及原有缩减。其它平台实机状态保持pending。
- [x] PKG-07.perf-startup / perf-dispatch / perf-store / perf-terminal的旧量化保证按V2登记本轮移出且非通过；本轮仅记录有依据的有限观测，明显卡顿、失控内存、取消失效等功能问题已修复，不作20%/30%达标声明。
- [x] 在已确认T-N入口和现有语义seam上执行TDD，保存可核实的red→green；相关原版测试/fixture随功能迁移，避免测试当前实现的自证断言。
- [x] 更新本票独有的证据，注明环境、源码/依赖版本、命令、输入/预期/实际及清理结果；产品自动、真实模型和终端体验不混为同一通过状态。
- [x] 合并最新集成分支到本分支，完成相关回归并本地提交；交主代理集成和状态验收，不能自行代填用户体验。

跨票母案例按本票路径展开子ID；本票完成不表示整族或全量规格通过。源故障、迁移回归、确认差异、环境无效和未验证分别记录。

## 验证证据

2026-11-12 已复跑 [D14 清单核对](../../ruocun-discovery/evidence/b09-d14/audit-map.py)，逐个核对了冻结归档的 805 个成员及其对应行、215 个案例族的责任票和任务图。84 个历史任务的依赖无环，有效范围为 79 票。20、37、50、75、80 的原始状态和排除理由分别保留在各票；仅由排除票拥有的案例为 `CMD-plugin`、`EXT-04`、`PKG-02`、`PKG-03`、`TEST-04`、`TOOL-NotebookEdit`。V2 的四个正式量化子项仍按范围移出登记。[D14 原始回执](../../ruocun-discovery/evidence/b09-d14/b09-d14-audit/stdout.bin) · [范围决定](../../../docs/adr/0014-terminal-and-scope.md)

374 个来源验证资产已按路径和职责对照冻结清单。58 个来源脚本包括 5 个确定性脚本、2 个 live 运行时脚本、38 个模型专题、4 个记忆/缓存/反思脚本、1 个协议诊断、3 个预览、3 个 VHS 演示、1 个欢迎资源生成和 1 个版本同步。保留的离线语义读取各负责票的产品验证回执，具体入口见 [D11 源资产分类](../../ruocun-discovery/research/11-test-replay-gates.md#资产处置与拥有任务)、[离线运行时](../../ruocun-next24h/evidence/batch-09/eval/n76/README.md)、[记忆与缓存](../../ruocun-next24h/evidence/batch-09/eval/n73/README.md)、[反思](../../ruocun-next24h/evidence/batch-09/eval/n74/README.md)及[最终终端](../../ruocun-next24h/batch-final.md)。模型专题及 live 脚本保留来源和协议，实际调用结果按 V1 记录。欢迎帧随包可用，外部 PNG/生成清单和独立授权仍按 E-02 记录。版本由 Python 包和 CLI 核对。[发布说明](../../../docs/release/batch-09.md)

83、84、D14、77、78 均已结题。用户确认最终 Windows 体验正常，实际重启、同一会话和凭据清理的回执齐全。79 张有效任务均通过，PKG-07 通过。固定 b09-r4 标准 wheel/sdist 已核对摘要及 309 个实际安装成员。macOS 实机、完整 POSIX 安装运行、其它 Windows 本地账户安全负例及托管 CI 按实际状态保留待验。[当前实机记录](../../ruocun-next24h/batch-final.md)

## Comments

- 2026-11-10：用户按表批准九项缩减，保留75/80历史票但本轮excluded，不将范围取消充作完成；85仍须当前范围的真实证据和用户确认，现为blocked/HITL pending。

- 2026-11-05：用户确认84张任务拆分并授权持续实施；从02开始发布，保留已解决01号确认票。前置满足才进入frontier。
