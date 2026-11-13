# D14 · 迁移决策地图核验

2026-11-12，D13 已完成。依据冻结快照、现行规格、逐文件对应、验收矩阵与任务图核对。现有路线足以编写和执行完整迁移规格，未发现需要新增架构决定的缺口。[D13 收录](../issues/13-module-sequence-decision.md) · [完整规格](../../ruocun/spec.md)

| CONTEXT 目标 | 规则、执行与可观察验收 |
| --- | --- |
| 1. AI 开发、用户决策及体验 | 协作由 [ADR-0015](../../../docs/adr/0015-batch-validation-and-packaging.md)规定，技术与用户验收分列。人工体验集中 77、78、85。[ADR-0004](../../../docs/adr/0004-final-batch-human-acceptance.md) |
| 2. Python 迁移与完整终端 | 保留完整终端及修订后的能力清单。验收按 ENT、RUN、WT 和 WIN 入口逐项读取。[ADR-0014](../../../docs/adr/0014-terminal-and-scope.md) · [验收矩阵](../../ruocun/acceptance-matrix.md) |
| 3. 保持模块职责和调用关系 | 全部 805 个来源成员均有对应位置和处理方式。组合根、调度、工具分派、持久提交与终端观察分别归属。[模块对应](../../ruocun/module-map.md) · [D13 报告](13-module-sequence-route.md) |
| 4. Python 核心及可替换平台绑定 | D08 固定 asyncio、数据库线程及后台角色。D09 定义存储、扩展协议和兼容读取边界。[D08](../issues/08-python-runtime-decision.md) · [D09](../issues/09-storage-extension-decision.md) |
| 5. Windows 保留能力 | D10 与 ADR-0008 固定终端、IPC、文件和沙箱路线。Windows 系统定时、电源、通知及 OS 沙箱按现行支持边界验收。D22 的原严格路线失败归历史实验。[D10](../issues/10-terminal-windows-decision.md) · [ADR-0008](../../../docs/adr/0008-source-first-sandbox-parity.md) · [ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md) |
| 6. 配置、Skills、Hooks、MCP 兼容 | 原生数据与显式兼容源有固定发现及优先级。原版 MCP 未知结果按已批准规则保留现场。案例归 CFG、EXT、RUN 和相应工具族。[D09](../issues/09-storage-extension-decision.md) · [ADR-0003](../../../docs/adr/0003-mcp-unknown-outcome-no-replay.md) |
| 7. 自身正常恢复及失败边界 | 持久输入、提交和 runner 控制分别检查。原 DAO 会话、历史费用和特殊 fork 恢复按 R1/R3 边界处理。安装更新和数据保护继续由 81 核验。[D09](../issues/09-storage-extension-decision.md) · [ADR-0010](../../../docs/adr/0010-selected-scope-and-lean-workflow.md) |
| 8. Linux/macOS 保留适配 | 82 按平台分别记录导入、构建、可选后端及可用证据。macOS 和完整平台实机按当前支持矩阵单列。[D12](../issues/12-install-release-decision.md) · [82](../../ruocun/issues/82-crossci.md) |
| 9. 测试与标准包交付 | D11 登记 374 项资产，D12 固定标准包与兼容范围。79、81、82、83、84 承担包、数据保护、CI、许可和安装集成。发布及验收遵循已确认的 D2/D3/V1/V2 范围。[D11](../issues/11-test-replay-decision.md) · [D12](../issues/12-install-release-decision.md) · [来源测试基线](../../../docs/adr/0009-source-test-baseline.md) |

八个调查重点在[调查与决策覆盖](../coverage.md)逐项追踪。D08–D13 均已结题，22 张研究票和 49 条研究边有有效归属。产品历史 84 票及 177 条边，有效 79 票及 167 条边，依赖无环，逐票前置与图一致。805 个冻结成员逐字节摘要与清单一致，215 个验收母族均有责任票。[检查脚本](../evidence/b09-d14/audit-map.py) · [原始回执](../evidence/b09-d14/b09-d14-audit/stdout.bin)

批次 08 的自动出口在对应候选已实际取得。候选产品输入或权威矩阵改变时按真实证据重新校验。85 继续等待 D14、83、84 以及 77、78 的完整用户验收。早期 D06 的原型 IME 反馈和既有缩放、剪贴板回执按各自证据归档，最终产品的真实中文 IME 候选窗仍待验。研究收口与最终产品验收各读取对应记录。[自动出口证据](../../ruocun/evidence/b08-automatic/README.md) · [任务图](../../ruocun/dependencies.md)
